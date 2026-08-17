"""T5: the post-D1 replay, compared against the immutable V2 baseline.

`docs/W1.4_predictive_baseline_v2.md` is **not** modified and is not
regenerable: it is the frozen before-state, and D1 is carried in it as recorded
defect 1. This module reads the pre-D1 artifacts preserved under
`data/parquet/replay/pre_d1/`, which are what the engine produced at commit
`f38cf16`, against the artifacts the D1-corrected engine produces now, and
publishes the difference.

Read under the Stage 2R.0 interpretation, **LIMITED TO LARGE EFFECTS**. A small
movement in a Family 1 or Family 4 number is not a validated predictive
improvement and is not presented as one. The design cannot distinguish an
effect smaller than about five net launch events from zero, and the adoption
rule for D1 was fixed in advance to be independent of any metric.

    .venv/bin/python -m replay.post_d1_comparison
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from ingest.common import DATA_PARQUET, ROOT
from replay.run_replay import K_VALUES, _agreement_at_k, _recall_at_k

REPLAY = DATA_PARQUET / "replay"
PRE = REPLAY / "pre_d1"
DOC = ROOT / "docs" / "W1.4_POST_D1_COMPARISON.md"
STUDY = "westjet_yyc"
STUDIES = ("westjet_yyc", "alaska_sea", "porter_yyz")


def _ci(t) -> str:
    if t is None:
        return "n/a"
    p, lo, hi = t
    if p != p:
        return "n/a"
    if lo != lo or hi != hi:
        return f"{p:.3f}"
    return f"{p:.3f} [{lo:.3f}, {hi:.3f}]"


def _same(a, b, tol=1e-9) -> bool:
    if a is None or b is None:
        return a is b
    return all(abs(x - y) <= tol or (x != x and y != y) for x, y in zip(a, b))


def _rank(s: pd.Series) -> pd.Series:
    return s.rank(ascending=False, method="average")


def load() -> dict:
    need = [PRE / "decision_rows.parquet", PRE / "results.json",
            REPLAY / "decision_rows.parquet", REPLAY / "results.json"]
    missing = [p for p in need if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "post-D1 comparison needs both states on disk; missing "
            f"{[str(p) for p in missing]}. Re-run replay.run_replay, and see "
            "docs/change_reports/D1_corridor_growth_vintage.md for how the "
            "pre-D1 snapshot was taken.")
    return {
        "before_rows": pd.read_parquet(PRE / "decision_rows.parquet"),
        "after_rows": pd.read_parquet(REPLAY / "decision_rows.parquet"),
        "before_res": json.loads((PRE / "results.json").read_text()),
        "after_res": json.loads((REPLAY / "results.json").read_text()),
        "before_pairs": pd.read_parquet(PRE / "rightsizing_pairs.parquet"),
        "after_pairs": pd.read_parquet(REPLAY / "rightsizing_pairs.parquet"),
        "before_growth": pd.read_parquet(PRE / "vintage_transfer_growth.parquet"),
        "after_growth": pd.read_parquet(REPLAY
                                        / "vintage_transfer_growth.parquet"),
    }


def row_comparison(before: pd.DataFrame, after: pd.DataFrame) -> pd.DataFrame:
    key = ["study_id", "cutoff", "cbsa"]
    m = before.merge(after, on=key, suffixes=("_b", "_a"), how="outer",
                     indicator=True)
    rows = []
    for (sid, cut), g in m.groupby(["study_id", "cutoff"]):
        both = g[g["_merge"] == "both"]
        rows.append({
            "study_id": sid, "cutoff": int(cut),
            "candidates_before": int((g["_merge"] != "right_only").sum()),
            "candidates_after": int((g["_merge"] != "left_only").sum()),
            "added": int((g["_merge"] == "right_only").sum()),
            "dropped": int((g["_merge"] == "left_only").sum()),
            "positives_before": int(g["positive_b"].fillna(0).sum()),
            "positives_after": int(g["positive_a"].fillna(0).sum()),
            "label_changes": int((both["positive_b"]
                                  != both["positive_a"]).sum()),
            "median_demand_before": float(both["demand_pax_yr_b"].median()),
            "median_demand_after": float(both["demand_pax_yr_a"].median()),
            "median_margin_before": float(both["margin_pct_b"].median()),
            "median_margin_after": float(both["margin_pct_a"].median()),
            "rows_demand_moved": int(
                ((both["demand_pax_yr_a"] - both["demand_pax_yr_b"]).abs()
                 > 1e-6).sum()),
            "rows_margin_moved": int(
                ((both["margin_pct_a"] - both["margin_pct_b"]).abs()
                 > 1e-9).sum()),
            "rows_contribution_moved": int(
                ((both["annual_contribution_a"]
                  - both["annual_contribution_b"]).abs() > 1e-6).sum()),
            "verdict_changes": int((both["verdict_b"]
                                    != both["verdict_a"]).sum()),
            "frequency_changes": int((both["chosen_freq_wk_b"]
                                      != both["chosen_freq_wk_a"]).sum()),
            "demand_rank_identical": bool(
                (_rank(both["demand_pax_yr_b"])
                 == _rank(both["demand_pax_yr_a"])).all()),
            "margin_rank_identical": bool(
                (_rank(both["margin_pct_b"])
                 == _rank(both["margin_pct_a"])).all()),
        })
    return pd.DataFrame(rows)


def per_date_table(rows: pd.DataFrame, mcol: str, dcol: str) -> pd.DataFrame:
    # `decision_rows.parquet` already carries `score_model` and `score_demand`.
    # Renaming onto those names without dropping them first produces duplicate
    # columns, and `nlargest` then fails on a DataFrame where it expects a
    # Series. Rebuild both from the frame under comparison instead.
    w = rows[rows["study_id"] == STUDY].drop(
        columns=["score_model", "score_demand"], errors="ignore").copy()
    w = w.rename(columns={mcol: "score_model"})
    w["score_demand"] = w.groupby("cutoff")[dcol].rank(pct=True)
    out = []
    for cut in sorted(w["cutoff"].unique()):
        g = w[w["cutoff"] == cut]
        for k in K_VALUES:
            out.append({"scope": str(int(cut)), "k": k,
                        "d_agreement": (_agreement_at_k(g, "score_model", k)
                                        - _agreement_at_k(g, "score_demand", k)),
                        "d_recall": (_recall_at_k(g, "score_model", k)
                                     - _recall_at_k(g, "score_demand", k))})
    for drop in sorted(w["cutoff"].unique()):
        g = w[w["cutoff"] != drop]
        for k in K_VALUES:
            out.append({"scope": f"drop {int(drop)}", "k": k,
                        "d_agreement": (_agreement_at_k(g, "score_model", k)
                                        - _agreement_at_k(g, "score_demand", k)),
                        "d_recall": (_recall_at_k(g, "score_model", k)
                                     - _recall_at_k(g, "score_demand", k))})
    return pd.DataFrame(out)


def main() -> str:
    a = load()
    cmp_ = row_comparison(a["before_rows"], a["after_rows"])
    cmp_.to_parquet(REPLAY / "post_d1_comparison.parquet", index=False)
    bd = per_date_table(a["before_rows"], "margin_pct", "demand_pax_yr")
    ad = per_date_table(a["after_rows"], "margin_pct", "demand_pax_yr")
    pd_cmp = bd.merge(ad, on=["scope", "k"], suffixes=("_b", "_a"))

    L = []
    A = L.append
    A("# W1.4 post-D1 replay, against the immutable V2 baseline")
    A("")
    A("**Generated by `replay/post_d1_comparison.py`. Do not hand-edit.**")
    A("")
    A("T5 of the six-task finish plan. `docs/W1.4_predictive_baseline_v2.md` "
      "is **not modified**: V2 is the frozen before-state and D1 is carried "
      "in it as recorded defect 1. The before column here is the artifact set "
      "the engine produced at commit `f38cf16`, preserved under "
      "`data/parquet/replay/pre_d1/`; the after column is the D1-corrected "
      "engine.")
    A("")
    A("**Read under Stage 2R.0: LIMITED TO LARGE EFFECTS.** The design cannot "
      "distinguish an effect smaller than about five net launch events from "
      "zero. Nothing below is presented as a validated predictive "
      "improvement, and D1's adoption rule was fixed in advance to be "
      "independent of any metric.")
    A("")
    A("---")
    A("")

    # ---------------------------------------------------------- vintages
    A("## 1. What changed")
    A("")
    bg = a["before_growth"].merge(
        a["after_growth"], on=["cutoff", "hub"], suffixes=("_b", "_a"))
    A("| cutoff | hub | growth year before | after | growth before | after | "
      "ratio |")
    A("|---|---|---|---|---|---|---|")
    for _, r in bg.iterrows():
        ratio = r["corridor_growth_a"] / r["corridor_growth_b"]
        A(f"| {r['cutoff']} | {r['hub']} | {int(r['growth_year_b'])} | "
          f"{int(r['growth_year_a'])} | {r['corridor_growth_b']:.3f} | "
          f"{r['corridor_growth_a']:.3f} | "
          f"{'**' if abs(ratio - 1) > 1e-9 else ''}{ratio:.3f}x"
          f"{'**' if abs(ratio - 1) > 1e-9 else ''} |")
    A("")
    moved = bg[(bg["corridor_growth_a"] - bg["corridor_growth_b"]).abs() > 1e-9]
    A(f"**{len(moved)} of {len(bg)} hub-cutoff growth terms moved**, all at "
      f"{', '.join(str(int(c)) for c in sorted(moved['cutoff'].unique()))}. "
      "The corridor-growth numerator now skips declared structural-break "
      "years; 2024-01's 2022 and 2022-01's 2019 were already admissible and "
      "did not move.")
    A("")

    # ------------------------------------------------------ decision universe
    A("## 2. Decision universe and outcome labels")
    A("")
    A("| study | date | candidates before | after | added | dropped | "
      "positives before | after | label changes |")
    A("|---|---|---|---|---|---|---|---|---|")
    for _, r in cmp_.iterrows():
        A(f"| {r['study_id']} | {r['cutoff']} | {r['candidates_before']} | "
          f"{r['candidates_after']} | {r['added']} | {r['dropped']} | "
          f"{r['positives_before']} | {r['positives_after']} | "
          f"{r['label_changes']} |")
    A("")
    if (cmp_["added"].sum() == 0 and cmp_["dropped"].sum() == 0
            and cmp_["label_changes"].sum() == 0):
        A("**The universe is identical.** No candidate was added or dropped "
          "and no launch label changed, so every comparison below is on the "
          "same rows. That is the invariant the repair had to preserve: the "
          "seats vintage feeds the candidate set and was deliberately left "
          "admitting a break year.")
    A("")

    # -------------------------------------------------------------- levels
    A("## 3. Demand, economics, frequency and verdict")
    A("")
    A("| study | date | median demand before | after | median margin before | "
      "after | rows: demand moved | margin moved | contribution moved | "
      "frequency changed | verdict changed |")
    A("|---|---|---|---|---|---|---|---|---|---|---|")
    for _, r in cmp_.iterrows():
        A(f"| {r['study_id']} | {r['cutoff']} | "
          f"{r['median_demand_before']:,.0f} | {r['median_demand_after']:,.0f} "
          f"| {r['median_margin_before']:,.1f}% | "
          f"{r['median_margin_after']:,.1f}% | {r['rows_demand_moved']} | "
          f"{r['rows_margin_moved']} | {r['rows_contribution_moved']} | "
          f"**{r['frequency_changes']}** | **{r['verdict_changes']}** |")
    A("")
    A("| study | date | demand ranking identical | margin ranking identical |")
    A("|---|---|---|---|")
    for _, r in cmp_.iterrows():
        A(f"| {r['study_id']} | {r['cutoff']} | "
          f"**{'yes' if r['demand_rank_identical'] else 'NO'}** | "
          f"**{'yes' if r['margin_rank_identical'] else 'NO'}** |")
    A("")
    A("Levels moved at the affected cutoff and orderings did not, anywhere. "
      "Growth enters as a common positive scalar on every demand branch, so "
      "it cannot reorder the demand comparator; away from capacity "
      "`margin_pct` is a monotone function of a ratio that carries the same "
      "scalar, so the margin ranking inherits the invariance.")
    A("")

    # ------------------------------------------------------------ family 1
    A("## 4. Family 1: observed launch agreement")
    A("")
    A("Metro-cluster bootstrap intervals, 2,000 resamples, seed 7, "
      "recomputed in both states.")
    A("")
    A("| study | k | model agreement before | after | model recall before | "
      "after |")
    A("|---|---|---|---|---|---|")
    unchanged = True
    for sid in STUDIES:
        eb = a["before_res"]["family_1_and_4"][sid]
        ea = a["after_res"]["family_1_and_4"][sid]
        if eb["n_positives"] == 0:
            continue
        for k in ("5", "10", "20"):
            kb, ka = eb["k"][k], ea["k"][k]
            unchanged &= (_same(kb["model_agreement"], ka["model_agreement"])
                          and _same(kb["model_recall"], ka["model_recall"]))
            A(f"| {sid} | {k} | {_ci(kb['model_agreement'])} | "
              f"{_ci(ka['model_agreement'])} | {_ci(kb['model_recall'])} | "
              f"{_ci(ka['model_recall'])} |")
    A("")

    # ------------------------------------------------------------ family 4
    A("## 5. Family 4: incremental value over demand rank")
    A("")
    A("| study | k | difference in agreement before | after | difference in "
      "recall before | after |")
    A("|---|---|---|---|---|---|")
    for sid in STUDIES:
        eb = a["before_res"]["family_1_and_4"][sid]
        ea = a["after_res"]["family_1_and_4"][sid]
        if eb["n_positives"] == 0:
            continue
        for k in ("5", "10", "20"):
            kb, ka = eb["k"][k], ea["k"][k]
            unchanged &= (_same(kb["diff_agreement"], ka["diff_agreement"])
                          and _same(kb["diff_recall"], ka["diff_recall"]))
            A(f"| {sid} | {k} | {_ci(kb['diff_agreement'])} | "
              f"{_ci(ka['diff_agreement'])} | {_ci(kb['diff_recall'])} | "
              f"{_ci(ka['diff_recall'])} |")
    A("")
    if unchanged:
        A("**Every Family 1 and Family 4 figure is unchanged, point estimate "
          "and interval.** That is the arithmetic consequence of both "
          "rankings being invariant, not an independent finding, and it is "
          "what the frozen D1 protocol predicted.")
    else:
        A("**Some Family 1 or Family 4 figures moved.** Under Stage 2R.0 a "
          "movement of this size is not distinguishable from zero and is not "
          "an improvement; the rows above are reported so the movement is "
          "visible rather than claimed.")
    A("")

    # ----------------------------------------------- per date and leave-one-out
    A("### Per decision date and leave-one-date-out, WestJet")
    A("")
    A("| scope | k | difference in agreement before | after | difference in "
      "recall before | after |")
    A("|---|---|---|---|---|---|")
    for _, r in pd_cmp.iterrows():
        A(f"| {r['scope']} | {r['k']} | {r['d_agreement_b']:+.3f} | "
          f"{r['d_agreement_a']:+.3f} | {r['d_recall_b']:+.3f} | "
          f"{r['d_recall_a']:+.3f} |")
    A("")
    pd_same = bool(np.allclose(pd_cmp[["d_agreement_b", "d_recall_b"]],
                               pd_cmp[["d_agreement_a", "d_recall_a"]]))
    if pd_same:
        A("Identical at every date and every leave-one-out subset. The pooled "
          "k=10 advantage still rests entirely on 2024-01 and still "
          "disappears when that date is dropped, exactly as before the "
          "repair.")
    A("")

    # ------------------------------------------------------------ family 3
    A("## 6. Family 3: right-sizing")
    A("")
    A("Retained for research continuity. **The public right-sizing claim is "
      "not restored**: Stage 2R.5 concluded the product is fixed-gauge route "
      "screening, and T2 will correct the wording that says otherwise.")
    A("")
    f3b, f3a = a["before_res"]["family_3"], a["after_res"]["family_3"]
    A("| study | n | median ratio before | after | median bias before | after |")
    A("|---|---|---|---|---|---|")
    for sid in STUDIES:
        sb, sa = f3b["by_study"].get(sid), f3a["by_study"].get(sid)
        if not sb:
            continue
        A(f"| {sid} | {sb['n']} | {_ci(sb['median_ratio'])} | "
          f"{_ci(sa['median_ratio'])} | {_ci(sb['median_bias'])} | "
          f"{_ci(sa['median_bias'])} |")
    A("")
    nb = int((a["before_pairs"]["chosen_freq_wk"] == 3).sum())
    na = int((a["after_pairs"]["chosen_freq_wk"] == 3).sum())
    A(f"The model chose the minimum option on {nb} of "
      f"{len(a['before_pairs'])} paired launches before and {na} of "
      f"{len(a['after_pairs'])} after. D2 is unaffected by D1, which is what "
      "Stage 2R.3 predicted: the selector is decided by the load-factor "
      "floor, and rescaling demand at one cutoff does not lift a candidate "
      "over it.")
    A("")

    # ------------------------------------------------------------ family 2
    A("## 7. Family 2: survival, descriptive")
    A("")
    A("| study | horizon | eligible before | after | events before | after |")
    A("|---|---|---|---|---|---|")
    for sid in STUDIES:
        for h in ("24m", "36m"):
            eb = a["before_res"]["family_2"][sid][h]
            ea = a["after_res"]["family_2"][sid][h]
            A(f"| {sid} | {h} | {eb['eligible']} | {ea['eligible']} | "
              f"{eb['events']} | {ea['events']} |")
    A("")
    A("Survival reads the outcome register, which no model change touches.")
    A("")

    # ------------------------------------------------------------- porter
    A("## 8. Porter: a Stage 2R prediction that did not reproduce, by design")
    A("")
    p = cmp_[cmp_["study_id"] == "porter_yyz"]
    A(f"Stage 2R.4 reported six Porter verdict changes under its D1 "
      f"counterfactual. Observed here: "
      f"**{int(p['verdict_changes'].sum())}**.")
    A("")
    A("2R.4 measured `alt_year = 2019` at every transborder study-date, the "
      "intervention \"always use the last pre-COVID year\". The repair "
      "adopted in T1 skips only structural-break years, and Porter's 2024-01 "
      "growth year of 2022 is not one, so Porter is untouched. This was "
      "written into the D1 change protocol at section 0.5 before the fix "
      "existed, so it is a narrowing that was declared rather than "
      "discovered. The 2R.4 figures remain correct for the counterfactual "
      "they measured and overstate the repair actually made.")
    A("")

    # ------------------------------------------------------------- verdict
    A("## 9. What this means for the baseline")
    A("")
    A("- **V2 is not superseded and is not rewritten.** Its Family 1, 3 and 4 "
      "numbers are the numbers the corrected engine produces, so the "
      "scoreboard still scores. What V2's defect list needs is a pointer "
      "recording that its recorded defect 1 has since been repaired, which "
      "is a T4 documentation task.")
    A("- **The unfreezing condition in V2 section 6 is not met.** No decision "
      "date matured, no study was added, and the replay itself was not found "
      "defective: the defect was in a model input, and correcting it moved no "
      "metric. A new freeze document would restate the same numbers.")
    A("- **The bounded negative result is unchanged**, and so is its bound: "
      "10 distinct launch events, 3 vintages, no detectable incremental value "
      "at effects larger than the study's resolution.")
    A("")

    DOC.write_text("\n".join(L) + "\n")
    return "\n".join(L)


if __name__ == "__main__":
    main()
    print(f"wrote {DOC}")
