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

## CORRECTION issued 2026-08-14, after the first version was committed

The first version of this document (commit `3c22797`) began the Alaska cells in
2019 and the Porter cells in 2022, while its own prose said the Alaska 737-9 was
anachronistic before 2021 and the Porter YYZ jet network began in 2023-11. Those
are contradictions and they inflated two studies' feasibility. It also left the
2021 question open rather than resolving it.

Three policies are now applied, and every count below reflects them:

1. **Literal configuration.** A study is applicable only from the month its
   **configured gauge** actually flew from its hub to a US destination, verified
   from T-100 `aircraft_type` rather than asserted. No study is redefined as a
   generic mainline proxy to preserve sample size.
2. **2020 and 2021 are both excluded** from the primary baseline, per the
   precommitment in `PHASE_5_6_PLAN.md` W1.6. This is the stricter of the two
   conflicting rules in the repository and it is adopted deliberately, **not**
   reopened because admitting 2021 would have added six positives.
3. **Snapshot floor 2019-01.** A launch that cannot be scored by the model at
   its own decision date does not enter a cohort. DB1B starts 2018Q1 and Form 41
   starts 2018, so with publication lag the earliest full-engine snapshot is
   2019-01.

**What changed materially.** Alaska Family 1 falls from 4 positives to **1**.
Porter Family 1 falls from 21 positives over three decision dates to **5 over
one**. WestJet is unchanged, because its configured gauge was in service from
2018-03 and its dates were already admissible. The overall verdict survives but
the scope is materially narrower, and one goal in `PHASE_5_6_PLAN.md` W1.4 is now
provably unreachable. See section 8.

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

**C4. 2020 and 2021 are both excluded from the primary baseline. RESOLVED.**
`LIMITATIONS.md` item 9 excludes 2020 only; `PHASE_5_6_PLAN.md` W1.6 pre-commits
that "2020 and 2021 are a structural break and are excluded". The two documents
disagree, and the **stricter precommitted rule wins**: 2020 and 2021 are
excluded as decision vintages and as launch-cohort years.

This is adopted as policy, not as a result. Admitting 2021 would have added 3
WestJet and 3 Alaska positives, and choosing the rule after seeing that would be
exactly the outcome-aware selection this stage exists to prevent. A
2021-admitted analysis may later be published as a **labelled sensitivity**. It
may not replace the primary baseline.

**C5. Configured gauge, verified rather than asserted.** Each study names a
specific aircraft. A study is not applicable before its gauge flew. From T-100
`aircraft_type`, restricted to hub to US destinations:

| study | configured gauge | BTS `aircraft_type` | first month | active months | departures |
|---|---|---|---|---|---|
| westjet_yyc | 737-8, 174 seats | 838 (B737 MAX 800) | **2018-03** | 74 | 7,690 |
| alaska_sea | 737-9, 178 seats | 839 (B737 MAX 900) | **2021-03** | 62 | 82,937 |
| porter_yyz | E195-E2, 132 seats | 748 (EMBRAER EMB195) | **2023-11** | 30 | 9,088 |

The test is applied to all three studies, not only the two under challenge.
WestJet's configured gauge was in service before the snapshot floor, so
WestJet's window is unaffected. That is a result of the test, not an exemption
from it.

**What is not a constraint, contrary to expectation.** The StatCan transborder
anchor turns out to be a 22-year annual panel covering 1997 to 2018, not a
single 2018 vintage. See the cache inventory, section 2.1. Point-in-time
transborder anchors are therefore available offline throughout the feasible
window. This removes the blocker that would have made the two transborder
studies unreplayable.

**Resulting decision dates**, annual on 1 January, after C1 to C5:

| study | admissible decision dates | n |
|---|---|---|
| westjet_yyc | 2019, 2022, 2023, 2024 | **4** |
| alaska_sea | 2022, 2023, 2024 | **3** |
| porter_yyz | 2024 | **1** |

**Cohort start** for the survival and right-sizing families is
`max(snapshot floor 2019-01, gauge first month)`, with 2020 and 2021 launch
years removed: WestJet 2019-01, Alaska 2021-03 (so effectively 2022-01 once 2021
is excluded), Porter 2023-11.

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

### 2.2 Alaska SEA, US domestic, 737-9. CORRECTED

- **Alaska at SEA predates the T-100 panel**; the first spell in the data is
  1990-01. 256 US spells from SEA, 142 in-scope, reaching 55 distinct in-scope
  metros. **None of that history is usable**, for the reason below.
