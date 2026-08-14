# W1 historical replay feasibility

**Date.** 2026-08-14
**Task.** Stage 0 of the finalization controller. Feasibility only.
**Scope honoured.** No model code, no `config/assumptions.yaml`, no model
parameter and no artifact was modified. `snapshot(t)` was not implemented. The
W1.4 replay was not implemented. Milestone B was not started. Every count below
was computed by read-only query against the local warehouse and the frozen
cache. No network call was made and `make data` was not run.

**Companion documents.** `docs/W1_OFFLINE_CACHE_INVENTORY.md` (what is on disk),
`docs/CODEX_TRANSITION_AUDIT.md` (what the failed transition established).

---

## 0. Baseline gates, re-verified before any analysis

| gate | command | result | expected |
|---|---|---|---|
| tests | `make test` | **45 passed** | 45 |
| reproducibility | `make reproducibility` | **27 artifacts identical** | 27 |

Candidate counts reproduced exactly: WestJet 76, Alaska 45, Porter 79. No
deviation from the previously reported values, so nothing needed investigation
and nothing was forced. The 14 documented float-churn artifacts were restored
rather than committed; the tree is clean.

---

## 1. What binds the replay window

Four constraints, in order of severity.

**C1. DB1B starts 2018Q1.** The cache holds 2018Q1 to 2025Q2, with 2020 absent.
There is no earlier DB1B. US domestic observed demand, observed fare, and the
DB1B-derived brand resolution all stop at 2018. **This is the binding
constraint on any full-engine replay.**

**C2. Form 41 starts 2018.** Cost rates and the indirect burden are annual, 2018
to 2025, 2020 absent. Economics cannot be reconstructed before 2018.

**C3. Outcome maturity ends 2024-04.** The T-100 panel ends 2026-04. A 24-month
outcome therefore requires a decision date at or before 2024-04; a 36-month
outcome at or before 2023-04.

**C4. 2020 is excluded everywhere** (LIMITATIONS item 9, and the warehouse has
no 2020 rows at all). `PHASE_5_6_PLAN.md` W1.6 additionally pre-commits that
"2020 and 2021 are a structural break and are excluded". **These two documents
disagree about 2021.** The code excludes 2020 only; 2021 is present in T-100,
DB1B and Form 41. The disagreement is recorded here rather than resolved
silently, and the protocol must choose explicitly. Counts below are given both
ways.

**What is not a constraint, contrary to expectation.** The StatCan transborder
anchor turns out to be a 22-year annual panel covering 1997 to 2018, not a
single 2018 vintage. See the cache inventory, section 2.1. Point-in-time
transborder anchors are therefore available offline throughout the feasible
window. This removes the blocker that would have made the two transborder
studies unreplayable.

**Resulting decision dates.** Annual, on 1 January: **2019, 2022, 2023, 2024**
(four dates), or five with 2021 admitted. Porter contributes only 2022, 2023 and
2024 for the reason in section 2.

---

## 2. Study applicability, determined separately (0D)

Applicability is not one window. Each study's carrier, hub, fleet and
competitive position came into existence at a different time, and the study
configuration must not be back-projected onto a period in which it did not
exist.

### 2.1 WestJet YYC, transborder, 737-8

- **First WestJet YYC to US route spell in T-100: 2002-01.** 46 spells from YYC
  to US destinations across the panel, 40 inside the study's distance and
  population gate, reaching 26 distinct in-scope metros.
- The 737 mainline transborder operation is continuous and long-established, so
  the configuration is not anachronistic anywhere in the feasible window.
- **Applicable for a full-engine replay: 2019-01 to 2024-04.**

### 2.2 Alaska SEA, US domestic, 737-9

- **Alaska at SEA predates the T-100 panel**; the first spell in the data is
  1990-01. 256 US spells from SEA, 142 in-scope, reaching 55 distinct in-scope
  metros.
- One anachronism to disclose rather than ignore: the configured gauge is the
  737 MAX 9, which Alaska did not operate before 2021. The gauge is a study
  parameter rather than observed data, so a 2019 replay is asking "what would
  this fleet decision have been", not "what did Alaska fly". That is a legitimate
  question and it must be labelled as such.
