# Phase 5 and 6: from asserted model to measured model

> **Status, 2026-08-16.** Milestone A is complete and frozen. **The W2 sequence
> in this document is superseded** by `docs/REMAINING_ROADMAP_REDESIGN.md`,
> following the independent review's roadmap verdict REDESIGN THE REMAINING
> ROADMAP. This file is preserved unchanged below as the project's research
> history and is not a current plan. Do not execute W2.1 through W2.5 from
> here.

Date: 2026-07-28. Written after Round 4 of INTEGRITY_REPORT.md closed the three
P0 defects found in AUDIT_2026-07-27_VERIFIED.md.

**Premise, agreed.** The binding constraint is no longer data coverage. It is
that almost nothing in the model has been measured against an outcome. The
demand model is validated, the reconciliation is validated, and as of Round 4
the share model is validated at one hub. The verdict function, the right-sizing
rule, the QSI weights, the connection heuristics and the cost build have never
been tested against anything.

**Scoping rule for this phase.** Ingestion is permitted only where it retires a
named assumption or validates a named output. Every ingestion task below cites
the assumption it kills. No task on this plan exists to raise the source count.

**Phase split.**
Phase 5 builds the scoreboard and the calibration data. It measures.
Phase 6 changes the model in response to what Phase 5 measured, and nothing
before then.

## Approved principles

These are settled and are not reopened by any task below.

1. Phase 5 measures. Phase 6 changes.
2. Every ingestion task must retire a named assumption or validate a named
   output. No task exists to raise the source count.
3. W1.4 must create a frozen baseline before any calibration work begins.
4. Continuous DB1B history is not pursued without a specific justification.

## Milestones

| milestone | contents | exit gate |
|---|---|---|
| **A** | T-100 full history, route spell extraction, point-in-time framework, frozen baseline backtest, Canadian demand diagnostic | baseline frozen and published; diagnostic answered in writing |
| **B** | DB1B Coupon and Ticket ingest, brand mapping observed, connection heuristics validated, QSI fitted, fare model by itinerary type | every change scored against the frozen baseline |
| **C** | ADS-B design note only. No implementation unless a trigger in W4 is met. | a decision document, not a prototype |

## Standing requirement: before and after report

Every change in Phase 5 and Phase 6 ships with a report carrying four fields.
A change without one does not merge, and this applies to changes that make
things worse, which are reported rather than reverted silently.

1. **Metric impact.** The affected metric before and after, on the frozen W1.4
   baseline where applicable.
2. **Verdict changes.** Per study, the LAUNCH, MONITOR and PASS counts before
   and after, and every market that moved between categories by name.
3. **Regression risk.** Which existing tests guard this change, and what class
   of error would still slip through.
4. **Statistical meaningfulness.** Whether the improvement exceeds the noise:
   an interval, a holdout comparison, or an explicit statement that the sample
   is too small to say. "The number moved in the right direction" is not an
   acceptable answer on its own.

The template lives at `docs/change_report_template.md`.

---

## Sizing reality that shapes the whole plan

Two numbers from the current warehouse decide what is cheap and what is not.

| table | rows, 8 year window | implied full history (1993 to 2026) |
|---|---|---|
| `fact_segment` (T-100) | 3.76 M | roughly 16 M |
| `fact_od_market` (DB1B Market) | 173.7 M | roughly 700 M |

T-100 full history is close to free: it is a small table and it contains every
route start and stop ever flown. DB1B full history is not, and the Coupon file
is larger again because an itinerary contributes one row per flight coupon
rather than one per market.

This asymmetry sets the design. **The backtest runs on the full T-100 panel and
on DB1B snapshot years only.** Continuous DB1B history is not proposed here and
should be resisted until something specifically needs it.

---

# Phase 5: build the scoreboard

## W1. Historical backtesting framework

The current backtest scores 48 hand-compiled launches with a single pre-2022
model and finds a +0.03 percentile gap between survivors and failures, which the
report correctly calls no signal. It cannot distinguish "the verdict function is
uninformative" from "48 rows is too few to tell".

### W1.1 Extend T-100 to full history

