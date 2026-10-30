"""Read-only sampled historical BTS AirportID/code trajectory evidence.

Input: JSON profiles emitted from *official full-field* T-100 Table 293 for
distinct source years, each with source_airport_identity_pairs. The report
never infers AirportID from code and never claims exhaustive 1990-2026
coverage, warehouse impact, or changed route decisions.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path


def summarize(profiles: list[dict], expected_months: dict[int, list[int]] | None = None):
    if len(profiles) < 2:
        raise ValueError("Two or more official source years are required")
    by_year = {}
    by_code = defaultdict(lambda: defaultdict(set))
    by_id = defaultdict(lambda: defaultdict(lambda: {
        "codes": set(), "markets": set(), "countries": set()}))
    code_legs = defaultdict(int)
    code_deps = defaultdict(int)
    observed_pairs = 0

    for profile in profiles:
        year = profile.get("source_year")
        if not isinstance(year, int) or year in by_year:
            raise ValueError("Unique integer source years required")
        pairs = profile.get("source_airport_identity_pairs")
        sha = profile.get("source_zip_sha256")
        if (not isinstance(pairs, list) or not pairs
                or not isinstance(sha, str) or len(sha) != 64
                or any(c not in "0123456789abcdef" for c in sha.lower())):
            raise ValueError(f"Incomplete source-ID provenance: {year}")
        if profile.get("missing_source_id_endpoints") != 0:
            raise ValueError(f"Missing published source airport IDs: {year}")
        months = profile.get("observed_months", [])
        if sorted(set(months)) != months or not months or (
                expected_months is not None
                and months != expected_months.get(year)):
            raise ValueError(f"Incomplete or unexpected source-month coverage: {year}")
        by_year[year] = {"zip_sha256": sha,
                         "observed_months": months,
                         "source_rows": profile.get("source_rows"),
                         "scheduled_passenger_rows": profile.get(
                             "scheduled_passenger_rows"),
                         "scheduled_endpoints": profile.get(
                             "scheduled_origin_dest_endpoints")}
        for pair in pairs:
            code = pair.get("code")
            aid = pair.get("airport_id")
            cmid = pair.get("city_market_id")
            country = pair.get("country")
            if (not isinstance(code, str) or not code
                    or not isinstance(aid, int) or aid <= 0
                    or not isinstance(cmid, int) or cmid <= 0
                    or not isinstance(country, str) or not country):
                raise ValueError(f"Invalid published identity pair: {year}")
            legs = pair.get("endpoint_segment_passenger_legs")
            deps = pair.get("endpoint_departures")
            if (not isinstance(legs, int) or not isinstance(deps, int)
                    or legs < 0 or deps < 0):
                raise ValueError(f"Invalid source traffic on identity pair: {year}")
            by_code[code][year].add(aid)
            id_y = by_id[aid][year]
            id_y["codes"].add(code)
            id_y["markets"].add(cmid)
            id_y["countries"].add(country)
            code_legs[(code, year)] += legs
            code_deps[(code, year)] += deps
            observed_pairs += 1

    years = sorted(by_year)
    code_reuse = []
    for code, by_code_year in sorted(by_code.items()):
        different_ids = set().union(*by_code_year.values())
        if len(different_ids) > 1:
            code_reuse.append({
                "code": code,
                "airport_ids_all_sampled_years": sorted(different_ids),
                "years": [{
                    "year": year, "airport_ids": sorted(ids),
                    "endpoint_segment_passenger_legs": code_legs[code, year],
                    "endpoint_departures": code_deps[code, year],
                } for year, ids in sorted(by_code_year.items())]
            })
    renames, reassigned_markets, country_changes = [], [], []
    for aid, by_id_year in sorted(by_id.items()):
        codes = set().union(*(v["codes"] for v in by_id_year.values()))
        markets = set().union(*(v["markets"] for v in by_id_year.values()))
        countries = set().union(*(v["countries"] for v in by_id_year.values()))
        detail = [{
            "year": year, "codes": sorted(value["codes"]),
            "city_market_ids": sorted(value["markets"]),
            "countries": sorted(value["countries"]),
        } for year, value in sorted(by_id_year.items())]
        if len(codes) > 1:
            renames.append({"stable_airport_id": aid, "observations": detail})
        if len(markets) > 1:
            reassigned_markets.append({
                "stable_airport_id": aid, "observations": detail})
        if len(countries) > 1:
            country_changes.append({
                "stable_airport_id": aid, "observations": detail})

    return {
        "scope": "SAMPLED official T-100 source years only; not complete history",
        "sampled_years": years,
        "source_evidence_by_year": {str(y): by_year[y] for y in years},
        "source_identity_pair_records": observed_pairs,
        "distinct_airport_code_strings": len(by_code),
        "distinct_stable_airport_ids": len(by_id),
        "code_reused_by_distinct_stable_ids": code_reuse,
        "same_stable_airport_id_different_codes": renames,
        "same_stable_airport_id_different_city_markets": reassigned_markets,
        "same_stable_airport_id_different_countries": country_changes,
        "source_stable_ids_not_imputed": True,
        "full_year_by_year_1990_to_2026_checked": False,
        "original_warehouse_compared": False,
        "screen_or_replay_deltas_measured": False,
        "caution": ("Year subsets are nonconsecutive. Distinct IDs for the same "
                    "code across sampled years flag possible historic code reuse; "
                    "traffic is endpoint segment legs, never ticket O&D or "
                    "proof of production misassignment."),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--profile", action="append", required=True, type=Path,
                   help="Repeat for each independently sourced full-field year")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    out = args.output.resolve()
    if out.exists() or out in [x.resolve() for x in args.profile]:
        p.error("Output must be new and distinct from every source profile")
    expected = {1990: list(range(1, 13)), 2018: list(range(1, 13)),
                2022: list(range(1, 13)), 2024: list(range(1, 13)),
                2026: list(range(1, 8))}
    reports = [json.loads(path.read_text(encoding="utf-8"))
               for path in args.profile]
    result = summarize(reports, expected_months=expected)
    if result["sampled_years"] != sorted(expected):
        p.error("Expected exactly the five study-scope research vintages")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps({
        "sampled_years": result["sampled_years"],
        "codes_with_different_ids_across_years": len(
            result["code_reused_by_distinct_stable_ids"]),
        "stable_ids_with_multiple_codes": len(
            result["same_stable_airport_id_different_codes"]),
        "stable_ids_with_multiple_markets": len(
            result["same_stable_airport_id_different_city_markets"]),
        "original_warehouse_compared": False,
    }, indent=2))


if __name__ == "__main__":
    main()
