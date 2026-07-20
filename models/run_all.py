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
        lines += [f"### {v} ({g['years'][0]}-{g['years'][1]})",
                  f"- markets: {g['n_markets']}, R2 {g['predict']['r2']:.3f}, "
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
              "## Alaska SEA end-to-end note",
              "",
              "The alaska_sea study runs the identical chain with demand and",
              "fares observed rather than modeled; its screen output plus the",
              "share MAE above constitute the ground-truth check on the",
              "machinery that scores Canadian transborder candidates.", ""]
    (ROOT / "docs" / "validation.md").write_text("\n".join(lines))
    log("validation.md written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
