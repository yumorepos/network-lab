# Phase 5 Milestone A: completion report

**Date.** 2026-08-14
**Branch.** `claude/network-lab-finalization`, branched from `e5f0e55`.
**Scope.** Stage 0 (feasibility) and Stage 1 (W1.3 snapshots, W1.4 replay,
V2 predictive baseline) of the finalization controller.

**Milestone A measures. It does not change the model.** No model default, no
value in `config/assumptions.yaml`, no threshold and no committed artifact was
modified. Every defect found while measuring is recorded for Phase 6 rather
than fixed in place, because a baseline that moved while it was being built is
not a baseline.

---

## 1. What Milestone A was missing, and what now exists

| task | state at handoff (`e5f0e55`) | state now |
|---|---|---|
| W1.1 T-100 full history | done | done |
| W1.2 route-spell register | done | done, and its role clarified: outcomes, not decisions |
| W1.3 point-in-time machinery | **audit only; `snapshot(t)` not built** | **built**, scoped to seven study-by-date pairs |
| W1.4 decision replay, four families | **not built** | **built and executed** |
| W1.4 predictive baseline | **did not exist** | **frozen**, `docs/W1.4_predictive_baseline_v2.md` |
| W3.1 Canadian demand diagnostic | done | done |

## 2. What was built

**Offline point-in-time data.** `replay/pit_metros.py` recovers 51,115 US
metro-years (920 metros, 1969 to 2024) and 3,916 Canadian metro-years (2001 to
2022) from the frozen cache. It imports no downloader and raises on a missing
input, because `ingest.common.download_file` fails **open** to the network by
design. Validated against the production ingest for the year they share:
**maximum relative difference 0.000e+00** on population, income and GDP across
919 metros.

**Vintage policy.** `replay/vintage.py` answers six questions per source
(reference period, original availability, data vintage, permitted cutoff,
policy, lookahead exception) under three policies: `as_available_by_cutoff`,
`latest_revised_historical_value`, `stale_historical_anchor`. Resolvers fail
closed rather than reaching forward.

**`snapshot(t)`.** `replay/snapshot.py` rebuilds candidates, demand,
competition and share, economics, right-sizing and verdict at a decision date.
It **imports** the production scoring functions rather than reimplementing
them; only the vintage-sensitive queries are rewritten.

**Three behaviour-preserving production refactors** so the replay shares real
code: `metro_anchor_points` gains `seats_year` and `metro_override`,
`fuel_price_base` gains `as_of`, and the anchor matcher is extracted to
`demand.anchor_finder(con, hub, year)`. All default to current behaviour,
verified by content comparison: 27 artifacts identical.

## 3. Evidence discipline

**Parity, 13 tests.** A snapshot pinned to production vintages must reproduce
every committed verdict **market by market**, plus chosen frequency, demand
within 1e-9, and the headline totals. This is the guard that
`models/share_validation.py` lacked when it silently measured a different model
in round 4. Counts alone hide compensating moves.

**Leakage, 36 tests, and 10 of 10 injected leaks demonstrated to fire.** Per
integrity round 4's lesson that a test never shown to fail is a test of nothing,
`scripts/demo_leakage_tests.py` reintroduces each leak and records whether the
guard caught it. Injections include the T-100 window moved to the panel end,
`db1b_year` forced to the production 2024, a gravity resolver that ignores
publication, the served-market window reading the future, and the offline
transform pointed at a missing file.

**Two defects in my own work were caught by these guards before results were
seen:** the geography guard keyed off the calendar year, so a 2023-01 cutoff
read as clean while using a delineation not released until 2023-07; and the
first gravity injection proved nothing because it tested that the resolver
refuses an unpublished window, which it correctly does.

