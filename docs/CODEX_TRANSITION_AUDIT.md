# Codex transition audit

**Date.** 2026-08-14
**Purpose.** Preserve, accurately and without upgrade, what happened during the
attempted transition of Network Lab to a second agent environment, and record
which of those findings this local session could and could not verify.

**Provenance rule applied throughout.** This document distinguishes three
classes of claim, and every row says which it is:

| class | meaning |
|---|---|
| **verified here** | reproduced in this local repository during this session |
| **reported** | supplied by the operator in the finalization controller; no artifact in this repository corroborates it |
| **inferred** | follows from something verified, and the inference is stated |

A reported item is not promoted to verified because it is plausible. A failed
gate is not recorded as a passed gate.

---

## A. What the transition was

Commit `e5f0e55` ("Transition: Codex handoff, AGENTS.md, two current-state
corrections") added `AGENTS.md` and `docs/CODEX_HANDOFF.md` and corrected two
current-state claims. It changed no model, config, artifact or default. That
much is **verified here**: `git show --stat e5f0e55` touches only documentation,
and the working tree at that commit is clean.

Work then moved to a second environment. It did not complete.

## B. Findings carried forward

### B1. The cloud Stage 1 execution failed

**Reported.** Stage 1 was attempted in a cloud environment and did not
complete.

**Reported.** The test suite there reported **33 passed and 12 skipped**, not
the 45 passed this repository produces.

**Verified here.** This local repository runs **45 passed, 0 skipped**
(`make test`, 2026-08-14, log retained). The 12-test gap is consistent with the
absence of a warehouse: the tests that require `data/warehouse.duckdb` skip when
it is missing, and the remainder are the pure-Python and document-consistency
tests that need only committed artifacts.

**Inferred.** A 33/12 result is therefore not a contradictory test outcome. It
is the same suite running with its data-dependent third disabled. It certifies
nothing about the model, and it must not be cited as a green gate.

### B2. The warehouse was absent in that environment

**Verified here (by construction).** `data/warehouse.duckdb` is 4.8 GB and is
gitignored. `.gitignore` excludes everything under `data/` except
`data/reference/`. No clone of this repository can contain the warehouse.

**Inferred.** Any environment reaching the repository through `git` alone starts
without a warehouse and must run `make data` to obtain one. That is the cold
path, and it is the path that failed.

### B3. Disk exhaustion during the cold build

**Reported.** The cold `make data` build exhausted disk in the cloud
environment.

**Verified here.** The local footprint that a cold build must materialize is
**8.7 GB** before the warehouse is finished, and **13.5 GB** with it:

| component | size |
|---|---|
| `data/raw` | 2.8 GB |
| `data/parquet` | 1.1 GB |
| `data/warehouse.duckdb` | 4.8 GB |
| DB1B raw zips alone | 2.3 GB |
| DB1B parquet alone | 950 MB |

**Inferred.** DuckDB additionally needs working space during the
173.7 M row `fact_od_market` load, so peak requirement exceeds the resting
13.5 GB. A cold build is not a small job and should not be scheduled into an
environment without a verified double-digit GB budget.

### B4. That environment could not independently certify the local gates

**Inferred from B1 to B3, and this is the operative conclusion.** With no
warehouse, 12 of 45 tests skipped, and the cold rebuild failing on disk, the
second environment had no path to reproducing `make reproducibility` at all.
`make reproducibility` rebuilds the marts from cached Parquet and compares 27
artifacts; without the cache and without disk it cannot start.

The transition therefore produced **no independent certification** of the local
result. It is not evidence against the local result either. It is an absence of
evidence, and it is recorded as such.

### B5. EIA live-vintage drift

**Reported.** An EIA fetch in that environment returned different values from
the cached copy.

**Verified here.** The cached EIA series is
`data/raw/eia/jet_gulf_weekly.xls`, sha256 prefix `d83248c77eee4389`, yielding
1,893 weekly observations ending 2026-07-10. `ingest/common.download_file`
skips the network entirely when the destination file exists, so this local
session never contacted EIA.

**This is the important classification, and it is a conclusion, not a report.**
A live source returning revised values is a **source-vintage change**. It is
not a computational reproducibility failure. `make reproducibility` deliberately
rebuilds from cached Parquet precisely so that the two are not conflated: it
proves the warehouse-to-model boundary is deterministic, and it makes no claim
about the ingest layer. `docs/W1.4_baseline_freeze.md` already states this
caveat, and it is correct.

The operational consequence is the standing rule now in force: **do not run
`make data`, and do not refresh any government source, during baseline and
calibration work.**

### B6. The cloud Stage 1.5 checkout was at the wrong commit

**Reported.** A cloud Stage 1.5 run checked out `79cbaa2`.

**Verified here.** `79cbaa2` is real, and it is `origin/main`. It is titled
"CI: bump checkout@v5 and setup-python@v6 (drop Node 20 deprecation)".

**Verified here, and this is why it matters.** `79cbaa2` is a direct ancestor of
the transition commit and **predates the whole of Phase 5 Milestone A and Phase
6A**. `git log --oneline origin/main..e5f0e55` is five commits: the Milestone A
integrity work, the A5 Canadian demand diagnostic, the Milestone A audit and
baseline freeze, Phase 6A Poisson, and the transition commit itself.

**Inferred.** Anything measured at `79cbaa2` was measured against a model
without the round-4 P0 fixes in their Milestone A form, without the route-spell
register, without the baseline freeze and without the Poisson estimator. Results
from that checkout describe a different codebase and are not comparable to
anything in this document or in the baseline freeze.

### B7. Phase 6A structural findings stand

**Verified here** by reading the artifacts and the committed reports; the
counterfactual itself was reproduced during the previous handoff and is not
re-run here.

The findings preserved, unchanged:

1. Poisson QMLE fixes a real level defect: aggregate predicted over observed
   moves from 0.44 to 0.95 on the `current` holdout, RMSE falls 28%.
2. It worsens relative-error metrics: median APE 0.615 to 0.740.
3. It did **not** meet all its own pre-declared success criteria, and the
   handoff records exactly which ones failed.
4. **Zero of 200 verdicts changed.** The spec predicted the opposite.
5. The mechanism has two parts. The transfer factor is estimated as
   `observed / gravity_pred`, so a *uniform* rescaling of gravity cancels
   exactly. Poisson is not uniform, so cancellation is only partial. What
   actually pins the verdicts is that the anchor rule and the survey cap discard
   the gravity product for all 155 transborder candidates before it reaches the
   screen.
6. `log_ols` remains the default and `tests/test_phase6a_poisson.py` asserts it.

Take the precise statement, not the slogan. "Transborder demand is structurally
invariant to any uniform rescaling of gravity" is true. "Nothing moves because
the transfer factor cancels it" is too strong.

## C. What this session verified independently

Run on 2026-08-14 in this repository, at `e5f0e55`, working tree clean, no
network, no `make data`.

| gate | command | result | expected |
|---|---|---|---|
| tests | `make test` | **45 passed** | 45 |
| reproducibility | `make reproducibility` | **27 artifacts identical** | 27 |

`make reproducibility` rebuilt the marts from cached Parquet
(`fact_segment` 13,630,379; `fact_od_market` 173,741,663; `fact_costs` 15,618;
`fact_fuel` 1,893), re-ran the models and the backtest, and compared every
artifact on content with a 1e-6 tolerance. Candidate counts reproduced exactly
at 76 WestJet, 45 Alaska, 79 Porter.

The run left the documented 14 float-churn files dirty. Their content was
verified unchanged by the gate that had just run, and they were restored with
`git checkout -- data/parquet/outputs/` rather than committed. The tree is
clean.

**The local gates are green and were green before any Stage 0 work began**, so
any later failure is attributable.

## D. What was not converted

Stated explicitly, because the failure mode this document exists to prevent is
quiet upgrade of a failed gate.

- The cloud Stage 1 run is recorded as **failed**. It is not recorded as
  "partially successful" or as "33 passing tests".
- The 12 skipped tests are recorded as **skipped**, not as passed.
- The cold build is recorded as **disk-exhausted**, not as "slow".
- The EIA difference is recorded as a **source-vintage change**, which is a
  reclassification with a stated reason, not a dismissal. The observation itself
  is preserved.
- The `79cbaa2` checkout is recorded as **wrong for the purpose**, and the
  reason is given in commits rather than in adjectives.
- Phase 6A remains **implemented, measured and not adopted**. Nothing here moves
  it toward adoption.
