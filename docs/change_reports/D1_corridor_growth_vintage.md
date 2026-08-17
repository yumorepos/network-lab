# Change report: D1, the corridor-growth vintage

**Task.** T1 of the six-task finish plan in `docs/STAGE_2R_DECISION.md`
section 6. Supersedes W2.x numbering; the old Milestone B sequence is closed.
**Date.** 2026-08-17
**Baseline.** The frozen V2 predictive baseline,
`docs/W1.4_predictive_baseline_v2.md`, which remains **immutable**. D1 is
carried *in* that baseline as recorded defect 1.

---

## 0. Protocol, frozen before any post-fix metric was computed

**Sections 0 and 1 of this document were written and committed before the fix
existed.** The results sections were appended afterwards. That ordering is the
point: the acceptance criteria below could not have been chosen to match an
outcome, in the same way `docs/W1.4_REPLAY_PROTOCOL.md` was frozen before the
replay ran.

### 0.1 The defect, exactly

`replay/snapshot.py:build_transfer` scales every anchored and every capped
transborder demand row by

    growth(hub) = T-100 transborder pax(hub, growth_year)
                / T-100 transborder pax(hub, anchor_year)

The numerator year is resolved by
`replay/vintage.py:Vintages.t100_corridor_growth_year`, which calls
`_t100_complete_year`. That helper returns the latest complete T-100 calendar
year inside the permitted point-in-time window and **applies no exclusion set
at all**.

Every other vintage resolver in the same class does apply one.
`_latest_complete_year`, which serves DB1B, Form 41 and BEA, takes an
`exclude` argument and is called with `excluded_data_years()`. The corridor
growth year is the one selection in the file that skips that step.

### 0.2 Why the current rule violates an already-approved policy

`config/replay_protocol.yaml` records, with its source, that **2020 and 2021
are a structural break**. The protocol then applies that finding to decision
vintages and launch cohorts, and deliberately keeps 2021 admissible as *input
data*, on the stated ground that a planner at 2023-01 did in fact hold 2021
data.

That reasoning is correct for a **level** input and wrong for a **ratio**. The
corridor growth term is not a level a planner read; it is a two-point trend
estimator whose numerator is one calendar year. Placing a declared
structural-break year at one end of a two-point trend and then applying the
result as a permanent level shift with no recovery expectation is a
specification error, not a point-in-time fact. `docs/W1.4_replay_results.md`
already says so in prose: a planner in January 2023 genuinely saw depressed
2021 traffic, and what no planner would have done is treat it as permanent.

So the defect is narrow and precisely stated: **a structural-break year is
admissible as a level input and is not admissible as an endpoint of a growth
ratio.** The repair makes the corridor-growth resolver apply the exclusion its
sibling resolvers already apply.

### 0.3 The rule adopted

> The corridor-growth numerator year is the latest complete T-100 calendar
> year inside the permitted point-in-time window that is **not a declared
> structural-break year**.

Smallest rule that removes the inconsistency. In particular:

- it does **not** pin the year to 2019, or to any fixed year;
- it does **not** change the permitted window, the reporting lag, or the
  anchor year;
- it does **not** change `t100_seats_year`, which shares the same helper.
  Seats are a level input feeding the candidate seat floor and the satellite
  rule. Excluding a break year there would change the **candidate set** at
  2023-01, which is a different and much larger change than D1, and is not the
  defect. The two uses are separated in the resolver for exactly this reason.

The structural-break years are not a new constant. They are the value already
declared in `config/replay_protocol.yaml` with its source
(`PHASE_5_6_PLAN.md` W1.6). The repair adds an explicit
`structural_break_years` entry carrying that same value and source, so that
the growth-ratio use is declared rather than borrowed from an entry about
decision vintages, and so a future change to one use cannot silently move the
other.

### 0.4 Scope: what must not change

- demand architecture, and the anchor / cap / gravity branching;
- the transfer factor;
- QSI and share;
- fares and costs;
- frequency selection;
- verdict thresholds;
- `SURVEY_THRESHOLD` and anything in `config/assumptions.yaml`;
- `t100_seats_year` and therefore the candidate set;
- every Milestone A provenance guarantee. The corrected year must still be
  recorded as a `Provenance` row naming the value actually used.

### 0.5 Which cutoffs the rule is expected to touch

Derived from the resolver and the cached T-100 years **before** the fix was
written, so this is a prediction and not an observation.

