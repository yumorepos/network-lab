"""Warehouse-free screening and mapping-reference contract tests.

The negative controls intentionally break in-memory copies of real rows.
Passing here does not assert complete source coverage or replay parity.
"""
from __future__ import annotations

import csv
from pathlib import Path

import yaml

from scripts.audit_publication_readiness import (
    audit, evaluate_carrier_reference, evaluate_screen, rows,
)
from scripts.audit_airport_join_exposure import ROOT


def _westjet():
    _, data = rows(ROOT / "data/parquet/outputs/screen_westjet_yyc.csv")
    canon = yaml.safe_load(
        (ROOT / "data/parquet/outputs/headline_metrics.yaml").read_text())
    return data, canon["studies"]["westjet_yyc"]


def test_tracked_publication_contracts_no_errors():
    result = audit()
    assert result["blocking_contract_errors"] == [], result["blocking_contract_errors"]
    assert result["candidate_total"] == 200
    assert not result["raw_download_completeness_verified"]
    assert not result["warehouse_mapping_completeness_verified"]
    assert not result["csv_to_parquet_row_parity_verified"]
    assert not result["historical_replay_recomputed"]


def test_carrier_reference_contracts_are_valid():
    result = audit()["carrier_reference"]
    assert result["errors"] == [], result["errors"]
    assert result["operator_rows"] == result["static"] + result["per_segment"]


def test_negative_control_duplicate_candidate_is_rejected():
    data, canon = _westjet()
    corrupt = [dict(x) for x in data]
    corrupt[1]["metro_name"] = corrupt[0]["metro_name"]
    result = evaluate_screen("westjet_yyc", corrupt, list(corrupt[0]), canon)
    assert any("duplicated metro_name" in m for m in result["errors"])


def test_negative_control_wrong_verdict_and_headline_are_rejected():
    data, canon = _westjet()
    corrupt = [dict(x) for x in data]
    corrupt[0]["verdict"] = "LAUNCH"
    result = evaluate_screen("westjet_yyc", corrupt, list(corrupt[0]), canon)
    assert any("versus canonical" in m for m in result["errors"])


def test_negative_control_missing_required_provenance_is_rejected():
    data, canon = _westjet()
    corrupt = [dict(x) for x in data]
    corrupt[0]["demand_method"] = ""
    result = evaluate_screen("westjet_yyc", corrupt, list(corrupt[0]), canon)
    assert any("blank demand_method" in m for m in result["errors"])


def test_negative_control_corrupt_model_share_is_rejected():
    data, canon = _westjet()
    corrupt = [dict(x) for x in data]
    corrupt[0]["proposed_share"] = "1.1"
    result = evaluate_screen("westjet_yyc", corrupt, list(corrupt[0]), canon)
    assert any("invalid LF/share/BELF" in m for m in result["errors"])


def test_negative_control_duplicate_operating_carrier_is_rejected():
    _, values = rows(ROOT / "data/reference/carrier_families.csv")
    corrupt = [dict(v) for v in values]
    corrupt[1]["operating_carrier"] = corrupt[0]["operating_carrier"]
    result = evaluate_carrier_reference(corrupt)
    assert any("duplicated operator" in m for m in result["errors"])


def test_negative_control_static_multibrand_assignment_is_rejected():
    _, values = rows(ROOT / "data/reference/carrier_families.csv")
    corrupt = [dict(v) for v in values]
    first = next(r for r in corrupt if r["resolution"] == "static")
    first["brand_partners"] = "AA|UA"
    result = evaluate_carrier_reference(corrupt)
    assert any("multi-brand static mapping" in m for m in result["errors"])
