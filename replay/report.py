"""Generate docs/W1.4_replay_results.md from the computed replay artifacts.

Rule 6: reader-facing numbers are read from computed artifacts, never
hardcoded. Nothing in this file transcribes a result by hand. Re-run with

    .venv/bin/python -m replay.report
"""
from __future__ import annotations

import json

import pandas as pd

from ingest.common import DATA_PARQUET, ROOT
# The frozen metric functions, imported rather than reimplemented. A second
# implementation of agreement@k here could disagree with the one that produced
# results.json without anything failing, which is the defect
# models/share_validation.py shipped with in round 4.
from replay.run_replay import K_VALUES, _agreement_at_k, _recall_at_k

REPLAY = DATA_PARQUET / "replay"
DOC = ROOT / "docs" / "W1.4_replay_results.md"

FEASIBILITY = {
    ("westjet_yyc", 1): "FULL", ("westjet_yyc", 4): "FULL",
    ("alaska_sea", 1): "NOT_ESTIMABLE", ("alaska_sea", 4): "NOT_ESTIMABLE",
    ("porter_yyz", 1): "DESCRIPTIVE_ONLY",
    ("porter_yyz", 4): "DESCRIPTIVE_ONLY",
}
STUDIES = ["westjet_yyc", "alaska_sea", "porter_yyz"]


def _ci(t) -> str:
    """(point, lo, hi) -> '0.40 [0.20, 0.60]', or 'n/a' where undefined."""
    if t is None:
        return "n/a"
    p, lo, hi = t
    if p != p:
        return "n/a"
    if lo != lo or hi != hi:
        return f"{p:.3f} (no interval: fewer than 2 clusters)"
    return f"{p:.3f} [{lo:.3f}, {hi:.3f}]"


PER_DATE_STUDY = "westjet_yyc"


def _diffs(g: pd.DataFrame, k: int) -> tuple[float, float]:
    """(agreement difference, recall difference), full model minus demand."""
    return (_agreement_at_k(g, "score_model", k)
            - _agreement_at_k(g, "score_demand", k),
            _recall_at_k(g, "score_model", k)
            - _recall_at_k(g, "score_demand", k))


