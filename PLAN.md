# Network Lab - Plan

A route evaluation platform for airline network planning, built on open data.
Flagship study: WestJet transborder opportunities from Calgary (YYC). Validation
study: Alaska at Seattle (SEA), the one config where demand, share, and fare are
all observed, so the full chain is checkable against truth. Portability proof:
Porter at Toronto Pearson (YYZ), ranked table only.

Everything is reproducible from public sources with `make data`. Every number is
downloaded or derived; anything that cannot be obtained is a labeled assumption
in `config/assumptions.yaml` with source, rationale, confidence, and sensitivity.

## Architecture

```
ingest/          one script per source -> data/raw/ (gitignored)
     |           cleaned, typed, partitioned by year
     v
data/parquet/    slim Parquet, only needed columns
     |
     v
warehouse/       DuckDB marts: dim_airport, dim_carrier, dim_metro,
build_marts.py   fact_segment (T-100), fact_od_market (DB1B),
                 fact_costs (Form 41), fact_fuel (EIA),
                 fact_ca_airport (StatCan), fact_od_transborder_2018
     |
     v
warehouse/       computed totals vs published StatCan/BTS figures,
reconcile.py     differences explained in writing, residuals reported as-is
     |
     v
models/          catchment -> demand (observed | gravity x transfer factor)
                 -> competition (reconstructed one-stops) -> QSI-lite share
                 -> spill -> economics (3 fare x 3 fuel grid) -> screen
     |
     v
outputs          ranked LAUNCH/MONITOR/PASS tables per study config,
                 business case reports, backtest vs data/reference/launches.csv,
                 Streamlit app reading precomputed marts
```

## Analytical chain (the project's core)

1. **Catchment**: metro population within a great-circle radius with distance
   decay; seat-share allocation between competing same-country airports.
2. **Demand**: observed where it exists (DB1B for US domestic), modeled where it
   does not (log-log gravity calibrated on US markets, transferred to Canada-US
   markets via a transfer factor estimated against the frozen StatCan 2018
   transborder city-pair table, forward-scaled with T-100 control totals).
   Every demand value carries an `observed` or `modeled` flag.
3. **Share**: QSI-lite. Competitor one-stop itineraries are reconstructed from
   T-100 segment frequencies before any share is computed - a proposed nonstop
   scored against no competition is a bug, not a result.
4. **Spill**: truncated-normal expected boardings at a given gauge.
5. **Economics**: decomposed cost build from a US comparator carrier's Form 41
   filings (fuel stripped and rebuilt at scenario prices), airport fee proxy,
   fare from DB1B or matched markets x documented premium. Output RASM, CASM,
   contribution margin, break-even load factor on a 3 fare x 3 fuel grid.
6. **Recommendation**: each market is right-sized across the study's frequency
   and gauge grid (the schedule that maximizes annual contribution at a feasible
   load factor is chosen, then judged), then emitted as LAUNCH / MONITOR / PASS
   with the two driving numbers, the top assumptions, the biggest risks, and a
   confidence level. Markets the carrier already serves (metro-level, from
   T-100) are dropped as candidates, and unanchored gravity demand is capped at
   the 2018 survey's own floor so thin markets cannot manufacture false LAUNCHes.

## Dataset manifest

