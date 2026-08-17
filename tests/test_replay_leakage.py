"""No-future-data guards for the W1.3 snapshot.

Every test here was demonstrated to FAIL when the corresponding leak is
deliberately reintroduced, not merely to pass now. The demonstration is
`scripts/demo_leakage_tests.py`, and its recorded output is in
docs/W1.4_REPLAY_PROTOCOL.md. This is the explicit lesson of integrity round 4:
a test that has never been shown to fail is a test of nothing.

The injections used to prove each guard bites are named in the test docstrings
so a reader can reproduce them.
"""
from __future__ import annotations

import pandas as pd
import pytest

from models.common import connect
from replay import snapshot as S
from replay import vintage as V

from tests.conftest import requires_warehouse

# Every test here reconstructs the model chain from the DuckDB
# warehouse, which is not committed. Skip cleanly rather than erroring
# on a fresh checkout; see tests/conftest.py.
pytestmark = requires_warehouse


CUTOFFS = [202201, 202301, 202401]


@pytest.fixture(scope="module")
def con():
    c = connect(read_only=True)
    yield c
    c.close()


def _ym_add(ym, n):
    y, m = divmod(ym, 100)
    t = y * 12 + (m - 1) + n
    return (t // 12) * 100 + (t % 12) + 1


# ------------------------------------------------------------------ vintages
@pytest.mark.parametrize("cutoff", CUTOFFS)
def test_t100_window_never_reaches_past_the_cutoff(cutoff, con):
    """T-100 months read must end at or before cutoff minus publication lag.

    Demonstrated to fail by setting publication_lag.t100_months to 0 and
    pointing the window at the panel end (2026-04), which is 27 to 51 months of
    future schedule data depending on the cutoff.
    """
    v = S.resolve_vintages(cutoff, con)
    lag = V.protocol()["publication_lag"]["t100_months"]["value"]
    assert v.t100_max_ym <= _ym_add(cutoff, -lag), (
        f"T-100 window ends {v.t100_max_ym}, after the permitted "
        f"{_ym_add(cutoff, -lag)} at cutoff {cutoff}")
    assert v.t100_max_ym < cutoff


@pytest.mark.parametrize("cutoff", CUTOFFS)
def test_db1b_year_is_complete_and_published_by_the_cutoff(cutoff, con):
    """Demonstrated to fail by forcing db1b_year to 2024 at every cutoff, which
    is the production value and is future data at all three."""
    v = S.resolve_vintages(cutoff, con)
    lag = V.protocol()["publication_lag"]["db1b_quarter_months"]["value"]
    assert _ym_add(v.db1b_year * 100 + 12, lag) <= cutoff, (
        f"DB1B {v.db1b_year} was not fully published by {cutoff}")


@pytest.mark.parametrize("cutoff", CUTOFFS)
def test_form41_year_is_complete_and_published_by_the_cutoff(cutoff, con):
    v = S.resolve_vintages(cutoff, con)
    lag = V.protocol()["publication_lag"]["form41_annual_months"]["value"]
    assert _ym_add(v.form41_year * 100 + 12, lag) <= cutoff


@pytest.mark.parametrize("cutoff", CUTOFFS)
def test_bea_year_is_published_by_the_cutoff(cutoff, con):
    v = S.resolve_vintages(cutoff, con)
    lag = V.protocol()["publication_lag"]["bea_annual_months"]["value"]
    assert _ym_add(v.bea_year * 100 + 12, lag) <= cutoff


@pytest.mark.parametrize("cutoff", CUTOFFS)
def test_gravity_calibration_is_never_from_the_future(cutoff, con):
    """The frozen model's `current` vintage is calibrated on 2023-2024 and is
    future data at every approved cutoff; `pre2022` (2018-2019) is not.

    Demonstrated to fail by adding a window {'future': (2030, 2031)} to
    GRAVITY_WINDOWS, which the resolver must refuse to select.
    """
    v = S.resolve_vintages(cutoff, con)
    lo, hi = S.GRAVITY_WINDOWS[v.gravity_vintage]
    lag = V.protocol()["publication_lag"]["db1b_quarter_months"]["value"]
    assert _ym_add(hi * 100 + 12, lag) <= cutoff, (
        f"gravity vintage {v.gravity_vintage} calibrated through {hi}, "
        f"not published by {cutoff}")
    assert v.gravity_vintage == "pre2022", (
        "at every approved cutoff the only published calibration is pre2022")


@pytest.mark.parametrize("cutoff", CUTOFFS)
def test_seats_year_is_a_complete_year_within_the_t100_window(cutoff, con):
    v = S.resolve_vintages(cutoff, con)
    assert v.seats_year * 100 + 12 <= v.t100_max_ym


@pytest.mark.parametrize("cutoff", CUTOFFS)
def test_decision_vintage_is_not_an_excluded_year(cutoff, con):
    assert cutoff // 100 not in V.excluded_decision_vintages()


# -------------------------------------------------------------- fails closed
def test_resolution_fails_closed_before_any_cached_data():
    """A cutoff earlier than the cache must raise, never silently reach
    forward to a later vintage."""
    c = V.Cutoff(199001)
    with pytest.raises(LookupError):
        c.db1b_year({2018, 2019, 2021, 2022})


def test_gravity_resolution_fails_closed_when_nothing_published():
    c = V.Cutoff(201001)
    with pytest.raises(LookupError):
        c.gravity_vintage(S.GRAVITY_WINDOWS)


def test_pit_metros_fail_closed_on_missing_cache(monkeypatch):
    """The offline transform must raise, not download, when an input is gone.

    This is the guard against `ingest.common.download_file` failing OPEN to the
    network, which it does by design for the production ingest.
    """
    from pathlib import Path

    from replay import pit_metros as P
    monkeypatch.setattr(P, "CAINC1", Path("/nonexistent/CAINC1.csv"))
    with pytest.raises(P.CacheMissing):
        P._read_bea(P.CAINC1, "BEA CAINC1 county file")


# ------------------------------------------------------------- provenance
@pytest.mark.parametrize("cutoff", CUTOFFS)
def test_every_source_carries_a_complete_provenance_record(cutoff, con):
    v = S.resolve_vintages(cutoff, con)
    df = v.provenance_frame()
    required = {"source", "reference_period", "original_availability_date",
                "data_vintage_date", "permitted_cutoff", "vintage_policy",
                "lookahead_exception"}
    assert required <= set(df.columns)
    assert df["vintage_policy"].isin(V.POLICIES).all()
    for col in ("source", "reference_period", "permitted_cutoff",
                "vintage_policy"):
        assert df[col].notna().all(), f"{col} has nulls"
    # the three policies must all be exercised: an all-`as_available` snapshot
    # would mean the revision and staleness lookaheads had been hidden
    assert {V.AS_AVAILABLE, V.LATEST_REVISED, V.STALE_ANCHOR} <= set(
        df["vintage_policy"])


@pytest.mark.parametrize("cutoff", CUTOFFS)
def test_known_irreducible_lookaheads_are_declared_not_silent(cutoff, con):
    """The three lookaheads that apply at every approved cutoff must always be
    declared: BEA revision, the discontinued StatCan anchor, and the carrier
    brand map that carries no effective dates."""
    v = S.resolve_vintages(cutoff, con)
    df = v.provenance_frame()
    declared = df[df["lookahead_exception"].notna()]["source"].tolist()
    for src in ("BEA CAINC1 / CAGDP2", "carrier operating-to-brand map",
                "StatCan 23-10-0256 transborder O&D"):
        assert any(src in d for d in declared), (
            f"{src} carries a known residual lookahead and must declare it")


@pytest.mark.parametrize("cutoff", CUTOFFS)
def test_geography_lookahead_is_declared_exactly_when_it_applies(cutoff, con):
    """The 2023 CBSA delineation was released 2023-07. Using it before that is
    future information and must be declared; using it after is not, and
    claiming an exception there would be false disclosure.

    This test caught a real defect on first run: the original implementation
    keyed the test off the calendar year, so a 2023-01 cutoff was reported
    clean while reading a file that did not exist for another six months.
    """
    v = S.resolve_vintages(cutoff, con)
    df = v.provenance_frame()
    row = df[df["source"] == "Census CBSA delineation"].iloc[0]
    # pandas coerces a None object column entry to NaN, so test emptiness
    # rather than identity
    declared = not pd.isna(row["lookahead_exception"])
    if cutoff < 202307:
        assert declared, (
            f"cutoff {cutoff} precedes the 2023-07 release; the delineation "
            "lookahead must be declared")
        assert row["vintage_policy"] == V.STALE_ANCHOR
    else:
        assert not declared, (
            f"cutoff {cutoff} follows the 2023-07 release; claiming a "
            "lookahead here would be false disclosure")
        assert row["vintage_policy"] == V.AS_AVAILABLE


def test_invalid_vintage_policy_is_rejected():
    with pytest.raises(ValueError):
        V.Provenance(source="x", reference_period="2020",
                     original_availability_date="2021-01",
                     data_vintage_date="2026-07-20",
                     permitted_cutoff="2022-01",
                     vintage_policy="whatever_seems_fine")


# -------------------------------------------------------------- behavioural
def test_porter_has_no_served_metros_before_its_network_existed(con):
    """The strongest behavioural leak check.

    Porter's YYZ to US jet network opened 2023-11. At a 2022-01 cutoff the
    served-market exclusion must remove nothing, because Porter served nothing.
    If future T-100 leaked into the trailing window, Orlando, Fort Myers, Tampa
    and the rest would be excluded as already-served and the candidate count
    would fall.

    Demonstrated to fail by replacing the window's upper bound with the panel
    max, which drops the candidate count as those metros become "served".
    """
    cand_2022 = S.build_candidates(
        "porter_yyz", con, S.resolve_vintages(202201, con))
    cand_prod = S.build_candidates(
        "porter_yyz", con, S.production_vintages())
    assert len(cand_2022) > len(cand_prod), (
        f"Porter had 0 US metros served from YYZ at 2022-01 and 11 by the "
        f"production window, so the historical candidate set must be LARGER; "
        f"got {len(cand_2022)} vs {len(cand_prod)}")
    served_now = {"Orlando-Kissimmee-Sanford, FL",
                  "Tampa-St. Petersburg-Clearwater, FL"}
    names_2022 = set(cand_2022["metro_name"])
    assert served_now <= names_2022, (
        "metros Porter only began serving in 2023-11 must still be candidates "
        "at a 2022-01 decision date")


def test_candidate_sets_actually_move_with_the_cutoff(con):
    """A snapshot that returns the same thing at every date is not a snapshot."""
    sizes = {c: len(S.build_candidates("westjet_yyc", con,
                                       S.resolve_vintages(c, con)))
             for c in CUTOFFS}
    prod = len(S.build_candidates("westjet_yyc", con, S.production_vintages()))
    assert len(set(list(sizes.values()) + [prod])) > 1, (
        f"candidate counts identical across cutoffs and production: {sizes}, "
        f"production {prod}. The vintaging is not biting.")
