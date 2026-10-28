"""Warehouse-free regression checks for published route-economics arithmetic.

These tests reconcile the committed per-market screen artifacts. They do NOT
independently validate cost, fare, demand, or comparator data in DuckDB.
No production model or scenario-grid values are changed by this audit.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

import pytest

OUTPUTS = Path("data/parquet/outputs")
STUDIES = ("westjet_yyc", "alaska_sea", "porter_yyz")


def _screen_rows(study_id: str) -> list[dict[str, str]]:
    path = OUTPUTS / f"screen_{study_id}.csv"
    assert path.is_file(), f"committed screen artifact missing: {path}"
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@pytest.mark.parametrize("study_id", STUDIES)
def test_published_margin_matches_belf_over_load_factor(study_id: str):
    """Because margin=(revenue-cost)/revenue and BELF=cost/(fare*seats),
    margin % must equal 100*(1 - BELF/LF) at a single chosen schedule.
    This catches unit, sign, scale and dashboard-artifact mismatches.
    """
    rows = _screen_rows(study_id)
    assert rows, f"{study_id}: empty screen artifact"
    for row in rows:
        market = row["metro_name"]
        lf = float(row["load_factor"])
        belf = float(row["belf"])
        margin = float(row["margin_pct"])
        share = float(row["proposed_share"])
        demand = float(row["demand_pax_yr"])
        assert all(math.isfinite(v) for v in (lf, belf, margin, share, demand)), market
        assert 0 < lf <= 1, f"{study_id} / {market}: invalid LF"
        assert belf > 0, f"{study_id} / {market}: invalid BELF"
        assert 0 <= share <= 1, f"{study_id} / {market}: invalid share"
        assert demand >= 0, f"{study_id} / {market}: invalid demand"
        derived_margin = 100 * (1 - belf / lf)
        assert margin == pytest.approx(derived_margin, abs=1e-7), (
            f"{study_id} / {market}: margin, LF and BELF disagree"
        )


@pytest.mark.parametrize("study_id", STUDIES)
def test_published_low_load_and_negative_verdicts_are_not_positive(study_id: str):
    """The currently shipped screens must not advertise a sub-floor or
    negative-margin schedule as LAUNCH/MONITOR. PASS means reject, not pass."""
    for row in _screen_rows(study_id):
        lf = float(row["load_factor"])
        margin = float(row["margin_pct"])
        verdict = row["verdict"]
        if lf < 0.50 or margin < 0:
            assert verdict == "PASS", (study_id, row["metro_name"], verdict)


def test_albany_extreme_margin_is_explained_by_sparse_bidirectional_load():
    """Golden case: the published Albany margin is a denominator effect,
    not proof of a -100% bound violation. A 3x weekly schedule means 312
    departures/year across both directions, NOT 156.
    """
    matches = [
        row for row in _screen_rows("westjet_yyc")
        if row["metro_name"] == "Albany-Schenectady-Troy, NY"
    ]
    assert len(matches) == 1
    row = matches[0]
    departures = int(row["chosen_freq_wk"]) * 52 * 2
    seats = int(row["chosen_seats"])
    carried_year = float(row["demand_pax_yr"]) * float(row["proposed_share"])
    passengers_per_departure = carried_year / departures
    expected_lf = passengers_per_departure / seats
    # At 11 expected boardings in a 174-seat aircraft, finite-capacity spill
    # is negligible; this is a bounded, market-specific identity check.
    assert departures == 312
    assert expected_lf == pytest.approx(float(row["load_factor"]), rel=1e-8)
    assert passengers_per_departure == pytest.approx(10.6577428582, rel=1e-6)
    assert float(row["load_factor"]) < 0.07
    assert float(row["belf"]) > 0.70
    assert float(row["margin_pct"]) < -1000
    assert row["verdict"] == "PASS"
    assert row["share_uncertainty"] == "True"
