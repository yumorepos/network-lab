# Change report: <short title>

Required for every Phase 5 and Phase 6 change (PHASE_5_6_PLAN.md, standing
requirement). A change without one does not merge. Changes that made things
worse get a report too; they are not reverted silently.

**Task.** W_._ from PHASE_5_6_PLAN.md
**Date.**
**Baseline.** Frozen W1.4 baseline commit, or "pre-baseline (Milestone A)".

## 1. Metric impact

The affected metric before and after. State which metric family from W1.4 this
touches, or "none" if the change is upstream of the scoreboard.

| metric | before | after | delta |
|---|---|---|---|

## 2. Verdict changes

Per study, before and after. Name every market that moved between categories;
counts alone hide compensating moves.

| study | LAUNCH | MONITOR | PASS |
|---|---|---|---|
| westjet_yyc | | | |
| alaska_sea | | | |
| porter_yyz | | | |

Markets that changed category:

## 3. Regression risk

Which existing tests guard this change, and what class of error would still slip
through. Be specific about the second part; every P0 in Round 4 passed a full
test suite.

- Guarded by:
- Would still slip through:

## 4. Statistical meaningfulness

Whether the improvement exceeds the noise. An interval, a holdout comparison, or
an explicit statement that the sample is too small to say.

"The number moved in the right direction" is not an acceptable answer on its own.

- Sample size:
- Interval or test:
- Verdict: improvement / no detectable change / regression / underpowered

## 5. Assumptions touched

Every constant added, removed, fitted or moved into `config/assumptions.yaml`,
with its source. Per hard rule 1, no numeric constant enters the codebase
without one.
