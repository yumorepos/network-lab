"""Run the full model chain for all three studies and write validation.md."""
from __future__ import annotations

import yaml

from ingest.common import ROOT, log
from . import competition, demand, economics, gravity, screen, \
    share_validation, transfer
from .common import OUTPUTS

STUDIES = ("westjet_yyc", "alaska_sea", "porter_yyz")


def main() -> int:
    log("gravity: fitting both vintages")
    grav = {v: gravity.fit(v) for v in ("current", "pre2022")}
    log("transfer factor")
    tf = transfer.estimate()
    for s in STUDIES:
        log(f"demand: {s}")
        demand.resolve(s)
    for s in STUDIES:
        log(f"share: {s}")
        competition.qsi_share(s)
    log("share validation vs DB1B (SEA)")
    sv = share_validation.validate()
    for s in STUDIES:
        log(f"economics: {s}")
        economics.scenario_grid(s)
    for s in STUDIES:
        log(f"screen: {s}")
        screen.run(s)

    lines = ["# Validation", "",
             "## Gravity model (holdout, prediction variant)", ""]
    for v, g in grav.items():
        # OLS reports R2; Poisson QMLE has no OLS R2 and reports level-scale
        # aggregate calibration instead, which is the metric that motivated it.
        # Keeping the OLS branch character-identical matters: validation.md is
        # a generated reader-facing doc pinned by the consistency tests.
        if "r2" in g["predict"]:
            fit_stat = f"R2 {g['predict']['r2']:.3f}"
        else:
            agg = g["holdout"].get("aggregate_pred_over_obs")
            fit_stat = (f"estimator {g.get('estimator', 'unknown')}, "
                        f"aggregate pred/obs {agg:.3f}" if agg is not None
                        else f"estimator {g.get('estimator', 'unknown')}")
        lines += [f"### {v} ({g['years'][0]}-{g['years'][1]})",
                  f"- markets: {g['n_markets']}, {fit_stat}, "
                  f"holdout median APE {g['holdout']['median_ape']:.2f}",
                  "",
                  "| size band (pax/yr) | n | median APE | mean APE |",
                  "|---|---|---|---|"]
        for b in g["holdout"]["by_band"]:
            lines.append(f"| {b['band']} | {b['n']} | {b['median_ape']:.2f} "
                         f"| {b['mean_ape']:.2f} |")
        lines.append("")
    lines += ["## Transfer factor (2018 anchor)", "",
              f"- pairs: {tf['n_pairs']}, median {tf['median']:.2f}, "
              f"IQR [{tf['iqr'][0]:.2f}, {tf['iqr'][1]:.2f}], "
              f"range [{tf['min']:.2f}, {tf['max']:.2f}]",
              f"- per-hub medians: "
              + ", ".join(f"{h} {m:.2f}"
                          for h, m in tf["per_hub_median"].items()),
              "- the dispersion is the honest uncertainty of transferring a "
              "US-calibrated model across the border; business cases carry it",
              ""]
    lines += ["## Share model vs observed DB1B shares "
              f"({sv['hub']}, {sv['year']})", "",
              f"- market-carrier rows: {sv['n_market_carrier_rows']}, "
              f"MAE {sv['mae_share_points']:.1f} share points", "",
              "| market structure | n | MAE (pts) |", "|---|---|---|"]
    for k, v in sv["by_structure"].items():
        lines.append(f"| {k} | {v['n']} | {v['mae_pts']:.1f} |")
    lines += ["",
              "Two figures the unweighted MAE hides. Most rows are tiny "
              "carriers in a market, so the",
              "passenger-weighted error is the one a planner should read: "
              f"**{sv['pax_weighted_mae_share_points']:.1f} share points**. "
              "And modeled shares sum to",
              f"{sv['mean_modeled_share_sum_per_market']:.3f} per market, "
              "which is the invariant that exposed the",
              "operating-versus-marketing carrier defect in Round 4 (it summed "
              "to 0.790 before).", ""]
    lines += ["",
              "## Alaska SEA end-to-end note",
              "",
              "The alaska_sea study runs the identical chain with demand and",
              "fares observed rather than modeled; its screen output plus the",
              "share MAE above constitute the ground-truth check on the",
              "machinery that scores Canadian transborder candidates.", ""]
    (ROOT / "docs" / "validation.md").write_text("\n".join(lines))
    log("validation.md written")
    write_headline_metrics(sv, tf)
    return 0