- **The configured 737-9 first flew SEA to US in 2021-03** (T-100
  `aircraft_type` 839, 62 active months, 82,937 departures). Alaska did not
  operate this gauge before then.
- The earlier version of this document called that an anachronism to disclose
  and then used 2019 anyway. Under the literal-configuration rule it is not a
  disclosure item, it is an applicability boundary.
- 2021 is excluded as a structural break, so the first admissible decision date
  is 2022-01.
- **Applicable for a full-engine replay: 2022-01 to 2024-04. Three decision
  dates.** Cohort start 2021-03, effectively 2022-01 after the exclusion.

The study was **not** redefined as a generic Alaska mainline-gauge proxy to
preserve sample size. That option was available and was rejected.

### 2.3 Porter YYZ, transborder, E195-E2. CORRECTED

- **Porter's YYZ jet network to the US begins 2023-11**, confirmed twice over:
  the first in-scope route spells are Orlando, Fort Myers and Tampa in 2023-11,
  and T-100 `aircraft_type` 748 first appears on YYZ to US in the same month.
  Then Miami and Fort Lauderdale 2023-12, Los Angeles and San Francisco 2024-01,
  Las Vegas 2024-03, Phoenix 2024-10, West Palm Beach 2024-11, Palm Springs and
  San Diego 2024-12, LaGuardia 2025-05.
- **There is exactly one earlier spell and it is excluded:** PD, YYZ to Newark,
  2008-05 to 2008-07, three months, 2.76 weekly frequency, ceased. It precedes
  the E195-E2 and the YYZ jet hub by fifteen years and is not the operation the
  study describes.
- **Applicable for a full-engine replay: 2023-11 to 2024-04.** With annual
  decision dates that is **one date, 2024-01**.

#### The cost of the literal rule here, stated plainly

Family 1 asks which markets a carrier **should launch**. It is inherently
prospective: the decision date must precede the launches being scored. Porter's
configuration became applicable in the same month the network opened, so under
the literal rule the only admissible decision date sits **after** six of the
thirteen launches have already happened, and those six are excluded as
already-served rather than scored.

The consequence is that the literal rule does not merely shrink Porter, it
removes the greenfield question the Porter study is best placed to answer. That
is a real cost and it is accepted here rather than argued around, because the
alternative requires a rule that lets a decision date precede any operation, and
such a rule is harder to bound than it looks.

**Labelled alternative, computed but NOT primary.** A fleet-commitment rule
would set applicability at Porter's public E195-E2 order rather than at first
flight, making 2022-01 the first admissible non-excluded date. Under that rule
Porter yields 3 decision dates, about 237 decision rows and **21** positives
instead of 1 date, 79 rows and **5**. The two are reported side by side in
section 7 so the cost of the choice is visible. **The primary baseline uses the
literal rule.**

Sub-annual decision dates (2023-11, 2024-01, 2024-04) were considered and
rejected: their 24-month outcome windows overlap so heavily that they observe
substantially the same launches, so bootstrapping across them would understate
uncertainty rather than measure it.

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

Dates marked "not applicable" are outside the study's configured-gauge window
and are **not** counted as zero positives. A blank is not a zero.

| decision date | WestJet YYC | Alaska SEA | Porter YYZ |
|---|---|---|---|
| 2019-01 | 3 | not applicable (gauge from 2021-03) | not applicable (gauge from 2023-11) |
| 2020-01, 2021-01 | excluded | excluded | excluded |
| 2022-01 | 7 | 1 | not applicable |
| 2023-01 | 5 | 0 | not applicable |
| 2024-01 | 3 | 0 | 5 |
| **decision dates** | **4** | **3** | **1** |
| **decision rows (approx)** | **304** | **135** | **79** |
| **total positives** | **18** | **1** | **5** |

**Alaska is degenerate on this family, and more so than first reported.** Under
the corrected window there is exactly **one** positive across three decision
dates. Two causes compound. First, the 737-9 window starts in 2021 and 2021 is
excluded, so only 2022 onward survives. Second, and structural: Alaska launched
31 in-scope spells into 21 distinct metros over the wider window, but nearly all
are re-entries into metros Alaska already serves, and the candidate rule excludes
already-served metros by construction. A new *spell* is not a new *market*.
Alaska's SEA network is mature and has stopped adding in-scope new markets: the
2023 and 2024 decision dates yield zero positives.

