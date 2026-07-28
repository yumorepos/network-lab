"""Headline numbers must be identical everywhere they appear. This test reads
the canonical values from the computed artifacts and fails if any
reader-facing doc drifts."""
from pathlib import Path

import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "parquet" / "outputs"


def _need(p):
    if not p.exists():
        pytest.skip(f"{p.name} not built yet")


def _live_text(p: Path) -> str:
    """A doc's LIVE claims, excluding dated historical entries.

    PROGRESS.md is a phase log: the block at the top states current values and
    the dated `## Phase N` sections below record what was true at the time. A
    phase log that gets rewritten every time the model changes is not a log, so
    history is left alone and only the live block is checked. PROGRESS.md says
    this explicitly, and the canonical block wins where they differ.
    """
    text = p.read_text()
    if p.name == "PROGRESS.md":
        marker = text.find("\n## Phase ")
        if marker > 0:
            return text[:marker]
    return text


def test_transfer_median_consistent():
    _need(OUT / "transfer_factor.yaml")
    tf = yaml.safe_load((OUT / "transfer_factor.yaml").read_text())
    canon = f"median {tf['median']:.2f}"
    for f in ("README.md", "docs/validation.md", "docs/interview_story.md"):
        assert canon in (ROOT / f).read_text(), f"{f} lacks '{canon}'"


def test_transfer_consistent_in_progress():
    """PROGRESS.md drifted to pre-fix transfer numbers once; guard it, and
    guard against stale values reappearing in any reader-facing doc."""
    _need(OUT / "transfer_factor.yaml")
    tf = yaml.safe_load((OUT / "transfer_factor.yaml").read_text())
    canon = (f"median {tf['median']:.2f}, IQR "
             f"[{tf['iqr'][0]:.2f}, {tf['iqr'][1]:.2f}]")
    assert canon in (ROOT / "PROGRESS.md").read_text(), \
        f"PROGRESS.md lacks '{canon}'"
    for f in ("PROGRESS.md", "README.md", "docs/validation.md",
              "docs/interview_story.md"):
        t = (ROOT / f).read_text()
        for stale in ("0.56, 2.10", "0.55, 2.04"):
            assert stale not in t, f"{f} has stale IQR {stale}"
        for stale in ("median 0.83", "median 0.86", "median 0.82",
                      "transfer 0.82", "transfer 0.83"):
            assert stale not in t, f"{f} has stale transfer median {stale}"


def test_share_mae_consistent():
    _need(OUT / "share_validation.parquet")
    sv = pd.read_parquet(OUT / "share_validation.parquet")
    canon = f"{100 * sv['abs_err'].mean():.1f} share"
    for f in ("README.md", "docs/validation.md", "docs/interview_story.md",
              "docs/resume_material.md", "reports/alaska_sea_validation.md"):
        assert canon in (ROOT / f).read_text(), f"{f} lacks '{canon}'"


def test_backtest_n_consistent():
    """Backtest N, counted on `outcome` (which folds seasonal into operating),
    not `status` (which does not). Reading `status` gives 42 instead of 48.

    The per-doc check was `f"{n} " in text`, a bare substring. That passed for
    the wrong reason: README contained the unrelated string "48 PASS / 1
    MONITOR" on the Alaska line, so the assertion was satisfied by a verdict
    count rather than by the backtest N. Correcting Alaska to 45 PASS removed
    the coincidence and exposed it. Now matched in context, which is stricter.
    """
    import re
    _need(OUT / "backtest_scores.parquet")
    df = pd.read_parquet(OUT / "backtest_scores.parquet").dropna(
        subset=["pctile"])
    n = int(df["outcome"].isin(["operating", "ceased"]).sum())
    assert f"N = {n}" in (ROOT / "docs" / "backtest.md").read_text()
    contexts = {
        "README.md": rf"\*{{0,2}}{n}\*{{0,2}} launched-and-resolved",
        "docs/interview_story.md": rf"{n} launched-and-resolved",
        "docs/resume_material.md": rf"Backtested {n} real",
    }
    for f, pattern in contexts.items():
        text = (ROOT / f).read_text()
        assert re.search(pattern, text), (
            f"{f} does not state the backtest N of {n} in context "
            f"(looked for /{pattern}/)")