- **Problem.** `ingest/bts_t100.py` pulls `YEARS = [2018, 2019, 2021 to 2026]`.
  Every route launch and exit before 2018 is invisible, so the launch sample is
  hand-compiled and tiny.
- **Limitation reference.** LIMITATIONS item 7 (single pre-2022 model, mild
  lookahead). INTEGRITY_REPORT Round 4 note on backtest weakness.
- **Expected impact.** Enables W1.2 through W1.6. On its own, none.
- **Effort.** 1 day. The client already works; this is a list literal and a
  backfill run. Watch for schema drift and carrier code reuse across decades.
- **Success criteria.** `fact_segment` covers 1993 to 2026 with per-year row
  counts monotonically plausible, the existing reconciliation still passes in
  band for overlapping years, and no year fails the existing
  `n > 10000` guard.

### W1.2 Derive a mechanical route-spell register

- **Problem.** `data/reference/launches.csv` has 74 rows, 34 of which carry an
  initial frequency. It is hand-compiled from news sources, so it is small,
  selection-biased toward newsworthy carriers (Flair and Lynx dominate), and
  cannot be extended without more hand work.
- **Limitation reference.** Backtest N = 48; INTEGRITY_REPORT Round 1 on ceased
  route composition.
- **Expected impact.** High. Turns 48 launches into thousands. This is the
  single largest change in evidentiary weight available anywhere in the project.
- **Effort.** 3 to 5 days. The hard parts are not the SQL: seasonal routes that
  stop and restart annually must not read as launch and exit, carrier mergers
  and code reuse must be handled, and charter or tag flights must be excluded.
- **Success criteria.** New table `dim_route_spell` with one row per (carrier,
  origin, dest, spell) carrying `first_month`, `last_month`, `initial_freq_wk`,
  `peak_freq_wk`, `status`, `seasonal_flag`. Validation gate: the mechanical
  register must reproduce at least 90% of the 74 hand-compiled rows in
  `launches.csv` within one month on launch date, and every disagreement must be
  explained in writing rather than tuned away. `launches.csv` is retained as the
  cross-check, not replaced by the derived table.

#### W1.2 scope clarification, 2026-08-14 (Stage 1A)

**The 89,502-spell register is a historical event and outcome resource. It is
not 89,502 historical model decisions, and it must never be described as one.**

A spell records that a carrier flew a pair between two months. Scoring a
*decision* additionally requires a candidate set, demand, competition, economics
and a verdict at that date, and those need DB1B (2018Q1 onward), Form 41 (2018
onward), and the study's configured gauge to have existed. After those
constraints the approved replay is **eight study-by-date pairs**, not tens of
thousands.

The register's role in Milestone A is to supply **outcomes**: launch events,
cessations, and observed opening frequencies. It is not the decision universe.

**Persist only the replay plumbing the approved studies need.** No universal
historical airline platform, no general-purpose snapshot service, and no
persisted `dim_route_spell` table beyond what the approved cells consume. The
register continues to be derived on demand by `warehouse.route_spells.build()`
in about ten seconds.

### W1.3 Point-in-time snapshot machinery

- **Problem.** The model reads current-vintage covariates. Replaying a decision
  as of 2015 with 2024 population, income and competitive structure is lookahead,
  and the current backtest already discloses a mild version of this.
- **Limitation reference.** LIMITATIONS item 7.
- **Expected impact.** High. Without it every backtest result is contaminated
  and a reviewer will say so immediately.
- **Effort.** 5 to 8 days. BEA and Census publish historical annual series so
  income and population are recoverable; CBSA boundary redefinitions (2013, 2023)
  are the genuine difficulty and must be handled explicitly, not silently.
- **Success criteria.** `snapshot(t)` returns candidates, demand, competition and
  costs using only data published on or before `t`. A test asserts that no
  column in a snapshot has a source vintage later than `t`. Boundary vintage
  changes are logged per snapshot, not smoothed over.

### W1.4 Decision replay and evaluation metrics

- **Problem.** The tool emits LAUNCH, MONITOR and PASS and nothing measures
  whether those labels predict anything.