- **Applicable for a full-engine replay: 2019-01 to 2024-04.**

### 2.3 Porter YYZ, transborder, E195-E2, and this is the important one

- **Porter's YYZ jet network to the US begins 2023-11.** The first three spells
  are Orlando, Fort Myers and Tampa, all 2023-11, followed by Miami and Fort
  Lauderdale 2023-12, Los Angeles and San Francisco 2024-01, Las Vegas 2024-03,
  Phoenix 2024-10, West Palm Beach 2024-11, Palm Springs and San Diego 2024-12,
  LaGuardia 2025-05.
- **There is exactly one earlier spell and it must be excluded:** PD, YYZ to
  Newark, 2008-05 to 2008-07, three months, 2.76 weekly frequency, ceased. It
  precedes the E195-E2 and the YYZ jet hub by fifteen years and is not the
  operation the study describes. Including it would be back-projecting the
  current strategy onto a carrier that did not have it.
- **The defensible decision-vintage start is 2022-01**, not 2023-11. Porter
  ordered and took delivery of the E195-E2 before flying it, so a January 2022
  decision date asks a real and answerable question: planning a YYZ E195-E2 US
  network from a standing start, which markets? All required inputs exist at that
  date.
- **Applicable for a full-engine replay: 2022-01 to 2024-04.** Three decision
  dates.

**Porter is the only genuine greenfield network build in the project**, and that
is what makes it the most informative study for launch agreement and the least
informative for survival.

---

## 3. Metric-family feasibility, with real counts (0E)

Counts are computed from the derived route-spell register restricted to each
study's brand family, hub, US destinations, and the study's own distance and
population gate. They are not a single common sample, and they are not
interchangeable between families.

### 3.1 Family 1: observed launch agreement, 24 months

Reader-facing terms, as required: `observed_launch_agreement_at_k` and
`observed_launch_recall`. **Unlaunched candidates are unlabeled, not confirmed
negatives.** A carrier that declines a good market for fleet or capital reasons
produces an unlabeled row, not a negative one, and no precision figure may be
reported without that caveat attached.

Positive events per decision date, where a positive is an in-scope metro that
the study carrier was not serving at `t` and did serve within 24 months:

| decision date | WestJet YYC | Alaska SEA | Porter YYZ |
|---|---|---|---|
| 2019-01 | 3 | 3 | 0 (no operation) |
| 2021-01 (disputed) | 3 | 3 | 0 (no operation) |
| 2022-01 | 7 | 1 | 6 |
| 2023-01 | 5 | 0 | 10 |
| 2024-01 | 3 | 0 | 5 |
| **total, 2020 and 2021 excluded** | **18** | **4** | **21** |
| **total, 2021 admitted** | **21** | **7** | **21** |

**Alaska is close to degenerate on this family and the reason is structural.**
Alaska launched 31 in-scope spells into 21 distinct metros between 2019-01 and
2024-04, but only 4 of those count as positives at a decision date, because the
rest are re-entries into metros Alaska was already serving. The study's own
candidate rule excludes already-served metros by construction, so a new *spell*
is not a new *market*. Alaska's SEA network is mature and it stopped adding
in-scope new markets: the 2023 and 2024 decision dates yield zero positives.

### 3.2 Family 2: survival, 24 and 36 month cohorts

Cohorts restricted to launches from 2019-01, which is the window in which the
model's own verdict could be computed at the decision date.

| study | horizon | eligible | events | censored | of which seasonal |
|---|---|---|---|---|---|
| westjet_yyc | 24m | 12 | **1** | 11 | 9 |
| westjet_yyc | 36m | 7 | **1** | 6 | 4 |
| alaska_sea | 24m | 31 | **13** | 18 | 22 |
| alaska_sea | 36m | 21 | **8** | 13 | 14 |
| porter_yyz | 24m | 8 | **0** | 8 | 3 |
| porter_yyz | 36m | 0 | **0** | 0 | 0 |
| **pooled** | **24m** | **51** | **14** | **37** | **34** |

