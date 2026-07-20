"""Generate the written deliverables from computed outputs.

- WestJet YYC: business cases for the top three anchor-backed candidates
  (markets with their own 2018 StatCan actual), whatever their verdict.
- Alaska SEA: validation report led by the share-model ground-truth check.
- Porter YYZ: portability demonstration, ranked table only.
Markdown by design (renders on GitHub where reviewers actually look).
"""
from __future__ import annotations

import pandas as pd
import yaml

from ingest.common import ROOT
from models.common import OUTPUTS, assumptions

RPT = ROOT / "reports"


def _grid_table(eco: pd.DataFrame, cbsa: str) -> str:
    e = eco[eco["cbsa"] == cbsa]
    lines = ["| fuel \\ fare | -15% | base | +10% |", "|---|---|---|---|"]
    for g in sorted(e["fuel_scenario_pct"].unique()):
        row = [f"| {g:+.0f}% fuel "]
        for f in (-15, 0, 10):
            m = e[(e.fuel_scenario_pct == g) & (e.fare_scenario_pct == f)]
            row.append(f"| {m['margin_pct'].iloc[0]:.1f}% ")
        lines.append("".join(row) + "|")
    return "\n".join(lines)


def westjet_cases(top_n: int = 3) -> list[str]:
    a = assumptions()
    scr = pd.read_parquet(OUTPUTS / "screen_westjet_yyc.parquet")
    eco = pd.read_parquet(OUTPUTS / "economics_westjet_yyc.parquet")
    dem = pd.read_parquet(OUTPUTS / "demand_westjet_yyc.parquet")
    comp = pd.read_parquet(OUTPUTS / "competition_westjet_yyc.parquet")
    tf = yaml.safe_load((OUTPUTS / "transfer_factor.yaml").read_text())
    anchored = scr[scr["demand_method"] == "anchor_x_growth"]
    picks = anchored.sort_values("margin_pct", ascending=False).head(top_n)
    files = []
    for _, r in picks.iterrows():
        d = dem[dem["metro_name"] == r["metro_name"]].iloc[0]
        c = comp[comp["cbsa"] == d["cbsa"]]
        slug = (r["metro_name"].split(",")[0].lower()
                .replace(" ", "_").replace("-", "_").replace(".", ""))
        flag = ("\n**Share-uncertainty flag:** modeled share exceeds 70% with "
                "no nonstop incumbent; competition reconstruction is likely "
                "incomplete. Verdict capped at MONITOR.\n"
                if r.get("share_uncertainty") else "")
        md = f"""# Business case: YYC - {r['metro_name']} (WestJet 737-8)

**Verdict: {r['verdict']}** (confidence: {r['confidence']})
{flag}
## The two numbers that drive this
1. {r['driver_1']}
2. {r['driver_2']}

## Market
- Distance {r['dist_mi']:.0f} mi, proposed 7x weekly, 174 seats.
- Demand {d['demand_pax_yr']:,.0f} pax/yr, method **{d['demand_method']}**:
  the market's own 2018 StatCan actual ({d['anchor_2018_pax']:,.0f} pax,
  frozen table 23-10-0256) times T-100 corridor growth
  {d['t100_growth']:.2f}. Market-specific evidence beats the hub-median
  gravity transfer wherever it exists.
- Gravity cross-check: the gravity x transfer path would have said
  {d['gravity_implied_pax']:,.0f} pax/yr, i.e.
  {d['implied_vs_anchor_ratio']:.2f}x the anchor-based estimate. That ratio
  is printed so a divergence from the last observed actual is never
  invisible. (Transfer factor context: hub median
  {d['transfer_factor']:.2f}, national median {tf['median']:.2f}, IQR
  [{tf['iqr'][0]:.2f}, {tf['iqr'][1]:.2f}].)

## Competition (reconstructed from T-100; no MIDT)
{c[['carrier','itin_type','freq_wk','elapsed_h']].sort_values(['itin_type','freq_wk'], ascending=[True,False]).head(8).to_markdown(index=False) if len(c) else 'No incumbent nonstop or qualifying one-stop found. Treat the share estimate skeptically.'}

Modeled share for the proposed service: {r['proposed_share']:.0%}.

## Economics (fully-allocated proxy: direct cost x comparator indirect burden + fee proxy)
{_grid_table(eco, d['cbsa'])}

Break-even load factor {r['belf']:.2f} vs planned {r['load_factor']:.2f}.
Fare from distance-matched US markets x {a['transborder_fare_premium']['value']:.2f}
premium (assumption, sensitivity in grid). Costs from Southwest P-5.2 filings
with fuel rebuilt at EIA scenario prices.

## Top risk
{r['top_risk']}

## Assumptions this rests on
{r['key_assumptions']} - all in config/assumptions.yaml with sources,
confidence, and sensitivity ranges. Margins carry the comparator's own
indirect burden (derived from Form 41), so the hurdle is fully-allocated.
"""
        path = RPT / f"westjet_yyc_{slug}.md"
        path.write_text(md)
        files.append(str(path))
    return files


