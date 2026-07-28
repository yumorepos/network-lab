# Change report: T-100 full history, and two non-determinism defects it exposed

**Task.** W1.1 (and an unplanned determinism fix) from PHASE_5_6_PLAN.md
**Date.** 2026-07-28
**Baseline.** Pre-baseline (Milestone A). No frozen baseline exists yet.

Milestone A is specified to contain no model changes. This report documents an
exception and argues for it: extending T-100 exposed two defects that make model
output depend on the order DuckDB happens to return rows. A baseline cannot be
frozen on a value that changes when the warehouse is rebuilt, so these are
prerequisites for the milestone rather than improvements to it.

## What was done

`ingest/bts_t100.py` extended from 8 years to 1990 through 2026 excluding 2020.
36 year files, 119 MB, `fact_segment` from 3.76 M to 13.63 M rows. 1990 was
probed before committing to the backfill: same 14 columns, 219 carriers, system
load factor 0.570 within the existing assertion band, foreign origins present.
System load factor rises monotonically from 0.571 in 1992 to 0.818 in 2015,
which is the known secular trend and evidence the parse is sound across the span.

The backfill itself should have changed nothing: every model query is windowed
to the trailing twelve months. A rebuild-and-diff was run specifically to
confirm that. It did not confirm it, which is the useful part.

## The two defects

**Ottawa's population, `models/transfer.py`.** StatCan splits the one
interprovincial CMA into three records:

```
Ottawa - Gatineau (CMA), Quebec part, Quebec        355,203
Ottawa - Gatineau (CMA), Ontario part, Ontario    1,143,407
Ottawa - Gatineau (CMA), Ontario/Quebec           1,498,610   correct for YOW
```

The code took `next((v for k, v in cma.items() if k.startswith(cma_key)), None)`.
Which of the three it returned depended on dict iteration order, which follows
DuckDB's row order and is not stable across a rebuild. The rebuild swapped
1,498,610 for 355,203, a factor of 4.2 in the gravity population term, changing
5 of 87 transfer pairs and the transfer factor that every Canadian demand
estimate rests on. YOW is the only ambiguous key of the eight.

Fixed by excluding the provincial part records, which is semantically exact
since YOW serves the whole CMA, and then **requiring the match to be unique and
raising if it is not.** Picking is how this went wrong the first time.

**Multi-city-market metros, `models/demand.py`.** A CBSA can contain more than
one BTS city market. Charlotte holds both CLT (31057) and Concord (32544), and
**43 CBSAs are like this, 6 of them in the Alaska candidate set.** The code built
`dict(...)` from a query returning multiple rows per CBSA, so the last arbitrary
row won and a metro's demand flipped between observed and modeled on row order.

Fixed by mapping every city market and aggregating: a metro's O&D is the sum
over its markets, not one of them, with fare as a passenger-weighted average.

## 1. Metric impact

No W1.4 metric family exists yet. Transfer factor returns to its committed
value; `transfer_pairs.parquet` is now identical to the pre-rebuild artifact,
confirming the Ottawa fix restores rather than changes.

| metric | before | after |
|---|---|---|
| transfer median / IQR | unchanged, restored after regression | unchanged |
| Alaska metros on observed demand | 41 of 45 | 45 of 45 |
| `fact_segment` rows | 3,762,962 | 13,630,379 |

## 2. Verdict changes

| study | LAUNCH | MONITOR | PASS |
|---|---|---|---|
| westjet_yyc | 0 / 0 | 0 / 0 | 76 / 76 |
| alaska_sea | 0 / 0 | 0 / 0 | 45 / 45 |
| porter_yyz | 1 / 1 | 1 / 1 | 77 / 77 |

**Zero markets changed category.** Five Alaska metros changed demand, all
staying PASS:

| metro | before | after | source |
|---|---|---|---|
| Charlotte-Concord-Gastonia, NC-SC | 95,186 | 175,730 | modeled to observed |
| Fayetteville-Springdale-Rogers, AR | 48,178 | 23,080 | modeled to observed |
| Albany-Schenectady-Troy, NY | 46,087 | 29,560 | modeled to observed |
| Gulfport-Biloxi, MS | 19,085 | 8,470 | modeled to observed |
| Brownsville-Harlingen, TX | 5,120 | 9,710 | observed, now summed |

Note Fayetteville-Springdale-Rogers: it was Alaska's lone MONITOR before the
Round 4 P0 fixes, and it sits on this list. That verdict was resting on an
arbitrary row order. It is PASS either way now, but it was luck rather than
correctness.

Four markets moved from modeled to observed, which is the direction that
matters: hard rule 4 requires demand to be observed where observation exists,
and for these metros it existed and was being missed.

## 3. Regression risk

**Guarded by.** `tests/test_consistency.py::test_transfer_median_consistent` and
`test_transfer_consistent_in_progress` both failed on the Ottawa regression and
are what caught it. The uniqueness assertion in `_cma_population` now converts a
silent wrong answer into a loud failure. `make test` is 32 of 32.

**Would still slip through.** Nothing tests that the CBSA to city-market
aggregation is complete rather than merely deterministic; a mapping that dropped
a market entirely would pass. Nothing asserts reproducibility across a warehouse
rebuild, which is the exact gap that let both defects live. Both are listed in
follow-ups below.

## 4. Statistical meaningfulness

Not applicable in the usual sense: these are correctness fixes, not estimates.
The relevant quantities are exact. 43 CBSAs are exposed to the city-market
defect and 6 appear in the current candidate set. 1 of 8 hub keys was exposed to
the CMA defect. Both were verified by reproducing the wrong value, applying the
fix, and confirming the corrected value.

## 5. Assumptions touched

`route_spell_min_deps_month` added: value 4, sensitivity 3 to 6, source measured
from the T-100 monthly route panel rather than asserted. 24.3% of route-months
carry one departure against a median of 26; the derived register loses 44% of
spells from floor 2 to 3 and 2.3% from floor 6 to 9, placing the elbow at 4 to 6.

No other constant added, removed or changed.

## Correction to an earlier claim

Round 4 reported the pipeline as reproducible on the basis of running
`models.run_all` twice and diffing. That check was too weak: it re-ran the models
against a **fixed warehouse**, and both defects here live at the warehouse to
model boundary and only fire on a rebuild. The honest statement is that model
execution was verified deterministic; the full pipeline was not, and was not.

## Follow-ups created

1. Add a rebuild-reproducibility test: rebuild marts and assert model outputs are
   unchanged. This is the check that would have caught both defects, and it
   currently does not exist.
2. Audit the codebase for other many-to-one lookups collapsed by `dict()`,
   `next()` or `drop_duplicates` without an explicit ordering. Two were found by
   accident; nobody has looked systematically.
3. W1.3 point-in-time snapshots must pin dimension construction, not just fact
   vintages. Both defects were in the dimension layer.