**Corporate-shutdown cessations: zero, in all three studies.** This is a clean
improvement on the existing backtest, whose 21 ceased routes include 9 Lynx
rows killed by a single corporate shutdown. All three study carriers are still
operating. The one corporate event in range is Swoop folding into WestJet in
October 2023, and Swoop (`WO`, 3,904 departures, 2021-01 to 2023-07) flew **no
YYC to US segments in scope**, so it contributes no cessations either. The
competing-risks problem that motivated Fine-Gray largely disappears when the
replay is scoped to the study carriers.

**Two findings that matter more than the counts.**

**Seasonality dominates the cohort.** 34 of 51 eligible launches are seasonal.
Across full history the proportion is similar: 26 of 37 WestJet, 90 of 136
Alaska. WestJet's Calgary transborder network and much of Alaska's Seattle spoke
network are seasonal sun and leisure service. A seasonal route stopping is not a
failure, and the study configurations (year-round service at 3, 7 or 14 weekly)
do not describe these routes at all. Any survival analysis that treats a
seasonal stop as an event is measuring the calendar.

**The event count forbids formal modelling.** Fourteen events pooled, against a
Cox model that would want distance, carrier, competitive structure and
seasonality, is roughly one covariate's worth of information under any
conventional events-per-variable rule. **Cox and Fine-Gray were not chosen in
advance and are not justified by these counts.**

A longer-history alternative exists and should be understood before it is
proposed: dropping the 2019 restriction gives 182 eligible and 57 events across
the three studies. But pre-2018 launches cannot be scored with the model's
verdict, because DB1B and Form 41 do not reach them. Such an analysis could
regress survival on crude covariates or on a gravity demand percentile only,
which is exactly what the existing backtest already does, and it found no
separation (0.89 operating against 0.86 ceased). It would add sample size
without adding the thing the family exists to test.

### 3.3 Family 3: right-sizing

`initial_freq_wk` in the derived register is **the maximum one-way frequency
over the first three active months**. It is a proxy for the opening schedule,
not the literal opening-day schedule. Three proxies were computed and compared.

Availability and disagreement, over all in-scope spells:

| study | n | full 3 months available | m1 median freq/wk | 3mo-max median | 3mo-median median | rows where m1 differs from 3mo-max | median ratio 3mo-max to m1 |
|---|---|---|---|---|---|---|---|
| westjet_yyc | 40 | 36 | 3.7 | 6.0 | 6.0 | **77.5%** | 1.28 |
| alaska_sea | 142 | 123 | 6.6 | 14.3 | 13.7 | **72.5%** | 1.46 |
| porter_yyz | 14 | 14 | 8.9 | 14.1 | 13.3 | **78.6%** | 1.41 |

The three proxies disagree on roughly three quarters of spells and the choice
moves the target by 28% to 46% at the median. **Which proxy the protocol picks
must be frozen before results are seen**, because it materially changes the
measured bias.

**There is already a decisive falsifying signal, and it is stronger than the
single Boston observation.** The model right-sizes **200 of 200 current
candidates to 3 weekly**, the minimum of the [3, 7, 14] option list, in all three
studies. Observed opening frequency, same in-scope markets:

| study | model chosen | observed opening, median (3mo-max) | p25 to p75 |
|---|---|---|---|
| westjet_yyc | 3x on 76 of 76 | **6.0** | 4.1 to 12.1 |
| alaska_sea | 3x on 45 of 45 | **14.3** | 12.0 to 21.0 |
| porter_yyz | 3x on 79 of 79 | **14.1** | 12.5 to 15.6 |

The Porter Boston case (model 3x, actual 14x) is therefore **not an outlier. It
is the modal behaviour of the right-sizing rule.** The rule selects the minimum
frequency universally under current demand estimates, and observed openings run
2x to 4.7x higher at the median.

This is a diagnostic on the current artifacts, not the W1.4 metric. The metric
itself requires `snapshot(t)`, because a launched market has to be scored at a
date when it was still unserved and therefore still in the candidate set. But
the diagnostic is strong enough that the replay should be expected to confirm a
systematic downward bias rather than to discover one.

