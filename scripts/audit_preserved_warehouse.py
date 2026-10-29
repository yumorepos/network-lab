"""Audit the preserved private Network Lab warehouse without modifying it.

Usage on the Mac that holds ~/Projects/network-lab:
  .venv/bin/python -m scripts.audit_preserved_warehouse

Produces a small, human-readable report under ~/Desktop/NetworkLab-Audit-*.
Does NOT run make, download data, rebuild anything, or modify the warehouse.
The report is evidence of detected join issues, not certification of source
completeness or a reason to change route verdicts.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import platform

import duckdb

from scripts.audit_warehouse_mapping import examine

ROOT = Path(__file__).resolve().parents[1]


def inventory(root: Path) -> dict:
    """Read filenames/sizes only; never hash gigabyte archives or follow symlinks."""
    result = {}
    for part in ("raw", "parquet"):
        source = root / "data" / part
        files = [p for p in source.rglob("*") if p.is_file() and not p.is_symlink()] if source.is_dir() else []
        by_suffix = Counter(p.suffix.lower() or "(no suffix)" for p in files)
        result[part] = {
            "exists": source.is_dir(),
            "file_count": len(files),
            "bytes": sum(p.stat().st_size for p in files),
            "extension_counts": dict(sorted(by_suffix.items())),
        }
    return result


def _table_stats(con: duckdb.DuckDBPyConnection) -> dict:
    names = {x[0] for x in con.execute("SHOW TABLES").fetchall()}
    checks = ("dim_airport", "dim_carrier", "dim_metro_us", "dim_metro_ca",
              "map_ca_airport_metro", "map_citymarket_cbsa", "fact_segment",
              "fact_od_market", "fact_od_transborder_2018",
              "fact_ca_airport", "fact_costs", "fact_fuel")
    result = {}
    for table in checks:
        result[table] = (
            int(con.execute(f"SELECT count(*) FROM {table}").fetchone()[0])
            if table in names else None
        )
    return result


def _year_month_gaps(months: list[dict]) -> list[str]:
    """Flag internal date gaps; do not mistake intentional scope gaps for errors."""
    observed = sorted({
        (int(m["year"]), int(m["month"]))
        for m in months if m.get("year") and m.get("month")
    })
    if not observed:
        return []
    year, month = observed[0]
    end = observed[-1]
    missing = []
    observed_set = set(observed)
    while (year, month) <= end:
        if (year, month) not in observed_set:
            missing.append(f"{year:04d}-{month:02d}")
        month += 1
        if month > 12:
            month = 1
            year += 1
    return missing


def _small_tracked_hashes(root: Path) -> dict:
    """Fingerprint ONLY small public outputs, not private warehouse or raw data."""
    out = {}
    paths = [root / "data/parquet/outputs/headline_metrics.yaml"]
    for study in ("westjet_yyc", "alaska_sea", "porter_yyz"):
        paths += [root / "data/parquet/outputs" / f"screen_{study}.csv",
                  root / "data/parquet/outputs" / f"screen_{study}.parquet"]
    for p in paths:
        key = p.relative_to(root).as_posix()
        if p.is_file() and 0 < p.stat().st_size < 2_000_000:
            out[key] = hashlib.sha256(p.read_bytes()).hexdigest()
        else:
            out[key] = None
    return out


def audit_preserved(root: Path) -> dict:
    """Read-only audit: never mutate source, leave route verdicts untouched."""
    root = root.expanduser().resolve()
    warehouse = root / "data/warehouse.duckdb"
    if not warehouse.is_file():
        raise FileNotFoundError(f"Preserved warehouse missing at {warehouse}")
    con = duckdb.connect(str(warehouse), read_only=True)
    try:
        # Avoid high parallel memory or transient spill during large aggregations.
        con.execute("SET threads = 2")
        tables = _table_stats(con)
        lookup = root / "data/parquet/lookups/master_coord.parquet"
        mapping = examine(con, lookup)
    finally:
        con.close()
    counts = inventory(root)
    gaps = _year_month_gaps(mapping["t100_month_coverage"])
    return {
        "scope": "preserved local data inventory and read-only built warehouse audit",
        "warehouse_exists": True,
        "warehouse_bytes": warehouse.stat().st_size,
        "platform": platform.platform(),
        "source_inventory": counts,
        "warehouse_table_rows": tables,
        "mapping_diagnostics": mapping,
        "t100_internal_missing_months_for_review": gaps,
        "tracked_output_sha256": _small_tracked_hashes(root),
        "full_external_source_completeness_verified": False,
        "source_manifest_hashes_verified": False,
        "cross_vintage_airport_id_correctness_verified": False,
        "historical_model_replay_regenerated": False,
        "production_verdict_delta_measured": False,
        "recommended_status": "REVIEW DIAGNOSTICS: NO MODEL OR DATA CHANGES AUTHORIZED",
    }


def summarize(report: dict) -> str:
    mapping = report["mapping_diagnostics"]
    unmatched = mapping["unmatched_us_segment_airport_by_year"]
    fanout = mapping["city_market_fanout_to_cbsa"]
    reuse = mapping.get("ambiguous_latest_airport_lookup")
    mismatched_labels = mapping.get("airport_dim_market_label_mismatches")
    rows = report["warehouse_table_rows"]
    raw = report["source_inventory"]["raw"]
    pq = report["source_inventory"]["parquet"]
    lines = [
        "# Network Lab preserved-data audit",
        "",
        "This was run against a local DuckDB database opened read-only.",
        "No official sources were redownloaded, no model was recomputed,",
        "and no route verdicts were updated.",
        "",
        f"- Warehouse size: {report['warehouse_bytes']:,} bytes.",
        f"- Raw files: {raw['file_count']:,}; {raw['bytes']:,} bytes.",
        f"- Parquet-tree files: {pq['file_count']:,}; {pq['bytes']:,} bytes.",
        f"- fact_segment rows: {rows['fact_segment']:,}." if rows['fact_segment'] is not None else "- fact_segment table MISSING.",
        f"- fact_od_market rows: {rows['fact_od_market']:,}." if rows['fact_od_market'] is not None else "- fact_od_market table MISSING.",
        f"- Unmatched US airport-code/year/side entries (top 100): {len(unmatched)}.",
        f"- Duplicate city-market-to-CBSA keys: {len(fanout)}.",
        f"- Ambiguous current lookup codes: {len(reuse) if reuse is not None else 'NOT CHECKED (lookup file missing)'}.",
        f"- Stored airport ID/name inconsistencies against lookup: {len(mismatched_labels) if mismatched_labels is not None else 'NOT CHECKED (label/lookup unavailable)'}.",
        f"- Internal T-100 monthly gaps to review: {len(report['t100_internal_missing_months_for_review'])}.",
        "",
        "## Important interpretation",
        "",
        "Unmatched passenger counts are T-100 passenger-legs, not ticket O&D.",
        "A zero in a diagnostic is not proof that a source never contained missing rows.",
        "Carrier reporting and historical airport-ID changes require independent",
        "source-vintage checks. Downloaded source completeness and end-to-end",
        "replay are NOT certified by this read-only audit.",
        "",
        "Inspect the companion JSON for every observed anomaly.",
        "Do not patch airport codes, carrier brands, or published route verdicts",
        "until a before/after consumer-impact evaluation has been completed.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.home() / "Projects/network-lab")
    parser.add_argument("--output-dir", type=Path,
                        help="New report directory, default Desktop timestamp")
    args = parser.parse_args()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = args.output_dir or (Path.home() / "Desktop" / f"NetworkLab-Audit-{stamp}")
    # Refuse to overwrite a report, and never write inside the source repository.
    root = args.root.expanduser().resolve()
    target = target.expanduser().resolve()
    if target == root or root in target.parents:
        raise SystemExit("Output cannot be inside the project repository")
    if target.exists():
        raise SystemExit(f"Output already exists; refusing overwrite: {target}")
    result = audit_preserved(root)  # no report directory created on failure
    target.mkdir(parents=True, exist_ok=False)
    (target / "audit_summary.md").write_text(summarize(result), encoding="utf-8")
    (target / "audit_diagnostics.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8")
    print(f"Read-only audit complete. Reports in: {target}")
    print("No production correction or source-completeness certification claimed.")


if __name__ == "__main__":
    main()