- **Limitation reference.** The whole verdict tree in `models/screen.py`;
  thresholds `hurdle_margin_pct` 8, `BELF_MAX` 0.85, `min_feasible_load_factor`
  0.50 are asserted, never fitted.
- **Expected impact.** Very high. This is the deliverable the phase exists for.
- **Effort.** 5 days once W1.1 to W1.3 land.
- **Success criteria.** **AMENDED 2026-08-14; see the amendment note below.**
  Original text, retained so the change is auditable: "`docs/backtest.md` reports
  all four metric families below, with confidence intervals, and states plainly
  where the model has no signal."

#### AMENDMENT to the W1.4 success criterion, 2026-08-14

**When this was made.** After the Stage 0 feasibility gate
(`docs/W1_REPLAY_FEASIBILITY.md`, commits `3c22797` and `a20a9a0`) and
**before any primary historical replay output was computed or viewed.** No
replay had been implemented at the time of writing. Nothing about model
performance was known.

**Why.** The feasibility gate established, from real counts, that several
study-by-family cells cannot support inferential estimation at any sample size
available offline: Alaska Family 1 has one positive event, Porter Family 1 has
five at a single decision date, and pooled 24-month survival has twelve events
across three studies with twenty-one of thirty-five eligible launches seasonal.
Requiring confidence intervals everywhere would force one of two bad outcomes:
fitting underpowered models and reporting their intervals as if meaningful, or
widening applicability windows and pooling studies until an interval appears.
Both manufacture power that the data does not contain.

**This is a change to the analysis contract based on a pre-results assessment of
sample size and data structure. It is not a change based on whether the model
performed well**, and it must not be re-opened later on the basis of results.

**Amended criterion.** All four precommitted metric families must still be
attempted and reported. Then, per cell:

| feasibility | what must be reported |
|---|---|
| **FULL** | the predeclared inferential analysis, with appropriate uncertainty intervals |
| **DESCRIPTIVE_ONLY** | descriptive estimates, sample and event counts, and uncertainty only where statistically meaningful; **no underpowered regression or survival model is forced** |
| **NOT_ESTIMABLE** | the exact reason, the available counts, and the blocking data or sample limitation |

**A metric family is not considered missing merely because the completed
feasibility gate established that inferential estimation is unsupported.**

The feasibility classification of each cell is frozen at
`docs/W1_REPLAY_FEASIBILITY.md` section 7 and **may not be upgraded by enlarging
a window or pooling studies.**

**Metric families. These answer different questions and must not be merged.**

1. **Agreement with the operator (calibration, weak oracle).** Of markets the
   model rated LAUNCH at time `t`, what fraction saw a launch by the study
   carrier within 24 months (precision)? Of markets that did see a launch, what
   fraction did the model rate LAUNCH (recall)? Report as precision at k and a
   PR curve, not accuracy.
2. **Outcome (strong oracle).** Among routes that did launch, does the verdict
   or the modeled margin predict survival to 24 and 36 months? Log-rank test and
   a Cox model with distance, carrier and competitive structure as covariates.
   This is the only family that measures whether the model is *right*, as
   opposed to whether it *agrees*.
3. **Right-sizing.** Modeled `chosen_freq_wk` against observed `initial_freq_wk`
   from W1.2. Report bias and MAE, split by carrier type. **There is already a
   falsifying observation:** the model right-sizes Porter YYZ to Boston at 3x
   weekly and Porter launched it on 2026-05-14 at 14x. The hand register's 34
   frequencies have a median of 4 and a maximum of 7, so that single case may be
   an outlier or may be a systematic gauge-and-frequency bias; with W1.2 there
   will be thousands of observations to settle it.
4. **Incremental value over the trivial baseline.** Does the full verdict beat
   demand percentile alone? The current backtest shows demand rank alone has no
   separation, so this is the comparison that justifies the economics and
   competition layers existing at all. If the full model does not beat demand
   rank, that is the finding and it gets published.

### W1.5 Required tables

