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


HISTORICAL_LOG_START = "\n## Phase 0"


def _live_text(p: Path) -> str:
    """A doc's LIVE claims, excluding dated historical entries.

    PROGRESS.md is a phase log: the block at the top states current values and
    the dated `## Phase N` sections below record what was true at the time. A
    phase log that gets rewritten every time the model changes is not a log, so
    history is left alone and only the live block is checked. PROGRESS.md says
    this explicitly, and the canonical block wins where they differ.

    The boundary is `## Phase 0`, the fixed first entry of the chronological
    log, NOT the first `## Phase ` heading. That earlier marker assumed the
    canonical block was the only thing above the log. When the Phase 6A entry
    was added at the top of the file it became the first `## Phase ` heading,
    so every guard below silently truncated PROGRESS.md to its title line and
    checked nothing. It stayed that way long enough for the canonical block to
    publish a backtest N of 42 against a computed 48. Anchoring on Phase 0
    keeps new current-state sections inside the checked region, which is where
    they need to be.
    """
    text = p.read_text()
    if p.name == "PROGRESS.md":
        marker = text.find(HISTORICAL_LOG_START)
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
    # docs/linkedin_posts.md added at T6: it was outside every guard and had
    # drifted to "7.0 share-point error" against a computed 5.7.
    for f in ("README.md", "docs/validation.md", "docs/interview_story.md",
              "docs/resume_material.md", "reports/alaska_sea_validation.md",
              "docs/linkedin_posts.md"):
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
    MAE 6.7.

    A second, legitimately different MAE entered the docs at T3: the per-stratum
    validation reports its own MAE per structural regime, and the flagship
    result is the one-stop-only stratum. Comparing every "MAE x.y" against the
    pooled value therefore flagged a correct number, and the guard was red from
    T3 (531c95e) until T2. Both quantities are now checked against their own
    artifact, and a stratum value is only accepted where the surrounding text
    identifies the stratum, so a pooled figure still cannot hide behind one.
    """
    import re
    _need(OUT / "headline_metrics.yaml")
    # Required, not optional. If this artifact were treated as absent-is-fine,
    # a doc could state any stratum MAE and the guard would wave it through,
    # which is the failure mode the `## Phase 0` boundary bug already caused
    # once in this file. It is tracked in git for exactly this reason.
    _need(OUT / "share_validation_by_stratum.parquet")
    hm = yaml.safe_load((OUT / "headline_metrics.yaml").read_text())
    mae = hm["share_validation"]["mae_share_points"]
    n_bt = hm["backtest"]["n_launched_and_resolved"]
    strata = pd.read_parquet(OUT / "share_validation_by_stratum.parquet")
    stratum_maes = [float(v) for v in strata["mae"]]
    STRATUM_TOKENS = ("stratum", "strata", "zero-nonstop", "one-stop",
                      "nonstop competition", "sole reconstructed")

    problems = []
    for rel in ("README.md", "PROGRESS.md", "docs/interview_story.md",
                "docs/resume_material.md"):
        p = ROOT / rel
        if not p.exists():
            continue
        text = _live_text(p)
        for m in re.finditer(r"MAE \*{0,2}(\d+\.\d+)", text):
            found = float(m.group(1))
            if abs(found - mae) <= 0.05:
                continue
            window = text[max(0, m.start() - 220):m.end() + 220].lower()
            named = any(t in window for t in STRATUM_TOKENS)
            matches_stratum = any(abs(found - s) <= 0.05 for s in stratum_maes)
            if named and matches_stratum:
                continue
            why = ("does not match any computed stratum MAE"
                   if named else
                   "is not the pooled MAE and does not name a stratum")
            problems.append(
                f"{rel} states MAE {found}, which {why} "
                f"(pooled {mae}, strata {[round(s, 1) for s in stratum_maes]})")
        # \s+ rather than a literal space: PROGRESS.md wraps between the count
        # and the phrase, so a single-space pattern matched nothing there and
        # the number went unguarded.
        for found in re.findall(
                r"\*{0,2}(\d+)\*{0,2}\s+launched-and-resolved"
                r"|Backtested\s+(\d+)\s+real",
                text):
            found = found[0] or found[1] if isinstance(found, tuple) else found
            if int(found) != n_bt:
                problems.append(f"{rel} states {found} launched-and-resolved, "
                                f"computed {n_bt}")
    assert not problems, "\n".join(problems)


def test_readme_degeneracy_count_matches_the_decision_document():
    """README restates one Stage 2R figure, the fallback count that makes the
    right-sizing de-scope legible, and it is the only place that figure appears
    outside its canonical source.

    Under the T2 packaging policy an exact value repeated outside its source of
    record must be checked against that record. The source here is
    `docs/STAGE_2R_DECISION.md`, which is generated from `diag_wide.parquet` by
    `replay/stage2r_gate_report.py` and guarded by
    `tests/test_stage2r_decision.py`. The diagnostic parquet is not tracked, so
    checking against the document rather than recomputing is what makes this
    guard run in CI instead of silently skipping there.
    """
    import re
    doc = (ROOT / "docs" / "STAGE_2R_DECISION.md").read_text()
    total = re.search(r"\|\s*decision rows\s*\|\s*\**(\d+)\**\s*\|", doc)
    fallback = re.search(
        r"\|\s*rows where no option clears the floor\s*\|\s*\**(\d+)\**\s*\|", doc)
    assert total and fallback, (
        "docs/STAGE_2R_DECISION.md no longer states the decision-row and "
        "fallback counts in the shape this guard reads")
    canon = f"{fallback.group(1)} of {total.group(1)}"
    for rel in ("README.md", "docs/PORTFOLIO_NARRATIVE.md",
                "docs/interview_story.md"):
        assert canon in (ROOT / rel).read_text(), (
            f"{rel} must state the fallback count as '{canon}' to match "
            f"docs/STAGE_2R_DECISION.md; it does not")


def test_limitations_d3a_figures_match_the_decision_document():
    """LIMITATIONS restates the D3A feasibility result, which is the
    measurement that makes D3A a documentation item rather than a fix.

    Checked against `docs/STAGE_2R_DECISION.md` rather than recomputed:
    `stage2r_gate.ceiling_feasibility()` rebuilds the replay snapshots and needs
    the warehouse, which CI does not have, so recomputing here would make the
    guard skip or error in exactly the environment it is meant to protect.
    `tests/test_stage2r_decision.py` recomputes it where the warehouse exists.
    """
    import re
    doc = (ROOT / "docs" / "STAGE_2R_DECISION.md").read_text()
    m = re.search(r"\*\*(\d+) of (\d+) survey-ceiling rows clear the floor\*\*",
                  doc)
    lf = re.search(r"the highest reaching a load factor of ([\d.]+)", doc)
    assert m and lf, "STAGE_2R_DECISION.md no longer states the D3A result"
    lim = (ROOT / "docs" / "LIMITATIONS.md").read_text()
    assert f"{m.group(1)} of {m.group(2)}" in lim, (
        f"LIMITATIONS must state the ceiling-feasibility result as "
        f"'{m.group(1)} of {m.group(2)}'")
    assert lf.group(1) in lim, (
        f"LIMITATIONS must state the maximum capped load factor {lf.group(1)}")


def test_limitations_resolution_bounds_match_the_resolution_document():
    """The predictive-resolution bound must travel with the predictive claim,
    and must agree with the document that measured it."""
    import re
    doc = (ROOT / "docs" / "STAGE_2R0_RESOLUTION.md").read_text()
    ev = re.search(r"\*\*(\d+) positive rows rest on (\d+) distinct launch "
                   r"events", doc)
    floor = re.search(r"\*\*(\d+) or more net launch events\*\*", doc)
    assert ev and floor, "STAGE_2R0_RESOLUTION.md no longer states its bounds"
    lim = (ROOT / "docs" / "LIMITATIONS.md").read_text()
    problems = []
    if f"{ev.group(1)} positive rows" not in lim:
        problems.append(f"LIMITATIONS lacks the {ev.group(1)} positive rows")
    if f"{ev.group(2)} distinct launch events" not in lim:
        problems.append(f"LIMITATIONS lacks the {ev.group(2)} distinct launches")
    if f"{floor.group(1)} or more net launch events" not in lim:
        problems.append(
            f"LIMITATIONS lacks the {floor.group(1)}-event detectability floor")
    assert not problems, "\n".join(problems)


def test_the_bounded_predictive_claim_is_never_shortened():
    """The two forbidden shortenings assert things the study cannot support:
    one claims a measured equivalence, the other a lift never observed. Neither
    may be asserted on a reader-facing surface.

    Quoted spans are stripped before searching. The documents that forbid these
    phrasings have to be able to name them, and a mention inside quotation
    marks is the opposite of an assertion. Without the use/mention split this
    guard fires on the very text that establishes the rule.
    """
    import re
    banned = ("the model does not beat demand",
              "the model beats demand",
              "no incremental value over demand")
    problems = []
    for rel in ("README.md", "docs/LIMITATIONS.md", "docs/interview_story.md",
                "docs/resume_material.md", "docs/FINAL_SCOPE_CONTRACT.md",
                "docs/linkedin_posts.md"):
        p = ROOT / rel
        if not p.exists():
            continue
        asserted = re.sub(r"[\"'`]{1,3}[^\"'`\n]*[\"'`]{1,3}", " ",
                          p.read_text().lower())
        for phrase in banned:
            if phrase in asserted:
                problems.append(f"{rel} asserts '{phrase}' without its bound")
    assert not problems, "\n".join(problems)


def test_connection_share_validation_status_is_stated_consistently():
    """W2.3 closed as a validation, not a refit. The verdict string is frozen
    vocabulary and must match the change report that issued it."""
    verdict = "CONNECTION SHARE VALIDATED FOR FINAL SCOPE"
    src = ROOT / "docs" / "change_reports" / "T3_connection_share_validation.md"
    assert verdict in src.read_text(), "the T3 report no longer issues its verdict"
    lim = (ROOT / "docs" / "LIMITATIONS.md").read_text()
    assert verdict in lim, "LIMITATIONS must publish the T3 validation verdict"


def test_v2_frozen_sections_are_immutable():
    """V2 is the pre-repair predictive baseline that the post-D1 comparison is
    read against, and "V2 is unchanged" is asserted in prose by three
    generators, by PROGRESS.md and by the release criteria. Nothing enforced it
    until T6.

    The real convention is append-only. Sections 1 to 6 are the freeze; two
    later commits appended sections 7 and 8, each of which states that it adds
    no number and changes none. This pins the frozen region and leaves the
    addendum mechanism available.

    The digest below was verified equal to the same region at the freeze commit
    `d514ec2`, so it pins the original baseline rather than whatever the file
    happened to contain when this guard was written. Trailing whitespace is
    normalised because the boundary is a truncation point.
    """
    import hashlib
    import re
    doc = (ROOT / "docs" / "W1.4_predictive_baseline_v2.md").read_text()
    boundary = re.search(r"\n+---\n+## 7\. Reporting addendum", doc)
    assert boundary, (
        "the V2 addendum boundary is gone; either section 7 was renamed or the "
        "frozen document was restructured, and neither is allowed")
    frozen = doc[:boundary.start()].rstrip()
    digest = hashlib.sha256(frozen.encode()).hexdigest()
    assert digest == ("445d02844d279a6780676a74ae63e701"
                      "9f19929c5bbbb25bebaa3b7dab2310a6"), (
        "sections 1 to 6 of the V2 predictive baseline changed. V2 is the "
        "immutable pre-repair scoreboard: a new result belongs in a new freeze "
        "document with a statement of what moved and why, never in this one.")


def test_v2_addenda_declare_that_they_change_nothing():
    """The append-only convention is only safe if an addendum cannot smuggle in
    a revision. Each one has to say so."""
    doc = (ROOT / "docs" / "W1.4_predictive_baseline_v2.md").read_text()
    for section in ("## 7. Reporting addendum", "## 8. Reporting addendum"):
        i = doc.find(section)
        assert i > 0, f"{section} is missing from the V2 baseline"
        head = doc[i:i + 400]
        assert "adds no number to the freeze and changes none" in head, (
            f"{section} no longer declares that it changes no frozen number")


def test_final_audit_ends_with_exactly_one_verdict():
    """The final audit issues a single verdict from a frozen vocabulary, as its
    last line. Two verdicts, a hedged verdict, or a verdict buried mid-document
    would each let the document avoid committing to one."""
    p = ROOT / "docs" / "FINAL_PROJECT_AUDIT.md"
    assert p.exists(), "docs/FINAL_PROJECT_AUDIT.md is missing"
    lines = [ln.strip() for ln in p.read_text().splitlines() if ln.strip()]
    verdicts = [ln for ln in lines
                if ln in ("PORTFOLIO READY", "NOT PORTFOLIO READY")]
    assert len(verdicts) == 1, (
        f"the final audit states {len(verdicts)} verdicts; it must state "
        f"exactly one")
    assert lines[-1] == verdicts[0], (
        "the verdict must be the last line of the final audit")


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
