# Final scope contract

The frozen statement of what Network Lab is, what it is not, and what it is
entitled to claim. Written before the final packaging edits and used as the
reference every reader-facing surface is corrected against.

Hand-written, not generated. It carries no measured quantity of its own: every
number it cites belongs to a canonical source listed in section 5, and the
wording here is bounded by those sources rather than by preference.

## 1. The product

**Fixed-gauge route screening.**

Given a configured hub, carrier, aircraft gauge and an allowed schedule menu,
the engine asks whether a candidate unserved market is economically supportable,
and how the supportable ones compare.

## 2. What it is not

- fleet assignment
- network design
- validated frequency selection
- aircraft or frequency right-sizing
- proven predictive superiority over a demand-only ranking

None of these five are supported by the evidence in this repository. The fifth
is bounded rather than refuted: see section 4.

## 3. What it may claim

The project constructs traceable route-screening inputs from public data;
estimates demand, competition and share, and route economics; screens candidate
routes against a configured gauge and schedule menu; replays those screens at
historical decision dates from point-in-time data; validates the one-stop
competition and share regime; records uncertainty, lookahead and approximation
wherever they occur; falsified unsupported parts of its own original design; and
reports bounded negative predictive evidence rather than burying it.

## 4. The final predictive claim

Stated in full, and not to be shortened:

> On the WestJet Calgary historical replay, the full engine showed no detectable
> incremental ranking value over a demand-only baseline at effects larger than
> the study's resolution. Smaller effects remain unresolved.

The evidence bounds travel with the claim wherever it is made:

- 10 distinct launch events, carrying 15 positive rows
- 3 decision vintages (2022-01, 2023-01, 2024-01)
- roughly 5 net launch events across at least two vintages is the optimistic
  detectability floor, and it is a floor because it was estimated by an oracle
  construction that moves exactly the right rows with no error elsewhere
- the largest observed difference was one event
- an effect confined to a single vintage cannot be separately identified at any
  magnitude this sample permits
- k=20 is arithmetically saturated: the demand comparator already places every
  positive inside its top 20 at all three dates, so no ranking can beat it there
  by any amount

Two shortenings are specifically forbidden, because each asserts something the
study cannot support:

- "the model does not beat demand" claims a measured equivalence the design
  cannot deliver
- "the model works" claims a validated lift that was never observed

Absence of a detected effect is not evidence of equivalence. The null is
underpowered, and saying so is part of the result.

## 5. Canonical sources of record

Under the Rule 6 policy adopted for final packaging, these documents own their
numbers. Reader-facing surfaces cite them rather than restating their figures,
and any figure that is repeated outside its canonical source is either generated
from the computed artifact or covered by a consistency guard.

| subject | canonical source |
|---|---|
| headline verdict counts and current-state metrics | `data/parquet/outputs/headline_metrics.yaml` |
| predictive resolution and detectability bound | `docs/STAGE_2R0_RESOLUTION.md` |
| layer attribution and defect mechanism | `docs/STAGE_2R_DIAGNOSTICS.md` |
| scope decision, necessity gates, defect dispositions | `docs/STAGE_2R_DECISION.md` |
| connection and share validation | `docs/change_reports/T3_connection_share_validation.md`, `data/parquet/outputs/share_validation*.parquet` |
| D1 defect and repair | `docs/change_reports/D1_corridor_growth_vintage.md` |
| post-D1 comparison against V2 | `docs/W1.4_POST_D1_COMPARISON.md` |
| the immutable pre-repair predictive baseline | `docs/W1.4_predictive_baseline_v2.md` |
| replay protocol frozen before results | `docs/W1.4_REPLAY_PROTOCOL.md` |

## 6. Component status, frozen

| component | status |
|---|---|
| demand | retained; observed where DB1B exists, anchor-scaled or gravity plus transfer elsewhere, path recorded per row |
| competition and share | retained and validated for the final scope (W2.3 closed) |
| economics | retained |
| schedule selection | de-scoped; evaluates a fixed menu on one gauge and was measured effectively degenerate under the tested candidate universe |
| verdict | retained |
| D1 corridor-growth vintage | fixed |
| D2 right-sizing claim | retired, not repaired |
| D3A survey censoring and downstream asymmetry | documented limitation |
| D3B fixed historical floor | documented approximation |
| W2.1, W2.2, W2.4, W2.5 | closed as not justified for the final scope |
| W2.3 | closed by validation, no refit |
| V2 predictive baseline | immutable |
| further model tuning | stopped |

## 7. What the screening implementation still does

The engine does evaluate 3x, 7x and 14x weekly against the configured gauge.
That code path exists and is not being hidden. The distinction the wording must
carry is narrow and exact:

- the system evaluates a predefined schedule menu for a configured gauge, and
  reports the best feasible option or that none is feasible
- it does not claim to produce a validated market-level right-sized schedule

The historical replay found the selector effectively degenerate under the tested
candidate universe. That finding is disclosed rather than described as a choice.
