"""Stage 2R.1 to 2R.4 guards.

The diagnostics make structural claims, not numeric predictions, so these
tests pin the structure. A golden test on today's Spearman values would fail
on any legitimate model change and prove nothing; an invariant that says
"correcting the growth vintage cannot reorder the demand comparator" is the
claim the document actually rests on, and it is checkable.

Five claims are load bearing.

1. The rebuilt chain is the frozen universe. Everything else is void otherwise.
2. Growth is a common positive scalar on every demand branch, so D1 cannot
   reorder the demand comparator. 2R.4's central argument.
3. Load factor falls monotonically with frequency, which is what makes the
   infeasibility fallback (`idxmax(load_factor)`) identical to "return the
   minimum frequency". 2R.3's central argument.
4. The survey ceiling assigns one value per study and date, and the size of
   that tied block does not shrink as the floor falls. This is the D3A versus
   D3B separation.
5. Ranking by margin at the minimum frequency and ranking by margin at the
   chosen frequency are the same ordering. 2R.1's control.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from models.common import assumptions, study
from replay import stage2r as X
from replay import stage2r_snapshots as SNAP

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "STAGE_2R_DIAGNOSTICS.md"
CAP = "unanchored_capped_at_ceiling"
TRANSBORDER = ("westjet_yyc", "porter_yyz")


def _need(p: Path):
    if not p.exists():
        pytest.skip(f"{p.name} not built yet; run replay.stage2r_snapshots")


@pytest.fixture(scope="module")
def cache():
    _need(SNAP.CACHE / "screen.parquet")
    return SNAP.build()


@pytest.fixture(scope="module")
def dec():
    p = X.REPLAY / "decision_rows.parquet"
    _need(p)
    return pd.read_parquet(p)


def test_rebuilt_chain_reproduces_the_frozen_replay(cache):
    """Claim 1. `build` asserts this before caching; assert it again against
    whatever is on disk, because a stale cache would silently describe a
    different universe."""
    SNAP._check_against_frozen(cache["screen"])


def test_growth_is_a_common_scalar_on_every_demand_branch(cache):
    """Claim 2, stated as arithmetic rather than measured.

    `build_demand` forms `anchor * growth`, `gravity * factor * growth` and
    `SURVEY_THRESHOLD * growth`, then takes a min of the last two. Every term
    carries the same factor, so dividing demand by growth must leave a frame
    that does not depend on the growth vintage at all.
    """
    dem, tf = cache["demand"], cache["transfer"]
    for _, t in tf.iterrows():
        if study(t["study_id"])["market_scope"] != "transborder":
            continue
        g = dem[(dem["study_id"] == t["study_id"])
                & (dem["cutoff"] == t["cutoff"])]
        growth = float(t["growth"])
        capped = g[g["demand_method"] == CAP]
        if len(capped):
            # the ceiling is exactly SURVEY_THRESHOLD * growth
            assert np.allclose(capped["demand_pax_yr"] / growth, 4000.0), (
                f"{t['study_id']} @ {t['cutoff']}: capped rows are not "
                "SURVEY_THRESHOLD * growth")
        anch = g[g["demand_method"] == "anchor_x_growth"]
        if len(anch):
            assert np.allclose(anch["demand_pax_yr"] / growth,
                               anch["anchor_2018_pax"]), (
                f"{t['study_id']} @ {t['cutoff']}: anchored rows are not "
                "anchor * growth")


def test_rescaling_growth_cannot_reorder_the_demand_comparator(cache):
    """Claim 2's consequence, which is what 2R.4 actually reports.

    A positive rescale of every demand value leaves every rank identical and
    leaves the capped/anchored branch assignment identical, because the branch
    test compares two quantities that scale together.
    """
    dem = cache["demand"]
    for (sid, cut), g in dem.groupby(["study_id", "cutoff"]):
        if study(sid)["market_scope"] != "transborder":
            continue
        for factor in (0.25, 5.4):
            scaled = g["demand_pax_yr"] * factor
            assert (X._rank(g["demand_pax_yr"])
                    == X._rank(scaled)).all(), (
                f"{sid} @ {cut}: rescaling demand by {factor} reordered the "
                "demand comparator")
            method = np.where(
                g["anchor_2018_pax"].notna(), "anchor_x_growth",
                np.where(g["gravity_implied_pax"] * factor
                         > g["survey_ceiling_pax"] * factor,
                         CAP, "gravity_x_transfer"))
            assert (method == g["demand_method"].to_numpy()).all(), (
                f"{sid} @ {cut}: rescaling by {factor} changed a demand branch")


def test_load_factor_falls_monotonically_with_frequency(cache):
    """Claim 3. `_select_service` falls back to `idxmax(load_factor)` when no
    option clears the floor. That fallback is only equivalent to "return the
    minimum frequency" while this holds, and 2R.3's headline depends on it."""
    eco = X._base(cache["economics"])
    bad = []
    for (sid, cut, cbsa), g in eco.groupby(["study_id", "cutoff", "cbsa"]):
        g = g.sort_values("freq_wk")
        lf = g["load_factor"].to_numpy()
        if not np.all(np.diff(lf) < 0):
            bad.append((sid, cut, cbsa, lf.tolist()))
    assert not bad, ("load factor is not strictly decreasing in frequency "
                     f"for {len(bad)} markets, e.g. {bad[:3]}")


