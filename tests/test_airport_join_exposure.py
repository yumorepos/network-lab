"""Regression coverage and negative controls for audit evidence boundaries."""
from __future__ import annotations

from scripts.audit_airport_join_exposure import (
    audit, code_join_loss_by_code,
)


def test_published_screen_inventory_and_reference_exposure():
    result = audit()
    assert result["per_study_count"] == {
        "westjet_yyc": 76, "alaska_sea": 45, "porter_yyz": 79,
    }
    assert result["row_count"] == 200
    assert result["direct_PBI_DJT_destinations"] == []
    hits = result["PBI_DJT_incumbent_reference_rows"]
    assert any(
        r["study"] == "porter_yyz"
        and r["sample_airport"] == "PBI"
        and "Miami-Fort Lauderdale-West Palm Beach" in r["metro"]
        for r in hits
    )
    assert all(x["all_patterns_present"] for x in result["join_exposure_paths"].values())


def test_no_unmeasured_verdict_or_warehouse_impact_is_claimed():
    result = audit()
    assert result["route_verdict_delta_measured"] is False
    assert result["raw_warehouse_impact_measured"] is False
    assert "UNRESOLVED" in result["disposition"]


def test_negative_control_code_only_join_drops_historical_pbi():
    latest_codes = {"DJT"}  # intentionally incomplete latest-code fixture
    assert code_join_loss_by_code("PBI", latest_codes) is True
    # A stable identifier survives the spelling change. Simulated AirportID.
    historic_airport_id = 14307  # synthetic fixture, NOT a BTS identifier
    latest_id_mapping = {historic_airport_id: "DJT"}
    assert latest_id_mapping[historic_airport_id] == "DJT"
    assert code_join_loss_by_code("DJT", latest_codes) is False