**Protocol frozen before results.** `docs/W1.4_REPLAY_PROTOCOL.md`, commit
`e6ea62e`, committed when no metric code existed. It freezes the ranking score,
the `k` values, the frequency proxy, the bootstrap design, the corporate and
seasonal treatment, and the decision not to fit any survival model. Section 8.1
discloses the partial outputs already observed during implementation rather than
claiming a clean freeze.

## 4. Results

Full detail in `docs/W1.4_replay_results.md` (generated, never hand-edited).
Scoreboard in `docs/W1.4_predictive_baseline_v2.md`.

### 4.1 The headline

On **WestJet YYC**, the only cell the feasibility gate classified FULL: 244
decision rows, 89 metros, three decision dates, 15 positives.

| metric | model | demand percentile |
|---|---|---|
| agreement@10 | 0.333 [0.133, 0.500] | 0.300 [0.133, 0.500] |
| recall@10 | 0.679 [0.325, 0.953] | 0.568 [0.319, 0.933] |

The engine does find launches: roughly two thirds of them land in its top ten
of about eighty candidates. But on identical rows:

| k | difference in agreement@k | difference in recall@k |
|---|---|---|
| 5 | -0.067 [-0.200, 0.133] | -0.048 [-0.222, 0.179] |
| 10 | +0.033 [-0.100, 0.100] | +0.111 [-0.333, 0.333] |
| 20 | 0.000 [-0.033, 0.033] | 0.000 [-0.167, 0.167] |

**Every interval spans zero. The full engine shows no measurable incremental
value over ranking markets by modeled demand alone.** The protocol pre-committed
to publishing this if it happened, and it happened. Porter is directionally
worse than demand rank at k=20.

### 4.2 Right-sizing

18 launches paired with the decision date preceding them. The model chose the
minimum of its frequency list on **18 of 18**, and on **461 of 463** decision
rows overall.

| study | n | median ratio, chosen to observed |
|---|---|---|
| westjet_yyc | 10 | 1.003 [0.725, 1.449] |
| alaska_sea | 2 | **0.428 [0.421, 0.435]** |
| porter_yyz | 6 | **0.461 [0.285, 0.864]** |

**This refines the Stage 0 prior rather than confirming it.** Stage 0 compared
all historical spells against the current all-3x screen and inferred a uniform
downward bias. Paired properly, the bias is study-specific: absent at WestJet,
about a factor of two at Alaska and Porter. WestJet's 1.00 is not calibration,
because a constant cannot correlate with anything; WestJet's recent openings
simply happen to be thin.

### 4.3 Survival

Descriptive only, as frozen. Alaska 24m: 22 eligible, 12 events, 7 of them
seasonal. WestJet 24m: 9 eligible, 1 event. Porter 24m: 3 eligible, 0 events.
**Corporate-shutdown events: zero in all three studies.** No Cox or Fine-Gray
model was fitted.

## 5. Defects discovered. Recorded, not fixed.

**D1. Corridor growth collapses transborder demand at a COVID vintage.** Growth
is a raw ratio of two single T-100 years with no COVID handling. At a 2023-01
cutoff the latest complete year is 2021, giving growth **0.196** at YYC and
**0.166** at YYZ. Median anchored WestJet demand falls from 13,156 to 2,023 and
median margin to -3,829%. The 2023-01 cell is dominated by this artifact and
contributes 5 of WestJet's 15 positives. Production avoids it only because it
happens to read 2024. **This is the most consequential finding after the
Family 4 null.**

**D2. Right-sizing has no discriminating power.** 461 of 463 decision rows
choose the minimum option.

**D3. The survey threshold is a fixed 4,000** while the true StatCan publication
floor moves by vintage (280 to 3,090). Retained deliberately; carried to W3.4.

**D4. Stage 0's snapshot floor was too early.** It was derived from cache
coverage without publication lag. A 2019-01 cutoff needs 2017 DB1B and Form 41,
which are not cached, so WestJet has three decision dates rather than four.
Corrected in the protocol.