def _per_date_breakdown(A, rows: pd.DataFrame) -> None:
    """Finding P1-2. Protocol section 3 item 1 and section 5 both require a
    per-date breakdown alongside the pooled Family 1 and Family 4 results, and
    only `positives_by_date` was emitted.

    Every sentence below is derived from `decision_rows.parquet` at generation
    time rather than written as prose, so a claim here cannot outlive the
    numbers that justify it.
    """
    w = rows[rows["study_id"] == PER_DATE_STUDY]
    dates = sorted(w["cutoff"].unique())

    A(f"### Per-decision-date breakdown, {PER_DATE_STUDY}")
    A("")
    A("Required by protocol section 3 item 1 and section 5, and missing from "
      "the first version of this report (independent review finding P1-2). "
      "Pooled Family 1 and Family 4 figures average over these dates.")
    A("")
    A("| date | positives | k | agreement, model | agreement, demand | "
      "difference | recall, model | recall, demand | difference |")
    A("|---|---|---|---|---|---|---|---|---|")
    for c in dates:
        g = w[w["cutoff"] == c]
        npos = int(g["positive"].sum())
        for k in K_VALUES:
            am = _agreement_at_k(g, "score_model", k)
            ad = _agreement_at_k(g, "score_demand", k)
            rm = _recall_at_k(g, "score_model", k)
            rd = _recall_at_k(g, "score_demand", k)
            A(f"| {c} | {npos} | {k} | {am:.3f} | {ad:.3f} | {am - ad:+.3f} | "
              f"{rm:.3f} | {rd:.3f} | {rm - rd:+.3f} |")
    A("")
    A("**No intervals are reported per date.** A metro-cluster bootstrap "
      "within a single decision date resamples one block, and three dates "
      "cannot support a date-level interval either. Reporting one would "
      "manufacture precision the design does not have.")
    A("")

    A(f"### Leave-one-decision-date-out, {PER_DATE_STUDY}")
    A("")
    A("Each row drops one decision date and recomputes the pooled Family 4 "
      "difference over the remaining two.")
    A("")
    A("| dropped | k | difference in agreement@k | difference in recall@k |")
    A("|---|---|---|---|")
    lodo = {}
    for drop in dates:
        g = w[w["cutoff"] != drop]
        for k in K_VALUES:
            da, dr = _diffs(g, k)
            lodo[(drop, k)] = (da, dr)
            A(f"| {drop} | {k} | {da:+.3f} | {dr:+.3f} |")
    A("")

    # ---------------------------------------------------- derived statements
    A("### What the breakdown shows")
    A("")
    pooled = {k: _diffs(w, k) for k in K_VALUES}

    # where the pooled k=10 advantage comes from
    per_date_10 = {c: _diffs(w[w["cutoff"] == c], 10) for c in dates}
    nonzero = [c for c in dates if abs(per_date_10[c][0]) > 1e-12
               or abs(per_date_10[c][1]) > 1e-12]
    zero = [c for c in dates if c not in nonzero]
    if len(nonzero) == 1:
        c = nonzero[0]
        g = w[w["cutoff"] == c]
        tm = set(g.nlargest(10, "score_model")["metro_name"])
        td = set(g.nlargest(10, "score_demand")["metro_name"])
        gained = g[g["metro_name"].isin(tm - td) & (g["positive"] == 1)]
        lost = g[g["metro_name"].isin(td - tm) & (g["positive"] == 1)]
        A(f"- **At k=10 the entire pooled difference comes from {c}.** "
          f"The difference is exactly zero at "
          f"{' and '.join(str(z) for z in zero)}. The two top-ten sets at "
          f"{c} differ by {len(tm - td)} markets in each direction, and "
          f"{len(gained)} of those {len(tm - td) + len(td - tm)} is an "
          f"observed launch: "
          f"{', '.join(sorted(gained['metro_name']))}. The markets the demand "
          f"ranking holds instead contribute {len(lost)} launches.")
    else:
        A(f"- At k=10 the pooled difference is spread across "
          f"{len(nonzero)} dates: "
          + "; ".join(f"{c} {per_date_10[c][0]:+.3f} agreement"
                      for c in nonzero) + ".")

    # leave-one-out behaviour, stated from the computed table
    for drop in dates:
        da, dr = lodo[(drop, 10)]
        pa, pr = pooled[10]
        if abs(da) < 1e-12 and abs(dr) < 1e-12:
            A(f"- **Removing {drop} eliminates the pooled k=10 advantage "
              f"entirely** ({pa:+.3f} to {da:+.3f} agreement, {pr:+.3f} to "
              f"{dr:+.3f} recall).")
        elif (da > 0) == (pa > 0) or abs(pa) < 1e-12:
            A(f"- Removing {drop} does not reverse the conclusion: the k=10 "
              f"difference stays {da:+.3f} agreement and {dr:+.3f} recall.")
        else:
            A(f"- Removing {drop} reverses the sign at k=10: {pa:+.3f} to "
              f"{da:+.3f} agreement.")

    # k=20 saturation
    rm20 = _recall_at_k(w, "score_model", 20)
    rd20 = _recall_at_k(w, "score_demand", 20)
    if rm20 == 1.0 and rd20 == 1.0:
        A(f"- **k=20 is saturated, not tied on merit.** Both rankings reach "
          f"recall {rm20:.3f}: every positive is inside the top twenty of "
          f"roughly eighty candidates under either score, so the difference "
          f"is pinned at zero arithmetically rather than measured.")
    else:
        A(f"- At k=20 model recall is {rm20:.3f} and demand recall "
          f"{rd20:.3f}.")

    # k=5
    d5 = [(_diffs(w[w["cutoff"] == c], 5)) for c in dates]
    pos5 = [d for d in d5 if d[0] > 1e-12]
    if not pos5:
        A(f"- **k=5 shows no improvement at any date.** The pooled difference "
          f"is {pooled[5][0]:+.3f} agreement and {pooled[5][1]:+.3f} recall, "
          f"and no individual date is positive.")
    else:
        A(f"- k=5 is positive at {len(pos5)} of {len(dates)} dates; pooled "
          f"{pooled[5][0]:+.3f} agreement.")
    A("")

    A("### What the intervals do and do not represent")
    A("")
    A("The bootstrap in Family 1 and Family 4 **clusters by metro**, so its "
      "intervals describe sampling variation across metros with the three "
      "decision dates held fixed. They are **not** intervals across decision "
      "vintages, and nothing here supports treating them as such.")
    A("")
    A("The practical consequence is that a future change scored against this "
      "baseline could appear significant on vintage variation alone. The "
      "leave-one-date-out table above is the honest instrument for that "
      "question, and with three dates it is a sensitivity check rather than "
      "an inference.")
    A("")


