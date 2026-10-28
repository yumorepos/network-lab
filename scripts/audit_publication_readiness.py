"""Warehouse-free publication readiness checks over tracked reader-facing data.

Does NOT certify full source download completeness, warehouse joins or
historical point-in-time replay. Do NOT treat green CI as a data rebuild.
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path

import yaml

from scripts.audit_airport_join_exposure import STUDIES, ROOT

REQUIRED_SCREEN = {
    "study_id", "metro_name", "dest_airport", "verdict",
    "confidence", "chosen_freq_wk", "chosen_seats", "margin_pct",
    "belf", "load_factor", "proposed_share", "demand_pax_yr",
    "demand_source", "demand_method", "driver_service",
    "key_assumptions", "share_uncertainty", "n_nonstop_incumbents",
}
NUMERIC = ("margin_pct", "belf", "load_factor", "proposed_share",
           "demand_pax_yr", "chosen_freq_wk", "chosen_seats")
ALLOWED_VERDICTS = {"LAUNCH", "MONITOR", "PASS"}


def rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        names = reader.fieldnames or []
        return names, list(reader)


def evaluate_screen(study: str, data: list[dict], names: list[str],
                    expected: dict) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    missing_cols = REQUIRED_SCREEN - set(names)
    if missing_cols:
        errors.append(f"{study}: missing required columns {sorted(missing_cols)}")
        return {"rows": len(data), "errors": errors, "warnings": warnings}
    observed = Counter()
    seen_market: set[str] = set()
    seen_dest: set[str] = set()
    optional_missing = Counter()
    for i, row in enumerate(data, start=2):
        prefix = f"{study} row {i}"
        for name in ("study_id", "metro_name", "dest_airport", "confidence",
                     "demand_source", "demand_method", "driver_service",
                     "key_assumptions", "share_uncertainty"):
            if not (row.get(name) or "").strip():
                errors.append(f"{prefix}: blank {name}")
        if row["study_id"] != study:
            errors.append(f"{prefix}: study id mismatch")
        if row["metro_name"] in seen_market:
            errors.append(f"{prefix}: duplicated metro_name")
        seen_market.add(row["metro_name"])
        if row["dest_airport"] in seen_dest:
            errors.append(f"{prefix}: duplicated dest_airport")
        seen_dest.add(row["dest_airport"])
        verdict = row["verdict"]
        if verdict not in ALLOWED_VERDICTS:
            errors.append(f"{prefix}: unexpected verdict {verdict!r}")
        observed[verdict] += 1
        numeric = {}
        for k in NUMERIC:
            try:
                v = float(row[k])
                if not math.isfinite(v):
                    raise ValueError
                numeric[k] = v
            except (TypeError, ValueError, KeyError):
                errors.append(f"{prefix}: nonfinite or missing {k}")
        if len(numeric) == len(NUMERIC):
            lf, share, belf = (numeric["load_factor"],
                               numeric["proposed_share"], numeric["belf"])
            if not (0 < lf <= 1 and 0 <= share <= 1 and belf > 0):
                errors.append(f"{prefix}: physically invalid LF/share/BELF")
            if numeric["demand_pax_yr"] < 0 or numeric["chosen_freq_wk"] <= 0 or numeric["chosen_seats"] <= 0:
                errors.append(f"{prefix}: invalid demand, schedule or gauge")
            if lf and belf:
                derived = 100 * (1 - belf / lf)
                if abs(derived - numeric["margin_pct"]) > 1e-5:
                    errors.append(f"{prefix}: margin not reconciled")
            if (lf < 0.5 or numeric["margin_pct"] < 0) and verdict != "PASS":
                errors.append(f"{prefix}: optimistic verdict below load or margin floor")
            if share >= 0.9999 and not row.get("top_competitor", "").strip():
                warnings.append(
                    f"{prefix}: 100% modeled share, no named top competitor; "
                    "competition coverage not independently established"
                )
        for k in ("anchor_2018_pax", "implied_vs_anchor_ratio", "top_competitor"):
            if not (row.get(k) or "").strip():
                optional_missing[k] += 1
        if row["demand_source"] == "observed" and row.get("anchor_2018_pax"):
            warnings.append(f"{prefix}: observed DB1B with a transborder anchor field")
    exp_n = int(expected["n_candidates"])
    if len(data) != exp_n:
        errors.append(f"{study}: {len(data)} screen rows versus canonical {exp_n}")
    for v in ("LAUNCH", "MONITOR", "PASS"):
        if observed[v] != int(expected[v]):
            errors.append(f"{study}: {v} rows {observed[v]} versus canonical {expected[v]}")
    for v, field in (("LAUNCH", "launch_markets"), ("MONITOR", "monitor_markets")):
        actual = sorted(row["metro_name"] for row in data if row["verdict"] == v)
        if actual != sorted(expected[field]):
            errors.append(f"{study}: {v} market names disagree with headline")
    return {
        "rows": len(data), "verdicts": dict(observed),
        "missing_optional_field_rows": dict(optional_missing),
        "errors": errors, "warnings": warnings,
    }


def evaluate_carrier_reference(data: list[dict]) -> dict:
    """Contract checks only; brand relationships remain date-sensitive claims."""
    errors, warnings = [], []
    seen = set()
    for i, row in enumerate(data, start=2):
        op = row["operating_carrier"].strip()
        if not op or op in seen:
            errors.append(f"carrier_families row {i}: missing or duplicated operator")
        seen.add(op)
        partners = row["brand_partners"].split("|")
        if not partners or any(not p.strip() for p in partners) or len(partners) != len(set(partners)):
            errors.append(f"carrier_families row {i}: invalid partner set")
        typ = row["resolution"]
        if typ not in {"static", "db1b_per_segment"}:
            errors.append(f"carrier_families row {i}: unrecognized resolution")
        if typ == "static" and len(partners) != 1:
            errors.append(f"carrier_families row {i}: multi-brand static mapping")
        if typ == "db1b_per_segment" and len(partners) < 2:
            errors.append(f"carrier_families row {i}: single-brand multi mapping")
        if not row.get("source") or not row.get("db1b_evidence"):
            warnings.append(f"carrier_families row {i}: evidence/source missing")
    return {"operator_rows": len(data),
            "static": sum(r["resolution"] == "static" for r in data),
            "per_segment": sum(r["resolution"] == "db1b_per_segment" for r in data),
            "errors": errors, "warnings": warnings}


def audit(root: Path = ROOT) -> dict:
    headline = yaml.safe_load(
        (root / "data/parquet/outputs/headline_metrics.yaml").read_text())
    screens = {}
    for study in STUDIES:
        names, data = rows(root / "data/parquet/outputs" / f"screen_{study}.csv")
        screens[study] = evaluate_screen(study, data, names, headline["studies"][study])
    _, cr = rows(root / "data/reference/carrier_families.csv")
    carriers = evaluate_carrier_reference(cr)
    total = sum(s["rows"] for s in screens.values())
    errors = [e for s in screens.values() for e in s["errors"]] + carriers["errors"]
    if total != headline["n_candidates_total"]:
        errors.append(f"total {total} differs from canonical {headline['n_candidates_total']}")
    exposure = {
        "latest_airport_code_lookup": "warehouse/build_marts.py: max(CITY_MARKET_ID) by AIRPORT",
        "metro_crosswalk": "warehouse/metro_map.py: token/override selection, largest-CBSA fallback",
        "carrier_brand": "models/carriers.py: static mapping and DB1B per-segment lookup",
        "point_in_time": "2026 publication cannot be certified from a current lookup alone",
    }
    return {
        "scope": "tracked screen CSVs, canonical headline YAML and carrier mapping reference",
        "screen": screens,
        "carrier_reference": carriers,
        "candidate_total": total,
        "blocking_contract_errors": errors,
        "known_untested_mapping_paths": exposure,
        "raw_download_completeness_verified": False,
        "warehouse_mapping_completeness_verified": False,
        "csv_to_parquet_row_parity_verified": False,
        "historical_replay_recomputed": False,
        "public_dashboard_renders_verified": False,
        "publication_certification": (
            "BLOCKED: committed contract checks only, raw warehouse parity "
            "and actual source-completeness audit still required"
        ),
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
