"""Stage 2R.1 through 2R.4: mechanism diagnostics on the frozen engine.

Defined in `docs/REMAINING_ROADMAP_REDESIGN.md` and run under the Stage 2R.0
evidence standard frozen at commit `230be19`: **LIMITED TO LARGE EFFECTS**, and
for every practical decision here, **DESCRIPTIVE / MECHANISM ATTRIBUTION
ONLY**. Nothing in this module fits, calibrates, or changes a model default,
assumption, threshold or scoring function. It reads the frozen chain through
`replay/stage2r_snapshots.py`, which asserts it reproduces
`decision_rows.parquet` before caching anything.

Two conventions run through all four stages.

**Row labels are not launch events.** The replay carries 15 positive rows on
10 distinct launches, because a launch inside the 24 month window of two
cutoffs is a positive at both. Every outcome count below reports both.

**An interval spanning zero is not equivalence, and no new inferential test is
computed.** Agreement and recall appear descriptively, under 2R.0.

Regenerate with

    .venv/bin/python -m replay.stage2r
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from ingest.common import DATA_PARQUET, ROOT
from models.common import assumptions, connect, study
from replay import snapshot as S
from replay import stage2r_snapshots as SNAP
from replay.run_replay import (K_VALUES, _agreement_at_k, _recall_at_k,
                               _ym_from_yyyymm, HORIZON_F1)

REPLAY = DATA_PARQUET / "replay"
OUT = REPLAY / "stage2r"
DOC = ROOT / "docs" / "STAGE_2R_DIAGNOSTICS.md"

STUDY = "westjet_yyc"          # the only cell carrying a predictive claim
STUDIES = ("westjet_yyc", "alaska_sea", "porter_yyz")

# Diagnostic reporting conventions, not model constants. Declared here and
# disclosed in the generated document so a classification cannot be read as a
# fitted threshold. The top-10 rule is grounded in Stage 2R.0: one change of
# top-10 membership is exactly one lattice step, the smallest movement the
# frozen evaluation can represent, so "changes at least one top-10 place at a
# majority of decision dates" is the weakest defensible reading of "materially
# alters the ordering".
MATERIAL_K = 10
MATERIAL_MIN_DATES = 2

LAYER_ORDER = ["A", "B", "C", "D", "E"]
LAYER_NAME = {
    "A": "demand only",
    "B": "demand x share at the reference frequency",
    "C": "margin at the reference frequency",
    "D": "margin at the chosen frequency (the production score)",
    "E": "final verdict",
}
VERDICT_RANK = {"PASS": 0, "MONITOR": 1, "LAUNCH": 2}

LAYER_CLASSES = ("MEANINGFUL DIFFERENTIATION", "MOSTLY REDUNDANT WITH DEMAND",
                 "MECHANICALLY DISTORTIVE", "NOT SEPARABLY IDENTIFIABLE")


# ------------------------------------------------------------------ helpers
def _base(eco: pd.DataFrame) -> pd.DataFrame:
    return eco[(eco["fare_scenario_pct"] == 0) & (eco["fuel_scenario_pct"] == 0)]


def ref_freq(study_id: str = STUDY) -> int:
    """The production share layer's own reference frequency.

    `models/competition.py:qsi_share` and `replay/snapshot.py:build_share` both
    emit `proposed_share` at `target_frequency_weekly[1]`. Using the same value
    keeps layer B and layer C on the schedule the architecture already treats
    as the reference, rather than one chosen here.
    """
    return int(study(study_id)["candidates"]["target_frequency_weekly"][1])


def launch_events(outcomes: pd.DataFrame) -> pd.DataFrame:
    """Map every positive decision row to the distinct launches behind it.

    Returns one row per (study_id, cutoff, cbsa, first_ym). Counting `cbsa`
    values overstates nothing, but counting positive ROWS double counts the
    five WestJet launches that fall inside two cutoff windows.
    """
    rows = []
    for sid, dates in SNAP.DECISION_DATES.items():
        o = outcomes[outcomes["study_id"] == sid]
        for cut in dates:
            lo, hi = _ym_from_yyyymm(cut), _ym_from_yyyymm(cut) + HORIZON_F1
            w = o[(o["first_ym"] > lo) & (o["first_ym"] <= hi)]
            for _, r in w.iterrows():
                rows.append({"study_id": sid, "cutoff": cut,
                             "cbsa": r["cbsa"], "first_ym": int(r["first_ym"])})
    return pd.DataFrame(rows).drop_duplicates()


def outcome_counts(sel: pd.DataFrame, ev: pd.DataFrame) -> tuple[int, int]:
    """(row-level positive labels, distinct launch events) for a selection of
    decision rows. `sel` needs study_id, cutoff, cbsa, positive."""
    rows = int(sel["positive"].sum()) if len(sel) else 0
    if not rows:
        return 0, 0
    hit = sel[sel["positive"] == 1][["study_id", "cutoff", "cbsa"]]
    m = ev.merge(hit, on=["study_id", "cutoff", "cbsa"])
    return rows, int(m[["cbsa", "first_ym"]].drop_duplicates().shape[0])


def _rank(s: pd.Series) -> pd.Series:
    """Descending competition rank: 1 is best. Ties share the average rank,
    which is how `Series.rank(pct=True)` treats the demand comparator."""
    return s.rank(ascending=False, method="average")


# ================================================================== 2R.1
def build_layers(cache: dict) -> pd.DataFrame:
    """One row per (study, cutoff, market) with every layer score attached.

    The layers are read off the production architecture rather than invented:

    A  `demand_pax_yr`                     `build_demand`
    B  `demand_pax_yr * share(ref)`        `build_share`, captured demand
    C  `margin_pct` at ref frequency       `build_economics`, base scenario
    D  `margin_pct` at chosen frequency    `build_screen`, the frozen score
    E  verdict                             `build_screen`

    B and C are separable because the economics grid keeps `demand_pax_yr` and
    `proposed_share` per row. C and D differ only through the frequency the
    right-sizing search selects.
    """
    eco = _base(cache["economics"])
    scr = cache["screen"]
    rows = []
    for sid in STUDIES:
        rf = ref_freq(sid)
        lof = int(min(study(sid)["candidates"]["target_frequency_weekly"]))
        e = eco[(eco["study_id"] == sid) & (eco["freq_wk"] == rf)]
        lo = eco[(eco["study_id"] == sid) & (eco["freq_wk"] == lof)]
        s = scr[scr["study_id"] == sid]
        m = e[["study_id", "cutoff", "cbsa", "metro_name", "demand_pax_yr",
               "proposed_share", "margin_pct", "load_factor", "belf",
               "annual_contribution", "demand_method", "dist_mi",
               "n_nonstop_incumbents"]].rename(
            columns={"proposed_share": "share_ref",
                     "margin_pct": "margin_ref",
                     "load_factor": "lf_ref", "belf": "belf_ref",
                     "annual_contribution": "ac_ref"})
        m = m.merge(lo[["study_id", "cutoff", "cbsa", "margin_pct"]]
                    .rename(columns={"margin_pct": "margin_min_freq"}),
                    on=["study_id", "cutoff", "cbsa"])
        m = m.merge(s[["study_id", "cutoff", "cbsa", "verdict",
                       "chosen_freq_wk", "margin_pct", "proposed_share"]]
                    .rename(columns={"margin_pct": "margin_chosen",
                                     "proposed_share": "share_chosen"}),
                    on=["study_id", "cutoff", "cbsa"])
        m["score_A"] = m["demand_pax_yr"]
        m["score_B"] = m["demand_pax_yr"] * m["share_ref"]
        m["score_C"] = m["margin_ref"]
        m["score_D"] = m["margin_chosen"]
        m["score_E"] = m["verdict"].map(VERDICT_RANK)
        # Not a layer. The control that separates "right-sizing differentiates
        # markets" from "the margin ranking depends on which common frequency
        # it is evaluated at": margin at the minimum option, which is what the
        # search returns for all but two rows in the whole replay.
        m["score_Cmin"] = m["margin_min_freq"]
        rows.append(m)
    return pd.concat(rows, ignore_index=True)


def _straddles(s: pd.Series, k: int) -> bool:
    """True when a tie spans the k-th and (k+1)-th place, so the top k is not
    determined by the score alone."""
    if len(s) <= k:
        return False
    v = np.sort(s.to_numpy(float))[::-1]
    return bool(v[k - 1] == v[k])


def _transition(g: pd.DataFrame, prev: str, cur: str, sid: str,
                ev: pd.DataFrame) -> dict:
    sp, sc = g[f"score_{prev}"], g[f"score_{cur}"]
    rec = {"study_id": sid, "cutoff": int(g["cutoff"].iloc[0]),
           "transition": f"{prev} to {cur}", "n": len(g)}
    # A constant score is not a ranking. Spearman is undefined against it and
    # `nlargest` would return an arbitrary slice of the tied block, so the
    # top-k columns are left empty rather than filled with a tie-break.
    rec["degenerate"] = bool(sc.nunique() <= 1)
    rec["distinct_values"] = int(sc.nunique())
    if rec["degenerate"]:
        for c in ("rho_prev", "rho_demand", "median_abs_rank_move",
                  "p90_abs_rank_move", "max_abs_rank_move"):
            rec[c] = np.nan
        for k in K_VALUES:
            rec[f"tie_broken_{k}"] = True
            for c in ("overlap", "promoted", "demoted", "promoted_pos_rows",
                      "promoted_pos_events", "demoted_pos_rows",
                      "demoted_pos_events", "promoted_capped"):
                rec[f"{c}_{k}"] = np.nan
        return rec
    rec["rho_prev"] = float(spearmanr(sp, sc).statistic)
    rec["rho_demand"] = float(spearmanr(g["score_A"], sc).statistic)
    disp = (_rank(sc) - _rank(sp)).abs()
    rec["median_abs_rank_move"] = float(disp.median())
    rec["p90_abs_rank_move"] = float(disp.quantile(0.90))
    rec["max_abs_rank_move"] = float(disp.max())
    for k in K_VALUES:
        # A tie spanning the k-th and (k+1)-th place makes the top k an
        # arbitrary slice of the tied block: `nlargest` breaks it by row order.
        # The verdict layer does exactly this, and reporting its promotions as
        # if they were rank moves would invent a finding out of DataFrame
        # ordering. Those cells are left empty instead.
        rec[f"tie_broken_{k}"] = bool(_straddles(g[f"score_{cur}"], k)
                                      or _straddles(g[f"score_{prev}"], k))
        if rec[f"tie_broken_{k}"]:
            for c in ("overlap", "promoted", "demoted", "promoted_pos_rows",
                      "promoted_pos_events", "demoted_pos_rows",
                      "demoted_pos_events", "promoted_capped"):
                rec[f"{c}_{k}"] = np.nan
            continue
        tp = set(g.nlargest(min(k, len(g)), f"score_{prev}")["cbsa"])
        tc = set(g.nlargest(min(k, len(g)), f"score_{cur}")["cbsa"])
        promoted = g[g["cbsa"].isin(tc - tp)]
        demoted = g[g["cbsa"].isin(tp - tc)]
        pr, pe = outcome_counts(promoted.assign(study_id=sid), ev)
        dr, de = outcome_counts(demoted.assign(study_id=sid), ev)
        rec[f"overlap_{k}"] = len(tp & tc)
        rec[f"promoted_{k}"] = len(tc - tp)
        rec[f"demoted_{k}"] = len(tp - tc)
        rec[f"promoted_pos_rows_{k}"] = pr
        rec[f"promoted_pos_events_{k}"] = pe
        rec[f"demoted_pos_rows_{k}"] = dr
        rec[f"demoted_pos_events_{k}"] = de
        rec[f"promoted_capped_{k}"] = int(
            (promoted["demand_method"] == "unanchored_capped_at_ceiling").sum())
    return rec


def layer_transitions(lay: pd.DataFrame, dec: pd.DataFrame,
                      ev: pd.DataFrame, sid: str = STUDY) -> pd.DataFrame:
    """Every layer transition, per decision date.

    The control transition `Cmin to D` is appended: it isolates whether the
    right-sizing search differentiates markets from whether the margin ranking
    simply depends on the frequency it is evaluated at.
    """
    L = lay[lay["study_id"] == sid]
    d = dec[dec["study_id"] == sid][["cutoff", "cbsa", "positive"]]
    L = L.merge(d, on=["cutoff", "cbsa"])
    pairs = [(LAYER_ORDER[i - 1], LAYER_ORDER[i])
             for i in range(1, len(LAYER_ORDER))] + [("Cmin", "D")]
    out = []
    for prev, cur in pairs:
        for cut in sorted(L["cutoff"].unique()):
            out.append(_transition(L[L["cutoff"] == cut], prev, cur, sid, ev))
    return pd.DataFrame(out)


def layer_top_k_membership(lay: pd.DataFrame, dec: pd.DataFrame,
                           sid: str = STUDY, k: int = MATERIAL_K
                           ) -> pd.DataFrame:
    """Named top-k membership at every layer and date, for the mechanism
    narrative. This is where the promotions and demotions can be read off
    rather than described."""
    L = lay[lay["study_id"] == sid].merge(
        dec[dec["study_id"] == sid][["cutoff", "cbsa", "positive"]],
        on=["cutoff", "cbsa"])
    rows = []
    for cut in sorted(L["cutoff"].unique()):
        g = L[L["cutoff"] == cut]
        for lyr in LAYER_ORDER:
            top = g.nlargest(min(k, len(g)), f"score_{lyr}")
            for pos, (_, r) in enumerate(top.iterrows(), start=1):
                rows.append({
                    "cutoff": int(cut), "layer": lyr, "position": pos,
                    "metro_name": r["metro_name"], "cbsa": r["cbsa"],
                    "positive": int(r["positive"]),
                    "demand_method": r["demand_method"],
                    "demand_pax_yr": r["demand_pax_yr"],
                    "share_ref": r["share_ref"], "margin_ref": r["margin_ref"],
                    "margin_chosen": r["margin_chosen"],
                    "dist_mi": r["dist_mi"],
                    "n_nonstop_incumbents": r["n_nonstop_incumbents"],
                    "verdict": r["verdict"],
                })
    return pd.DataFrame(rows)


def classify_layers(tr: pd.DataFrame) -> pd.DataFrame:
    """Classify each transition against the declared conventions."""
    rows = []
    for t, g in tr.groupby("transition", sort=False):
        n_dates = len(g)
        deg = int(g["degenerate"].sum())
        live = g[~g["degenerate"]]
        # A date whose top-k straddles a tie carries no measurable membership
        # change, so it leaves the denominator rather than counting as "no
        # change".
        meas = live[~live[f"tie_broken_{MATERIAL_K}"].astype(bool)]
        monotone = bool(len(live)
                        and np.allclose(live["rho_prev"], 1.0, atol=1e-12))
        changed = int((meas[f"promoted_{MATERIAL_K}"] > 0).sum())
        material = changed >= MATERIAL_MIN_DATES
        capped = int(meas[f"promoted_capped_{MATERIAL_K}"].sum())
        promoted = int(meas[f"promoted_{MATERIAL_K}"].sum())
        pos_ev = int(meas[f"promoted_pos_events_{MATERIAL_K}"].sum())
        if deg or not len(meas):
            cls = "NOT SEPARABLY IDENTIFIABLE"
            why = (f"the layer score takes a single value at {deg} of "
                   f"{n_dates} dates and its top {MATERIAL_K} is decided "
                   f"by a tie at {n_dates - len(meas)} of them, so it "
                   "cannot order the candidate set. Ranking it would "
                   "return an arbitrary slice of one tied block.")
        elif monotone:
            cls = "NOT SEPARABLY IDENTIFIABLE"
            why = ("Spearman with the previous layer is exactly 1.0 at every "
                   "date: the layer is a monotone transform of its input and "
                   "reorders nothing.")
        elif not material:
            cls = "MOSTLY REDUNDANT WITH DEMAND"
            why = (f"top-{MATERIAL_K} membership changes at {changed} of "
                   f"{len(meas)} measurable dates, below the "
                   f"{MATERIAL_MIN_DATES}-date convention for a material "
                   "change.")
        elif promoted and capped / promoted >= 0.5:
            cls = "MECHANICALLY DISTORTIVE"
            why = (f"{capped} of {promoted} promotions into the top "
                   f"{MATERIAL_K} are survey-ceiling rows, which carry one "
                   "tied demand value and no launch, so the promotion cannot "
                   "be explained by the mechanism the layer represents.")
        else:
            cls = "MEANINGFUL DIFFERENTIATION"
            why = (f"top-{MATERIAL_K} membership changes at {changed} of "
                   f"{len(meas)} measurable dates, {promoted} promotions "
                   f"carrying {pos_ev} distinct launch events, and "
                   f"{capped} of them are ceiling rows.")
        rows.append({"transition": t, "classification": cls, "why": why,
                     "dates_changing_top_k": changed, "n_dates": n_dates,
                     "degenerate_dates": deg,
                     "tie_broken_dates": int(len(live) - len(meas)),
                     "measurable_dates": int(len(meas)),
                     "promotions": promoted, "capped_promotions": capped,
                     "promoted_launch_events": pos_ev,
                     "rho_demand_min": float(live["rho_demand"].min())
                     if len(live) else np.nan,
                     "rho_demand_max": float(live["rho_demand"].max())
                     if len(live) else np.nan})
    return pd.DataFrame(rows)


# ================================================================== 2R.2
def ceiling_diagnostic(cache: dict, dec: pd.DataFrame,
                       ev: pd.DataFrame) -> pd.DataFrame:
    """D3A (censoring and tie structure) and D3B (the floor's value), kept
    apart. Alaska is `us_domestic` and reads observed DB1B, so no row is
    capped and the study is out of scope."""
    dem = cache["demand"]
    lay = build_layers(cache)
    rows = []
    for sid in ("westjet_yyc", "porter_yyz"):
        for cut in sorted(dem[dem["study_id"] == sid]["cutoff"].unique()):
            g = dem[(dem["study_id"] == sid) & (dem["cutoff"] == cut)]
            L = lay[(lay["study_id"] == sid) & (lay["cutoff"] == cut)].merge(
                dec[dec["study_id"] == sid][["cutoff", "cbsa", "positive"]],
                on=["cutoff", "cbsa"])
            capped = g["demand_method"] == "unanchored_capped_at_ceiling"
            vc = g["demand_pax_yr"].value_counts()
            ties = vc[vc > 1]
            r = {"study_id": sid, "cutoff": int(cut), "n": len(g),
                 "anchored": int((g["demand_method"] == "anchor_x_growth").sum()),
                 "capped": int(capped.sum()),
                 "gravity": int((g["demand_method"] == "gravity_x_transfer").sum()),
                 "frac_capped": float(capped.mean()),
                 "capped_value": float(g.loc[capped, "demand_pax_yr"].iloc[0])
                 if capped.any() else np.nan,
                 "n_tie_groups": int(len(ties)),
                 "largest_tie_group": int(ties.max()) if len(ties) else 0,
                 "rows_in_ties": int(ties.sum()) if len(ties) else 0}
            dr = _rank(L["score_A"])
            cap_rank = dr[L["demand_method"]
                          == "unanchored_capped_at_ceiling"]
            r["capped_best_demand_rank"] = (float(cap_rank.min())
                                            if len(cap_rank) else np.nan)
            for k in K_VALUES:
                for lyr, tag in (("A", "demand"), ("D", "model")):
                    top = L.nlargest(min(k, len(L)), f"score_{lyr}")
                    r[f"capped_in_{tag}_top{k}"] = int(
                        (top["demand_method"]
                         == "unanchored_capped_at_ceiling").sum())
            cap_rows = L[L["demand_method"] == "unanchored_capped_at_ceiling"]
            pr, pe = outcome_counts(cap_rows.assign(study_id=sid), ev)
            r["capped_positive_rows"] = pr
            r["capped_launch_events"] = pe
            # how far the downstream layers move the ceiling block
            if len(cap_rows):
                r["capped_median_demand_rank"] = float(
                    _rank(L["score_A"])[cap_rows.index].median())
                r["capped_median_model_rank"] = float(
                    _rank(L["score_D"])[cap_rows.index].median())
            rows.append(r)
    return pd.DataFrame(rows)


def floor_sensitivity(cache: dict, floors=(280.0, 1000.0, 3090.0, 4000.0)
                      ) -> pd.DataFrame:
    """D3B, isolated. Re-derive which rows the ceiling captures at candidate
    publication floors, **without changing `SURVEY_THRESHOLD`**.

    `replay/snapshot.py:build_demand` sets `ceiling = SURVEY_THRESHOLD *
    growth` and takes `min(gravity_est, ceiling)` on unanchored rows, so the
    counterfactual is arithmetic on frames already computed: no model is run
    and no default is touched. The point is to show that lowering the floor
    moves and enlarges the tied block without untying it.
    """
    dem = cache["demand"]
    rows = []
    for sid in ("westjet_yyc", "porter_yyz"):
        for cut in sorted(dem[dem["study_id"] == sid]["cutoff"].unique()):
            g = dem[(dem["study_id"] == sid) & (dem["cutoff"] == cut)].copy()
            un = g["demand_method"] != "anchor_x_growth"
            # ceiling = floor * growth, recovered from the frozen frame so the
            # growth vintage is the one the decision actually used
            growth = float(g["survey_ceiling_pax"].iloc[0]) / 4000.0
            for f in floors:
                ceil = f * growth
                capped = un & (g["gravity_implied_pax"] > ceil)
                rows.append({
                    "study_id": sid, "cutoff": int(cut), "floor": f,
                    "ceiling_value": ceil,
                    "capped": int(capped.sum()),
                    "frac_capped": float(capped.sum() / len(g)),
                    "tie_group_size": int(capped.sum()),
                    "distinct_values_among_unanchored": int(
                        pd.concat([
                            pd.Series([ceil] * int(capped.sum())),
                            g.loc[un & ~capped, "gravity_implied_pax"]
                        ]).nunique()) if un.any() else 0,
                })
    return pd.DataFrame(rows)


# ================================================================== 2R.3
def frequency_diagnostic(cache: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """D2. Why the right-sizing search returns the minimum option.

    Deterministic and unaffected by the 2R.0 power limit: it is a
    decomposition of the frozen objective, not an estimate.
    """
    eco = _base(cache["economics"]).copy()
    scr = cache["screen"]
    lf_floor = float(assumptions()["min_feasible_load_factor"]["value"])

    key = ["study_id", "cutoff", "cbsa"]
    wide = eco.pivot_table(index=key + ["metro_name", "dist_mi", "seats"],
                           columns="freq_wk",
                           values=["annual_contribution", "load_factor",
                                   "margin_pct", "belf", "pax_per_dep",
                                   "proposed_share", "demand_pax_yr"]).reset_index()
    wide.columns = [f"{a}_{int(b)}" if b != "" else a for a, b in wide.columns]
    freqs = sorted(eco["freq_wk"].unique())
    lo, mid, hi = freqs[0], freqs[1], freqs[-1]

    wide["feasible_count"] = sum(
        (wide[f"load_factor_{f}"] >= lf_floor).astype(int) for f in freqs)
    wide["ac_positive_at_lo"] = wide[f"annual_contribution_{lo}"] > 0
    wide[f"beats_{mid}"] = (wide[f"annual_contribution_{lo}"]
                            > wide[f"annual_contribution_{mid}"])
    wide[f"beats_{hi}"] = (wide[f"annual_contribution_{lo}"]
                           > wide[f"annual_contribution_{hi}"])
    wide[f"{mid}_beats_{hi}"] = (wide[f"annual_contribution_{mid}"]
                                 > wide[f"annual_contribution_{hi}"])
    # The selection path each row actually took through `_select_service`.
    def path(r):
        if r["feasible_count"] == 0:
            return "fallback: no option clears the load-factor floor"
        if r[f"load_factor_{mid}"] < lf_floor:
            return f"feasibility: only {lo}x clears the floor"
        if not r["ac_positive_at_lo"]:
            return "negative contribution: more departures lose more money"
        return "economics: contribution compared among feasible options"
    wide["selection_path"] = wide.apply(path, axis=1)

    # Which regime each row sits in. Away from capacity, spill is negligible
    # and `pax_per_dep` is exactly `carried / deps_yr`, so
    #   AC(f) = fare * demand * share(f) - 104 * f * cost
    # with revenue growing as share(f), concave in f, and cost growing
    # linearly. The low option then wins for arithmetic reasons. Against
    # capacity, `pax_per_dep` saturates at `seats` and
    #   AC(f) -> 104 * f * (fare * seats - cost),
    # which increases in f whenever the break-even load factor is under 1.
    # The two regimes, not the frequency exponent alone, decide the outcome.
    with np.errstate(divide="ignore", invalid="ignore"):
        wide["spill_loss_lo"] = 1 - (
            wide[f"pax_per_dep_{lo}"]
            / (wide[f"demand_pax_yr_{lo}"] * wide[f"proposed_share_{lo}"]
               / (lo * 52 * 2)))
        share_gain = wide[f"proposed_share_{mid}"] / wide[f"proposed_share_{lo}"]
        wide["share_gain_lo_to_mid"] = share_gain
        # Extra revenue the step to `mid` must find, as a multiple of the
        # captured demand the low option already carries. Unspilled algebra.
        wide["required_demand_multiple_mid"] = (
            (mid - lo) * 52 * 2 * wide[f"belf_{lo}"] * wide["seats"]
            / (lo * 52 * 2 * wide[f"pax_per_dep_{lo}"] * (share_gain - 1)))
        wide["unspilled_predicts_lo_wins"] = (
            wide["required_demand_multiple_mid"] > 1)
    wide[f"{lo}_actually_wins_over_{mid}"] = wide[f"beats_{mid}"]

    chosen = scr[key + ["chosen_freq_wk"]]
    wide = wide.merge(chosen, on=key)
    return wide, eco


def frequency_summary(wide: pd.DataFrame) -> dict:
    """The counts the D2 classification rests on."""
    freqs = sorted(int(c.split("_")[-1]) for c in wide.columns
                   if c.startswith("load_factor_"))
    lo, mid = freqs[0], freqs[1]
    lf_floor = float(assumptions()["min_feasible_load_factor"]["value"])
    won = wide[~wide[f"beats_{mid}"]]
    lost = wide[wide[f"beats_{mid}"]]
    agree = int((wide["unspilled_predicts_lo_wins"]
                 == wide[f"beats_{mid}"]).sum())
    return {
        "n": int(len(wide)), "lo": lo, "mid": mid, "hi": freqs[-1],
        "lf_floor": lf_floor,
        "chose_lo": int((wide["chosen_freq_wk"] == lo).sum()),
        "paths": wide["selection_path"].value_counts().to_dict(),
        "rows_lf_lo_above_floor": int((wide[f"load_factor_{lo}"]
                                       >= lf_floor).sum()),
        "rows_lf_mid_above_floor": int((wide[f"load_factor_{mid}"]
                                        >= lf_floor).sum()),
        "rows_ac_lo_positive": int((wide[f"annual_contribution_{lo}"]
                                    > 0).sum()),
        "median_lf_lo": float(wide[f"load_factor_{lo}"].median()),
        "median_ac_lo": float(wide[f"annual_contribution_{lo}"].median()),
        "mid_wins": int(len(won)),
        "max_lf_lo_where_lo_wins": float(lost[f"load_factor_{lo}"].max()),
        "min_lf_lo_where_mid_wins": (float(won[f"load_factor_{lo}"].min())
                                     if len(won) else float("nan")),
        "unspilled_rule_agrees": agree,
        "median_required_demand_multiple": float(
            wide["required_demand_multiple_mid"].replace(
                [np.inf, -np.inf], np.nan).median()),
    }


def frequency_representatives(cache: dict, wide: pd.DataFrame,
                              dec: pd.DataFrame) -> pd.DataFrame:
    """A spanning set of markets, decomposed term by term at every frequency.

    Strata are declared, and the pick inside each is the highest-demand row
    that qualifies, so the selection is reproducible rather than chosen after
    seeing the decomposition. The strata span the axes the roadmap names:
    demand level, competition, censoring status, launch outcome, and study.
    """
    eco = _base(cache["economics"])
    freqs = sorted(int(c.split("_")[-1]) for c in wide.columns
                   if c.startswith("load_factor_"))
    lo = freqs[0]
    dem_col, shr_col = f"demand_pax_yr_{lo}", f"proposed_share_{lo}"
    lf_floor = float(assumptions()["min_feasible_load_factor"]["value"])
    w = wide.merge(dec[["study_id", "cutoff", "cbsa", "positive"]],
                   on=["study_id", "cutoff", "cbsa"], how="left")
    # `pivot_table` keeps only the index and the pivoted values, so the two
    # stratifying columns come back from the frames that carry them.
    w = w.merge(cache["demand"][["study_id", "cutoff", "cbsa",
                                 "demand_method"]],
                on=["study_id", "cutoff", "cbsa"], how="left")
    w = w.merge(cache["share"][["study_id", "cutoff", "cbsa",
                                "n_nonstop_incumbents"]],
                on=["study_id", "cutoff", "cbsa"], how="left")
    picks = []
    for sid, g0 in w.groupby("study_id"):
        cut = int(g0["cutoff"].max())
        g = g0[g0["cutoff"] == cut]
        strata = {
            "highest demand, no nonstop incumbent":
                g[g["n_nonstop_incumbents"] == 0],
            "highest demand, nonstop incumbent present":
                g[g["n_nonstop_incumbents"] > 0],
            "median demand": g,
            "survey-ceiling demand": g[g["demand_method"] == "unanchored"
                                       "_capped_at_ceiling"],
            "observed launch": g[g["positive"] == 1],
            "load factor clears the floor":
                g[g[f"load_factor_{lo}"] >= lf_floor],
        }
        for name, sub in strata.items():
            if not len(sub):
                continue
            if name == "median demand":
                i = (sub[dem_col] - sub[dem_col].median()).abs().idxmin()
                r = sub.loc[i]
            else:
                r = sub.nlargest(1, dem_col).iloc[0]
            picks.append({"stratum": name, "study_id": sid, "cutoff": cut,
                          "cbsa": r["cbsa"], "metro_name": r["metro_name"]})
    # A market can satisfy several strata. Keep it once and name every stratum
    # it stands for, rather than silently dropping the later labels.
    sel = (pd.DataFrame(picks)
           .groupby(["study_id", "cutoff", "cbsa"], as_index=False)
           .agg(stratum=("stratum", "; ".join)))
    cols = ["study_id", "cutoff", "cbsa", "metro_name", "dist_mi", "seats",
            "freq_wk", "proposed_share", "demand_pax_yr", "pax_per_dep",
            "load_factor", "belf", "margin_pct", "annual_contribution"]
    return eco[cols].merge(
        sel[["stratum", "study_id", "cutoff", "cbsa"]],
        on=["study_id", "cutoff", "cbsa"]).sort_values(
            ["study_id", "stratum", "freq_wk"])


# ================================================================== 2R.4
def d1_blast_radius(cache: dict, dec: pd.DataFrame) -> tuple:
    """Measure what correcting the corridor-growth vintage would move.

    **The fix is not made here.** `growth` enters `build_demand` as a scalar on
    every branch (`anchor_est = anchor * growth`, `gravity_est = gravity *
    factor * growth`, `ceiling = SURVEY_THRESHOLD * growth`), so a corrected
    growth is exactly a rescale of `demand_pax_yr` and the counterfactual can
    be built from the frozen frames rather than by editing the model. The
    rescale is asserted against a re-derivation before anything is reported.

    The alternative growth year is the last complete pre-COVID year inside the
    same permitted T-100 window: the sensitivity `docs/W1.4_replay_results.md`
    already names and declines to run.
    """
    con = connect(read_only=True)
    try:
        tf = cache["transfer"]
        rows, screens = [], []
        for _, t in tf.iterrows():
            sid, cut, hub = t["study_id"], int(t["cutoff"]), t["hub"]
            if study(sid)["market_scope"] != "transborder":
                continue
            anchor_year, gy = int(t["anchor_year"]), int(t["growth_year"])
            alt_year = gy if gy < 2020 else 2019
            g_alt = con.execute("""
                WITH t AS (
                  SELECT year, sum(passengers) AS pax FROM fact_segment
                  WHERE service_class IN ('F','L')
                    AND ((origin=? AND dest_country='US')
                      OR (dest=? AND origin_country='US'))
                    AND year IN (?, ?)
                  GROUP BY year
                )
                SELECT max(CASE WHEN year=? THEN pax END)
                     / max(CASE WHEN year=? THEN pax END) FROM t
            """, [hub, hub, anchor_year, alt_year, alt_year,
                  anchor_year]).fetchone()[0]
            rows.append({"study_id": sid, "cutoff": cut, "hub": hub,
                         "anchor_year": anchor_year, "growth_year": gy,
                         "growth": float(t["growth"]),
                         "alt_growth_year": alt_year,
                         "alt_growth": float(g_alt),
                         "ratio": float(g_alt) / float(t["growth"])})
        vint = pd.DataFrame(rows)

        for _, v in vint.iterrows():
            sid, cut = v["study_id"], int(v["cutoff"])
            dem = cache["demand"]
            dem = dem[(dem["study_id"] == sid) & (dem["cutoff"] == cut)].copy()
            shr = cache["share"]
            shr = shr[(shr["study_id"] == sid) & (shr["cutoff"] == cut)].copy()
            alt = dem.copy()
            for col in ("demand_pax_yr", "gravity_implied_pax",
                        "survey_ceiling_pax", "anchor_2018_pax"):
                if col == "anchor_2018_pax":
                    continue
                alt[col] = alt[col] * v["ratio"]
            # the branch test is growth-invariant: both sides scale together
            method_alt = np.where(
                alt["anchor_2018_pax"].notna(), "anchor_x_growth",
                np.where(alt["gravity_implied_pax"] > alt["survey_ceiling_pax"],
                         "unanchored_capped_at_ceiling", "gravity_x_transfer"))
            assert (method_alt == dem["demand_method"].to_numpy()).all(), (
                f"{sid} @ {cut}: rescaling growth changed a demand branch; the "
                "common-scalar claim does not hold and 2R.4 must stop")
            vs = S.resolve_vintages(cut, con)
            eco_alt = S.build_economics(sid, con, vs, alt, shr)
            scr_alt = S.build_screen(sid, eco_alt)
            scr_alt["study_id"], scr_alt["cutoff"] = sid, cut
            screens.append(scr_alt)
    finally:
        con.close()
    return vint, pd.concat(screens, ignore_index=True)


def d1_comparison(cache: dict, alt_screen: pd.DataFrame,
                  dec: pd.DataFrame, ev: pd.DataFrame) -> tuple:
    """Frozen versus corrected-growth, per study and date."""
    base = cache["screen"]
    key = ["study_id", "cutoff", "cbsa"]
    m = base[key + ["metro_name", "verdict", "chosen_freq_wk", "margin_pct",
                    "demand_pax_yr", "annual_contribution", "load_factor"]
             ].merge(
        alt_screen[key + ["verdict", "chosen_freq_wk", "margin_pct",
                          "demand_pax_yr", "annual_contribution",
                          "load_factor"]],
        on=key, suffixes=("", "_alt"))
    m = m.merge(dec[key + ["positive"]], on=key, how="left")
    m["demand_ratio"] = m["demand_pax_yr_alt"] / m["demand_pax_yr"]
    m["margin_delta"] = m["margin_pct_alt"] - m["margin_pct"]
    m["verdict_changed"] = m["verdict"] != m["verdict_alt"]
    m["freq_changed"] = m["chosen_freq_wk"] != m["chosen_freq_wk_alt"]

    rows = []
    for (sid, cut), g in m.groupby(["study_id", "cutoff"]):
        gd = g.copy()
        gd["score_demand_base"] = gd["demand_pax_yr"].rank(pct=True)
        gd["score_demand_alt"] = gd["demand_pax_yr_alt"].rank(pct=True)
        rank_id = bool((_rank(gd["demand_pax_yr"])
                        == _rank(gd["demand_pax_yr_alt"])).all())
        model_rank_id = bool((_rank(gd["margin_pct"])
                              == _rank(gd["margin_pct_alt"])).all())
        r = {"study_id": sid, "cutoff": int(cut), "n": len(g),
             "model_rank_identical": model_rank_id,
             "demand_ratio_min": float(g["demand_ratio"].min()),
             "demand_ratio_max": float(g["demand_ratio"].max()),
             "median_demand_base": float(g["demand_pax_yr"].median()),
             "median_demand_alt": float(g["demand_pax_yr_alt"].median()),
             "median_margin_base": float(g["margin_pct"].median()),
             "median_margin_alt": float(g["margin_pct_alt"].median()),
             "median_margin_delta": float(g["margin_delta"].median()),
             "rows_margin_moved": int((g["margin_delta"].abs() > 1e-9).sum()),
             "verdicts_changed": int(g["verdict_changed"].sum()),
             "freq_changed": int(g["freq_changed"].sum()),
             "demand_rank_identical": rank_id}
        for k in K_VALUES:
            tb = set(g.nlargest(min(k, len(g)), "margin_pct")["cbsa"])
            ta = set(g.nlargest(min(k, len(g)), "margin_pct_alt")["cbsa"])
            r[f"model_top{k}_changed"] = len(tb - ta)
            db = set(gd.nlargest(min(k, len(gd)), "score_demand_base")["cbsa"])
            da = set(gd.nlargest(min(k, len(gd)), "score_demand_alt")["cbsa"])
            r[f"demand_top{k}_changed"] = len(db - da)
        rows.append(r)
    return pd.DataFrame(rows), m


def d1_descriptive_metrics(m: pd.DataFrame, sid: str = STUDY) -> pd.DataFrame:
    """Family 1 and Family 4, descriptively, frozen versus corrected growth."""
    g = m[(m["study_id"] == sid) & m["positive"].notna()].copy()
    g["positive"] = g["positive"].astype(int)
    rows = []
    for tag, mcol, dcol in (("frozen", "margin_pct", "demand_pax_yr"),
                            ("corrected", "margin_pct_alt",
                             "demand_pax_yr_alt")):
        d = g.rename(columns={mcol: "score_model"}).copy()
        d["score_demand"] = d.groupby("cutoff")[dcol].rank(pct=True)
        for k in K_VALUES:
            rows.append({
                "variant": tag, "k": k,
                "agreement_model": _agreement_at_k(d, "score_model", k),
                "recall_model": _recall_at_k(d, "score_model", k),
                "agreement_demand": _agreement_at_k(d, "score_demand", k),
                "recall_demand": _recall_at_k(d, "score_demand", k),
            })
    df = pd.DataFrame(rows)
    df["diff_agreement"] = df["agreement_model"] - df["agreement_demand"]
    df["diff_recall"] = df["recall_model"] - df["recall_demand"]
    return df