| table | status | purpose |
|---|---|---|
| `fact_segment` 1993 to 2026 | W1.1 | route spells, frequency, capacity |
| `dim_route_spell` | new, W1.2 | launch and exit events, initial frequency |
| `fact_od_market` snapshot years | partial ingest | demand at vintage, US domestic |
| `dim_metro_us_pit` | new, W1.3 | point-in-time population, income, GDP |
| `dim_carrier_lineage` | new, W1.2 | merger and code-reuse mapping over 30 years |
| `fact_costs` by year | already annual | cost vintage at `t` |

### W1.6 Expected limitations, to be stated before results are seen

Pre-committing these so they cannot be discovered conveniently later.

- **The oracle is weak.** Airlines launch bad routes. This project's own
  post-mortems show Flair and Lynx both flying YYC to LAS into a fortress hub.
  Agreement with an airline's decision is a calibration signal, not a
  correctness signal. Metric family 2 is the only one that measures correctness.
- **Positive-unlabeled, not positive-negative.** Routes an airline considered
  and rejected are unobservable. Treating every non-launched candidate as a
  negative is wrong, because airlines are fleet-constrained and decline good
  routes for capital reasons. Precision must be reported with this caveat
  attached, and PU-learning corrections considered rather than assumed away.
- **Fleet and capital constraints are unmodeled.** A LAUNCH verdict on a market
  the carrier never flew may be a correct market call and an incorrect capacity
  assumption.
- **2020 and 2021 are a structural break** and are excluded, consistent with
  LIMITATIONS item 9.
- **Schema and definition drift over 30 years** in carrier codes, service class
  and CBSA boundaries. Every handled case gets logged.
- **Survivorship in the covariates.** Metro income and population series get
  revised; using the latest revision of a historical year is a mild lookahead
  that cannot be fully removed.

---

## W2. Passenger behavior calibration (DB1B Coupon and Ticket)

The competition and share layer has produced two of the three P0 defects. Its
parameters are still assertions.

### W2.1 Ingest DB1B Coupon and Ticket, scoped

- **Problem.** `ingest/bts_db1b.py` pulls the Market file only. The Coupon file
  carries `OpCarrier` alongside `TkCarrier` per coupon, and a coupon sequence is
  an *observed connecting itinerary*. The audit asserted that MIDT is the real
  source for itineraries and is priced out; for US domestic markets that is
  wrong, and the substitute is free.
- **Limitation reference.** LIMITATIONS item 3 (no MIDT or OAG).
- **Expected impact.** High, and it is the input to W2.2 through W2.5.
- **Effort.** 3 to 4 days ingest. **Scope discipline required:** Market alone is
  173.7 M rows for 8 years. Coupon is larger per year. Pull Coupon and Ticket for
  the two calibration vintages only (2018 to 2019 and 2023 to 2024), not full
  history. Revisit only if a specific question needs more.
- **Success criteria.** `fact_od_coupon` and `fact_od_ticket` built for the two
  vintages; row counts reconcile against `fact_od_market` passenger totals within
  a stated band; the existing DB1B reconciliation still passes.

### W2.2 Replace inferred brand mapping with observed

- **Problem.** `models/carriers.py` infers operating-to-marketing brand from
  "which permitted brand sells nonstop on this airport pair." It is corroborated
  at 95.9% to 100% for single-brand operators and resolves 85% to 94% of
  multi-brand segments, but it is still an inference with an unresolved
  remainder.
- **Limitation reference.** INTEGRITY_REPORT Round 4 item 2; the `unresolved`
  basis value in `segment_brands`.
- **Expected impact.** Medium. The inference is already good. The win is
  converting a clever workaround into a measured fact and eliminating the
  unresolved tail, including for Air Wisconsin which currently has no DB1B
  coverage at all.
- **Effort.** 2 days.
- **Success criteria.** `segment_brands` gains a `basis = 'db1b_coupon_observed'`
  tier that takes precedence; the share of segments on the `unresolved` basis
  falls below 2%; the existing corroboration test in
  `tests/test_p0_regressions.py` still passes and is tightened.

### W2.3 Validate the connection heuristics against observed itineraries

- **Problem.** `DETOUR_MAX = 2.0`, `DETOUR_ABS_MI = 700`, the minimum leg
  frequency of 3 and the 26-departure segment floor are all invented constants
  in `models/competition.py`, in violation of hard rule 1. Nobody has checked
  what circuity passengers actually accept.