def test_the_fallback_branch_returns_the_minimum_frequency(cache):
    """Claim 3, end to end: every row whose best load factor misses the floor
    must have been assigned the lowest frequency in the option list."""
    eco = X._base(cache["economics"])
    scr = cache["screen"]
    floor = float(assumptions()["min_feasible_load_factor"]["value"])
    best = eco.groupby(["study_id", "cutoff", "cbsa"])["load_factor"].max()
    lows = eco.groupby(["study_id", "cutoff", "cbsa"])["freq_wk"].min()
    infeasible = best[best < floor].index
    got = scr.set_index(["study_id", "cutoff", "cbsa"]).loc[
        infeasible, "chosen_freq_wk"]
    assert (got == lows.loc[infeasible]).all(), (
        "a market with no feasible schedule was assigned something other than "
        "the minimum frequency")


def test_survey_ceiling_assigns_exactly_one_value(cache):
    """Claim 4, first half: D3A is a single tied block, not a spread."""
    dem = cache["demand"]
    for (sid, cut), g in dem.groupby(["study_id", "cutoff"]):
        capped = g[g["demand_method"] == CAP]
        if not len(capped):
            continue
        assert capped["demand_pax_yr"].nunique() == 1, (
            f"{sid} @ {cut}: capped rows carry "
            f"{capped['demand_pax_yr'].nunique()} distinct values")


def test_lowering_the_floor_does_not_untie_the_capped_block(cache):
    """Claim 4, second half, and the point the stage exists to make.

    D3B changes the ceiling's level. It cannot reduce the number of tied rows,
    because a lower ceiling captures a superset of the rows a higher one
    captured.
    """
    fl = X.floor_sensitivity(cache)
    for (sid, cut), g in fl.groupby(["study_id", "cutoff"]):
        g = g.sort_values("floor")
        sizes = g["tie_group_size"].to_numpy()
        assert np.all(np.diff(sizes) <= 0), (
            f"{sid} @ {cut}: the tied block shrank as the floor rose, which "
            f"contradicts min(gravity, floor * growth): {sizes.tolist()}")
        assert sizes.min() > 1, (
            f"{sid} @ {cut}: no floor in the tested range leaves the block "
            "untied, so a floor correction cannot be sold as removing the "
            "compression")


def test_right_sizing_does_not_reorder(cache, dec):
    """Claim 5. Ranking by margin at the minimum option and ranking by margin
    at the chosen option are the same ordering, because the search returns the
    minimum almost everywhere. This is what makes "right-sizing differentiates
    markets" a testable statement rather than an impression."""
    lay = X.build_layers(cache)
    w = lay[lay["study_id"] == X.STUDY]
    for cut, g in w.groupby("cutoff"):
        assert (X._rank(g["score_Cmin"]) == X._rank(g["score_D"])).all(), (
            f"{cut}: margin at the minimum frequency and margin at the chosen "
            "frequency no longer induce the same ranking")


def test_straddles_detects_a_boundary_tie():
    s = pd.Series([10.0, 9.0, 8.0, 8.0, 7.0])
    assert X._straddles(s, 3) is True
    assert X._straddles(s, 2) is False
    assert X._straddles(s, 4) is False
    assert X._straddles(pd.Series([1.0, 2.0]), 5) is False


def test_launch_events_never_exceed_positive_rows(cache, dec):
    """The reporting convention itself: distinct launches are a coarsening of
    positive rows, so the event count can only be the smaller of the two."""
    out = pd.read_parquet(X.REPLAY / "outcomes.parquet")
    ev = X.launch_events(out)
    for sid, g in dec.groupby("study_id"):
        rows, events = X.outcome_counts(g, ev)
        assert events <= rows, f"{sid}: {events} events from {rows} rows"
        if sid == X.STUDY:
            assert events < rows, (
                "WestJet is the study whose windows overlap; if events equal "
                "rows the double counting has silently gone away and the "
                "reporting convention needs revisiting")


def test_document_is_generated_and_follows_rule_9():
    _need(DOC)
    text = DOC.read_text()
    assert "Do not hand-edit" in text
    prose = "\n".join(
        ln for ln in text.splitlines()
        if not set(ln.strip()) <= set("|- ") or not ln.strip())
    for bad in ("—", "–"):
        assert bad not in text, f"generated document contains {bad!r}"
    # Metro names legitimately carry a double hyphen, so only flag lines that
    # are not table rows.
    offenders = [ln for ln in prose.splitlines()
                 if "--" in ln and not ln.lstrip().startswith("|")]
    assert not offenders, f"'--' outside a table row: {offenders[:2]}"


def test_no_model_default_was_changed():
    """The stage's own promise. `SURVEY_THRESHOLD` lives in the replay
    snapshot builder and the rest live in assumptions.yaml."""
    a = assumptions()
    assert float(a["min_feasible_load_factor"]["value"]) == 0.50
    assert float(a["hurdle_margin_pct"]["value"]) == 8.0
    assert float(a["qsi_weights"]["frequency_exponent"]) == 0.6
    src = (ROOT / "replay" / "snapshot.py").read_text()
    assert "SURVEY_THRESHOLD = 4000.0" in src
    assert study(X.STUDY)["candidates"]["target_frequency_weekly"] == [3, 7, 14]