**D5. `metro_anchor_points` pins seats to 2024** against a panel running to
2026-04 (W1.3 audit vector L10), and production's stale vintages are reproduced
in `production_vintages()` so parity isolates pipeline equivalence from vintage
selection.

## 6. Gate status

Run from the frozen cache. No network, `make data` not run.

| gate | result | exit |
|---|---|---|
| `make all` | green; no generated markdown changed | 0 |
| `make test` | **94 passed** (45 pre-existing, all still green; 49 new) | 0 |
| `make reproducibility`, run 1 | **27 artifacts identical** across a warehouse rebuild | 0 |
| `make reproducibility`, run 2 | **27 artifacts identical** across a warehouse rebuild | 0 |

The `make test` row records the gate as measured at `d514ec2`. The independent
review then found finding P1-1, and closing it took two commits: the execution
half at `4f8dbae` (the historical chain was executed by no test) and the
provenance half at the closure commit (two high-leverage vintage paths carried
no record and no guard). The suite is now **143 passed**. See
docs/MILESTONE_A_INDEPENDENT_REVIEW.md addenda A.2 and B.

### 6.1 Reproducibility, run twice as required

Both runs rebuilt the DuckDB marts from cached Parquet, re-ran the models and
the backtest, and compared every artifact on **content** (joined on keys, 1e-6
float tolerance, covering Parquet, CSV and YAML) rather than on bytes. Byte
equality is explicitly not the contract: `make all` rewrites 14 tracked files
with float last-bit noise of order 1e-15 from parallel float summation in
DuckDB.

The count stayed at 27 rather than growing, which is the correct outcome:
Milestone A added no model artifact. The replay writes to
`data/parquet/replay/`, which is gitignored and outside the gate, because it is
evidence about the model rather than an output of it.

**Headline numbers unchanged throughout.** WestJet 0/0/76, Alaska 0/0/45, Porter
1 LAUNCH (Boston) / 1 MONITOR (Hartford) / 77 PASS, 200 candidates. The parity
tests assert this independently, market by market, from the replay side.

## 7. What this baseline may not be used to claim

Repeated from the V2 freeze because it is the thing most likely to be misused.

- **No cross-study predictive claim.**
- **No Alaska predictive claim.** One positive event.
- **No Porter claim with an interval.** One decision date.
- **No survival claim with an interval**, any horizon, any study.
- **An improvement inside an interval that spans zero is not an improvement.**

## 8. Consequence for Milestone B, stated as evidence not as a decision

The Family 4 null is directly relevant to how much of Milestone B is worth
doing, and that call belongs to the reviewer rather than to this report.

The competition, share and economics layers are what separate the full engine
from a demand ranking. On the one cell where the question is answerable, they
add nothing measurable. Milestone B (W2.2 brand mapping, W2.3 connection
heuristics, W2.4 QSI weights, W2.5 fare structure) is calibration of exactly
those layers.

Two readings are consistent with the evidence and this report does not choose
between them:

1. **The layers are miscalibrated**, and Milestone B is what would make them
   informative. The Family 4 null is then a reason to do Milestone B.
2. **The layers are the wrong place to spend**, because 15 positives on one
   study cannot detect the size of improvement Milestone B would deliver even
   if it worked perfectly.

What the evidence does say clearly is that **D1 is a larger defect than
anything Milestone B targets**, is cheap to fix, and currently corrupts a third
of the replay. On the numbers, it is the strongest candidate for the next piece
of work.

## 9. Verdict

Every Stage 1 objective is complete: the scope amendment is made prospectively,
the offline transforms are built and validated, `snapshot(t)` exists and is
guarded, the leakage tests are demonstrated to fail on injection, the protocol
was frozen before results, only approved cells were run, the V2 baseline is
frozen, and the gates are green.

The project now has what it did not have at handoff: a predictive scoreboard,
and an honest statement of how narrow it is.

---

## 10. Independent review and closure