### 3.4 Family 4: incremental value over demand rank

The matched universe on which the full engine and a demand-percentile baseline
could later be compared on **identical rows, dates, candidates, cutoffs and
outcomes** is exactly the Family 1 universe. No separate sample exists and none
should be constructed.

| study | decision dates | candidates per date | matched decision rows | positives, 24m |
|---|---|---|---|---|
| westjet_yyc | 4 (2019, 2022, 2023, 2024) | about 76 | **about 304** | 18 |
| alaska_sea | 4 | about 45 | **about 180** | 4 |
| porter_yyz | 3 (2022, 2023, 2024) | about 79 | **about 237** | 21 |

Candidate counts per date are the current-vintage values and will move once the
candidate set is generated point-in-time, particularly through the served-market
exclusion, which is why they are given as approximate. **No predictive
performance was computed here**, because W1.3 does not exist yet and computing it
against current-vintage covariates would produce exactly the contaminated number
this stage is meant to prevent.

---

## 4. DB1C decision (0F)

**No dataset named DB1C exists in this repository, and none exists in the BTS
DB1B family.** A full-text search across the code, configuration, documentation
and reference data returns zero matches. The BTS Airline Origin and Destination
Survey publishes three files: **Coupon**, **Market** and **Ticket**. This project
ingests Market only (`ingest/bts_db1b.py`).

Reading the requirement as it was most likely meant, namely the DB1B files
beyond Market:

**DB1B COUPON AND TICKET ARE NOT REQUIRED FOR MILESTONE A.**

Reasons, in order:

1. They are `W2.1`, which `PHASE_5_6_PLAN.md` places in **Milestone B**, and the
   plan's own sequencing puts the whole of Milestone A ahead of them.
2. Nothing in the four metric families needs an itinerary-level file. Family 1
   and Family 4 need candidates and launch events; Family 2 needs spells; Family
   3 needs frequencies. All four come from T-100 and the existing Market file.
3. The Market file already supplies observed O&D demand and average fare for the
   Alaska study, which is the only study where demand is observed at all.

Coupon and Ticket remain required for W2.2 through W2.5, and neither is cached,
so Milestone B will need a scoped ingest for the two calibration vintages. That
is a Stage 2 problem and no download is proposed here.

---

## 5. Geography feasibility (0G)

**Cached historical delineations: none.** `data/raw/census/` contains exactly
one file, `list1_2023.xlsx`, the 2023 vintage.

Consequences, stated plainly rather than smoothed over:

- Every historical snapshot must roll counties up to **2023 metro boundaries**,
  including snapshots at 2019 and 2022, which predate the 2023 redefinition.
- This is leakage vector **L4** from `docs/W1.3_point_in_time_audit.md` and it
  **cannot be removed under the no-network rule**. It is a permanent, disclosed
  limitation of the replay, not a defect to be fixed in Stage 1.
- The effect is bounded. It distorts covariates only for metros whose county
  composition changed between vintages, and it changes the airport-to-metro
  rollup for the same metros. The feasible window is 2019 to 2024, which spans
  one boundary revision (2023), not several.
- **The snapshot must record the geography vintage on every row** rather than
  applying 2023 boundaries silently. That is a Stage 1 requirement.

**Do not silently use 2023 geography everywhere.** Use it, and say so per
snapshot.

---

## 6. Known-before disclosure (0H)

**This protocol is a prospective analysis plan. It is not a blind
preregistration**, and it must not be described as one. The following was known
before any replay was designed, and each item could have influenced the design.

`known_before_protocol`:

1. **Current verdicts**, in full: WestJet 0 LAUNCH / 0 MONITOR / 76 PASS; Alaska
   0 / 0 / 45; Porter 1 LAUNCH (Boston-Cambridge-Newton) / 1 MONITOR
   (Hartford) / 77 PASS. Total 200 candidates, 1 LAUNCH.
2. **The Boston right-sizing mismatch**: the model sizes Porter YYZ to Boston at
   3 weekly; Porter launched it on 2026-05-14 at 14 weekly.