**Porter has 5 positives at a single decision date.** With one date there is no
variation across dates to bootstrap, so an interval cannot be computed by
resampling decision vintages. Agreement at k is computable for that one date and
the five named markets can be reported with their model ranks. That is a finding,
not a test.

### 3.2 Family 2: survival, 24 and 36 month cohorts

Cohort start is `max(snapshot floor 2019-01, gauge first month)` with 2020 and
2021 launch years removed: WestJet 2019-01, Alaska 2021-03, Porter 2023-11.

| study | horizon | eligible | events | censored | of which seasonal | unique markets |
|---|---|---|---|---|---|---|
| westjet_yyc | 24m | 10 | **1** | 9 | 9 | 9 |
| westjet_yyc | 36m | 5 | **1** | 4 | 4 | 5 |
| alaska_sea | 24m | 17 | **11** | 6 | 9 | 11 |
| alaska_sea | 36m | 7 | **3** | 4 | 1 | 7 |
| porter_yyz | 24m | 8 | **0** | 8 | 3 | 7 |
| porter_yyz | 36m | 0 | **0** | 0 | 0 | 0 |
| **pooled** | **24m** | **35** | **12** | **23** | **21** | **27** |

**Corporate-shutdown cessations: zero, in all three studies.** This is a clean
improvement on the existing backtest, whose 21 ceased routes include 9 Lynx
rows killed by a single corporate shutdown. All three study carriers are still
operating. The one corporate event in range is Swoop folding into WestJet in
October 2023, and Swoop (`WO`, 3,904 departures, 2021-01 to 2023-07) flew **no
YYC to US segments in scope**, so it contributes no cessations either. The
competing-risks problem that motivated Fine-Gray largely disappears when the
replay is scoped to the study carriers.

**Two findings that matter more than the counts.**

**Seasonality dominates the cohort.** 21 of 35 eligible launches are seasonal,
and 9 of WestJet's 10 eligible are. Across full history the proportion is
similar: 26 of 37 WestJet, 90 of 136 Alaska. WestJet's Calgary transborder
network and much of Alaska's Seattle spoke network are seasonal sun and leisure
service. A seasonal route stopping is not a failure, and the study
configurations (year-round service at 3, 7 or 14 weekly) do not describe these
routes at all. Any survival analysis that treats a seasonal stop as an event is
measuring the calendar.

**The event count forbids formal modelling, more firmly than before.** Twelve
events pooled, of which eleven are Alaska, against a Cox model that would want
distance, carrier, competitive structure and seasonality. That is under one
covariate's worth of information by any conventional events-per-variable rule,
and the events are concentrated in the one study whose Family 1 cell is
degenerate. **Cox and Fine-Gray were not chosen in advance and are not justified
by these counts.** WestJet contributes 1 event and Porter 0.

A longer-history alternative exists and should be understood before anyone
proposes it as a rescue. Dropping both the applicability and snapshot floors
gives 182 eligible and 57 events across the three studies, which would carry a
modest Cox model. **It would not answer the question.** Pre-2018 launches cannot
be scored with the model's verdict, because DB1B and Form 41 do not reach them,
and pre-gauge launches were flown by an aircraft the study does not configure.
Such an analysis could regress survival on crude covariates or on a gravity
demand percentile only, which is exactly what the existing backtest already
does, and it found no separation (0.89 operating against 0.86 ceased). It would
add sample size without adding the thing the family exists to test, and it would
reintroduce the back-projection this correction pass removed.

### 3.3 Family 3: right-sizing

`initial_freq_wk` in the derived register is **the maximum one-way frequency
over the first three active months**. It is a proxy for the opening schedule,
not the literal opening-day schedule. Three proxies were computed and compared.

Availability and disagreement, over all in-scope spells (the wider sample is
retained here because proxy disagreement is a property of the measurement, not
of the replay cohort):

| study | n | full 3 months available | m1 median freq/wk | 3mo-max median | 3mo-median median | rows where m1 differs from 3mo-max | median ratio 3mo-max to m1 |
|---|---|---|---|---|---|---|---|
| westjet_yyc | 40 | 36 | 3.7 | 6.0 | 6.0 | **77.5%** | 1.28 |
| alaska_sea | 142 | 123 | 6.6 | 14.3 | 13.7 | **72.5%** | 1.46 |
| porter_yyz | 14 | 14 | 8.9 | 14.1 | 13.3 | **78.6%** | 1.41 |

The three proxies disagree on roughly three quarters of spells and the choice
moves the target by 28% to 46% at the median. **Which proxy the protocol picks
must be frozen before results are seen**, because it materially changes the
measured bias.

