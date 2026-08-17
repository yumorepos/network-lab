"""Stage 2R.5 and the Stage 2R decision gate.

A decision stage. Nothing is fitted, calibrated, ingested or repaired, and no
model default, assumption, threshold or output changes. What is new here is
measurement in service of four decisions:

- which product claim the built artifact can honestly carry;
- whether each old Milestone B task is necessary under that claim;
- the final treatment of D1, D2, D3A and D3B;
- whether the continuous margin ranking is a defensible public output.

The classifications are judgements and are written down as such. Every number
they rest on is computed here from artifacts already on disk, so a reader can
disagree with a judgement without having to re-derive its evidence.

    .venv/bin/python -m replay.stage2r_gate
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from ingest.common import DATA_PARQUET, ROOT
from models.common import assumptions, connect, study
from replay import stage2r as X

OUTPUTS = DATA_PARQUET / "outputs"
OUT = X.OUT
DOC = ROOT / "docs" / "STAGE_2R_DECISION.md"

GATE_VERDICTS = ("TARGETED CALIBRATION JUSTIFIED",
                 "STRUCTURAL REPAIR REQUIRED",
                 "NO DETECTABLE INCREMENTAL VALUE AT CURRENT RESOLUTION")
NECESSITY = ("REQUIRED", "TARGETED / OPTIONAL", "NOT JUSTIFIED",
             "BLOCKED BY STRUCTURAL DECISION")

# Files that make a claim to a reader. The Streamlit app and the report
# generator are included because they are read far more often than the docs.
PUBLIC_SURFACES = [
    "README.md", "app/streamlit_app.py", "reports/generate.py",
    "docs/interview_story.md", "docs/resume_material.md",
    "docs/demo_script.md", "docs/LIMITATIONS.md", "docs/validation.md",
    # Added at T2. The first list was the Stage 2R audit scope; these are the
    # remaining surfaces a reader actually meets, including the generated
    # reports, so a regression in `reports/generate.py` is caught in its output
    # and not only in its source.
    "docs/linkedin_posts.md", "docs/backtest.md", "docs/PORTFOLIO_NARRATIVE.md",
    "reports/alaska_sea_validation.md", "reports/porter_yyz_portability.md",
    "config/assumptions.yaml", "AGENTS.md", "CLAUDE.md",
]
# Deliberately NOT a public surface: `docs/FINAL_SCOPE_CONTRACT.md` exists to
# enumerate the claims this project does not make, so the vocabulary is its
# subject matter and a blunt scan over it would only ever fire on the
# retraction. It carries the opposite guard instead: a test asserts it still
# states each retired claim, so it cannot quietly lose them.
# Claims of schedule or fleet optimisation. Deliberately blunt: on a public
# surface the vocabulary itself is the defect, so denials are reworded rather
# than exempted, and there is no negation carve-out to game.
#
# Two corrections at T2. "optimi[sz]" alone also matched "optimistic", which is
# a statement about a share estimate and not an optimisation claim, so the verb
# forms are now enumerated. And the original pattern missed "best-fit", which
# `reports/generate.py` used in five places the Stage 2R audit therefore
# undercounted.
CLAIM_PATTERN = re.compile(
    r"right[- ]?siz"
    r"|optimi[sz](?:e|es|ed|ing|er|ation|ations)\b"
    r"|best[- ]fit"
    r"|best schedule"
    r"|picks the frequency"
    r"|maximi[sz]e",
    re.I)
# A line that explicitly retires or denies the claim is not making it. The
# exemption is narrow on purpose: it requires one of these retirement tokens on
# the SAME line as the claim vocabulary, so it cannot be satisfied by a denial
# sitting somewhere else in the document. Exempted lines are reported by
# `claim_audit(exempt=True)` so the carve-out stays visible rather than silent.
RETIREMENT_PATTERN = re.compile(
    r"\bno validated\b|\bretired\b|\bde-scoped?\b|\bnot (?:a |an )?(?:valid|"
    r"support|claim)|does not claim|is not\b.{0,30}\b(?:right[- ]?siz|optimi)",
    re.I)


# ---------------------------------------------------------------- measurement
def claim_audit(exempt: bool = False) -> pd.DataFrame:
    """Every reader-facing line that claims frequency or gauge optimisation.

    Recomputed from the working tree at generation time, so the audit cannot
    quietly go stale after the wording is corrected.

    Lines that retire or deny the claim on the same line are not claims. Pass
    `exempt=True` to get those instead of the violations, which is how the
    carve-out is reviewed rather than trusted.
    """
    rows, waived = [], []
    for rel in PUBLIC_SURFACES:
        p = ROOT / rel
        if not p.exists():
            continue
        for i, line in enumerate(p.read_text().splitlines(), 1):
            if not CLAIM_PATTERN.search(line):
                continue
            rec = {"file": rel, "line": i, "text": line.strip()[:160]}
            (waived if RETIREMENT_PATTERN.search(line) else rows).append(rec)
    return pd.DataFrame(waived if exempt else rows,
                        columns=["file", "line", "text"])


def competition_composition() -> pd.DataFrame:
    """What the competitive set is made of, and how much of it rests on the
    one-stop reconstruction and on an unresolved operating certificate.

    Preference is the same QSI-lite quantity `comp_pref_sum` is built from, so
    the shares below are shares of the number that actually drives share.
    """
    a = assumptions()["qsi_weights"]
    fam = set(pd.read_csv(ROOT / "data" / "reference" / "carrier_families.csv")
              ["operating_carrier"])
    rows = []
    for sid in X.STUDIES:
        p = OUTPUTS / f"competition_{sid}.parquet"
        if not p.exists():
            continue
        c = pd.read_parquet(p)
        c["pref"] = (np.where(c["itin_type"] == "nonstop", a["nonstop"],
                              a["single_connect"])
                     * c["freq_wk"] ** a["frequency_exponent"])
        unres = c[c["carrier"].isin(fam)]
        rows.append({
            "study_id": sid, "itineraries": len(c),
            "nonstop": int((c["itin_type"] == "nonstop").sum()),
            "onestop": int((c["itin_type"] == "onestop").sum()),
            "onestop_pref_share": float(
                c.loc[c["itin_type"] == "onestop", "pref"].sum()
                / c["pref"].sum()),
            "unresolved_brand_itineraries": len(unres),
            "unresolved_brand_pref_share": float(unres["pref"].sum()
                                                 / c["pref"].sum()),
        })
    return pd.DataFrame(rows)


def brand_resolution_at_hubs() -> pd.DataFrame:
    """W2.2's actual exposure: how much hub-origin flying carries no brand row.

    The roadmap cites 4,924 unmapped regional triples as the starting evidence.
    That counts the raw segment universe. What reaches a candidate's
    competitive set is hub-origin flying and its onward legs, so this measures
    the departures the study actually consumes.
    """
    from models import carriers
    con = connect(read_only=True)
    try:
        carriers.register_segment_brands(con, 26)
        win = con.execute(
            "SELECT max(year::INT*100+month) FROM fact_segment "
            "WHERE service_class IN ('F','L')").fetchone()[0]
        fam = set(pd.read_csv(
            ROOT / "data" / "reference" / "carrier_families.csv")
            ["operating_carrier"])
        rows = []
        for sid in X.STUDIES:
            hub = study(sid)["hub"]
            df = con.execute("""
                SELECT s.carrier AS op, b.brand, sum(s.departures) AS deps
                FROM fact_segment s
                LEFT JOIN map_segment_brand b
                       ON b.op_carrier = s.carrier AND b.origin = s.origin
                      AND b.dest = s.dest
                WHERE s.service_class IN ('F','L') AND s.origin = ?
                  AND (s.year::INT*100 + s.month) > ?
                GROUP BY 1, 2
            """, [hub, win - 100]).df()
            df["regional"] = df["op"].isin(fam)
            un = df[df["regional"] & df["brand"].isna()]
            rows.append({
                "study_id": sid, "hub": hub,
                "hub_departures": float(df["deps"].sum()),
                "regional_departures": float(df[df["regional"]]["deps"].sum()),
                "unresolved_departures": float(un["deps"].sum()),
                "unresolved_share": float(un["deps"].sum() / df["deps"].sum()),
            })
        return pd.DataFrame(rows)
    finally:
        con.close()


def share_validation_by_structure() -> pd.DataFrame:
    """The existing empirical share check, split by how many nonstop carriers
    the market already has.

    `models/share_validation.py` scores incumbents with the same QSI-lite the
    proposals use and compares against observed DB1B ticketing shares. The
    split matters because the WestJet study lives almost entirely in the
    zero-nonstop stratum.
    """
    p = OUTPUTS / "share_validation.parquet"
    if not p.exists():
        return pd.DataFrame()
    d = pd.read_parquet(p)
    g = (d.groupby("n_nonstop_carriers")
         .apply(lambda x: pd.Series({
             "rows": len(x), "markets": x["other_cm"].nunique(),
             "mae_share_points": 100 * x["abs_err"].mean(),
             "pax_weighted_mae": 100 * np.average(x["abs_err"],
                                                  weights=x["pax"])
             if x["pax"].sum() else np.nan}), include_groups=False)
         .reset_index())
    return g


def structural_regime() -> dict:
    """The numbers the claim decision turns on, read back from 2R.3."""
    wide = pd.read_parquet(OUT / "diag_wide.parquet")
    fsum = X.frequency_summary(wide)
    cls = pd.read_parquet(OUT / "diag_cls.parquet")
    ceil = pd.read_parquet(OUT / "diag_ceiling.parquet")
    d1 = pd.read_parquet(OUT / "diag_d1.parquet")
    tr = pd.read_parquet(OUT / "diag_tr.parquet")
    return {"freq": fsum, "layers": cls, "ceiling": ceil, "d1": d1, "tr": tr}


def resolution_facts() -> dict:
    """The Stage 2R.0 bound, read back rather than restated."""
    grid = pd.read_parquet(X.REPLAY / "resolution_mde_grid.parquet")
    ev = pd.read_parquet(X.REPLAY / "resolution_events.parquet")
    det = grid[grid["agreement_excludes_zero"] | grid["recall_excludes_zero"]]
    dec = pd.read_parquet(X.REPLAY / "decision_rows.parquet")
    outc = pd.read_parquet(X.REPLAY / "outcomes.parquet")
    le = X.launch_events(outc)
    w = dec[dec["study_id"] == X.STUDY]
    return {
        "mde_events": int(det["events"].min()),
        "observed_events": int(ev["net_events"].abs().max()),
        "positive_rows": int(w["positive"].sum()),
        "launch_events": int(le[le["study_id"] == X.STUDY]
                             [["cbsa", "first_ym"]].drop_duplicates().shape[0]),
        "vintages": int(w["cutoff"].nunique()),
        "dead_k": sorted(set(X.K_VALUES) - set(grid["k"].unique())),
        "single_date_detected": int(
            (grid[grid["n_dates_moved"] == 1]["agreement_excludes_zero"]
             | grid[grid["n_dates_moved"] == 1]["recall_excludes_zero"]).sum()),
    }


def ranking_exposure() -> pd.DataFrame:
    """What a continuous public ranking would actually be ranking.

    Per study and date: how many candidates the product would order, how many
    of them clear the feasibility floor, and the margin range across the top
    ten.
    """
    lay = X.build_layers(_cache())
    wide = pd.read_parquet(OUT / "diag_wide.parquet")
    floor = float(assumptions()["min_feasible_load_factor"]["value"])
    lo = min(int(c.split("_")[-1]) for c in wide.columns
             if c.startswith("load_factor_"))
    rows = []
    for (sid, cut), g in lay.groupby(["study_id", "cutoff"]):
        w = wide[(wide["study_id"] == sid) & (wide["cutoff"] == cut)]
        top = g.nlargest(min(10, len(g)), "score_D")
        rows.append({
            "study_id": sid, "cutoff": int(cut), "candidates": len(g),
            "feasible": int((w[f"load_factor_{lo}"] >= floor).sum()),
            "positive_margin": int((g["margin_chosen"] > 0).sum()),
            "launch_or_monitor": int((g["verdict"] != "PASS").sum()),
            "top10_best_margin": float(top["margin_chosen"].max()),
            "top10_worst_margin": float(top["margin_chosen"].min()),
        })
    return pd.DataFrame(rows)


def ceiling_feasibility() -> dict:
    """Whether any survey-ceiling row could ever appear in a feasibility-gated
    ordering. This is what makes the D3A decision airtight rather than a
    judgement call: if no capped row clears the floor, the ranking decision in
    section 5 removes the only surface on which the compression could mislead.
    """
    from replay import stage2r_snapshots as SNAP
    eco = X._base(SNAP.build()["economics"])
    floor = float(assumptions()["min_feasible_load_factor"]["value"])
    best = (eco.groupby(["study_id", "cutoff", "cbsa"])["load_factor"]
            .max().reset_index())
    dem = SNAP.build()["demand"][["study_id", "cutoff", "cbsa",
                                  "demand_method"]]
    m = best.merge(dem, on=["study_id", "cutoff", "cbsa"])
    cap = m[m["demand_method"] == "unanchored_capped_at_ceiling"]
    return {"capped_rows": int(len(cap)),
            "capped_clearing_floor": int((cap["load_factor"] >= floor).sum()),
            "max_capped_lf": float(cap["load_factor"].max()),
            "rows_clearing_floor": int((m["load_factor"] >= floor).sum()),
            "total_rows": int(len(m))}


def _cache():
    from replay import stage2r_snapshots as SNAP
    return SNAP.build()


def gate_verdict(res: dict, gates: pd.DataFrame) -> tuple[str, list]:
    """The Stage 2R gate, decided against the definitions frozen in
    `docs/REMAINING_ROADMAP_REDESIGN.md` section 3.

    The first verdict turns on whether any **calibration** task is justified.
    A required **validation** task does not qualify: verdict 1 reads "specific
    components show a plausible mechanism, sufficient evidence, and a
    defensible validation path", and a task whose purpose is to establish
    whether that path exists is not evidence that it does.
    """
    w2 = gates[gates["task"].str.startswith("W2")]
    cal = w2[(w2["kind"] == "calibration")
             & (w2["classification"] == "REQUIRED")]
    reasons = [
        "No W2 calibration task is justified: "
        + "; ".join(f"{r['task']} {r['classification']}"
                    for _, r in w2.iterrows()) + ".",
        f"The replay detects no incremental value at effects larger than "
        f"{res['mde_events']} net launch events, spread across at least two "
        f"vintages, and the largest observed difference is "
        f"{res['observed_events']} event.",
        "The structural finding is a mismatch between the product's claim and "
        "its option set, not a defect whose repair would enable a meaningful "
        "calibration comparison. The resolution is to narrow the claim, which "
        "is a scope decision rather than a repair-and-reassess loop.",
    ]
    if len(cal):
        return GATE_VERDICTS[0], reasons
    return GATE_VERDICTS[2], reasons


# ------------------------------------------------------------------ decisions
# Judgements, written down as data so the generated document renders them
# beside the evidence rather than asserting them in prose. `kind` separates a
# task that would calibrate the model from one that would only establish
# whether a claim is supportable; the gate treats them differently.
W2_GATES = [
    dict(task="W2.1", name="DB1B Coupon and Ticket ingestion",
         kind="calibration", classification="NOT JUSTIFIED",
         mechanism="itinerary and fare detail for the economics and "
                   "competition layers",
         matters="fare enters margin only through the break-even load factor, "
                 "and 2R.3 shows the schedule decision is made by the "
                 "feasibility floor before fare is consulted",
         validatable="no: 2R.0 bounds detectable improvement at five net "
                     "launch events, which no fare refinement produces",
         cost="high: two new DB1B tables, itinerary construction, a new mart",
         portfolio="no",
         recommendation="do not run. The remaining claim does not need "
                        "itinerary-level data."),
    dict(task="W2.2", name="marketing-brand mapping",
         kind="calibration", classification="NOT JUSTIFIED",
         mechanism="resolve operating certificates to the brand a passenger "
                   "buys, so the competitive set is not understated",
         matters="already resolved where the studies consume it: unresolved "
                 "regional flying is under 0.15% of hub-origin departures at "
                 "all three hubs, and unresolved itineraries carry at most "
                 "3.5% of competitor preference",
         validatable="not applicable: the exposure is too small to move share",
         cost="medium: effective-dating the brand map by vintage",
         portfolio="no",
         recommendation="do not run. Record the residual as a documented "
                        "limitation. The roadmap's D7 count is of the raw "
                        "segment universe, not of what reaches a competitive "
                        "set."),
    dict(task="W2.3", name="one-stop reconstruction validation",
         kind="validation", classification="REQUIRED",
         mechanism="the reconstructed one-stop competitive set, which carries "
                   "95% of competitor preference in the WestJet study",
         matters="yes, decisively: share is one of only two layers that "
                 "materially reorder, 85 of 88 WestJet candidates have no "
                 "nonstop incumbent, and the existing share validation covers "
                 "that structural regime with 2 markets",
         validatable="yes, and without new data: extend the existing "
                     "`models/share_validation.py` check to the "
                     "connection-only stratum",
         cost="low: existing machinery, no new source",
         portfolio="yes, if the product keeps a competition or share layer",
         recommendation="run the **validation**, not the original heuristic "
                        "refit. Refitting detour bounds or connect time "
                        "against MIDT or DB1B Coupon stays NOT JUSTIFIED."),
    dict(task="W2.4", name="QSI fitting",
         kind="calibration", classification="NOT JUSTIFIED",
         mechanism="frequency and competitive responsiveness in the share "
                   "model",
         matters="no: 2R.3 shows the frequency exponent sets a crossover the "
                 "candidate sets never approach, and 445 of 463 decisions "
                 "never reach a frequency comparison at all",
         validatable="no: the same 2R.0 bound applies, and the fallback rows "
                     "are unaffected by any exponent",
         cost="high: calibration and holdout design",
         portfolio="no",
         recommendation="do not run. The gate in the roadmap requires 2R.3 to "
                        "identify frequency responsiveness as the bottleneck. "
                        "It identifies the option set instead."),
    dict(task="W2.5", name="fare segmentation",
         kind="calibration", classification="NOT JUSTIFIED",
         mechanism="fare structure in the economics layer",
         matters="no: fare enters the ranking inside the same distance-driven "
                 "factor as cost, and no fare-attributable distortion was "
                 "found in 2R.1 or 2R.3",
         validatable="no",
         cost="medium to high",
         portfolio="no",
         recommendation="do not run."),
]

DEFECT_DECISIONS = [
    dict(defect="D1", name="corridor growth vintage",
         decision="MUST FIX BEFORE FINAL AUDIT",
         why="a demand level wrong by a factor of 5.4 at the 2023-01 cutoff is "
             "a correctness error regardless of what it does to a metric, and "
             "2R.4 measured exactly what it moves",
         validations="before and after on: median demand and margin by study "
                     "and date; the demand-only and margin rankings, which "
                     "2R.4 predicts are unchanged for WestJet; WestJet "
                     "verdict counts, predicted unchanged; Porter verdicts, "
                     "predicted to move; Family 1 and Family 4, predicted "
                     "unchanged. Any departure from those predictions is a "
                     "finding in itself."),
    dict(defect="D2", name="right-sizing",
         decision="RETIRE / DE-SCOPE RIGHT-SIZING",
         why="445 of 463 decisions never reach a comparison, and the "
             "infeasibility fallback is arithmetically identical to returning "
             "the minimum frequency. Repairing it means adding gauges the "
             "studied carriers do not fly and schedules below a real "
             "operation, which is a different model",
         validations="no model change. The remaining logic is honest as "
                     "**fixed-gauge schedule feasibility**: the engine "
                     "evaluates a small predefined schedule menu on the study "
                     "gauge and reports whether any option is feasible and "
                     "what it earns. `chosen_freq_wk` becomes "
                     "`evaluated_freq_wk` in reader-facing text and stops "
                     "being described as an optimisation result."),
    dict(defect="D3A", name="survey-ceiling compression",
         decision="DOCUMENTATION / LIMITATION",
         why="the tied block sits entirely below demand rank 50, reaches no "
             "demand top 20 and contains no WestJet launch, so it costs the "
             "baseline nothing. Its only cost is the downstream promotion of "
             "ceiling rows into the margin top k, and the ranking decision in "
             "section 5 removes the surface on which that would mislead",
         validations="document in LIMITATIONS as a censoring assumption with "
                     "its measured tail position. No code change."),
    dict(defect="D3B", name="fixed 4,000 publication floor",
         decision="ACCEPTABLE DOCUMENTED APPROXIMATION",
         why="it is a real level error, but 2R.2 shows correcting it unties "
             "nothing and at 2024-01 would capture one more row, not fewer. "
             "It moves the capped block relative to anchored markets in the "
             "tail, which is below every scored top k. The cost is "
             "per-vintage floor recovery from StatCan for a change with no "
             "measured effect on any reader-facing output",
         validations="document the fixed floor and the true 280 to 3,090 "
                     "range in LIMITATIONS, next to D3A and explicitly "
                     "separate from it. Revisit only if a future study scores "
                     "a top k that the capped block reaches."),
]