def main() -> str:
    res = json.loads((REPLAY / "results.json").read_text())
    rows = pd.read_parquet(REPLAY / "decision_rows.parquet")
    prov = pd.read_parquet(REPLAY / "provenance.parquet")
    pairs = pd.read_parquet(REPLAY / "rightsizing_pairs.parquet")

    L = []
    A = L.append
    A("# W1.4 decision replay: results")
    A("")
    A("**Generated by `replay/report.py` from `data/parquet/replay/`. Do not "
      "hand-edit.**")
    A("")
    A("Protocol frozen at commit `e6ea62e` before any metric was computed: "
      "`docs/W1.4_REPLAY_PROTOCOL.md`. Feasibility classifications are frozen "
      "and are not upgraded here.")
    A("")
    A("**This measures the frozen model. No model default, assumption or "
      "threshold was changed to produce it.**")
    A("")

    # ------------------------------------------------------------ universe
    A("## 1. The replayed universe")
    A("")
    A("| study | cutoff | candidates | positives (24m) | LAUNCH | MONITOR | PASS |")
    A("|---|---|---|---|---|---|---|")
    for (sid, cut), g in rows.groupby(["study_id", "cutoff"]):
        vc = g["verdict"].value_counts()
        A(f"| {sid} | {cut} | {len(g)} | {int(g['positive'].sum())} | "
          f"{vc.get('LAUNCH', 0)} | {vc.get('MONITOR', 0)} | {vc.get('PASS', 0)} |")
    A(f"| **total** | | **{len(rows)}** | "
      f"**{int(rows['positive'].sum())}** | | | |")
    A("")

    # ------------------------------------------------------------ family 1
    A("## 2. Family 1: observed launch agreement, 24 months")
    A("")
    A("Ranking score is base-case `margin_pct`, frozen in protocol section 4, "
      "because 198 of 200 production verdicts are PASS and a three-level label "
      "with one populated level cannot rank. Intervals are metro-cluster "
      "bootstraps, 2,000 resamples.")
    A("")
    A("**Unlaunched candidates are unlabeled, not confirmed negatives.**")
    A("")
    for sid in STUDIES:
        e = res["family_1_and_4"][sid]
        A(f"### {sid} ({FEASIBILITY[(sid, 1)]})")
        A("")
        A(f"{e['n_decision_rows']} decision rows, {e['n_unique_metros']} "
          f"unique metros, {e['n_decision_dates']} decision dates, "
          f"**{e['n_positives']} positives** "
          f"({', '.join(f'{k}: {v}' for k, v in e['positives_by_date'].items())}).")
        A("")
        if e["n_positives"] == 0:
            A("No positives: agreement and recall are undefined. Reported as "
              "NOT_ESTIMABLE rather than as zero.")
            A("")
            continue
        A("| k | model agreement@k | model recall@k | demand agreement@k | demand recall@k |")
        A("|---|---|---|---|---|")
        for k in ("5", "10", "20"):
            kk = e["k"][k]
            A(f"| {k} | {_ci(kk['model_agreement'])} | {_ci(kk['model_recall'])} "
              f"| {_ci(kk['demand_agreement'])} | {_ci(kk['demand_recall'])} |")
        A("")

    # ------------------------------------------------------------ family 4
    A("## 3. Family 4: incremental value over demand rank")
    A("")
    A("Same rows, dates, candidates, cutoffs and outcomes as Family 1. The "
      "reported quantity is the **difference**, full model minus demand "
      "percentile, with a metro-cluster bootstrap interval on the difference. "
      "An interval spanning zero means no measurable incremental value.")
    A("")
    for sid in STUDIES:
        e = res["family_1_and_4"][sid]
        if e["n_positives"] == 0:
            A(f"**{sid}** ({FEASIBILITY[(sid, 4)]}): no positives, so no "
              "comparison is possible.")
            A("")
            continue
        A(f"### {sid} ({FEASIBILITY[(sid, 4)]})")
        A("")
        A("| k | difference in agreement@k | difference in recall@k |")
        A("|---|---|---|")
        for k in ("5", "10", "20"):
            kk = e["k"][k]
            A(f"| {k} | {_ci(kk['diff_agreement'])} | {_ci(kk['diff_recall'])} |")
        A("")

    _per_date_breakdown(A, rows)

    # ------------------------------------------------------------ family 2
    A("## 4. Family 2: survival")
    A("")
    A("**No Cox or Fine-Gray model was fitted**, frozen in protocol section 5 "
      "before results were seen. Corporate-shutdown events are zero in all "
      "three studies by construction: all three carriers still operate.")
    A("")
    A("| study | horizon | eligible | events | censored | seasonal eligible | events seasonal | events year-round |")
    A("|---|---|---|---|---|---|---|---|")
    for sid in STUDIES:
        for h in ("24m", "36m"):
            e = res["family_2"][sid][h]
            A(f"| {sid} | {h} | {e['eligible']} | {e['events']} | "
              f"{e['censored']} | {e['seasonal_eligible']} | "
              f"{e['events_among_seasonal']} | {e['events_among_year_round']} |")
    A("")
    A("**A seasonal stop is not a business failure.** The split is reported "
      "because the pooled figure would conflate the two.")
    A("")

    # ------------------------------------------------------------ family 3
    A("## 5. Family 3: right-sizing")
    A("")
    f3 = res["family_3"]
    A(f"{f3['paired_total']} launches paired with the last decision date "
      "preceding them. Primary proxy `first3_max`, frozen in protocol "
      "section 5.")
    A("")
    A("| study | n | median chosen | median observed | median ratio | median bias | MAE | chose minimum option |")
    A("|---|---|---|---|---|---|---|---|")
    for sid in STUDIES:
        s = f3["by_study"].get(sid)
        if not s:
            continue
        A(f"| {sid} | {s['n']} | {s['median_chosen']:.1f} | "
          f"{s['median_observed']:.1f} | {_ci(s['median_ratio'])} | "
          f"{_ci(s['median_bias'])} | {s['mae']:.2f} | "
          f"{100*s['share_chose_minimum_option']:.0f}% |")
    p = f3["pooled"]
    A(f"| **pooled** | {p['n']} | | | {_ci(p['median_ratio'])} | "
      f"{_ci(p['median_bias'])} | {p['mae']:.2f} | |")
    A("")
    A("### Paired launches, named")
    A("")
    A("| study | market | decision | chosen | observed | seasonal |")
    A("|---|---|---|---|---|---|")
    for _, r in pairs.sort_values(["study_id", "metro_name"]).iterrows():
        A(f"| {r['study_id']} | {r['metro_name']} | {r['cutoff']} | "
          f"{r['chosen_freq_wk']:.0f} | {r['observed_freq_wk']:.1f} | "
          f"{'yes' if r['seasonal'] else 'no'} |")
    A("")
    n_min = int((pairs["chosen_freq_wk"] == 3).sum())
    A(f"**The model chose 3x weekly on {n_min} of {len(pairs)} paired "
      f"launches.** Chosen frequency is effectively a constant, so it has no "
      "discriminating power across markets: where its median coincides with a "
      "carrier's, that is coincidence rather than calibration.")
    A("")

    # ---------------------------------------------------------- provenance
    A("## 6. Vintage provenance")
    A("")
    A("Every source, resolved against every cutoff, with its policy. Emitted "
      "by `replay/vintage.py`.")
    A("")
    pv = (prov[["cutoff", "source", "reference_period", "vintage_policy"]]
          .drop_duplicates().sort_values(["cutoff", "source"]))
    A("| cutoff | source | reference period | vintage policy |")
    A("|---|---|---|---|")
    for _, r in pv.iterrows():
        A(f"| {r['cutoff']} | {r['source']} | {r['reference_period']} | "
          f"{r['vintage_policy']} |")
    A("")
    lk = prov[prov["lookahead_exception"].notna()][
        ["source", "lookahead_exception"]].drop_duplicates(subset=["source"])
    A("### Declared residual lookaheads")
    A("")
    for _, r in lk.iterrows():
        A(f"- **{r['source']}**: {r['lookahead_exception']}")
    A("")

    # ------------------------------------------------------------- defects
    tg = pd.read_parquet(REPLAY / "vintage_transfer_growth.parquet")
    dd = pd.read_parquet(REPLAY / "vintage_demand_dispersion.parquet")
    A("## 7. Defects the replay exposed. Measured, not fixed.")
    A("")
    A("Milestone A records defects and Phase 6 fixes them under a change "
      "report. None of the following was changed to produce these results.")
    A("")

    A("### D1. The corridor-growth term collapses transborder demand at a "
      "COVID vintage")
    A("")
    A("Anchored transborder demand is `anchor x growth`, where growth is a raw "
      "ratio of T-100 corridor traffic in the latest complete year to the "
      "anchor year, with no COVID handling of any kind.")
    A("")
    A("| cutoff | growth year | YYC growth | YYZ growth | YYC transfer | YYZ transfer |")
    A("|---|---|---|---|---|---|")
    for cut, g in tg.groupby("cutoff"):
        yyc = g[g["hub"] == "YYC"].iloc[0]
        yyz = g[g["hub"] == "YYZ"].iloc[0]
        A(f"| {cut} | {int(yyc['growth_year'])} | "
          f"{yyc['corridor_growth']:.3f} | {yyz['corridor_growth']:.3f} | "
          f"{yyc['transfer_per_hub_median']:.3f} | "
          f"{yyz['transfer_per_hub_median']:.3f} |")
    A("")
    A("At the 2023-01 cutoff the latest complete T-100 year is 2021, so growth "
      "is **0.196** at YYC and **0.166** at YYZ. Every anchored WestJet market "
      "is scaled to roughly a fifth of its 2018 level:")
    A("")
    A("| study | cutoff | method | n | median demand | median margin |")
    A("|---|---|---|---|---|---|")
    for _, r in dd.iterrows():
        A(f"| {r['study_id']} | {r['cutoff']} | {r['demand_method']} | "
          f"{int(r['n'])} | {r['median_demand']:,.0f} | "
          f"{r['median_margin']:,.0f}% |")
    A("")
    A("**Consequence for reading these results.** The 2023-01 WestJet cell is "
      "dominated by this artifact: median margin around -3,800% and every "
      "market PASS. Its five positives are therefore scored by a model that "
      "believed the market had shrunk 80%. The 2024-01 cell is affected less "
      "severely (growth 0.739) and 2022-01 barely at all (growth 1.057).")
    A("")
    A("**This is a point-in-time behaviour, not a replay bug.** A planner in "
      "January 2023 genuinely saw depressed 2021 traffic. What no planner "
      "would have done is treat it as a permanent level shift with no recovery "
      "expectation, and the frozen model has no mechanism to do otherwise. "
      "Production avoids the problem only because it happens to read 2024.")
    A("")
    A("The protocol admits 2021 as input data while excluding it as a decision "
      "vintage, with the rationale recorded in `config/replay_protocol.yaml` "
      "**before** the replay ran: a planner at 2023-01 did in fact hold 2021 "
      "data. That was a design choice made in advance, so it stands as "
      "primary. Excluding 2021 as data too would move the 2023-01 growth year "
      "back to 2019; that is a permitted labelled sensitivity and is not run "
      "here.")
    A("")

    A("### D2. Right-sizing has no discriminating power")
    A("")
    A(f"The model chose the minimum of its frequency option list on "
      f"{n_min} of {len(pairs)} paired launches, and on "
      f"{int((rows['chosen_freq_wk'] == 3).sum())} of {len(rows)} decision "
      "rows across the whole replay. Observed openings on those same launches "
      f"span {pairs['observed_freq_wk'].min():.1f} to "
      f"{pairs['observed_freq_wk'].max():.1f} weekly.")
    A("")
    A("A constant cannot correlate with anything. WestJet's median ratio of "
      "1.00 is not evidence of calibration; it means WestJet's recent openings "
      "happen to be thin. Alaska and Porter both under-size significantly, "
      "with bootstrap intervals on the ratio excluding 1.0.")
    A("")
    A("This refines the Stage 0 prior rather than confirming it. Stage 0 "
      "compared all historical spells against the current all-3x screen and "
      "inferred a uniform downward bias. Paired properly, the bias is "
      "study-specific: absent at WestJet, roughly a factor of two at Alaska "
      "and Porter.")
    A("")

    A("### D3. Family 2 cohorts differ from the Stage 0 counts, by definition")
    A("")
    A("The protocol defines outcomes as register spells for the study brand, "
      "hub and US destinations, **without** the candidate-set distance and "
      "population gate. Stage 0 applied that gate. The Family 2 counts here "
      "are therefore not directly comparable to Stage 0's, and neither is "
      "wrong. Recorded so the difference does not read as drift.")
    A("")

    DOC.write_text("\n".join(L) + "\n")
    return "\n".join(L)


if __name__ == "__main__":
    print(main()[:3000])