def write_headline_metrics(sv: dict, tf: dict) -> dict:
    """One generated file every hand-written doc's headline numbers must match.

    README, PROGRESS.md, the interview story and the resume material each
    restated verdict counts and validation figures from memory, and each
    drifted. After Round 4 the README still advertised Porter at 5 LAUNCH when
    the corrected model said 1, and nothing failed: the consistency suite
    guarded the GENERATED reports and never looked at the hand-written docs.

    This is the single source of truth. `tests/test_consistency.py` reads it and
    fails the build if any hand-written doc states a verdict count that
    disagrees. Regenerated by `make models`; never hand-edit.
    """
    import pandas as pd
    out = {"studies": {}}
    for sid in STUDIES:
        scr = pd.read_parquet(OUTPUTS / f"screen_{sid}.parquet")
        counts = scr["verdict"].value_counts()
        out["studies"][sid] = {
            "n_candidates": int(len(scr)),
            "LAUNCH": int(counts.get("LAUNCH", 0)),
            "MONITOR": int(counts.get("MONITOR", 0)),
            "PASS": int(counts.get("PASS", 0)),
            "launch_markets": sorted(
                scr[scr["verdict"] == "LAUNCH"]["metro_name"].tolist()),
            "monitor_markets": sorted(
                scr[scr["verdict"] == "MONITOR"]["metro_name"].tolist()),
        }
    out["n_candidates_total"] = sum(s["n_candidates"]
                                    for s in out["studies"].values())
    out["share_validation"] = {
        "n_rows": int(sv["n_market_carrier_rows"]),
        "mae_share_points": round(float(sv["mae_share_points"]), 1),
        "pax_weighted_mae_share_points":
            round(float(sv["pax_weighted_mae_share_points"]), 1)}
    out["transfer_factor"] = {
        "median": round(float(tf["median"]), 2),
        "iqr": [round(float(tf["iqr"][0]), 2), round(float(tf["iqr"][1]), 2)],
        "n_pairs": int(tf.get("n_pairs") or tf.get("pairs") or 0)}

    bt_path = OUTPUTS / "backtest_scores.parquet"
    if bt_path.exists():
        bt = pd.read_parquet(bt_path).dropna(subset=["pctile"])
        # `outcome`, not `status`. `outcome` is the derived grouping that folds
        # seasonal routes into operating (a seasonal route is still flying, just
        # not year-round); `status` keeps them separate. Reading `status` here
        # gave 42 instead of 48 and briefly put a wrong N into the README, which
        # test_backtest_n_consistent caught.
        resolved = bt[bt["outcome"].isin(["operating", "ceased"])]
        out["backtest"] = {
            "n_scored": int(len(bt)),
            "n_launched_and_resolved": int(len(resolved)),
            "median_pctile_operating": round(float(
                bt[bt["outcome"] == "operating"]["pctile"].median()), 2),
            "median_pctile_ceased": round(float(
                bt[bt["outcome"] == "ceased"]["pctile"].median()), 2)}

    (OUTPUTS / "headline_metrics.yaml").write_text(
        "# GENERATED by models/run_all.py. Single source of truth for every\n"
        "# headline number quoted in a hand-written doc. Never hand-edit.\n"
        + yaml.safe_dump(out, sort_keys=False))
    log("headline_metrics.yaml written")
    return out


if __name__ == "__main__":
    raise SystemExit(main())
