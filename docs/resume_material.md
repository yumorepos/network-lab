# Resume material

Fill-ins marked [N] are read directly from the repo's outputs so every number
on the resume is reproducible from `make data && make models`.

## Resume bullets (pick per posting)

- Built an airline route-evaluation platform (Python, DuckDB, statsmodels,
  Streamlit) on fully open data: gravity demand model calibrated on 6,002
  US markets (2018-19 vintage; 6,092 in the current 2023-24 fit), transferred to Canada-US markets via a factor anchored to the
  discontinued StatCan city-pair survey, with computed totals reconciling to
  published StatCan/BTS figures within 1%.
- Reconstructed competitive one-stop itineraries from T-100 segment
  frequencies and validated a QSI-lite share model against observed DB1B
  carrier shares (MAE 5.7 share points), then screened 200 candidate markets
  across three hub studies into LAUNCH/MONITOR/PASS, evaluating each market
  against a fixed 3x/7x/14x weekly schedule menu on one configured gauge and a
  3x3 fare-fuel scenario grid.
- Backtested 48 real 2021-2025 transborder route launches against a
  fixed pre-2022 model and published the honest result: demand percentile
  does not separate survivors from failures (0.89 vs 0.86 median), even
  after excluding Lynx's corporate-shutdown casualties: genuine route cuts
  by continuing carriers were also top-decile demand markets - with the
  lookahead limitation disclosed.
- Delivered a defensible negative as the flagship result: the engine recommended
  zero new WestJet transborder routes from Calgary because every viable market is
  already served or structurally held (Dallas at 23% share vs American), matching
  the carrier's own network decisions; paired it with two route post-mortems
  (Flair vs Lynx on the same Calgary-Las Vegas market) that separate an economic
  route failure from a corporate shutdown to show what a demand-first screen
  cannot see.
- Built a point-in-time historical replay (three decision vintages, leakage
  tests with all ten injected leaks demonstrated to fire) and benchmarked the
  full engine against a demand-only ranking: no detectable incremental ranking
  value at effects larger than the study's measured resolution, published as
  the finding under a protocol frozen before results existed. Measured the
  detectable effect size first, so the null is reported as bounded and
  underpowered rather than as equivalence.
- Used that replay to find and retire a headline component: the frequency and
  gauge selection was effectively degenerate under the tested candidates, so
  the product claim was narrowed to evidence-supported fixed-gauge screening
  instead of adding a fleet layer to rescue it. Separately validated the
  competition and share layer in the structural regime the flagship study
  occupies, and kept it.

## One-line project framing

Built and validated a Python/DuckDB airline route-screening engine using BTS,
DB1B, Form 41, StatCan and economic data. Developed point-in-time historical
replay and regression tests that exposed demand, carrier-mapping and schedule
selection defects; narrowed the final model to evidence-supported fixed-gauge
screening after benchmarking against a demand-only baseline.

## LinkedIn project description

Network Lab is an airline route-screening engine built entirely on open data.
It sizes markets with a US-calibrated gravity model, carries demand across the
border with a factor anchored to Canada's last published transborder O&D
survey, reconstructs competing itineraries from T-100 frequencies, and turns
Form 41 cost filings into route-level scenario grids. Every demand number is
flagged observed or modeled; every assumption lives in one YAML file with
source, confidence, and sensitivity; and the whole warehouse reconciles against
published government totals within 1%. Flagship study: WestJet transborder
opportunities from Calgary. Validation study: Alaska at Seattle, where the full
chain is checkable against observed truth.

The part I would actually talk about is what happened when I tested it: a
point-in-time replay showed no detectable ranking advantage over a demand-only
baseline at any effect the study could resolve, and showed that one headline
component was doing no work. I narrowed the product claim rather than adding
complexity to rescue it, validated the one layer that had mechanistic evidence,
and stopped.

## Terms not to use

Each of these overstates what the evidence supports, and each appears nowhere
in the repository.

| term | why |
|---|---|
| "optimized route network" | not claimed; nothing is optimised and no network-level decision is made |
| "validated route predictor" | not claimed; the predictive comparison returned a bounded negative |
| "right-sizing optimizer" | not claimed; the schedule step is a fixed menu evaluation, retired as an optimisation claim |
| "AI-powered network planner" | not claimed; there is no model here that anyone would call AI |

The defensible framing is fixed-gauge route screening with a bounded negative
predictive result.

## Talking points on honest tradeoffs

1. Single-vintage backtest (lookahead disclosed; production refits per
   decision date).
2. Airport-fee proxy (flat, sensitivity-tested; per-airport tariffs do not
   flip decisions at this margin scale).
3. No audit trail (explainability, not cryptographic reproducibility, is the
   requirement for decision support; versioned runs exist in my trading
   project and would come here the day money moved on these outputs).
4. Canadian domestic is out of evidentiary reach for anyone without IATA
   data - and being able to prove exactly why is worth more than a study
   that cannot be checked.
