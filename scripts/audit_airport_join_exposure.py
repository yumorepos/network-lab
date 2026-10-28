"""Read-only, warehouse-free airport identity exposure audit.

This script intentionally does not estimate changed route verdicts. That
requires an archived production warehouse, a versioned lookup, full pipeline
rebuild and a before/after report. Stage B's live result is a separate
July 2026 experiment; it is NOT a measured effect on stored route screens.

Run:
    python -m scripts.audit_airport_join_exposure
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDIES = ("westjet_yyc", "alaska_sea", "porter_yyz")
CHANGED_CODES = {"PBI", "DJT"}


def _rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def audit(root: Path = ROOT) -> dict:
    """Inventory direct mentions and relevant join paths, without re-running a model."""
    screens = {
        study: _rows(root / "data/parquet/outputs" / f"screen_{study}.csv")
        for study in STUDIES
    }
    incumbents = _rows(root / "data/reference/incumbent_network_202604.csv")
    directly_named = [
        {"study": study, "market": row.get("metro_name", ""),
         "dest_airport": row.get("dest_airport", "")}
        for study, rows in screens.items() for row in rows
        if row.get("dest_airport", "").upper() in CHANGED_CODES
    ]
    reference_hits = [
        {"study": r["study_id"], "metro": r["dest_metro_name"],
         "sample_airport": r["sample_airport"],
         "source": r.get("source", "")}
        for r in incumbents
        if r.get("sample_airport", "").upper() in CHANGED_CODES
    ]
    paths = {
        "latest_code_to_market": (
            "warehouse/build_marts.py",
            ["max(CITY_MARKET_ID) AS city_market_id",
             "GROUP BY AIRPORT"]),
        "candidate_served_exclusion": (
            "models/candidates.py",
            ["JOIN dim_airport a2 ON a2.iata_code = s.dest",
             "JOIN map_citymarket_cbsa m ON m.city_market_id = a2.city_market_id"]),
        "competition_dest_airports": (
            "models/competition.py",
            ["JOIN dim_airport a ON a.city_market_id = m.city_market_id"]),
        "metro_traffic_mapping": (
            "warehouse/metro_map.py",
            ["JOIN dim_airport a ON a.iata_code = s.origin"]),
        "t100_persisted_only_airport_codes": (
            "ingest/bts_t100.py",
            ["ORIGIN AS origin", "DEST AS dest"]),
    }
    risk_paths = {}
    for k, (p, needles) in paths.items():
        src = (root / p).read_text(encoding="utf-8")
        risk_paths[k] = {"file": p,
                         "all_patterns_present": all(s in src for s in needles)}
    return {
        "source": "committed outputs/reference and repo code as of audit",
        "row_count": sum(len(rows) for rows in screens.values()),
        "per_study_count": {k: len(v) for k, v in screens.items()},
        "direct_PBI_DJT_destinations": directly_named,
        "PBI_DJT_incumbent_reference_rows": reference_hits,
        "join_exposure_paths": risk_paths,
        "route_verdict_delta_measured": False,
        "raw_warehouse_impact_measured": False,
        "disposition": (
            "CODE-ONLY JOIN RISK CONFIRMED IN SOURCE; actual 2026 vintage "
            "and verdict effects UNRESOLVED; do not patch or claim zero impact"
        ),
    }


def code_join_loss_by_code(source_code: str, latest_codes: set[str]) -> bool:
    """Minimal negative-control example: historical codes can disappear."""
    return source_code not in latest_codes


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