Sections 1 to 9 above are the report as submitted for review, unchanged apart
from the test count in section 6. This section records what the review returned
and how it was closed.

### 10.1 Verdicts

| subject | verdict |
|---|---|
| Milestone A | **APPROVE WITH NONBLOCKING FINDINGS** |
| the remaining roadmap | **REDESIGN THE REMAINING ROADMAP** |

No P0. The review is `docs/MILESTONE_A_INDEPENDENT_REVIEW.md`; addendum A is a
second reviewer session that re-derived P1-1 independently and widened it;
addendum B records the closure.

### 10.2 Finding status at freeze

| finding | status | note |
|---|---|---|
| **P1-1** two high-leverage vintage paths have no guard and no provenance | **CLOSED** | execution coverage at `4f8dbae`, provenance records and guards at the closure commit |
| **P1-2** the headline is a one-date result and the per-date breakdown was not published | **OPEN** | a reporting addition to unchanged numbers; see 10.3 |
| P2-1 to P2-4 | open, nonblocking | recorded in the review, section 15 |

### 10.3 P1-2 is open, deliberately, and is a prerequisite for the roadmap

The required resolution is to emit the per-date and leave-one-date-out tables
from `replay/report.py` into `docs/W1.4_replay_results.md` and the V2 document,
and to state that the intervals do not represent variation across decision
vintages. Addendum A.6 verified those numbers reproduce; it did not publish
them.

This is now load-bearing beyond the review. The per-date breakdown is the
evidence the roadmap redesign rests on: that the pooled agreement@10 advantage
is one market at one date, that 2022-01 and 2023-01 are zero, and that k=5 is
negative. Those facts should be cited from a generated artifact rather than
from a review appendix.

### 10.4 Gate status at freeze

| gate | result |
|---|---|
| `make test` | **143 passed** |
| `make reproducibility` | **27 artifacts identical** across a warehouse rebuild |
| replay re-executed end to end | `results.json` **bit-identical**; every family metric and bootstrap interval unchanged |

The replay was re-run in full after the closure change. `outcomes`,
`rightsizing_pairs`, `vintage_demand_dispersion` and `vintage_transfer_growth`
are identical row for row. `decision_rows` differs only in `margin_pct`,
`annual_contribution` and the `score_model` derived from `margin_pct`, at a
maximum **3.3e-15 relative**, with zero verdict changes, zero frequency
changes, and identical top-5, top-10 and top-20 sets at every decision date.
`demand_pax_yr`, the column the corridor-growth path feeds, is bit-identical.

That residual is not attributable to the change. Two runs of **identical**
code in separate processes reproduce the same noise (`margin_pct` differing on
79 rows at 9.1e-12 absolute), which is the DuckDB parallel float summation
already documented in section 6.1.

`provenance.parquet` gains 21 rows, three sources across seven study-by-date
snapshots. That is the change, not a side effect of it.

### 10.5 No model behaviour changed during closure

- No value in `config/assumptions.yaml`, no study config, no threshold.
- No model default and no scoring function.
- `docs/W1.4_predictive_baseline_v2.md` is untouched. V2 remains the immutable
  baseline describing the frozen pre-calibration engine.
- No source data, no network call, `make data` not run.

### 10.6 What this baseline still may not be used to claim

Section 7 stands in full and is the most misusable part of this report. Added
to it, from the review: the Family 4 null is measured on **15 positives across
three dates on one study**, and the recall@10 difference interval is
[-0.333, 0.333]. At k=20 both models reach recall 1.000, so the difference
there is pinned at zero arithmetically rather than measured. A null on an
instrument this blunt is not the same claim as a demonstrated absence of
value, and the two should not be collapsed in any downstream write-up.

### 10.7 Freeze

**MILESTONE A FROZEN.** Reviewed, closed on P1-1, gates green, V2 immutable.
The remaining roadmap is redesigned separately and is not part of this
milestone.
