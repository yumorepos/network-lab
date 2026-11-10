# Network Lab

**Evidence-first airline route-screening research using public aviation and
economic datasets.** A Python, DuckDB and Parquet pipeline combines BTS, StatCan,
BEA and EIA source information to evaluate configured route scenarios. Each
candidate receives a LAUNCH / MONITOR / PASS research classification, with
observed versus modeled demand and source limitations disclosed.

**Start here:** [Recruiter case study](https://yumorepos.github.io/network-lab.html) · [Live dashboard](https://network-lab-tweqoqjxhfrhj7imgmuftl.streamlit.app/) · [Documentation index](docs/README.md) · [Source and scope limits](docs/FINAL_SCOPE_CONTRACT.md) · [Repository maintenance policy](docs/REPOSITORY_MAINTENANCE_POLICY.md)

[![Live demo](https://img.shields.io/badge/live%20demo-Streamlit-ff4b4b?logo=streamlit&logoColor=white)](https://network-lab-tweqoqjxhfrhj7imgmuftl.streamlit.app)
[![tests](https://github.com/yumorepos/network-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/yumorepos/network-lab/actions/workflows/ci.yml)
![python](https://img.shields.io/badge/python-3.11-blue)
![license](https://img.shields.io/badge/license-MIT-green)
![data](https://img.shields.io/badge/data-open%20government-informational)

**Live dashboard: https://network-lab-tweqoqjxhfrhj7imgmuftl.streamlit.app** -
inspect frozen route screens, per-market scenario economics, validation and
historical replay. Streamlit reads committed precomputed artifacts, not the
original local 5.19 GB warehouse. A full source rebuild uses `make data && make
all` and depends on historical public source availability/vintage; see
[deployment guidance](docs/deploy.md) and [limitations](docs/LIMITATIONS.md).

**Scope, stated once:** this is fixed-gauge route screening. It is not fleet
assignment, network design, frequency selection, or a validated predictor. The
full contract is [docs/FINAL_SCOPE_CONTRACT.md](docs/FINAL_SCOPE_CONTRACT.md);
the story of how the claim got narrowed to that is
[docs/PORTFOLIO_NARRATIVE.md](docs/PORTFOLIO_NARRATIVE.md).

**Visual evidence note (2026-11):** Retired pre-final dashboard screenshots are removed from the active repository tree because they showed obsolete verdicts and right-sizing claims. Historical versions remain in Git history, **not** as current deployment evidence. The verified Porter figures are **1 LAUNCH / 1 MONITOR / 77 PASS**, as recorded in [`headline_metrics.yaml`](data/parquet/outputs/headline_metrics.yaml) and [`screen_porter_yyz.csv`](data/parquet/outputs/screen_porter_yyz.csv). Use the current [live dashboard](https://network-lab-tweqoqjxhfrhj7imgmuftl.streamlit.app/) for presentation; a fresh, independently checked screenshot is still required before adding static visual evidence.

## Reviewer overview

| Question | Verified research result |
|---|---|
| **What was built?** | Python/DuckDB airline route screening, economics scenarios, public-source reconciliation and a read-only Streamlit research dashboard |
| **What was tested?** | 200 candidate screens across WestJet YYC, Alaska SEA and Porter YYZ; 463 historical replay decisions |
| **What survived validation?** | Fixed-gauge screening and explicit source/method evidence; *no detectable incremental ranking lift* over demand-only at effects larger than the study's resolution |
| **What are the limits?** | Not a validated route predictor, frequency optimizer, fleet assignment model, or commercial airline decision system |

The project is designed to show **data engineering, model validation, independent error detection and sound stopping decisions**—not to manufacture profitable route recommendations. [See the concise employer-facing case study](https://yumorepos.github.io/network-lab.html).

---

## The decision it produces

Three studies run through the same engine. The point is not that the model says
yes; it is that the model says yes, no, and "watch it" for defensible, traceable
reasons, and admits what it cannot see.

**1. Porter at Toronto Pearson (YYZ): 1 LAUNCH / 1 MONITOR / 77 PASS.**
The single LAUNCH is Boston, a large anchor-backed market the engine enters at
16% share against real incumbents, evaluated at 3x weekly. This is the
low-cost entry logic of taking a slice of a big market rather than owning a
small one. It is a market Porter does not serve nonstop from YYZ inside the
T-100 window this study reads.

An earlier version of this study reported five LAUNCHes. That result did not
survive correctness review: it divided bidirectional demand by one-directional
departures, and it reconstructed competitors by operating certificate rather
than marketing brand, which made every mainline-plus-regional itinerary
invisible. Both defects are fixed and the before and after is in
[historical integrity report](docs/history/INTEGRITY_REPORT.md).

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
| Schedule evaluation | evaluate the configured schedule menu (3x/7x/14x weekly) on the study gauge, and report the best feasible option or that none is feasible | `min_feasible_load_factor` 0.50 (when nothing clears the floor: report the highest-LF option, which is always the smallest) |
| Economics | 3 fare x 3 fuel scenario grid, fully-allocated margin and break-even load factor | `hurdle_margin_pct` 8, `fare_scenario_grid_pct`, `fuel_scenario_grid` |
| Verdict | **PASS** if base margin < 0; **LAUNCH** if margin >= 8% and the fare-downside stays positive and break-even LF <= 0.85; else **MONITOR** | hurdle 8%, BELF cap 0.85 |
| Competition guard | a modeled share above 70% with zero nonstop incumbents caps LAUNCH to MONITOR (the one-stop reconstruction probably missed real competition) | `> 0.70` share, 0 incumbents |

So Porter's lone MONITOR (Hartford) is fully traceable: its margin at the
evaluated schedule is +4.9%, positive but below the 8% hurdle, so it is held for
watching, not launched or rejected.

**What the schedule step is, and is not.** The engine evaluates a fixed menu of
3x, 7x and 14x weekly against the one gauge each study configures. It does not
choose an aircraft, and it is not a frequency selector: the historical replay
found the step effectively degenerate under the tested candidate universe, with
445 of 463 decisions reaching no schedule comparison at all because no tested
option clears the load-factor floor. That measurement, and the decision to
retire the claim rather than repair it, are in
[docs/STAGE_2R_DECISION.md](docs/STAGE_2R_DECISION.md). The scope this project
does claim is in
[docs/FINAL_SCOPE_CONTRACT.md](docs/FINAL_SCOPE_CONTRACT.md).

Every market carries a 3 fare x 3 fuel contribution-margin grid, so a verdict is
read against its own downside, not a single point estimate. The example below is
a thin Porter candidate that is negative in all nine cells, a clean PASS the tool
does not dress up:

*The old scenario-grid screenshot was also retired from the active tree. Inspect the live market-detail view for current scenario visuals; historical image versions remain in Git history.*

## Validation: the numbers behind the verdicts

- **Reconciliation.** Computed T-100 transborder totals match StatCan published
  figures within **1%** nationally and at YYZ/YVR/YYC/YUL (the definitional
  relationship is derived before comparing; see
  [docs/reconciliation.md](docs/reconciliation.md)).
- **Share model against truth.** At SEA, where DB1B carrier shares are observed,
  the QSI-lite share model lands at **MAE 5.7 share points** across 503
  market-carrier rows, reported by market structure in
  [docs/validation.md](docs/validation.md). The Alaska SEA study exists to run
  the whole chain where demand, share, and fare are all observable: it resolves
  to **45 PASS**, a negative check that the engine does not invent opportunity
  at a mature hub.
- **Transfer factor.** Anchored to the discontinued 2018 StatCan transborder
  city-pair survey: **median 0.80, IQR [0.55, 2.02]** across 87 pairs, with the
  dispersion reported everywhere the factor is used.
- **Launch backtest.** **48** launched-and-resolved transborder routes
  (2021-2025) scored by a pre-2022 model: survivors and ceased routes both sit
  in the top demand decile (**0.89 vs 0.86** median percentile), and the gap
  barely moves when Lynx's shutdown casualties are excluded. Demand rank alone
  does not predict survival, and [the report](docs/backtest.md) says so rather
  than overclaiming a signal that is not there.
- **Point-in-time replay, and the result the project leads with.** The verdict
  chain is reconstructed at three historical decision dates from offline
  point-in-time data and scored against the launches that actually happened.
  On the WestJet Calgary replay, **the full engine showed no detectable
  incremental ranking value over a demand-only baseline at effects larger than
  the study's resolution; smaller effects remain unresolved.** The resolution
  was measured before the comparison was read: 15 positive rows rest on only 10
  distinct launch events over 3 vintages, roughly 5 net events spread across
  two vintages is the optimistic detectability floor, the largest observed
  difference is one event, and k=20 is arithmetically saturated. This is a
  bounded negative, not a demonstration of equivalence and not a failure. It is
  why the product claim was narrowed instead of the model being expanded to
  rescue it. See [docs/STAGE_2R0_RESOLUTION.md](docs/STAGE_2R0_RESOLUTION.md)
  and [docs/LIMITATIONS.md](docs/LIMITATIONS.md).

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
the model is calibrated on US market data, transferred to Canada-US markets
with a dispersion-reported correction factor, and component-tested using
observed US hub data. This is not proof of route-outcome prediction. Each
demand estimate is identified as `observed` or `modeled`,
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
            economics (3x3 grid) -> screen (fixed-gauge LAUNCH/MONITOR/PASS)
backtest/   score real 2021-2025 launches with a pre-2022 model; post-mortems
reports/    generated markdown business cases and ranked tables
app/        Streamlit dashboard reading only the precomputed outputs
```

The project integrates DB1B, T-100, Form 41 and economic data into an
auditable, config-driven screening workflow. Each new study has a YAML
configuration (`config/studies/`), but data suitability and source coverage
still require study-specific verification. Continuous
integration runs on every push ([.github/workflows/ci.yml](.github/workflows/ci.yml)),
and the consistency tests fail the build if any reader-facing number, verdict
count or scope claim drifts from the computed artifacts. CI runs the subset
that does not need the DuckDB warehouse, because the raw data is deliberately
not committed; the point-in-time replay, leakage and parity tests skip there
with a reason and run in full under `make test` against a built warehouse.

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

Start with [docs/FINAL_SCOPE_CONTRACT.md](docs/FINAL_SCOPE_CONTRACT.md) for what
this project does and does not claim, and
[docs/PORTFOLIO_NARRATIVE.md](docs/PORTFOLIO_NARRATIVE.md) for how it got there,
including the components it falsified and retired.

See [docs/LIMITATIONS.md](docs/LIMITATIONS.md): the limitations are stated with
the design decision each one forced, including the single-vintage backtest
lookahead, the airport-fee proxy, the fixed-gauge schedule-menu scope, the
unanchored-demand cap, and the fact that the served-market exclusion trusts the
T-100 join (cross-checked by the committed incumbent-network file). Closed and
rejected research tasks are recorded there as decisions, not as a backlog.

## Data sources and licenses

The repository's original source code is under the [MIT License](LICENSE).
Upstream source data retains its own license and provenance terms: BTS
TranStats, BEA, EIA and US Census public-sector data; Statistics Canada under
the [Open Government Licence – Canada](https://open.canada.ca/en/open-government-licence-canada)
(tables 23-10-0253/0256/0249/0255/0257/0259/0312 and 17-10-0135); and
[OurAirports data](https://ourairports.com/data/) under its published terms.
Review the upstream licenses before redistributing raw archives. The committed
output artifacts contain derived research results, not those large raw archives.