def alaska_validation() -> str:
    scr = pd.read_parquet(OUTPUTS / "screen_alaska_sea.parquet")
    obs = scr[scr["demand_source"] == "observed"]
    sv = pd.read_parquet(OUTPUTS / "share_validation.parquet")
    mae = 100 * sv["abs_err"].mean()
    md = f"""# Alaska SEA: end-to-end validation study

US domestic is the one arena where demand, share, and fare are all observed.
The ground-truth check that matters is the share model: the same QSI-lite
machinery that scores Canadian candidates, scored here against observed DB1B
carrier shares.

## The ground-truth result

- **Share model MAE: {mae:.1f} share points** across {len(sv)} market-carrier
  rows at SEA, reported by market structure in docs/validation.md.
- Demand for screened candidates is observed DB1B ({len(obs)} of {len(scr)}
  markets); every gravity-filled row is flagged `modeled`.

## Reading the all-PASS screen honestly

All {len(scr)} remaining unserved candidates screen PASS. That is largely a
fixed-gauge artifact, not proof of hub saturation: this study evaluates one
schedule shape (daily, 178-seat mainline), and the remaining unserved SEA
markets are thin enough that a daily 737-9 loses money by construction. A
frequency-and-gauge optimization step (out of scope here, listed as an
extension) would evaluate 4x-weekly or regional-gauge service and would
plausibly turn some of these into viable candidates. What the uniform PASS
does show is that the screen does not invent opportunities at a mature hub
where the observed network has already taken the markets that fit this
gauge - a useful negative check on the machinery, stated no more strongly
than that.

## Ranked screen (top 15 by margin)
{scr.head(15)[['metro_name','verdict','margin_pct','belf','load_factor','proposed_share','demand_source','n_nonstop_incumbents']].to_markdown(index=False)}
"""
    path = RPT / "alaska_sea_validation.md"
    path.write_text(md)
    return str(path)


def porter_table() -> str:
    scr = pd.read_parquet(OUTPUTS / "screen_porter_yyz.parquet")
    md = f"""# Porter YYZ: portability demonstration

Same engine, different config: carrier PD, hub YYZ, E195-E2 economics (B6
E190 proxy with the documented E2 fuel adjustment), YYZ competitive set.
Ranked table only by design; no full business cases.

Verdicts: {scr['verdict'].value_counts().to_dict()}

{scr.head(20)[['metro_name','verdict','margin_pct','belf','proposed_share','share_uncertainty','demand_method','demand_pax_yr','n_nonstop_incumbents','top_competitor']].to_markdown(index=False)}
"""
    path = RPT / "porter_yyz_portability.md"
    path.write_text(md)
    return str(path)


if __name__ == "__main__":
    print(westjet_cases())
    print(alaska_validation())
    print(porter_table())
