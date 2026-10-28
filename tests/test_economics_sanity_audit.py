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


def _assert_margin_row(study_id: str, row: dict[str, str]) -> None:
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


def _assert_verdict_row(study_id: str, row: dict[str, str]) -> None:
    lf = float(row["load_factor"])
    margin = float(row["margin_pct"])
    verdict = row["verdict"]
    if lf < 0.50 or margin < 0:
        assert verdict == "PASS", (study_id, row["metro_name"], verdict)


def _albany_row() -> dict[str, str]:
    matches = [
        row for row in _screen_rows("westjet_yyc")
        if row["metro_name"] == "Albany-Schenectady-Troy, NY"
    ]
    assert len(matches) == 1
    return matches[0]


def _assert_albany_row(row: dict[str, str]) -> None:
    departures = int(row["chosen_freq_wk"]) * 52 * 2
    seats = int(row["chosen_seats"])
    carried_year = float(row["demand_pax_yr"]) * float(row["proposed_share"])
    passengers_per_departure = carried_year / departures
    expected_lf = passengers_per_departure / seats
    # At roughly 11 boardings in 174 seats, modeled capacity spill is negligible.
    assert departures == 312
    assert expected_lf == pytest.approx(float(row["load_factor"]), rel=1e-8), (
        f"Albany load factor inconsistent: expected {expected_lf:.9f}, "
        f"published {float(row['load_factor']):.9f}"
    )
    assert passengers_per_departure == pytest.approx(10.6577428582, rel=1e-6)
    assert float(row["load_factor"]) < 0.07
    assert float(row["belf"]) > 0.70
    assert float(row["margin_pct"]) < -1000
    assert row["verdict"] == "PASS"
    assert row["share_uncertainty"] == "True"


@pytest.mark.parametrize("study_id", STUDIES)
def test_published_margin_matches_belf_over_load_factor(study_id: str):
    """Margin on revenue equals 100*(1 - BELF/LF) at the chosen schedule."""
    rows = _screen_rows(study_id)
    assert rows, f"{study_id}: empty screen artifact"
    for row in rows:
        _assert_margin_row(study_id, row)


@pytest.mark.parametrize("study_id", STUDIES)
def test_published_low_load_and_negative_verdicts_are_not_positive(study_id: str):
    """Sub-floor or negative-margin schedules must not advertise launch."""
    for row in _screen_rows(study_id):
        _assert_verdict_row(study_id, row)


def test_albany_extreme_margin_is_explained_by_sparse_bidirectional_load():
    """Three weekly one-way departures mean 312 annual bidirectional legs."""
    _assert_albany_row(_albany_row())


# Executable negative controls: intentionally corrupt in-memory copies, never
# the committed CSVs. Each test FAILS if the guard stops detecting its defect.

def test_negative_control_margin_discrepancy_is_rejected():
    row = dict(_albany_row())
    row["margin_pct"] = str(float(row["margin_pct"]) + 100.0)
    with pytest.raises(AssertionError, match="margin, LF and BELF disagree"):
        _assert_margin_row("westjet_yyc", row)


def test_negative_control_one_direction_load_factor_is_rejected():
    row = dict(_albany_row())
    # Reproduce the old unit error: only 156 annual departures rather than 312.
    row["load_factor"] = str(float(row["load_factor"]) * 2.0)
    with pytest.raises(AssertionError, match="Albany load factor inconsistent"):
        _assert_albany_row(row)


def test_negative_control_false_launch_verdict_is_rejected():
    row = dict(_albany_row())
    row["verdict"] = "LAUNCH"
    with pytest.raises(AssertionError):
        _assert_verdict_row("westjet_yyc", row)
