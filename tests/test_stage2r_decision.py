"""Stage 2R.5 and decision-gate guards.

A decision document is mostly judgement, so these tests pin the two things
that are not: the evidence the judgements cite, and the promise that the stage
changed nothing.

The claim audit is the load-bearing one. `docs/STAGE_2R_DECISION.md` says the
audit table "empties itself when the wording is corrected", which is only true
if the audit reads the working tree rather than a stored snapshot. That is
tested directly.
"""
from pathlib import Path

import pandas as pd
import pytest

from models.common import assumptions, study
from replay import stage2r as X
from replay import stage2r_gate as G

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "STAGE_2R_DECISION.md"


def _need(p: Path):
    if not p.exists():
        pytest.skip(f"{p.name} not built yet; run replay.stage2r_report first")


def test_claim_audit_reads_the_working_tree(tmp_path):
    """The audit must be recomputed, not stored. If it ever reads a cached
    frame this test fails, and the document's central promise about T2 with
    it."""
    df = G.claim_audit()
    assert len(df), "no claim lines found; the pattern or the surface list broke"
    for rel in df["file"].unique():
        assert (ROOT / rel).exists()
    # every reported line must still be present at the reported position
    for _, r in df.iterrows():
        line = (ROOT / r["file"]).read_text().splitlines()[r["line"] - 1]
        assert G.CLAIM_PATTERN.search(line), (
            f"{r['file']}:{r['line']} no longer matches; the audit is stale")


def test_claim_audit_covers_every_public_surface_that_exists():
    """A surface silently dropped from the list would understate T2's scope."""
    missing = [s for s in G.PUBLIC_SURFACES if not (ROOT / s).exists()]
    assert not missing, f"public surfaces listed but absent: {missing}"


def test_the_option_set_does_not_span_the_demand():
    """The claim decision rests on this and nothing else: the smallest option
    on the menu is more capacity than most candidates can fill."""
    _need(G.OUT / "diag_wide.parquet")
    wide = pd.read_parquet(G.OUT / "diag_wide.parquet")
    f = X.frequency_summary(wide)
    assert f["median_lf_lo"] < f["lf_floor"], (
        "the median candidate now clears the feasibility floor at the minimum "
        "frequency; the claim-A decision needs revisiting")
    assert f["rows_lf_lo_above_floor"] < f["n"] / 2


def test_no_survey_ceiling_row_clears_the_feasibility_floor():
    """The D3A decision is DOCUMENTATION rather than FIX precisely because a
    feasibility-gated ordering cannot contain a ceiling row. If one ever
    clears the floor, D3A becomes a live ranking problem again."""
    cf = G.ceiling_feasibility()
    assert cf["capped_rows"] > 0
    assert cf["capped_clearing_floor"] == 0, (
        f"{cf['capped_clearing_floor']} survey-ceiling rows now clear the "
        "feasibility floor, so option B no longer excludes the tied block")


def test_brand_resolution_is_immaterial_where_the_studies_consume_it():
    """W2.2's NOT JUSTIFIED classification, stated as a threshold on the
    measurement rather than on the conclusion."""
    b = G.brand_resolution_at_hubs()
    assert len(b) == len(X.STUDIES)
    assert b["unresolved_share"].max() < 0.01, (
        "unresolved regional flying at a study hub now exceeds 1% of "
        "departures; W2.2 needs reclassifying\n" + b.to_string())


def test_share_layer_rests_on_the_one_stop_reconstruction():
    """W2.3's REQUIRED classification. If nonstop competition ever dominates,
    the validation gap this task closes stops being the binding one."""
    c = G.competition_composition()
    wj = c[c["study_id"] == X.STUDY].iloc[0]
    assert wj["onestop_pref_share"] > 0.5, (
        "one-stop itineraries no longer carry most of WestJet's competitor "
        f"preference ({wj['onestop_pref_share']:.1%})")


def test_share_validation_barely_covers_the_flagship_regime():
    """The specific gap W2.3 exists to close: the validation set is dominated
    by markets with nonstop incumbents while the flagship study is not."""
    sv = G.share_validation_by_structure()
    if sv.empty:
        pytest.skip("share_validation.parquet not built")
    zero = sv[sv["n_nonstop_carriers"] == 0]["markets"].sum()
    assert zero < 0.2 * sv["markets"].sum(), (
        "the zero-nonstop stratum is no longer thin; W2.3 may already be "
        "satisfied")


def test_gate_verdict_is_one_of_the_frozen_three_and_matches_the_document():
    res = G.resolution_facts()
    gates = pd.DataFrame(G.W2_GATES)
    verdict, reasons = G.gate_verdict(res, gates)
    assert verdict in G.GATE_VERDICTS
    assert reasons
    _need(DOC)
    text = DOC.read_text()
    assert f"Gate verdict: {verdict}" in text
    for other in G.GATE_VERDICTS:
        if other != verdict:
            assert f"Gate verdict: {other}" not in text


def test_a_required_validation_task_does_not_flip_the_gate():
    """The gate turns on calibration, not validation. W2.3 is REQUIRED and the
    verdict must still be the third one; if `kind` is ever dropped this fires.
    """
    gates = pd.DataFrame(G.W2_GATES)
    assert (gates["classification"] == "REQUIRED").any()
    assert set(gates["kind"]) <= {"calibration", "validation"}
    v, _ = G.gate_verdict(G.resolution_facts(), gates)
    assert v == G.GATE_VERDICTS[2]
    flipped = gates.copy()
    flipped.loc[flipped["task"] == "W2.4", "classification"] = "REQUIRED"
    v2, _ = G.gate_verdict(G.resolution_facts(), flipped)
    assert v2 == G.GATE_VERDICTS[0], (
        "a required calibration task must move the gate to TARGETED "
        "CALIBRATION JUSTIFIED")


def test_every_classification_is_from_the_frozen_vocabulary():
    gates = pd.DataFrame(G.W2_GATES)
    assert set(gates["classification"]) <= set(G.NECESSITY)
    assert set(gates["task"]) == {"W2.1", "W2.2", "W2.3", "W2.4", "W2.5"}
    defects = pd.DataFrame(G.DEFECT_DECISIONS)
    assert set(defects["defect"]) == {"D1", "D2", "D3A", "D3B"}


def test_the_decision_stage_changed_nothing():
    """The stage's own promise, checked against the values it promises not to
    have moved."""
    a = assumptions()
    assert float(a["min_feasible_load_factor"]["value"]) == 0.50
    assert float(a["hurdle_margin_pct"]["value"]) == 8.0
    assert "SURVEY_THRESHOLD = 4000.0" in (
        ROOT / "replay" / "snapshot.py").read_text()
    assert study(X.STUDY)["candidates"]["target_frequency_weekly"] == [3, 7, 14]
    assert len(study(X.STUDY)["gauges"]) == 1


def test_document_is_generated_and_follows_rule_9():
    _need(DOC)
    text = DOC.read_text()
    assert "Do not hand-edit" in text
    prose = "\n".join(
        ln for ln in text.splitlines()
        if not set(ln.strip()) <= set("|- ") or not ln.strip())
    for bad in ("—", "–"):
        assert bad not in text, f"generated document contains {bad!r}"
    offenders = [ln for ln in prose.splitlines()
                 if "--" in ln and not ln.lstrip().startswith("|")]
    assert not offenders, f"'--' outside a table row: {offenders[:2]}"
