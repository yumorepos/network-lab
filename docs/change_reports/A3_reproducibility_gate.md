# Change report: reproducibility gate and the integrity sweep

**Task.** Milestone A integrity prerequisites, PHASE_5_6_PLAN.md
**Date.** 2026-07-28
**Baseline.** Pre-baseline. This is the work that makes a baseline possible.

Milestone A's product is a baseline **plus the evidence that it reproduces**.
`make test` runs the models against a fixed warehouse, so the mart-to-model
boundary was never exercised twice in one run and no existing test could see a
defect that only fires on a rebuild. `make reproducibility` closes that gap.

## The gate

`make reproducibility` snapshots the current outputs, rebuilds the warehouse
from cached Parquet, re-runs the models and the backtest, and asserts every
artifact is unchanged. `scripts/check_reproducible.py` does the comparison.

Four defects in the gate itself were found and fixed before it was trusted:

- `backtest_scores` and `share_validation` had no join key defined, so both were
  reported as "cannot compare" and would have failed the gate spuriously.
- `competition_*` has a null `connect_ap` and 3 duplicate itinerary tuples, so a
  key-based merge fans out. Those files fall back to a canonical sort compared
  positionally, and keys are rejected automatically when they contain nulls or
  duplicates on either side.
- YAML and CSV outputs were not compared at all. `transfer_factor.yaml` is
  precisely where the Ottawa defect surfaced, so a Parquet-only gate would have
  missed the thing it was written for.

**Result: 24 artifacts identical across a warehouse rebuild.** `make test` 36 of 36.

## What the gate found, classified

### (c) Remaining non-deterministic defect: `op_carriers`

`string_agg(DISTINCT s.carrier, '+')` has no guaranteed ordering in DuckDB, so
the same certificate set alternated between `AA+MQ` and `MQ+AA` between builds.
Moved on 144, 246 and 169 rows across the three competition files.

Introduced by me in the Round 4 P0-2 work. Cosmetic: `op_carriers` is an
auditability column and feeds no calculation. But it makes the artifact
unreproducible and buries real diffs in noise. Fixed with an explicit
`ORDER BY` in `models/competition.py` and `models/candidates.py`.

### (c) Remaining non-deterministic defect: Ottawa, in a third location

After the gate cleared `op_carriers`, `modeled_pax` still moved on exactly 2
rows, both YOW: **17,907.96 to 6,455.55**, a factor of 2.77.

This is the Ottawa CMA defect again. `backtest/run_backtest.py` ran its own
`dim_metro_ca m ON m.cma LIKE c.cma_name || '%'` and collapsed it with `dict()`,
so YOW took whichever of the three Ottawa-Gatineau records came last.

**The sweep should have caught this and did not.** I checked `hub_pop` for
duplicate keys against `dim_metro_us` when the query reads `dim_metro_ca`. I
tested the wrong table and reported the site clean.

A follow-up grep found the same `LIKE ... || '%'` prefix join in **four** places:
`models/demand.py`, `models/catchment.py`, `backtest/run_backtest.py`, and
`models/transfer.py` (already fixed). Only Ottawa is ambiguous today, so only
the backtest surfaced it, but any future interprovincial or renamed CMA would
hit the other three.

Fixed once at the warehouse layer rather than four times in the callers:
`warehouse/build_marts.py` now builds `map_ca_airport_metro`, excluding
provincial parts and **asserting the mapping is unique** so a future ambiguity
fails loudly. All four call sites read the resolved table. 18 airports resolve.

### (b) Artifact regeneration requirement: `demand_alaska_sea.parquet`

The corrected multi-city-market aggregation is the intended baseline, so all
downstream artifacts and reports were regenerated with `make all`.
`reports/`, `docs/LIMITATIONS.md`, `docs/validation.md` and the screen CSVs now
match the computed outputs, satisfying hard rule 6.

### (a) Expected deterministic correction

Five Alaska metros moved from modeled to observed demand, reported in
`A1_t100_full_history.md`. Correct under hard rule 4: demand is observed where
observation exists.

## 1. Metric impact

| metric | before | after |
|---|---|---|
| artifacts verified reproducible across rebuild | 0 | 24 |
| non-deterministic lookup sites known | 0 | 0 (5 found, 5 fixed) |
| tests | 32 | 36 |

## 2. Verdict changes

**The integrity fixes alone move zero verdicts in any screen.** The Ottawa fix
changes 2 backtest rows; the `op_carriers` fix changes nothing numeric.

Against the last commit the counts do differ, but that is the cumulative effect
of the Round 4 P0 fixes, which are also uncommitted:

| study | HEAD | now | driver |
|---|---|---|---|
| westjet_yyc | 0/0/76 | 0/0/76 | unchanged |
| alaska_sea | 0/1/48 (49 rows) | 0/0/45 (45 rows) | P0-3 removed 4 Horizon-served metros |
| porter_yyz | 5/3/71 | 1/1/77 | P0-1 directionality, P0-2 brand competition |

Fayetteville-Springdale-Rogers moved MONITOR to PASS. It is one of the 6
multi-city-market CBSAs, so its former MONITOR was resting on row order.

## 3. Regression risk

**Guarded by.** `make reproducibility` is the gate and fails on any artifact
drift. `test_no_ambiguous_lookup_keys_in_reference_mappings` and
`test_cbsa_to_city_market_is_many_to_one_and_aggregated` guard the pattern. The
uniqueness assertions in `build_marts` and `_cma_population` raise rather than
pick.

**Would still slip through.** The gate rebuilds marts from cached Parquet; it
does not re-download, so ingest-layer non-determinism is untested. It compares
one rebuild against one prior state, so a defect that alternates on a longer
cycle, or depends on machine or DuckDB version, needs more runs to surface.
Nothing yet asserts the mapping is *complete*, only that it is unique and
deterministic: a mapping that dropped an airport entirely would pass. The gate
is not wired into CI, which has no warehouse.

## 4. Statistical meaningfulness

Not applicable. These are exact correctness properties, verified by reproducing
the wrong value, applying the fix, and confirming the corrected value. One
rebuild proving equality is weaker evidence than N rebuilds; the honest claim is
"one rebuild reproduces exactly", not "the pipeline is proven deterministic".

## 5. Assumptions touched

None added or changed.

## Correction to the record

The Milestone A sweep was reported clean on `backtest hub_pop`. It was not. The
check queried `dim_metro_us` while the code queries `dim_metro_ca`, and the gate
caught what the sweep missed. Worth stating plainly: the automated gate found a
defect that a targeted manual audit had already declared absent.