3. **Now additionally known, and stronger than item 2**: the model selects 3
   weekly on **200 of 200** candidates, and observed opening frequency medians
   are 6.0, 14.3 and 14.1 weekly for the three studies. The direction and rough
   magnitude of the right-sizing bias is known in advance.
4. **The existing demand-rank backtest is weak and null**: 61 scored, 48
   launched and resolved, operating median percentile 0.89 against ceased 0.86,
   a gap of +0.03 in every cut.
5. **Route-spell register N: 89,502** spells, 657 carriers, 19,442 airport
   pairs.
6. **Route-spell validation rate: 90.7%** (49 of 54 reproducible hand-register
   rows), with a Wilson 95% interval of roughly [80%, 96%], so "above 90%" is
   consistent with the data rather than established by it.
7. **Phase 6A returned a zero-verdict result**: Poisson QMLE changed none of 200
   verdicts.
8. **The transborder gravity bypass and cap structure**: `gravity_x_transfer`
   fires zero times in both transborder studies under the baseline. WestJet 24
   anchored and 52 capped; Porter 58 anchored and 21 capped. All 73 capped
   markets receive one identical value per hub (4,659 YYC, 3,729 YYZ) with
   standard deviation exactly zero.
9. **Alaska is 45 of 45 observed DB1B**, so gravity never fires there.
10. **Eleven point-in-time leakage vectors**, three severe, catalogued in the
    W1.3 audit.
11. **Newly known from this stage**: the StatCan transborder anchor covers 1997
    to 2018, and its publication floor varies by vintage (minimum published
    values 280 to 3,090) rather than being a constant 4,000.
12. **Newly known from this stage**: Alaska has zero Family 1 positives at the
    2023 and 2024 decision dates.

---

## 7. Feasibility table (0I)

`required_data_complete` means the warehouse holds every input the cell needs.
`offline_cache_complete` means it can be built without a network call.
Feasibility is one of **FULL**, **DESCRIPTIVE_ONLY**, **NOT_ESTIMABLE**. Blank
means not applicable, never a fabricated zero.

| study | metric_family | horizon | applicable_start | applicable_end | decision_rows | unique_markets | launches | events | censored | corporate_shutdown_events | required_data_complete | offline_cache_complete | major_lookahead | recommended_analysis | feasibility |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| westjet_yyc | 1 launch agreement | 24m | 2019-01 | 2024-04 | ~304 | 76 | 18 | | | 0 | yes | yes | 2023 CBSA geography; carrier brand map not effective-dated | agreement at k with PU caveat; bootstrap CI over decision dates | **FULL** |
| alaska_sea | 1 launch agreement | 24m | 2019-01 | 2024-04 | ~180 | 45 | **4** | | | 0 | yes | yes | 2023 CBSA geography; 737-9 gauge anachronistic at 2019 | report counts and named markets only; no PR curve | **DESCRIPTIVE_ONLY** |
| porter_yyz | 1 launch agreement | 24m | 2022-01 | 2024-04 | ~237 | 79 | 21 | | | 0 | yes | yes | 2023 CBSA geography; greenfield network, no served-market history | agreement at k with PU caveat; bootstrap CI | **FULL** |
| westjet_yyc | 2 survival | 24m | 2019-01 | 2024-04 | | 11 | 12 | **1** | 11 | 0 | yes | yes | seasonal stops indistinguishable from failure | descriptive: KM curve, no covariates | **DESCRIPTIVE_ONLY** |
| westjet_yyc | 2 survival | 36m | 2019-01 | 2023-04 | | 7 | 7 | **1** | 6 | 0 | yes | yes | as above | none; report N | **NOT_ESTIMABLE** |
| alaska_sea | 2 survival | 24m | 2019-01 | 2024-04 | | 21 | 31 | **13** | 18 | 0 | yes | yes | 22 of 31 seasonal | descriptive: KM, at most one covariate | **DESCRIPTIVE_ONLY** |
| alaska_sea | 2 survival | 36m | 2019-01 | 2023-04 | | 15 | 21 | **8** | 13 | 0 | yes | yes | 14 of 21 seasonal | descriptive only | **DESCRIPTIVE_ONLY** |
| porter_yyz | 2 survival | 24m | 2023-11 | 2024-04 | | 7 | 8 | **0** | 8 | 0 | yes | yes | no variation to explain | none; report zero events | **NOT_ESTIMABLE** |
| porter_yyz | 2 survival | 36m | 2023-11 | 2023-04 | | 0 | **0** | **0** | 0 | 0 | no: window empty | yes | window closes before it opens | none | **NOT_ESTIMABLE** |
| westjet_yyc | 3 right-sizing | opening | 2019-01 | 2024-04 | | 11 | 12 | | | 0 | yes | yes | proxy choice moves target 28% | bias and MAE against frozen proxy; report all three proxies | **FULL** |
| alaska_sea | 3 right-sizing | opening | 2019-01 | 2024-04 | | 21 | 31 | | | 0 | yes | yes | proxy choice moves target 46% | bias and MAE; split by seasonal flag | **FULL** |
| porter_yyz | 3 right-sizing | opening | 2023-11 | 2024-04 | | 7 | 8 | | | 0 | yes | yes | proxy choice moves target 41% | bias and MAE; small N stated | **FULL** |
| westjet_yyc | 4 incremental value | 24m | 2019-01 | 2024-04 | ~304 | 76 | 18 | | | 0 | yes | yes | same as family 1 | full verdict against demand percentile, identical rows | **FULL** |
| alaska_sea | 4 incremental value | 24m | 2019-01 | 2024-04 | ~180 | 45 | **4** | | | 0 | yes | yes | same as family 1 | report, do not test | **DESCRIPTIVE_ONLY** |
| porter_yyz | 4 incremental value | 24m | 2022-01 | 2024-04 | ~237 | 79 | 21 | | | 0 | yes | yes | same as family 1 | full verdict against demand percentile, identical rows | **FULL** |

