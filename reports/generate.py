"""Generate the written deliverables from computed outputs.

- WestJet YYC: full business cases for the top three screened candidates.
- Alaska SEA: validation report (chain vs observed truth).
- Porter YYZ: portability demonstration, ranked table only.
Markdown by design (the plan allows md when no HTML-to-PDF tool is present;
none is installed here, and md renders on GitHub where reviewers actually
look).
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
    ranked = scr.sort_values(["margin_pct"], ascending=False)
    picks = ranked.head(top_n)
    files = []
    for _, r in picks.iterrows():
        d = dem[dem["metro_name"] == r["metro_name"]].iloc[0]
        c = comp[comp["cbsa"] == d["cbsa"]]
        slug = (r["metro_name"].split(",")[0].lower()
                .replace(" ", "_").replace("-", "_").replace(".", ""))
        anchor = (f"{d['anchor_2018_pax']:,.0f} pax in the 2018 StatCan "
                  "survey (frozen table 23-10-0256)"
                  if pd.notna(d.get("anchor_2018_pax"))
                  else "not separately reported in the 2018 survey")
        md = f"""# Business case: YYC - {r['metro_name']} (WestJet 737-8)

**Verdict: {r['verdict']}** (confidence: {r['confidence']})

## The two numbers that drive this
1. {r['driver_1']}
2. {r['driver_2']}

## Market
- Distance {r['dist_mi']:.0f} mi, proposed 7x weekly, 174 seats.
- Modeled O&D demand: {d['demand_pax_yr']:,.0f} pax/yr — **modeled, not
  observed**: gravity (US-calibrated) x transfer factor
  {d['transfer_factor']:.2f} (hub median; national median {tf['median']:.2f},
  IQR [{tf['iqr'][0]:.2f}, {tf['iqr'][1]:.2f}]) x T-100 corridor growth
  {d['t100_growth']:.2f}.
- 2018 anchor cross-check: {anchor}.

## Competition (reconstructed from T-100; no MIDT)
{c[['carrier','itin_type','freq_wk','elapsed_h']].sort_values(['itin_type','freq_wk'], ascending=[True,False]).head(8).to_markdown(index=False) if len(c) else 'No incumbent nonstop or qualifying one-stop found. Treat the share estimate skeptically.'}

Modeled share for the proposed service: {r['proposed_share']:.0%}.

## Economics (contribution over direct operating cost + fee proxy)
{_grid_table(eco, d['cbsa'])}

Break-even load factor {r['belf']:.2f} vs planned {r['load_factor']:.2f}.
Fare from distance-matched US markets x {a['transborder_fare_premium']['value']:.2f}
premium (assumption, sensitivity in grid). Costs from Southwest P-5.2 filings
with fuel rebuilt at EIA scenario prices.

## Top risk
{r['top_risk']}

## Assumptions this rests on
{r['key_assumptions']} — all in config/assumptions.yaml with sources,
confidence, and sensitivity ranges. Indirect costs excluded (stated scope).
"""
        path = RPT / f"westjet_yyc_{slug}.md"
        path.write_text(md)
        files.append(str(path))
    return files


def alaska_validation() -> str:
    scr = pd.read_parquet(OUTPUTS / "screen_alaska_sea.parquet")
    obs = scr[scr["demand_source"] == "observed"]
    md = f"""# Alaska SEA: end-to-end validation study

US domestic is the one arena where demand, share, and fare are all observed,
so the full chain runs here with truth available at every stage.

- Candidates screened: {len(scr)} ({len(obs)} with observed DB1B demand).
- Verdicts: {scr['verdict'].value_counts().to_dict()}.
- Share-model accuracy vs observed DB1B carrier shares is reported in
  docs/validation.md (MAE by market structure); the same QSI-lite machinery
  scores the Canadian studies.
- Demand for screened candidates is observed; the gravity model is only used
  where DB1B is too thin, and every such row is flagged `modeled`.

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

{scr.head(20)[['metro_name','verdict','margin_pct','belf','proposed_share','demand_pax_yr','n_nonstop_incumbents','top_competitor']].to_markdown(index=False)}
"""
    path = RPT / "porter_yyz_portability.md"
    path.write_text(md)
    return str(path)


if __name__ == "__main__":
    print(westjet_cases())
    print(alaska_validation())
    print(porter_table())