def test_screen_reports_state_computed_verdict_counts():
    """Each generated report must state its study's verdict counts exactly as
    computed, so prose can never drift from the screen. This is the claim-level
    guard the numeric tests lacked: it caught the Alaska report asserting
    'all-PASS' when the screen was 48 PASS / 1 MONITOR."""
    reports = {
        "porter_yyz": "reports/porter_yyz_portability.md",
        "alaska_sea": "reports/alaska_sea_validation.md",
    }
    for sid, rel in reports.items():
        _need(OUT / f"screen_{sid}.parquet")
        scr = pd.read_parquet(OUT / f"screen_{sid}.parquet")
        text = (ROOT / rel).read_text()
        for verdict, n in scr["verdict"].value_counts().items():
            assert f"{n} {verdict}" in text, \
                f"{rel} lacks '{n} {verdict}'; verdict counts drifted from screen"
    # This guard used to forbid the string "all-PASS" in the Alaska report,
    # because at the time the screen was 48 PASS / 1 MONITOR and the prose
    # overclaimed. After the Round 4 candidate-leak fix the study IS all-PASS at
    # 45 PASS / 0 MONITOR, so that assertion would have forbidden a true
    # statement. Replaced by a guard against the specific superseded counts,
    # which cannot invert as the model changes.
    alaska = (ROOT / reports["alaska_sea"]).read_text()
    for stale in ("48 PASS", "49 PASS", "All 49 remaining"):
        assert stale not in alaska, f"alaska report has stale claim '{stale}'"


def test_handwritten_docs_match_generated_headline_metrics():
    """Hand-written docs may not state a verdict count that contradicts the
    computed screen.

    README advertised Porter at 5 LAUNCH / 3 MONITOR / 71 PASS for a full round
    after the corrected model said 1 / 1 / 77, and every test still passed:
    test_screen_reports_state_computed_verdict_counts guards the GENERATED
    reports and never looked at the hand-written ones. Hard rule 6 says
    reader-facing verdict counts come from computed artifacts, and README is the
    most-read reader-facing document in the repo.

    Every "X LAUNCH / Y MONITOR / Z PASS" triple in a hand-written doc must
    match some study exactly. Source of truth is
    data/parquet/outputs/headline_metrics.yaml, written by models/run_all.py.
    """
    import re
    _need(OUT / "headline_metrics.yaml")
    hm = yaml.safe_load((OUT / "headline_metrics.yaml").read_text())
    valid = {(s["LAUNCH"], s["MONITOR"], s["PASS"])
             for s in hm["studies"].values()}
    pattern = re.compile(
        r"(\d+)\s*LAUNCH\s*/\s*(\d+)\s*MONITOR\s*/\s*(\d+)\s*PASS")

    problems = []
    for rel in ("README.md", "PROGRESS.md", "docs/interview_story.md",
                "docs/resume_material.md", "docs/demo_script.md"):
        p = ROOT / rel
        if not p.exists():
            continue
        for line_no, line in enumerate(_live_text(p).splitlines(), 1):
            for m in pattern.finditer(line):
                triple = tuple(int(g) for g in m.groups())
                if triple not in valid:
                    problems.append(
                        f"{rel}:{line_no} states {triple[0]} LAUNCH / "
                        f"{triple[1]} MONITOR / {triple[2]} PASS, "
                        "which matches no study")
    assert not problems, (
        "hand-written docs disagree with headline_metrics.yaml "
        f"(valid triples {sorted(valid)}):\n" + "\n".join(problems))


def test_handwritten_docs_match_generated_scalar_metrics():
    """Share MAE and backtest N must match the generated metrics wherever a
    hand-written doc states them. These drifted independently of the verdict
    counts: README said MAE 7.0 against a computed 5.7, and PROGRESS drifted to
    MAE 6.7."""
    import re
    _need(OUT / "headline_metrics.yaml")
    hm = yaml.safe_load((OUT / "headline_metrics.yaml").read_text())
    mae = hm["share_validation"]["mae_share_points"]
    n_bt = hm["backtest"]["n_launched_and_resolved"]

    problems = []
    for rel in ("README.md", "PROGRESS.md", "docs/interview_story.md",
                "docs/resume_material.md"):
        p = ROOT / rel
        if not p.exists():
            continue
        text = _live_text(p)
        for found in re.findall(r"MAE \*{0,2}(\d+\.\d+)", text):
            if abs(float(found) - mae) > 0.05:
                problems.append(f"{rel} states MAE {found}, computed {mae}")
        for found in re.findall(
                r"\*{0,2}(\d+)\*{0,2} launched-and-resolved|Backtested (\d+) real",
                text):
            found = found[0] or found[1] if isinstance(found, tuple) else found
            if int(found) != n_bt:
                problems.append(f"{rel} states {found} launched-and-resolved, "
                                f"computed {n_bt}")
    assert not problems, "\n".join(problems)


def test_gravity_counts_labeled_by_vintage():
    _need(OUT / "gravity_pre2022.yaml")
    pre = yaml.safe_load((OUT / "gravity_pre2022.yaml").read_text())
    cur = yaml.safe_load((OUT / "gravity_current.yaml").read_text())
    v = (ROOT / "docs" / "validation.md").read_text()
    assert f"markets: {pre['n_markets']}" in v
    assert f"markets: {cur['n_markets']}" in v
    # docs must never blend the two counts into one unlabeled number
    readme = (ROOT / "README.md").read_text()
    assert f"{pre['n_markets']:,}" in readme
