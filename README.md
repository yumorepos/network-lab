# Network Lab

**A route-evaluation engine for airline network planning, built entirely on
open government data.** One config-driven pipeline turns raw BTS, StatCan, BEA,
and EIA files into LAUNCH / MONITOR / PASS verdicts for new airline routes, with
every demand number flagged observed or modeled and every assumption traceable
to a source.

![python](https://img.shields.io/badge/python-3.11-blue)
![tests](https://img.shields.io/badge/tests-13%20passing-brightgreen)
![data](https://img.shields.io/badge/data-open%20government-informational)
![license](https://img.shields.io/badge/license-public%20sources-lightgrey)

> Live demo: add the Streamlit Community Cloud URL here after deploying (see
> [docs/deploy.md](docs/deploy.md)). Everything below is reproducible from
> public sources with `make data && make all`.

---

## The decision it produces

Three studies run through the same engine. The point is not that the model says
yes; it is that the model says yes, no, and "watch it" for defensible, traceable
reasons, and admits what it cannot see.

**1. Porter at Toronto Pearson (YYZ): 5 LAUNCH / 3 MONITOR / 71 PASS.**
The five LAUNCHes (Washington, Chicago, Boston, Philadelphia, Atlanta) are all
large, anchor-backed markets that the engine enters at modest share against real
incumbents, then right-sizes down to 3x or 14x weekly. This is the low-cost
entry logic of taking a slice of a big market rather than owning a small one.
Each is a market Porter does not serve nonstop from YYZ today (verified against
Porter's actual T-100 network; the one edge case, Chicago, is documented on the
page).

**2. WestJet transborder from Calgary (YYC): 0 LAUNCH / 0 MONITOR / 76 PASS.**
The flagship study recommends nothing, and that is the finding. Every viable
unserved YYC transborder market is either already served by WestJet (New York,
the California/Nevada/Arizona leisure markets, Houston, the Florida sun routes)
or too thin or too thoroughly held by a US carrier's connecting hub (Dallas at
23% share against American). This is consistent with WestJet directing its recent
transborder growth to Edmonton and Vancouver, not to more YYC breadth. A model
that only ever says yes is a sales tool, not an analysis.

**3. Two route post-mortems, same market, two failure modes.** Flair and Lynx
both flew YYC-LAS into WestJet's fortress hub and both exited. A demand screen
ranks the market in the top 17% and would have green-lit both. But
[Flair](reports/postmortem_f8_yyc_las.md) sustained the route for two and a half
years at a 0.59-0.70 load factor against WestJet's 0.90 and made a route-level
economic cut, while [Lynx](reports/postmortem_y9_yyc_las.md) flew one year at
0.53 and died in a corporate shutdown that took every route at once. Same market,
one economic verdict and one balance-sheet death. That distinction is the whole
argument for why a demand-first screen needs an economics and competition layer,
and it is invisible to the demand rank alone.

## How a verdict is reached

Every candidate market runs the same decision tree. Each threshold lives in
[config/assumptions.yaml](config/assumptions.yaml) with a source, a confidence
grade, and a sensitivity range.

| Step | Rule | Threshold (assumptions.yaml) |
|---|---|---|
| Candidate filter | metro population floor, distance in range, not already served by the carrier (metro-level, from T-100), real airport, not a satellite of a bigger one | `candidate_min_metro_pop` 400k, `served_market_min_deps_yr` 26, `candidate_min_airport_seats_yr` 250k, `satellite_airport_rule` 60mi/5x |
| Demand | observed DB1B where it exists; else the market's own 2018 StatCan actual x T-100 corridor growth; else gravity x transfer, capped at the survey's own floor for unanchored markets | `transfer_factor` (median 0.80), unanchored cap 4,000 x growth |
| Share | QSI-lite vs one-stop competitors reconstructed from T-100 frequencies | `qsi_weights`, `qsi_elapsed_time_exponent` |
| Right-size | pick the frequency and gauge that maximize annual contribution at a feasible load factor | `min_feasible_load_factor` 0.50 (fallback: keep the highest-LF option) |
| Economics | 3 fare x 3 fuel scenario grid, fully-allocated margin and break-even load factor | `hurdle_margin_pct` 8, `fare_scenario_grid_pct`, `fuel_scenario_grid` |
| Verdict | **PASS** if base margin < 0; **LAUNCH** if margin >= 8% and the fare-downside stays positive and break-even LF <= 0.85; else **MONITOR** | hurdle 8%, BELF cap 0.85 |
| Competition guard | a modeled share above 70% with zero nonstop incumbents caps LAUNCH to MONITOR (the one-stop reconstruction probably missed real competition) | `> 0.70` share, 0 incumbents |

So Alaska's lone MONITOR (Fayetteville-Springdale-Rogers) is fully traceable: its
best-fit margin is +0.2%, positive but below the 8% hurdle, so it is held for
watching, not launched or rejected.

## Validation: the numbers behind the verdicts

- **Reconciliation.** Computed T-100 transborder totals match StatCan published
  figures within **1%** nationally and at YYZ/YVR/YYC/YUL (the definitional
  relationship is derived before comparing; see
  [docs/reconciliation.md](docs/reconciliation.md)).
- **Share model against truth.** At SEA, where DB1B carrier shares are observed,
  the QSI-lite share model lands at **MAE 7.0 share points** across 503
  market-carrier rows, reported by market structure in
  [docs/validation.md](docs/validation.md). The Alaska SEA study exists to run
  the whole chain where demand, share, and fare are all observable: it resolves
  to **48 PASS / 1 MONITOR**, a negative check that the engine does not invent
  opportunity at a mature hub.
- **Transfer factor.** Anchored to the discontinued 2018 StatCan transborder
  city-pair survey: **median 0.80, IQR [0.55, 2.02]** across 87 pairs, with the
  dispersion reported everywhere the factor is used.
- **Launch backtest.** **48** launched-and-resolved transborder routes
  (2021-2025) scored by a pre-2022 model: survivors and ceased routes both sit
  in the top demand decile (**0.89 vs 0.86** median percentile), and the gap
  barely moves when Lynx's shutdown casualties are excluded. Demand rank alone
  does not predict survival, and [the report](docs/backtest.md) says so rather
  than overclaiming a signal that is not there.

## Method, and where it comes from

The engine implements standard airline-planning methods on open data rather than
inventing new ones:

- **Gravity demand.** A log-linear gravity model, the most widely used method
  for air passenger demand forecasting, calibrated on 6,002 US city-market pairs
  (2018-19 vintage; 6,092 in the 2023-24 fit) so its coefficients read as
  elasticities ([gravity models for air passenger volume estimation, Grosche et
  al.](https://www.sciencedirect.com/science/article/abs/pii/S0969699707000178)).
- **QSI-lite share.** A Quality of Service Index share model weighting nonstop
  over connecting service and discounting frequency, the industry-standard
  frequency-share approach ([Cirium](https://www.cirium.com/thoughtcloud/qsi-analytics-for-airline-supplier-negotiations/),
  [OAG](https://knowledge.oag.com/docs/what-is-qsi)).
- **Spill and economics.** Truncated-normal spill to expected boardings and a
  RASM-vs-CASM contribution build with a break-even load factor, per standard
  airline route economics ([MIT 16.75J airline
  management](https://ocw.mit.edu/courses/16-75j-airline-management-spring-2006/f990b2cd2141f75cd9b348051af762e7_lect4b.pdf)).

The hard part is not the methods; it is that there is no public Canadian domestic
O&D, no transborder fare data, and the transborder O&D survey froze in 2018. So
the model is calibrated where truth exists (US markets), transferred to Canada-US
markets with an anchored, dispersion-reported correction factor, and validated
end to end on a US hub. Every demand number carries an `observed`/`modeled` flag,
every non-derived value lives in one YAML file with source and sensitivity, and a
proposed nonstop is never scored against an empty market: competitor one-stops
are reconstructed from T-100 first.

## Architecture

```
ingest/     one client per source -> data/raw/ (gitignored), typed Parquet
warehouse/  DuckDB marts: dim_airport/carrier/metro, fact_segment (T-100),
            fact_od_market (DB1B), fact_costs (Form 41), fact_fuel (EIA),
            reconcile.py checks computed vs published totals in writing
models/     catchment -> demand -> competition -> QSI-lite share -> spill ->
            economics (3x3 grid) -> screen (right-sized LAUNCH/MONITOR/PASS)
backtest/   score real 2021-2025 launches with a pre-2022 model; post-mortems
reports/    generated markdown business cases and ranked tables
app/        Streamlit dashboard reading only the precomputed outputs
```

No single open-source project combines DB1B, T-100, Form 41, gravity, QSI, and
route economics end to end, which is what this repo is. It is config-driven: a
new study is a YAML file (`config/studies/`), not a code change. Continuous
integration runs the sanity and consistency tests on every push
([.github/workflows/ci.yml](.github/workflows/ci.yml)); the consistency tests
fail the build if any reader-facing number or verdict count drifts from the
computed artifacts.

## Run it

```
make setup   # venv + dependencies                         (~1-2 min)
make data    # download sources, build warehouse, reconcile (~50 min cold, ~1 s cached)
make all     # models + backtest + reports                 (~40 s)
make test    # sanity + consistency tests                  (~4 s)
make app     # Streamlit dashboard (reads precomputed outputs)
```

No API keys required. Raw downloads stay out of git; the hand-compiled reference
files (`data/reference/`: the launch register and the incumbent-network audit
file) are committed. Deploy steps in [docs/deploy.md](docs/deploy.md); demo
storyboard in [docs/demo_script.md](docs/demo_script.md).

## Honest limitations

See [docs/LIMITATIONS.md](docs/LIMITATIONS.md): the limitations are stated with
the design decision each one forced, including the single-vintage backtest
lookahead, the airport-fee proxy, the frequency/gauge right-sizing scope, the
unanchored-demand cap, and the fact that the served-market exclusion trusts the
T-100 join (cross-checked by the committed incumbent-network file). Planned
extensions (per-vintage backtest refit, connectivity view, full Porter business
cases, ACS income with a key) are listed there rather than implied to exist.

## Data sources and licenses

BTS TranStats (public domain), StatCan (Open Government Licence - Canada; tables
23-10-0253/0256/0249/0255/0257/0259/0312, 17-10-0135), BEA (public domain), EIA
(public domain), Census delineation files (public domain), OurAirports (public
domain).
