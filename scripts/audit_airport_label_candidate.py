"""Read-only Mac warehouse counterfactual for proposed AirportID/label pairing.

This is NOT a production rebuild or a 200-screen/463-replay rerun.
It projects the deterministic candidate from the local archived lookup
and compares all stored dim_airport codes and market IDs/names in memory.
Only small reports are created outside the project repository.

Usage:
  python -m scripts.audit_airport_label_candidate \
    --root "$HOME/Projects/network-lab" \
    --output-dir "$HOME/Desktop/NetworkLab-Label-Review-YYYYMMDD"
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path

EXPECTED_PREVIOUS_MISMATCH_CODES = frozenset({
    "BAT", "BDN", "BGN", "ISL", "KMC",
    "LAC", "LOM", "NEU", "SAW", "TIC",
})
STUDY_COUNTS = {"westjet_yyc": 76, "alaska_sea": 45, "porter_yyz": 79}
STUDIES = tuple(STUDY_COUNTS)


def sha256_small(path: Path, max_bytes: int = 10_000_000):
    if not path.is_file() or path.stat().st_size > max_bytes:
        return None
    d = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            d.update(block)
    return d.hexdigest()


def project_labels(con, lookup: Path) -> list[dict]:
    """Audit only: no CREATE, UPDATE or DELETE, no read of large fact tables."""
    columns = {row[0] for row in con.execute("DESCRIBE dim_airport").fetchall()}
    needed = {"iata_code", "city_market_id", "city_market_name"}
    if missing := sorted(needed - columns):
        raise ValueError(f"Required dim_airport columns absent: {missing}")
    sql = """
        WITH mc_ranked AS (
            SELECT AIRPORT AS code, CITY_MARKET_ID AS market_id,
                   DISPLAY_CITY_MARKET_NAME_FULL AS market_name,
                   ROW_NUMBER() OVER (
                       PARTITION BY AIRPORT
                       ORDER BY CITY_MARKET_ID DESC NULLS LAST,
                                DISPLAY_CITY_MARKET_NAME_FULL ASC NULLS LAST,
                                AIRPORT_ID DESC NULLS LAST
                   ) AS rn
            FROM read_parquet(?)
            WHERE AIRPORT_IS_LATEST = 'true'
               OR AIRPORT_IS_LATEST = '1'
        )
        SELECT a.iata_code,
               CAST(a.city_market_id AS VARCHAR) AS stored_market_id,
               a.city_market_name AS stored_market_name,
               CAST(m.market_id AS VARCHAR) AS candidate_market_id,
               m.market_name AS candidate_market_name
        FROM dim_airport a
        LEFT JOIN mc_ranked m ON m.code = a.iata_code AND m.rn = 1
        ORDER BY a.iata_code NULLS FIRST
    """
    cur = con.execute(sql, [str(lookup)])
    columns = [x[0] for x in cur.description]
    return [dict(zip(columns, row)) for row in cur.fetchall()]


def direct_screen_exposure(root: Path, changed_codes: set[str]):
    output = {}
    for study in STUDIES:
        path = root / "data" / "parquet" / "outputs" / f"screen_{study}.csv"
        if not path.is_file():
            output[study] = {"checked": False, "reason": "CSV not present"}
            continue
        with path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or "dest_airport" not in reader.fieldnames:
                output[study] = {"checked": False, "reason": "dest_airport missing"}
                continue
            rows = list(reader)
        hits = sorted({(r.get("dest_airport") or "").strip() for r in rows}
                      & changed_codes)
        output[study] = {
            "checked": True, "published_rows": len(rows),
            "direct_changed_destination_codes": hits,
            "sha256": sha256_small(path),
        }
    return output


def analyze_rows(rows: list[dict], root: Path, lookup: Path, warehouse: Path):
    codes = [r["iata_code"] for r in rows]
    nonnull_codes = [x for x in codes if x is not None]
    duplicates = sorted(c for c, n in Counter(nonnull_codes).items() if n > 1)
    changed_ids = [
        r for r in rows if r["stored_market_id"] != r["candidate_market_id"]
    ]
    changed_names = [
        r for r in rows if r["stored_market_name"] != r["candidate_market_name"]
    ]
    missing_candidate = [
        r["iata_code"] for r in rows if r["stored_market_id"] is not None
        and r["candidate_market_id"] is None
    ]
    changed_codes = {r["iata_code"] for r in changed_names}
    unexpected = sorted(changed_codes - EXPECTED_PREVIOUS_MISMATCH_CODES)
    unresolved_expected = sorted(EXPECTED_PREVIOUS_MISMATCH_CODES - changed_codes)
    screen = direct_screen_exposure(root, changed_codes)
    exact_200_screen_readback = all(
        screen[study].get("checked")
        and screen[study].get("published_rows") == STUDY_COUNTS[study]
        for study in STUDIES
    )
    model_change_measured = False

    # Source-local candidate preflight only: pass means 8,802 code+numeric
    # market mappings can be projected without changing numeric IDs.
    # Never imply it proves regenerated model and replay outputs are equal.
    gate_pass = (not duplicates and not changed_ids and not missing_candidate
                 and not unexpected and not unresolved_expected
                 and len(rows) == 8802
                 and exact_200_screen_readback
                 and all(not x["direct_changed_destination_codes"]
                         for x in screen.values()))
    return {
        "scope": "READ-ONLY warehouse dimension candidate, not regenerated model",
        "result": "PASS_DIMENSION_PROJECTION" if gate_pass else "REVIEW_REQUIRED",
        "warehouse_bytes": warehouse.stat().st_size,
        "source_lookup_sha256": sha256_small(lookup),
        "dimension_airport_rows": len(rows),
        "duplicate_nonnull_airport_codes": duplicates,
        "numeric_market_id_change_count": len(changed_ids),
        "numeric_market_id_changes": changed_ids[:150],
        "candidate_label_change_count": len(changed_names),
        "candidate_label_changes": changed_names,
        "stored_nonnull_id_without_source": missing_candidate,
        "unexpected_name_changes_vs_oct29_audit": unexpected,
        "oct29_audit_codes_no_longer_changed": unresolved_expected,
        "screen_direct_destination_exposure": screen,
        "prior_expected_name_mismatches": sorted(EXPECTED_PREVIOUS_MISMATCH_CODES),
        "candidate_warehouse_written": False,
        "screen_outputs_regenerated": False,
        "463_historical_replay_decisions_recomputed": False,
        "full_200_screen_model_parity_certified": model_change_measured,
        "historical_source_airport_id_correctness_certified": False,
        "interpretation": (
            "PASS_DIMENSION_PROJECTION permits review of the patch's chosen "
            "CityMarketID/name pairs ONLY; it does not authorize changing "
            "the preserved warehouse or certify route or replay parity."
        ),
    }


def summarize(result: dict) -> str:
    return "\n".join([
        "# Read-only airport-label candidate projection",
        "",
        f"- Result: **{result['result']}**",
        f"- Original dimension airport rows: {result['dimension_airport_rows']:,}",
        f"- Numeric CityMarketID changes: {result['numeric_market_id_change_count']}",
        f"- Proposed city-market name changes: {result['candidate_label_change_count']}",
        f"- Unexpected label changes compared with Oct 29 original audit: "
        f"{len(result['unexpected_name_changes_vs_oct29_audit'])}",
        f"- Missing expected original mismatch codes: "
        f"{len(result['oct29_audit_codes_no_longer_changed'])}",
        "",
        "**Important:** The original DuckDB was opened read-only. No warehouse "
        "copy, in-place patch, source download, full screen regeneration or "
        "historical replay was executed.",
        "",
        "A dimension-projection pass is **not** a full output-parity certificate.",
        "Inspect the JSON and CSV before proceeding with any separate build.",
        "",
    ]) + "\n"


def audit(root: Path):
    import duckdb

    root = root.expanduser().resolve()
    warehouse = root / "data" / "warehouse.duckdb"
    lookup = root / "data" / "parquet" / "lookups" / "master_coord.parquet"
    for path in (warehouse, lookup):
        if not path.is_file():
            raise FileNotFoundError(path)
    con = duckdb.connect(str(warehouse), read_only=True)
    try:
        con.execute("SET threads = 2")
        rows = project_labels(con, lookup)
    finally:
        con.close()
    return analyze_rows(rows, root, lookup, warehouse)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path,
                   default=Path.home() / "Projects" / "network-lab")
    p.add_argument("--output-dir", type=Path)
    args = p.parse_args()
    root = args.root.expanduser().resolve()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = (args.output_dir or (Path.home() / "Desktop" /
            f"NetworkLab-Label-Preflight-{stamp}")).expanduser().resolve()
    if dest.exists() or dest == root or root in dest.parents:
        p.error("Output must be new and outside the original project repository")
    result = audit(root)
    dest.mkdir(parents=True, exist_ok=False)
    (dest / "candidate_label_audit.json").write_text(
        json.dumps(result, sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8")
    with (dest / "candidate_label_changes.csv").open(
            "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "iata_code", "stored_market_id", "stored_market_name",
            "candidate_market_id", "candidate_market_name"])
        writer.writeheader()
        writer.writerows(result["candidate_label_changes"])
    (dest / "README.md").write_text(summarize(result), encoding="utf-8")
    print("Report folder:", dest)
    print("Status:", result["result"])
    print("No original data or model output was modified.")
    if result["result"] != "PASS_DIMENSION_PROJECTION":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