- **Limitation reference.** LIMITATIONS item 3; the rule-1 violations catalogued
  in AUDIT_2026-07-27_VERIFIED section 6.
- **Expected impact.** High. This is the layer whose errors moved verdicts twice.
- **Effort.** 3 days.
- **Success criteria.** The observed distribution of circuity ratio and connect
  frequency is published in `docs/validation.md`; each constant is either moved
  into `assumptions.yaml` with the measured distribution as its source and
  sensitivity, or replaced by a fitted value. A reviewer can see the empirical
  basis for every bound.

### W2.4 Fit the QSI weights

- **Problem.** `qsi_weights` (nonstop against single connect, frequency
  exponent) and `qsi_elapsed_time_exponent` are assumptions. The share model is
  validated at SEA in aggregate but its parameters were never estimated.
- **Limitation reference.** `config/assumptions.yaml` qsi blocks; validation
  currently reports fit, not parameter recovery.
- **Expected impact.** High. Converts the central behavioural model in the
  project from asserted to estimated.
- **Effort.** 5 days. A conditional logit or a constrained least-squares fit of
  itinerary shares, with the existing SEA validation held out.
- **Success criteria.** Fitted weights with standard errors written to an
  artifact; passenger-weighted share MAE at SEA improves against the current
  10.9 points on a held-out sample; the fitted values land in
  `assumptions.yaml` with confidence and sensitivity derived from the fit rather
  than asserted. If the fitted weights do not beat the asserted ones, that is
  published and the asserted ones stay.

### W2.5 Fare structure by itinerary type

- **Problem.** `fare_curve()` is one linear fit of fare against distance across
  all itineraries, so a nonstop and a two-stop connection at the same distance
  get the same fare. Revenue is fare times passengers, so this is the most
  leveraged single input in the margin calculation.
- **Limitation reference.** LIMITATIONS item 4; `transborder_fare_premium` is an
  assumption applied on top of an unconditional curve.
- **Expected impact.** High, and currently unmeasured in either direction.
- **Effort.** 3 days. The Ticket file gives itinerary fare; joining to Coupon
  gives itinerary structure.
- **Success criteria.** A nonstop premium is estimated and reported with a
  confidence interval; the fare model is refit conditional on itinerary type;
  the effect on every study's verdict counts is reported before and after.

---

# Phase 6: change the model, driven by Phase 5

Nothing in Phase 6 starts before the W1.4 baseline exists, so that every change
can be scored against a fixed scoreboard.

## W3. Canadian demand: methodology first

### W3.1 Diagnose before adding anything (MILESTONE A EXIT GATE)

Scheduled in Milestone A, ahead of all calibration work, and diagnostic only.

Note precisely why the gate sits here, so it is not removed later as a
dependency error. It is **not** a technical dependency: DB1B is US domestic, so
the QSI fit in W2.4 runs on Seattle data and would execute regardless of the
state of Canadian demand. The gate is an allocation argument. If 52 of 76
markets in the flagship study report a bound rather than an estimate, then
sharpening the competition layer on those markets refines a term already
dominated by demand uncertainty. Confirm the demand layer produces meaningful
estimates before spending Milestone B on downstream precision.

The gate opens on a written answer, not on a fix. Adding datasets here is
forbidden unless the diagnosis proves they are needed, and the one candidate
already identified (W3.3, Canadian metro income) stays contingent on it.


- **Problem.** The flagship study's demand path barely functions. Of 76 WestJet
  candidate markets, 52 sit pinned at exactly 4,659 passengers, the unanchored
  cap. The `gravity_x_transfer` path fires zero times for either transborder
  study. So for two thirds of the flagship study the model does not estimate
  demand, it reports an upper bound.
- **Limitation reference.** LIMITATIONS item 13; AUDIT_2026-07-27_VERIFIED P1-2.
- **Expected impact.** Diagnostic. Determines whether W3.2 or W3.3 is the real
  work.
- **Effort.** 2 days.
- **Success criteria.** A written answer to the question the plan asks: is this
  methodology or missing data? **The current evidence says mostly methodology.**
  The cap binds because the US-calibrated gravity model over-predicts small
  markets by 5x to 8x, which is a specification problem, not a coverage problem.
  The task is to prove or overturn that, not to assume it.