| cutoff | complete years in window | current growth year | expected after |
|---|---|---|---|
| 2022-01 | ... 2019 | 2019 | **2019, unchanged** |
| 2023-01 | ... 2019, 2021 | **2021** | **2019, changed** |
| 2024-01 | ... 2019, 2021, 2022 | 2022 | **2022, unchanged** |

2020 is absent from the warehouse entirely, so it never competes.

**Expected blast radius: the WestJet 2023-01 cell, and nothing else.** Alaska
is `us_domestic` and has no growth term. Porter's only decision date is
2024-01, whose growth year 2022 is not a break year.

**This is narrower than the Stage 2R.4 counterfactual.** 2R.4 measured
`alt_year = 2019` at *every* transborder study-date, which is the stronger
intervention "always use the last pre-COVID year". The repair adopted here is
"skip structural-break years", which leaves 2024-01 alone. The 2R.4 Porter
numbers therefore describe a change that is **not** being made, and the Porter
predictions in that stage should not be expected to reproduce. Recorded here,
before measurement, so the divergence cannot later be presented as a surprise
or as a repair that quietly grew.

### 0.6 Invariants the repair must preserve

1. `t100_seats_year` unchanged at every cutoff, and therefore the candidate
   set unchanged: identical `cbsa` sets per study and date.
2. Growth enters as a common positive scalar on every demand branch, so within
   an affected study and date the demand ratio before-to-after is **constant
   across rows**, and the demand-only comparator ranking is **identical**.
3. The branch assignment (`anchor_x_growth`, `unanchored_capped_at_ceiling`,
   `gravity_x_transfer`) is unchanged, because the ceiling scales with growth.
4. Every unaffected study-date is bit-identical up to float noise.
5. A provenance row still records the corridor growth year at every cutoff.
6. Production outputs are unchanged. `build_transfer` returns early for the
   production vintage, and `models/transfer.py` reads a fixed 2018-to-2024
   ratio in which no break year appears.

### 0.7 Acceptance tests

The repair is accepted only if all of the following hold.

- **A1.** The corridor-growth year at 2023-01 is 2019; at 2022-01 and 2024-01
  it is unchanged.
- **A2.** A regression test fails if a structural-break year is ever selected
  as the corridor-growth numerator again, at any cutoff, including one
  constructed for the purpose.
- **A3.** Seats year and candidate sets unchanged at every cutoff.
- **A4.** At WestJet 2023-01 the demand ratio is constant across all rows to
  within float tolerance, and the demand-only ranking is identical.
- **A5.** Verdict counts and named verdicts at WestJet 2022-01 and 2024-01,
  and at Porter and Alaska, are unchanged.
- **A6.** Production artifacts reproduce: `make reproducibility` reports every
  artifact identical.
- **A7.** The full test suite passes with no assertion relaxed, no tolerance
  widened and no expected value edited.

### 0.8 Adoption rule, fixed in advance

**D1 is adopted because it corrects an established historical-input defect.**
Adoption is **not** conditional on any metric improving. Under the Stage 2R.0
resolution limit, no movement in Family 1 or Family 4 that this repair could
produce would be detectable, and a movement that did appear would be one
launch event, which the design cannot distinguish from zero. If a Family 4
number moves, it is reported and explicitly **not** claimed as an improvement.

The one outcome that would block adoption is a violation of an invariant in
section 0.6: it would mean growth is not the common scalar the analysis
assumed, and the defect would need re-diagnosis before repair.

---

## 1. Predictions to test

Restated as falsifiable claims, from Stage 2R.4 where it applies to the
narrower repair actually being made.

| # | prediction | source |
|---|---|---|
| P1 | only WestJet 2023-01 changes | section 0.5 |
| P2 | demand at WestJet 2023-01 rises by a single constant factor across all rows | 2R.4, growth is a common scalar |
| P3 | the demand-only ranking is identical at every study and date | 2R.4, verified |
| P4 | the margin ranking is identical at WestJet 2023-01 | 2R.4, unspilled regime |
| P5 | zero verdict changes anywhere | 2R.4 measured 0 WestJet verdict changes; Porter is now out of scope |
| P6 | Family 1 and Family 4 unchanged at every k | follows from P3 and P4 |
| P7 | chosen frequency unchanged everywhere | 2R.3: 445 of 463 rows are decided by the infeasibility fallback, which a demand rescale does not move off the minimum |
| P8 | Porter is entirely unchanged, contrary to the 2R.4 counterfactual | section 0.5 |

Any prediction that fails is investigated and reported rather than
accommodated.