| Source | Contents | URL pattern | License |
|---|---|---|---|
| OurAirports | airport coords, codes, countries | https://davidmegginson.github.io/ourairports-data/airports.csv (also https://ourairports.com/data/) | Public domain |
| BTS DB1B Market | 10% itinerary O&D sample, market fares, city market IDs | https://transtats.bts.gov/PREZIP/Origin_and_Destination_Survey_DB1BMarket_{YYYY}_{Q}.zip | Public domain |
| BTS T-100 Segment (Domestic + International) | seats, pax, departures by carrier/segment/aircraft/month | TranStats download (PREZIP or DL_SelectFields; verified at ingest time) | Public domain |
| BTS Form 41 P-5.2, P-1.2 | operating cost by carrier and aircraft type, fuel separable | TranStats (same) | Public domain |
| BTS lookups | L_CITY_MARKET_ID, L_UNIQUE_CARRIERS, L_AIRPORT_ID | https://transtats.bts.gov/Download_Lookup.asp?Lookup={NAME} | Public domain |
| StatCan 23-10-0253 | airport traffic by sector (control totals) | https://www150.statcan.gc.ca/n1/tbl/csv/23100253-eng.zip | Open Licence |
| StatCan 23-10-0256 | transborder city-pair >4000 pax (frozen ~2018; the transfer anchor) | .../23100256-eng.zip | Open Licence |
| StatCan 23-10-0249/0255/0257 | transborder O&D detail (frozen) | same pattern | Open Licence |
| StatCan 23-10-0259 | quarterly pax by sector (reconciliation control) | same pattern | Open Licence |
| StatCan 23-10-0312 | monthly screened pax (seasonality) | same pattern | Open Licence |
| US Census ACS | CBSA population, median household income | https://api.census.gov/data/{yr}/acs/acs1 | Public domain |
| BEA CAGDP2 | metro GDP (flat file, no API key) | https://apps.bea.gov/regional/zip/CAGDP2.zip | Public domain |
| StatCan census/estimates | CMA population, income; province GDP proxy | stable table CSVs, same zip pattern | Open Licence |
| EIA | Gulf Coast jet fuel spot, weekly | https://www.eia.gov/dnav/pet/hist_xls/EER_EPJK_PF4_RGC_DPGw.xls | Public domain |

Vintages: DB1B and T-100 for 2018-2019 (pre-COVID calibration), 2023-present
(current), 2021-2022 (backtest only). Raw files live in `data/raw/`
(gitignored); only derived aggregates are committed.

## Study configs

- `config/studies/westjet_yyc.yaml` - WS, YYC, transborder candidates. Flagship:
  full chain + three business cases.
- `config/studies/alaska_sea.yaml` - AS, SEA, US domestic candidates. Validation:
  every stage scored against observed truth.
- `config/studies/porter_yyz.yaml` - PD, YYZ, transborder candidates. Portability:
  ranked table only.

## Milestones

| Phase | Output | Done when |
|---|---|---|
| 0 | PLAN.md, assumptions.yaml, study configs, repo | committed |
| 1 | `make data`: ingest + Parquet + DuckDB marts + reconciliation | warehouse rebuilds from scratch; reconciliation numbers reported |
| 2 | catchment, gravity, transfer factor, observed/modeled resolution | demand resolves for all three configs; validation.md has holdout metrics |
| 3 | reconstructed one-stops, QSI-lite share | share computed for all candidates; DB1B share MAE in validation.md |
| 4 | spill + economics scenario grids | per-candidate 3x3 grid for all studies |
| 5 | recommendation screen | ranked LAUNCH/MONITOR/PASS for WS YYC, AS SEA, PD YYZ |
| 6 | validation writeup, backtest, business cases, Streamlit app, docs | reports + validation.md + app exist |

## Honest limitations (maintained in docs/LIMITATIONS.md)

Known at the outset: DB1B has no transborder fares (rule: never imply it does);
T-100 has no Canadian domestic segments; the backtest uses a single pre-2022
model and therefore carries mild lookahead for later launches (a production
system would refit per vintage); airport fees are a documented proxy, not
per-airport schedules; no MIDT/OAG, so connecting competition is reconstructed
from T-100 rather than observed schedules.

## Non-goals

No audit trail, config hashing, orchestration, FastAPI, Next.js, or VPS
deployment. Explainability over ceremony: every recommendation traces to a
documented assumption, and that is the requirement here. Determinism turned out
to be in scope after all: the fits are order-stable and
tests/test_consistency.py fails if any reader-facing number or verdict count
drifts from the computed artifacts.