### W3.2 Model the transfer factor instead of averaging it

- **Problem.** The transfer factor is a scalar median of 0.80 with IQR
  [0.55, 2.02] over 87 pairs, applied to every Canadian market. The dispersion
  is reported honestly but never explained, and it has visible structure: the 11
  YYC anchor pairs run LAS 8.78, PHX 3.68, MCO 3.26 against BOS 0.44, DFW 0.63,
  ORD 0.73. That is a leisure and business axis being averaged away. The
  per-hub medians the studies actually use are also not the quantity that
  `test_transfer_median_consistent` pins.
- **Limitation reference.** LIMITATIONS item 2; AUDIT_2026-07-27_VERIFIED P1-3.
- **Expected impact.** Highest value per unit effort in the whole plan. It
  converts the project's largest reported uncertainty into a modeled effect
  using data already in the warehouse.
- **Effort.** 3 days.
- **Success criteria.** `ln(transfer)` regressed on a leisure indicator and
  market covariates; residual dispersion materially below the current IQR;
  leave-one-out reported on the per-hub medians the studies actually consume,
  not on the national median; `test_transfer_median_consistent` repointed
  accordingly.

### W3.3 Canadian metro income, a targeted and justified addition

- **Problem.** `dim_metro_ca` has exactly two columns, `cma` and `population`.
  There is no Canadian income, so `models/demand.py` sets `inc_a = inc_b =
  destination income` for both terms of the gravity income product. With a
  fitted `ln_income_product` coefficient of 1.0257, the destination-income
  elasticity is silently doubled.
- **Limitation reference.** AUDIT_2026-07-27_VERIFIED P2; the docstring in
  `models/demand.py` discloses the substitution but argues the level error
  cancels, which is untested.
- **Expected impact.** Medium, and it removes a known specification error rather
  than adding breadth.
- **Effort.** 1 day. StatCan publishes CMA-level income.
- **Success criteria.** This is the one ingestion task in the plan that adds a
  source, and it qualifies under the scoping rule because it kills a named
  defect: one variable, one table, fixing a doubled elasticity. Success is the
  substitution removed from `demand.py` and the effect on demand estimates
  reported.

### W3.4 Small-market gravity specification

- **Problem.** The cap exists because gravity over-predicts thin markets by 5x
  to 8x. Capping is a patch on a specification failure.
- **Limitation reference.** LIMITATIONS item 13.
- **Expected impact.** Medium to high. If the specification is fixed the cap can
  be relaxed and 52 markets get real estimates instead of a bound.
- **Effort.** 4 days.
- **Success criteria.** Holdout APE in the 4,000 to 25,000 passenger band
  improves against the current 0.69 median; the share of WestJet markets pinned
  at the cap falls; if it does not improve, the cap stays and the attempt is
  documented.

## W5. Cost layer validation

- **Problem.** Nothing validates the cost build at all. Costs are a US
  comparator proxy (Southwest for WestJet, JetBlue E190 with a 12% Embraer
  haircut for Porter), and the Canadian airport and navigation fee is a flat
  proxy graded low confidence with a plus or minus 30% band and a possible
  double-count against the indirect burden. Cost is half of every margin in the
  project and has zero external check.
- **Limitation reference.** LIMITATIONS item 5; `E2_FUEL_IMPROVEMENT` and
  `airport_fee_proxy` in `assumptions.yaml`.
- **Expected impact.** Medium to high, and high confidence of a clean result.
  NAV CANADA publishes its customer service charges as a formula on aircraft
  weight and distance; YYC and the GTAA publish aeronautical fee schedules.
  These replace a guess with a published rate card. StatCan air carrier
  operating statistics at carrier level give a coarse band to sanity check
  implied CASM.
- **Effort.** 3 days.
- **Success criteria.** The flat fee proxy is replaced by computed charges from
  published tariffs, with the schedule cited in `assumptions.yaml`; implied CASM
  for each study carrier is reported against the Canadian carrier-level band;
  the double-count question in LIMITATIONS item 5 is resolved in one direction
  or the other rather than left open.