Pooled across studies, 24-month survival: **51 eligible, 14 events, 34 of the
eligible seasonal.** Pooling does not change the verdict; it remains
DESCRIPTIVE_ONLY.

---

## 8. Stage 0 verdict

The empirical counts support a replay, but a **narrower** one than
`PHASE_5_6_PLAN.md` W1.4 assumed. Three of the four metric families have at
least one cell that is genuinely estimable, the largest anticipated blocker
(historical transborder anchors) turned out not to exist, and the two genuine
blockers (DB1B start date, historical geography) are bounded and disclosable
rather than fatal. Family 2 is underpowered and must be reported descriptively;
that is a result, not a failure of the plan.

**SAFE TO IMPLEMENT SCOPED W1.3/W1.4**

Scope, and nothing beyond it:

1. **Build `snapshot(t)` for four annual decision dates only** (2019, 2022, 2023,
   2024; Porter 2022 to 2024), not a general historical engine. Persist only the
   plumbing those dates need.
2. **Vintage what can be vintaged offline**: BEA income, population and GDP from
   the cached full-year columns; StatCan CMA population 2001 to 2022; the StatCan
   transborder anchor at its own reference year; T-100 and DB1B windows ending at
   the cutoff; Form 41 and EIA at vintage.
3. **Disclose what cannot**: 2023 CBSA geography everywhere, and carrier brand
   resolution that is not effective-dated. Record both on every snapshot row.
4. **Freeze the frequency proxy and the 2021 decision in the protocol before
   running anything**, since both move the answer.
5. **Run Families 1, 3 and 4 as primary. Run Family 2 as descriptive only**, with
   the seasonal-stop ambiguity stated in the same table as the numbers.
6. **Do not fix any defect found while measuring.** Record it for Stage 2 or 3.

Two items to settle before Stage 1 writes code, both flagged rather than
decided here because they change results:

- **The 2021 question.** `LIMITATIONS.md` excludes 2020 only; `PHASE_5_6_PLAN.md`
  W1.6 excludes 2020 and 2021. Admitting 2021 adds 3 WestJet and 3 Alaska
  positives and changes no Porter cell.
- **The per-vintage survey floor.** The negative-space cap assumes a constant
  4,000. The published floor moves by vintage. A replay applying the 2018
  constant to a 2019 snapshot is using the wrong bound.
