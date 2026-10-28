"""Warehouse-free integrity checks for the published Streamlit artifacts.

These tests protect provenance visibility and counts; they do not evaluate
predictive validity, refresh history, or alter research results.
"""
from pathlib import Path

import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "parquet" / "outputs"
STUDIES = ("porter_yyz", "westjet_yyc", "alaska_sea")
EVIDENCE = {
    "study_id", "metro_name", "verdict", "confidence", "demand_source",
    "demand_method", "driver_1", "driver_2", "driver_service",
    "top_risk", "key_assumptions", "anchor_2018_pax",
    "share_uncertainty",
}


@pytest.fixture(scope="module")
def headline():
    return yaml.safe_load((OUT / "headline_metrics.yaml").read_text())["studies"]


@pytest.mark.parametrize("study", STUDIES)
def test_route_screen_counts_match_generated_headline(study, headline):
    csv = OUT / f"screen_{study}.csv"
    assert csv.is_file(), f"Committed dashboard screen missing: {csv}"
    screen = pd.read_csv(csv)
    expected = headline[study]
    actual = screen["verdict"].value_counts()
    assert len(screen) == expected["n_candidates"]
    assert len(screen) == screen["metro_name"].nunique()
    for verdict in ("LAUNCH", "MONITOR", "PASS"):
        assert int(actual.get(verdict, 0)) == int(expected[verdict])


@pytest.mark.parametrize("study", STUDIES)
def test_screen_carries_evidence_needed_for_dashboard(study):
    screen = pd.read_csv(OUT / f"screen_{study}.csv")
    assert not (EVIDENCE - set(screen.columns)), (
        f"Dashboard evidence columns missing in {study}: "
        f"{sorted(EVIDENCE - set(screen.columns))}"
    )
    for col in ("study_id", "metro_name", "verdict", "confidence",
                "demand_source", "demand_method", "driver_1", "driver_2"):
        assert screen[col].notna().all(), (study, col)
    assert (screen["study_id"] == study).all()
    assert screen["verdict"].isin(("LAUNCH", "MONITOR", "PASS")).all()


def test_dashboard_reads_committed_outputs_without_rescoring():
    src = (ROOT / "app" / "streamlit_app.py").read_text()
    assert 'OUT / name' in src
    assert 'st.expander("Data sources & verdict evidence")' in src
    assert 'evidence = scr.loc[scr["metro_name"] == mkt].iloc[0]' in src