**Corrected replay cohort** (applicability window, 2020 and 2021 excluded):

| study | cohort n | unique markets | observed opening median, 3mo-max |
|---|---|---|---|
| westjet_yyc | 13 | 12 | 6.0 |
| alaska_sea | 23 | 16 | 11.5 |
| porter_yyz | 13 | 11 | 14.3 |
| **pooled** | **49** | **39** | |

Family 3 is the one family the corrections barely touch, because it needs
launches rather than decision dates.

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
| alaska_sea | 3 (2022, 2023, 2024) | about 45 | **about 135** | **1** |
| porter_yyz | 1 (2024) | about 79 | **about 79** | **5** |

Candidate counts per date are the current-vintage values and will move once the
candidate set is generated point-in-time, particularly through the served-market
exclusion, which is why they are given as approximate. **No predictive
performance was computed here**, because W1.3 does not exist yet and computing it
against current-vintage covariates would produce exactly the contaminated number
this stage is meant to prevent.

**Only WestJet supports the comparison this family exists to make.** With one
positive, Alaska cannot distinguish the full verdict from a demand percentile at
any confidence. With five positives at a single decision date, Porter can rank
them under both methods and report the difference, but cannot attach an
interval. The question "does the full model beat demand rank" therefore has one
real test in this project, on the flagship study, with 18 positives across four
decision dates.

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

## 5b. The StatCan survey floor: a defect to record, not to fix

Stage 0 established two facts about the transborder anchor: it is a 1997 to 2018
annual panel, and **its publication floor moves by vintage** (minimum published
value 280 to 3,090 across years; 1st percentile 2,650 to 3,920). The frozen
model applies a single `SURVEY_THRESHOLD = 4000.0` in `models/demand.py`.

**This is a newly discovered defect in the frozen baseline.** It is recorded as
one and it is **not fixed during Milestone A.** Stage 1 measures the frozen
model; changing the model while measuring it produces a baseline that moved
while it was being built, which is not a baseline.

The policy for Stage 1, to be carried verbatim into the replay protocol:

| aspect | policy |
|---|---|
| point-in-time anchor value | **use the historically appropriate vintage** where the pair has one; this is snapshot reconstruction, not a model change |
| the cap threshold | **retain the frozen `SURVEY_THRESHOLD = 4000.0`** and the frozen cap behaviour, unchanged, in the primary baseline |
| the mismatch | **flag it** on every affected row and in the V2 baseline document as a known limitation |
| vintage-specific floor | **may be computed as a labelled sensitivity only**; it must not replace frozen behaviour |
| resolution | carried to **W3.4 / the Canadian thin-market calibration**, where it is decided on evidence with a change report |

Using the vintaged anchor value while retaining the frozen threshold is not
inconsistent. The anchor is **data at a date**, which point-in-time
reconstruction is obliged to get right. The threshold is a **model parameter**,
which Milestone A is obliged to leave alone.

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
    2023 and 2024 decision dates, and exactly one across its whole admissible
    window.
13. **Newly known from the correction pass**: the configured gauge of each study
    first flew hub to US in 2018-03 (WestJet), 2021-03 (Alaska) and 2023-11
    (Porter), which is what sets the applicability windows.
14. **Newly known from the correction pass**: under the literal rule Porter has
    exactly one admissible decision date, and the fleet-commitment alternative
    would give three. The difference is 5 positives against 21. **The choice was
    made on methodology before the protocol was frozen, and both numbers are
    published so the choice can be audited.**

---

## 7. Feasibility table (0I)

`required_data_complete` means the warehouse holds every input the cell needs.
`offline_cache_complete` means it can be built without a network call.
Feasibility is one of **FULL**, **DESCRIPTIVE_ONLY**, **NOT_ESTIMABLE**. Blank
means not applicable, never a fabricated zero.

Primary baseline: literal configuration, 2020 and 2021 excluded, snapshot floor
2019-01.

