"""Stage 2R.0 guards: the resolution analysis must stay tied to the frozen V2
numbers and to its own computed artifacts.

`replay/resolution.py` makes three kinds of claim, and each fails differently.

1. It restates the frozen bootstrap in an index-based form so the ~120
   counterfactual fits finish. If that restatement ever stops matching
   `results.json`, every minimum-detectable-difference number in the document
   is void and nothing else in the repository would notice.
2. It claims each observed Family 4 difference is exactly N launch label
   changes divided by the lattice step. That is an arithmetic identity, so it
   is checkable rather than assertable.
3. It publishes a verdict. The verdict must be the one the stored grid implies,
   not the one the prose happens to carry.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from replay import resolution as R
from replay.run_replay import K_VALUES, _agreement_at_k, _recall_at_k

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "STAGE_2R0_RESOLUTION.md"


def _need(p: Path):
    if not p.exists():
        pytest.skip(f"{p.name} not built yet; run replay.run_replay then "
                    "replay.resolution")


@pytest.fixture(scope="module")
def w():
    p = R.REPLAY / "decision_rows.parquet"
    _need(p)
    rows = pd.read_parquet(p)
    return rows[rows["study_id"] == R.STUDY].reset_index(drop=True)


@pytest.fixture(scope="module")
def grid():
    p = R.REPLAY / "resolution_mde_grid.parquet"
    _need(p)
    return pd.read_parquet(p)


@pytest.fixture(scope="module")
def events():
    p = R.REPLAY / "resolution_events.parquet"
    _need(p)
    return pd.read_parquet(p)


def test_fast_bootstrap_reproduces_the_frozen_slow_path(w):
    """The load-bearing assumption of the whole stage.

    `check_reproduces_frozen_bootstrap` raises with the offending cells rather
    than returning a boolean, so a failure here names the value that moved.
    """
    _need(R.REPLAY / "results.json")
    R.check_reproduces_frozen_bootstrap(w, R.resample_indices(w))


def test_observed_differences_are_exactly_n_launch_events(w, events):
    """Agreement@k pooled moves in steps of 1/(D*k). The observed difference
    must equal the net launch label changes times that step, exactly."""
    D = w["cutoff"].nunique()
    for k in K_VALUES:
        diff = (_agreement_at_k(w, "score_model", k)
                - _agreement_at_k(w, "score_demand", k))
        net = int(events[events["k"] == k]["net_events"].sum())
        assert diff == pytest.approx(net / (D * k), abs=1e-12), (
            f"k={k}: agreement difference {diff:.6f} is not {net} events at "
            f"the {1/(D*k):.6f} lattice step")


def test_per_date_differences_are_exactly_n_launch_events(w, events):
    """The same identity per date, where the step is 1/k for agreement and
    1/P_d for recall."""
    for _, r in events.iterrows():
        g = w[w["cutoff"] == r["cutoff"]]
        k, net = int(r["k"]), int(r["net_events"])
        da = (_agreement_at_k(g, "score_model", k)
              - _agreement_at_k(g, "score_demand", k))
        dr = (_recall_at_k(g, "score_model", k)
              - _recall_at_k(g, "score_demand", k))
        assert da == pytest.approx(net / k, abs=1e-12), (
            f"k={k} {r['cutoff']}: agreement difference {da:.6f} is not "
            f"{net} events")
        assert dr == pytest.approx(net / int(r["positives"]), abs=1e-12), (
            f"k={k} {r['cutoff']}: recall difference {dr:.6f} is not "
            f"{net} of {int(r['positives'])} positives")


def test_no_observed_difference_exceeds_one_event(events):
    """The headline finding of section 3. If a future replay ever produces a
    two-event difference this fails, and the document's central claim has to
    be rewritten rather than silently outgrown."""
    worst = int(events["net_events"].abs().max())
    assert worst <= 1, (
        f"section 3 claims every observed difference is one event; the "
        f"largest is now {worst}:\n"
        + events[events["net_events"].abs() > 1].to_string())


def test_k20_saturation_is_structural(w):
    """Both k=20 metrics are pinned, not tied. Every positive already sits in
    the demand top 20 at every date, so headroom is zero."""
    assert R.headroom(w, 20) == {int(c): 0 for c in sorted(w["cutoff"].unique())}
    for score in ("score_model", "score_demand"):
        assert _recall_at_k(w, score, 20) == 1.0
    # agreement@20 is then P_d/20 for both scores, identically
    assert (_agreement_at_k(w, "score_model", 20)
            == _agreement_at_k(w, "score_demand", 20))


def test_no_single_vintage_effect_is_detectable(grid):
    """Section 6's strongest claim, and the one that governs how the observed
    k=10 result may be read."""
    single = grid[grid["n_dates_moved"] == 1]
    assert len(single) > 0
    det = single[single["agreement_excludes_zero"]
                 | single["recall_excludes_zero"]]
    assert det.empty, (
        "a single-date allocation now excludes zero:\n" + det.to_string())


def test_published_verdict_matches_the_computed_one(w, grid, events):
    vd, _ = R.verdict(w, grid, events)
    assert vd in R.VERDICTS
    _need(DOC)
    text = DOC.read_text()
    assert f"# {vd}" in text, (
        f"the generated document does not carry the computed verdict {vd!r}; "
        "regenerate with `.venv/bin/python -m replay.resolution`")
    for other in R.VERDICTS:
        if other != vd:
            assert f"\n# {other}\n" not in text


def test_document_is_generated_not_hand_written():
    _need(DOC)
    text = DOC.read_text()
    assert "Do not hand-edit" in text
    # Rule 9: no em dashes, en dashes or double hyphens in generated text.
    # Markdown table separators and horizontal rules are structure, not text,
    # so they are stripped before the double-hyphen check.
    prose = "\n".join(
        ln for ln in text.splitlines()
        if not set(ln.strip()) <= set("|- ") or not ln.strip())
    for bad in ("—", "–"):
        assert bad not in text, f"generated document contains {bad!r}"
    assert "--" not in prose, (
        "generated document contains '--' outside a table separator: "
        + next(ln for ln in prose.splitlines() if "--" in ln))


def test_positive_counts_match_the_frozen_baseline(w):
    """Stage 2R.0 must not silently redefine the universe it is measuring."""
    import json
    p = R.REPLAY / "results.json"
    _need(p)
    frozen = json.loads(p.read_text())["family_1_and_4"][R.STUDY]
    assert int(w["positive"].sum()) == frozen["n_positives"]
    assert len(w) == frozen["n_decision_rows"]
    assert w["cutoff"].nunique() == frozen["n_decision_dates"]
    by_date = {str(int(c)): int(g["positive"].sum())
               for c, g in w.groupby("cutoff")}
    assert by_date == frozen["positives_by_date"]


def test_resample_indices_match_cluster_bootstrap_draws(w):
    """The fast path must draw the same metros in the same order as the frozen
    `cluster_bootstrap`, or the seed-7 reproducibility claim is empty."""
    from replay.run_replay import N_BOOT, RNG_SEED
    clusters = w[R.CLUSTER].unique()
    rng = np.random.default_rng(RNG_SEED)
    groups = {c: g for c, g in w.groupby(R.CLUSTER)}
    idx = R.resample_indices(w, n=5, seed=RNG_SEED)
    for i in range(5):
        pick = rng.choice(clusters, size=len(clusters), replace=True)
        want = pd.concat([groups[c] for c in pick], ignore_index=True)
        got = w.iloc[idx[i]].reset_index(drop=True)
        pd.testing.assert_frame_equal(got, want)
    assert len(R.resample_indices(w, n=N_BOOT)) == N_BOOT
