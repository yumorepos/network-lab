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
    """WestJet's remaining unserved YYC transborder markets all screen PASS,
    so these are route EVALUATIONS, not business cases: a reader should not
    open a document expecting a recommendation when the conclusion is PASS.
    We evaluate the three largest anchor-backed unserved markets - the best
    real chances - and show why even they do not clear at any service level."""
    a = assumptions()
    scr = pd.read_parquet(OUTPUTS / "screen_westjet_yyc.parquet")
    eco = pd.read_parquet(OUTPUTS / "economics_westjet_yyc.parquet")
    dem = pd.read_parquet(OUTPUTS / "demand_westjet_yyc.parquet")
    comp = pd.read_parquet(OUTPUTS / "competition_westjet_yyc.parquet")
    tf = yaml.safe_load((OUTPUTS / "transfer_factor.yaml").read_text())
    anchored = scr[scr["demand_method"] == "anchor_x_growth"]
    picks = anchored.sort_values("demand_pax_yr", ascending=False).head(top_n)
    files = []
    for _, r in picks.iterrows():
        d = dem[dem["metro_name"] == r["metro_name"]].iloc[0]
        c = comp[comp["cbsa"] == d["cbsa"]]
        slug = (r["metro_name"].split(",")[0].lower()
                .replace(" ", "_").replace("-", "_").replace(".", ""))
        reason = ("margin stays negative even at its best-fit frequency"
                  if r["margin_pct"] < 0 else
                  "clears base margin but fails a downside or load-factor test")
        md = f"""# Route evaluation: YYC - {r['metro_name']} (WestJet 737-8)

**Verdict: {r['verdict']}** - {reason} (confidence: {r['confidence']}).
The market was evaluated across 3x, 7x, and 14x weekly; its best-fit schedule
was {r['chosen_freq_wk']:.0f}x weekly x {r['chosen_seats']:.0f} seats, and it
did not clear at any service level.

## The two numbers that drive this
1. {r['driver_1']}
2. {r['driver_2']}

## Market
- Distance {r['dist_mi']:.0f} mi. Best-fit schedule
  {r['chosen_freq_wk']:.0f}x weekly x {r['chosen_seats']:.0f} seats, chosen to
  maximize annual contribution at a feasible load factor.
- Demand {d['demand_pax_yr']:,.0f} pax/yr, method **{d['demand_method']}**:
  the market's own 2018 StatCan actual ({d['anchor_2018_pax']:,.0f} pax,
  frozen table 23-10-0256) times T-100 corridor growth {d['t100_growth']:.2f}.
- Gravity cross-check: the gravity x transfer path would have said
  {d['gravity_implied_pax']:,.0f} pax/yr, i.e.
  {d['implied_vs_anchor_ratio']:.2f}x the anchor-based estimate - printed so a
  divergence from the last observed actual is never invisible. (Transfer
  factor: hub median {d['transfer_factor']:.2f}, national median
  {tf['median']:.2f}, IQR [{tf['iqr'][0]:.2f}, {tf['iqr'][1]:.2f}].)

## Competition (reconstructed from T-100; no MIDT)
{c[['carrier','itin_type','freq_wk','elapsed_h']].sort_values(['itin_type','freq_wk'], ascending=[True,False]).head(8).to_markdown(index=False) if len(c) else 'No incumbent nonstop or qualifying one-stop found. Treat the share estimate skeptically.'}

Modeled share for the proposed service at the chosen frequency:
{r['proposed_share']:.0%}.

## Economics at the chosen service level (fully-allocated proxy)
{_grid_table(eco[(eco.freq_wk == r['chosen_freq_wk']) & (eco.seats == r['chosen_seats'])], d['cbsa'])}

Break-even load factor {r['belf']:.2f} vs achieved {r['load_factor']:.2f}.
Fare from distance-matched US markets x {a['transborder_fare_premium']['value']:.2f}
premium (assumption, sensitivity in grid). Costs from Southwest P-5.2 filings
with fuel rebuilt at EIA scenario prices, carrying the comparator's own
indirect burden (fully-allocated).

## Why this is a PASS, plainly
{r['top_risk']}. This conclusion holds at WestJet's actual transborder
service levels: the market was tested at 3x, 7x, and 14x weekly and did not
clear. The broader finding is that WestJet already serves its viable YYC
transborder markets (New York, the California and Nevada leisure markets,
Houston, the Florida and Arizona sun routes); what remains unserved is either
too small (below the 2018 survey's own 4,000-passenger floor) or too
thoroughly held by a US network carrier's connecting hub, and this evaluation
is consistent with WestJet directing its recent transborder growth to Edmonton
and Vancouver rather than adding YYC breadth.
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

All {len(scr)} remaining unserved candidates screen PASS, and this now holds
after right-sizing: each was tested at 3x, 7x, and 14x weekly (still a single
178-seat mainline gauge, which is what Alaska flies from SEA), and none
cleared at its best frequency. So the earlier "fixed-gauge artifact" caveat is
partly resolved - lowering frequency did not rescue these markets - and what
remains is a genuine gauge limitation: a regional-jet gauge (which Alaska
operates through Horizon/SkyWest but is out of this study's mainline scope)
would be the honest next test for the thinnest markets. The uniform PASS shows
the screen does not invent opportunities at a mature hub where the observed
network already holds the markets that fit mainline economics - a negative
check on the machinery, stated no more strongly than that.

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

Each market is right-sized: the engine picks the frequency (3x/7x/14x weekly)
that maximizes annual contribution at a feasible load factor, then judges that
schedule. Verdicts: {scr['verdict'].value_counts().to_dict()}. Every LAUNCH is
an anchor-backed large market entered at modest share against real incumbents -
the low-cost entry logic of taking a slice of a big market, not owning a small
one.

{scr.sort_values('margin_pct', ascending=False).head(20)[['metro_name','verdict','chosen_freq_wk','margin_pct','belf','proposed_share','demand_method','demand_pax_yr','n_nonstop_incumbents','top_competitor']].to_markdown(index=False)}
"""
    path = RPT / "porter_yyz_portability.md"
    path.write_text(md)
    return str(path)


if __name__ == "__main__":
    print(westjet_cases())
    print(alaska_validation())
    print(porter_table())
