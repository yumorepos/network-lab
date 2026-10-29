"""Read-only source-side metro mapping diagnostic, no DuckDB warehouse required.

Replays the current name/token/override/population selection against the two
small archived Parquet inputs. It does NOT certify production mart rows or
change any maps, models, replay, or published screening results.

Usage:
  python -m scripts.audit_metro_source_preflight \
    --lookup data/parquet/lookups/master_coord.parquet \
    --metros data/parquet/census/metro_pop_income.parquet \
    --source warehouse/metro_map.py \
    --output /tmp/networklab-metro-preflight.json
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


def overrides_from_source(path: Path) -> dict[str, str]:
    """Extract the project's actual literal OVERRIDES without running build code."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "OVERRIDES" for t in node.targets
        ):
            val = ast.literal_eval(node.value)
            if not isinstance(val, dict) or not all(
                isinstance(k, str) and isinstance(v, str) for k, v in val.items()
            ):
                raise ValueError("OVERRIDES must be a literal string dictionary")
            return val
    raise ValueError("OVERRIDES not found")


def city_tokens(name: str):
    name = re.sub(r"\s*\(Metropolitan Area\)", "", name).strip()
    if "," not in name:
        return [name.lower()], ""
    cities, state = name.rsplit(",", 1)
    return [x.strip().lower() for x in cities.split("/")], state.strip()


def cbsa_tokens(name: str):
    if "," not in name:
        return [name.lower()], []
    cities, states = name.rsplit(",", 1)
    return ([x.strip().lower() for x in cities.split("-")],
            [x.strip() for x in states.split("-")])


def choose(cm_name: str, metros: list[dict], overrides: dict[str, str]):
    """Return the exact candidate set and evidence-bound selection disposition."""
    target = overrides.get(cm_name)
    if target is not None:
        hits = [m for m in metros if m["name"].startswith(target)]
        if len(hits) == 1:
            return "override", hits, hits[0]
        if len(hits) > 1:
            return "ambiguous_override", hits, None
        # The legacy code falls through to tokens; document the failed pin.
    tokens, state = city_tokens(cm_name)
    hits = [m for m in metros if
            (not state or state in cbsa_tokens(m["name"])[1])
            and any(t in cbsa_tokens(m["name"])[0] for t in tokens)]
    if not hits:
        return ("missing_override" if target is not None else "unmatched"), [], None
    non_null = sorted(
        [m for m in hits if m["population"] is not None],
        key=lambda m: m["population"], reverse=True,
    )
    if not non_null:
        return "no_population", hits, None
    top = [m for m in non_null if m["population"] == non_null[0]["population"]]
    if len(top) > 1:
        return "population_tie", hits, None
    status = "override_fell_through" if target is not None else (
        "ambiguous_population_choice" if len(hits) > 1 else "token"
    )
    return status, hits, non_null[0]


def examine(lookup_records: list[dict], metro_records: list[dict],
            overrides: dict[str, str]) -> dict:
    """Pure, independently testable audit; input records already normalized."""
    source = defaultdict(set)
    for r in lookup_records:
        if r.get("country") == "US" and r.get("latest"):
            if r.get("city_market_id") is not None and r.get("name"):
                source[str(r["city_market_id"])].add(str(r["name"]))
    counters = Counter()
    collisions = []
    multi_name = []
    for cmid in sorted(source):
        names = source[cmid]
        if len(names) > 1:
            multi_name.append({"city_market_id": cmid, "names": sorted(names)})
        for name in sorted(names):
            status, candidates, chosen = choose(name, metro_records, overrides)
            counters[status] += 1
            if (len(candidates) > 1 or status in {
                    "missing_override", "override_fell_through",
                    "population_tie", "ambiguous_override", "no_population"}):
                collisions.append({
                    "city_market_id": cmid, "name": name, "status": status,
                    "candidates": [
                        {"cbsa": str(c["cbsa"]), "name": c["name"],
                         "population": c["population"]}
                        for c in candidates
                    ],
                    "chosen": None if chosen is None else str(chosen["cbsa"]),
                    "source_only_not_warehouse_verified": True,
                })
    return {
        "scope": "Source reconstruction only, not warehouse or replay evidence",
        "unique_source_city_market_ids": len(source),
        "source_id_multiple_names": multi_name,
        "metros_count": len(metro_records),
        "statuses": dict(sorted(counters.items())),
        "ambiguous_or_override_cases": collisions,
        "production_verdict_change_verified": False,
        "candidate_population_recomputed": False,
    }


def read_inputs(lookup_path: Path, metro_path: Path):
    import pandas as pd
    lookup = pd.read_parquet(lookup_path)
    metros = pd.read_parquet(metro_path)
    required_lookup = {"CITY_MARKET_ID", "DISPLAY_CITY_MARKET_NAME_FULL",
                       "AIRPORT_COUNTRY_CODE_ISO", "AIRPORT_IS_LATEST"}
    required_metro = {"cbsa", "name", "population"}
    if missing := required_lookup - set(lookup.columns):
        raise ValueError("Missing Master Coordinate fields: " + ", ".join(sorted(missing)))
    if missing := required_metro - set(metros.columns):
        raise ValueError("Missing derived metro fields: " + ", ".join(sorted(missing)))
    a = [{"city_market_id": row.CITY_MARKET_ID,
          "name": row.DISPLAY_CITY_MARKET_NAME_FULL,
          "country": row.AIRPORT_COUNTRY_CODE_ISO,
          "latest": str(row.AIRPORT_IS_LATEST).strip().lower() in ("true", "1")}
         for row in lookup.itertuples(index=False)]
    b = [{"cbsa": str(row.cbsa), "name": str(row.name),
          "population": None if pd.isna(row.population) else float(row.population)}
         for row in metros.itertuples(index=False)]
    return a, b


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--lookup", type=Path, required=True)
    p.add_argument("--metros", type=Path, required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    sources = [args.lookup.resolve(), args.metros.resolve(), args.source.resolve()]
    for src in sources:
        if not src.is_file():
            p.error("Missing source: " + str(src))
    out = args.output.resolve()
    if out.exists() or any(out == src or out.is_relative_to(src.parent) for src in sources):
        p.error("Output must be new and outside input source directories")
    result = examine(*read_inputs(args.lookup, args.metros),
                     overrides_from_source(args.source))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Source-side metro preflight:", result["statuses"], "->", out)


if __name__ == "__main__":
    main()