---

## W4. ADS-B: design note only, no implementation

- **Problem being solved.** Two things no statistical source can supply. T-100
  carries no Canadian domestic segments, so Air Canada connecting itineraries
  out of YYZ over YUL or YVR cannot be reconstructed at all: leg two is in the
  data and leg one never is. And the competition layer has no times, so it
  cannot tell a bookable connection from an arithmetic one.
- **Limitation reference.** LIMITATIONS item 14 (added in Round 4); LIMITATIONS
  item 3 on bank alignment.
- **What current datasets cannot answer.** Whether Air Canada actually offers a
  same-day connection YYZ to a US destination over a Canadian hub, and at what
  frequency. This is not a coverage gap that better use of BTS data can close;
  it is a legal consequence of Canada's disclosure regime, and ADS-B is not
  bound by it because it observes physical flights rather than filed reports.
- **Estimated engineering cost.** 4 to 6 weeks for a scoped build, plus ongoing
  storage. Components: bulk historical state vectors from OpenSky or ADS-B
  Exchange for a defined airport set and window; state vector to flight leg
  reconstruction; callsign to carrier and registration to aircraft type mapping;
  deduplication across receivers; coverage-gap characterisation. Global
  multi-year raw volume is in the tens of terabytes, so airport-scoped
  extraction is mandatory rather than optional.
- **When it becomes worthwhile.** Three triggers, any one sufficient. First, if
  W1.4 shows the model's errors concentrate in Canadian hub markets where Air
  Canada connections are the likely missing competitor. Second, if W2.3 shows
  the connection heuristics are materially wrong in US markets, since bank
  alignment would then be a known error rather than a suspected one. Third, if
  the project acquires a use case that pays for six weeks of engineering.
- **Effort for the note itself.** 1 day.
- **Success criteria.** A written note in `docs/` that a reviewer can use to
  decide, containing the three triggers and an honest volume estimate. Not a
  prototype.

---

## Sequencing and dependencies

```
MILESTONE A  (measure, no model changes)
  W1.1 T-100 full history
    └─> W1.2 route spells
          └─> W1.3 point-in-time snapshots
                └─> W1.4 decision replay + 4 metric families
                      └─> BASELINE FROZEN and published
  W3.1 Canadian demand diagnostic (runs in parallel, no new data)
                      └─> EXIT GATE: baseline frozen + diagnostic answered

MILESTONE B  (calibrate, every change scored against the frozen baseline)
  W2.1 Coupon/Ticket ingest, scoped to 2018-19 and 2023-24
    ├─> W2.2 brand mapping observed
    ├─> W2.3 connection heuristics validated
    ├─> W2.4 QSI fitted
    └─> W2.5 fare by itinerary type

PHASE 6  (change the model, gated on what A and B measured)
  W3.2 transfer factor modeled | W3.3 CA income (contingent on W3.1)
  W3.4 small-market gravity    | W5 cost layer validation

MILESTONE C  (deferred)
  W4 ADS-B design note only, unless a W4 trigger fires
```

W1.4 must record a **pre-calibration baseline** before any Milestone B or Phase 6
change lands. Without it, W2.4 and W3.2 cannot be shown to have improved
anything, and the project repeats its historical failure mode of asserting an
improvement it never measured.

Milestone A contains no model changes by construction. If a defect is found
while building the baseline, it is recorded and fixed in Phase 6 with a before
and after report, not patched in place, because a baseline that moved while it
was being built is not a baseline.

## Definition of done for the phase

`make all && make test` green from clean. Every constant listed in
AUDIT_2026-07-27_VERIFIED section 6 is either fitted, moved into
`assumptions.yaml` with a measured source, or documented as deliberately
retained. `docs/backtest.md` reports all four metric families with intervals.
Every Phase 6 change carries a before and after against the frozen W1.4
baseline, including the changes that made things worse.

## Out of scope, deliberately

Any ingestion not named above. Continuous DB1B history. ADS-B implementation.
The README and portfolio document rewrite, which is tracked separately and
should follow the Phase 5 baseline rather than precede it, so that it describes
a validated model rather than a corrected one.