| study | metric_family | horizon | applicable_start | applicable_end | decision_rows | unique_markets | launches | events | censored | corporate_shutdown_events | required_data_complete | offline_cache_complete | major_lookahead | recommended_analysis | feasibility |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| westjet_yyc | 1 launch agreement | 24m | 2019-01 | 2024-04 | ~304 | 76 | 18 | | | 0 | yes | yes | 2023 CBSA geography; carrier brand map not effective-dated | agreement at k with PU caveat; bootstrap CI over 4 decision dates | **FULL** |
| alaska_sea | 1 launch agreement | 24m | 2022-01 | 2024-04 | ~135 | 45 | **1** | | | 0 | yes | yes | 2023 CBSA geography | report the single named market; no rate, no curve | **NOT_ESTIMABLE** |
| porter_yyz | 1 launch agreement | 24m | 2023-11 | 2024-04 | ~79 | 79 | **5** | | | 0 | yes | yes | 2023 CBSA geography; one decision date, no cross-date variation | agreement at k for one date; 5 named markets with model rank; no interval | **DESCRIPTIVE_ONLY** |
| westjet_yyc | 2 survival | 24m | 2019-01 | 2024-04 | | 9 | 10 | **1** | 9 | 0 | yes | yes | 9 of 10 seasonal; a seasonal stop is not a failure | none; report N and the single event | **NOT_ESTIMABLE** |
| westjet_yyc | 2 survival | 36m | 2019-01 | 2023-04 | | 5 | 5 | **1** | 4 | 0 | yes | yes | as above | none; report N | **NOT_ESTIMABLE** |
| alaska_sea | 2 survival | 24m | 2022-01 | 2024-04 | | 11 | 17 | **11** | 6 | 0 | yes | yes | 9 of 17 seasonal | descriptive KM; no covariates | **DESCRIPTIVE_ONLY** |
| alaska_sea | 2 survival | 36m | 2022-01 | 2023-04 | | 7 | 7 | **3** | 4 | 0 | yes | yes | as above | none; report N | **NOT_ESTIMABLE** |
| porter_yyz | 2 survival | 24m | 2023-11 | 2024-04 | | 7 | 8 | **0** | 8 | 0 | yes | yes | zero events, no variation to explain | none; report zero events | **NOT_ESTIMABLE** |
| porter_yyz | 2 survival | 36m | | | | | | | | 0 | no: window empty | yes | window closes before it opens | none | **NOT_ESTIMABLE** |
| westjet_yyc | 3 right-sizing | opening | 2019-01 | 2024-04 | | 12 | 13 | | | 0 | yes | yes | proxy choice moves target 28% | bias and MAE against frozen proxy; report all three proxies | **FULL** |
| alaska_sea | 3 right-sizing | opening | 2022-01 | 2024-04 | | 16 | 23 | | | 0 | yes | yes | proxy choice moves target 46% | bias and MAE; split by seasonal flag | **FULL** |
| porter_yyz | 3 right-sizing | opening | 2023-11 | 2024-04 | | 11 | 13 | | | 0 | yes | yes | proxy choice moves target 41% | bias and MAE; small N stated | **FULL** |
| westjet_yyc | 4 incremental value | 24m | 2019-01 | 2024-04 | ~304 | 76 | 18 | | | 0 | yes | yes | same as family 1 | full verdict against demand percentile, identical rows | **FULL** |
| alaska_sea | 4 incremental value | 24m | 2022-01 | 2024-04 | ~135 | 45 | **1** | | | 0 | yes | yes | same as family 1 | none | **NOT_ESTIMABLE** |
| porter_yyz | 4 incremental value | 24m | 2023-11 | 2024-04 | ~79 | 79 | **5** | | | 0 | yes | yes | same as family 1 | rank the 5 under both methods; report difference, no interval | **DESCRIPTIVE_ONLY** |

Pooled 24-month survival: **35 eligible, 12 events, 21 of the eligible
seasonal**, and 11 of the 12 events are Alaska. Pooling does not rescue the
family; it remains DESCRIPTIVE_ONLY at best.

### 7.1 Labelled alternative, not primary

Recorded so the effect of the applicability rule is auditable rather than
buried. Under a fleet-commitment rule for Porter (applicability at the public
E195-E2 order rather than at first flight, first admissible non-excluded date
2022-01):

| study | metric_family | decision_rows | launches | feasibility under alternative | feasibility under primary |
|---|---|---|---|---|---|
| porter_yyz | 1 launch agreement | ~237 (3 dates) | 21 | FULL | **DESCRIPTIVE_ONLY** |
| porter_yyz | 4 incremental value | ~237 (3 dates) | 21 | FULL | **DESCRIPTIVE_ONLY** |

No survival or right-sizing cell changes, because those depend on launches
rather than decision dates. **The primary baseline uses the literal rule.**

---

## 8. Stage 0 verdict

Reassessed after the correction pass. The verdict survives, and the reasoning
for it has changed.

**What survives as a real test.** Five cells are FULL: WestJet Family 1, WestJet
Family 4, and right-sizing in all three studies. That is 18 positive events
across 4 decision dates on the flagship study, plus 49 observed openings across
39 distinct markets for the family that already carries the project's strongest
falsifying signal. Both of the two genuine blockers (DB1B start date, historical
geography) are bounded and disclosable, and the largest anticipated blocker
(historical transborder anchors) turned out not to exist.

**What does not survive, stated without softening.** Alaska is
**NOT_ESTIMABLE** on Families 1 and 4: one positive. Porter is
**DESCRIPTIVE_ONLY** on Families 1 and 4: five positives at a single decision
date, so no interval. Family 2 is **NOT_ESTIMABLE** in five of six cells and
**DESCRIPTIVE_ONLY** in the sixth.

**SAFE TO IMPLEMENT SCOPED W1.3/W1.4**

The word "scoped" is now carrying considerably more weight, and one goal in the
approved plan is provably unreachable. See section 8.1.

Scope, and nothing beyond it:

1. **Build `snapshot(t)` for eight study-date pairs only**: WestJet at 2019,
   2022, 2023 and 2024; Alaska at 2022, 2023 and 2024; Porter at 2024. Not a
   general historical engine. Persist only the plumbing those dates need.
2. **Vintage what can be vintaged offline**: BEA income, population and GDP from
   the cached full-year columns; StatCan CMA population 2001 to 2022; the StatCan
   transborder anchor **at its own reference year**; T-100 and DB1B windows
   ending at the cutoff; Form 41 and EIA at vintage.
3. **Retain the frozen `SURVEY_THRESHOLD = 4000.0`** and all frozen cap
   behaviour. Vintage the anchor *value*, never the model *parameter*. Flag the
   mismatch; do not fix it. See section 5b.
4. **Disclose what cannot be vintaged**: 2023 CBSA geography everywhere, and
   carrier brand resolution that is not effective-dated. Record both on every
   snapshot row.
5. **Freeze the frequency proxy in the protocol before running anything**, since
   the three proxies move the target by 28% to 46%.
6. **Run WestJet Families 1 and 4, and right-sizing in all three studies, as
   primary.** Report every other cell at its stated feasibility and no higher.
7. **Do not fix any defect found while measuring.** Record it for Stage 2 or 3.

### 8.1 One approved goal is now provably unreachable

`PHASE_5_6_PLAN.md` W1.4 sets as its success criterion that "`docs/backtest.md`
reports all four metric families below, with confidence intervals, and states
plainly where the model has no signal."

**The first half cannot be met and the second half can.** Confidence intervals
are computable for exactly two cells (WestJet Families 1 and 4, by bootstrap over
four decision dates) and for right-sizing bias. They are not computable for any
survival cell, for Alaska Family 1 or 4, or for Porter Family 1 or 4.

This is flagged rather than worked around, per the plan's own instruction not to
reorder it silently: **the W1.4 success criterion should be amended in writing
before Stage 1 begins**, to require intervals where estimable and an explicit
feasibility label everywhere else. The alternative, which is to widen windows or
pool studies until an interval appears, would manufacture the certainty this
whole stage exists to prevent.

### 8.2 What the V2 predictive baseline can and cannot claim

Recorded now so Stage 1F does not overreach when it freezes the baseline.

**Can claim:** a point-in-time predictive baseline for the **WestJet flagship
study** on launch agreement and incremental value over demand rank; a
right-sizing bias measurement across all three studies; a descriptive survival
picture dominated by seasonality.

**Cannot claim:** a cross-study predictive baseline; any survival result with an
interval; any Alaska predictive result; any Porter result with an interval.

A later change that improves a WestJet Family 1 or 4 metric can be scored against
this baseline. A change whose only evidence is an Alaska or Porter predictive
metric cannot, and must not be adopted on that basis.

### 8.3 Settled during the correction pass

Both items previously left open are now closed, and both were closed on
methodology rather than on the counts they produce:

- **2021.** Excluded from the primary baseline, with 2020, per the
  `PHASE_5_6_PLAN.md` W1.6 precommitment. A 2021-admitted analysis may be
  published later as a labelled sensitivity only.
- **The per-vintage survey floor.** Recorded as a newly discovered defect in the
  frozen baseline; the frozen 4,000 threshold is retained for Stage 1; the fix is
  carried to W3.4 under a change report. See section 5b.
