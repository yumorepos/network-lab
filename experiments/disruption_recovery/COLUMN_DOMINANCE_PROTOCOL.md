# Exact completed-column dominance — research protocol

**Status:** Experimental optimization-engineering extension. Only the synthetic recovery MILP inside `experiments/disruption_recovery` changes. The main airline network-ranking study, its negative result, and the existing unpruned optimizer's defaults are untouched.

## Research question

Can **safe terminal column dominance** reduce the number of binary MILP variables and associated construction/solver effort without changing the exact finite-universe objective? Does it resolve the existing 14-flight connected `PATH_CAP` case, and if so what raw enumeration work remains?

**Expected value:** a small, independently verifiable algorithmic reduction instead of a speculative rewrite to time-space networks or column generation. Negative performance results are valuable and must be retained.

## Exactness argument and limits

The current master set-partitioning model selects exactly one feasible complete path per aircraft and exactly one service-or-cancellation outcome per flight. A path column has a coefficient of 1 in the row for its specific aircraft and in each row for the flights it covers, 0 elsewhere. Its objective contribution is the sum of passenger-delay penalties for those flights.

Two **complete**, independently feasible aircraft paths for the **same tail** covering the **same set of flight IDs** therefore have **identical constraint coefficients**. The higher-cost path is weakly dominated. Replacing it with the lower-cost path changes neither other aircraft assignments nor the coverage constraints and never increases the objective. Retain the first encountered path on ties for deterministic behavior.

This proof depends on the **current model having no terminal-position, end-time, crew-connection or following-day constraints**. It is **not** a valid rule for generic airline rotations or extensions with terminal-state decisions. Do not use it to prune partial paths based on the same visited flights alone: time, location and available future continuations differ.

## Methods

- **Control:** `optimize(..., prune_dominated_columns=False)`, the original full DFS and full column set with the existing 15,000-path **per-tail** cap.
- **Treatment:** `optimize(..., prune_dominated_columns=True)`; enumerate the same feasible complete rotations, but retain only the minimum-cost complete path for each `(tail, covered flight set)`. Pruned result is exact only if enumeration completes and HiGHS certifies optimality.
- A **separate 250,000 raw DFS-visit cap per tail** guards against interpreting a small retained model as a small search. `RAW_VISIT_CAP` and `PATH_CAP` are different censored states; neither is an optimum. The treatment's retained-column cap is 15,000 per tail; the raw visit cap is independently enforced.
- The existing isolated worker enforces **6 seconds wall time per case**, including spawn startup, separately for each method. OS process peak memory and optimizer-internal phase times are recorded.
- Each certified result is independently checked for flight/aircraft feasibility, cancellation coverage and exact objective arithmetic. Original and treatment are compared on the **same SHA-256 versioned synthetic scenario**. If both certify, their full-precision objectives must agree to `1e-6`, and treatment must retain no more columns than control.
- If the control caps and the treatment certifies, report it as a **one-sided improvement in this bounded test**. There is no empirical objective parity with the censored control; the analytical dominance proof and the treatment's independent feasibility checks are the basis for interpreting its certified result.
- Unadjusted wall timings are noisy because each method runs in a new Python process. Record raw counts, model construction and solver time; only make cautious machine-specific performance observations.

### Fixed study grid

Re-run the **unchanged** `recovery-scaling-v1` generator at seed `20261111` and:
- 5 flights: `connected`, case indices 0 and 1.
- 8 flights: `connected` and `distributed`, indices 0 and 1.
- 11 flights: `connected` and `distributed`, indices 0 and 1.
- 14 flights: `connected` and `distributed`, index 0 only.

Exactly **12 paired cases / 24 isolated method runs**, plus original 3-flight overtaking correctness and a separate independent 4-flight permutation oracle. The original 30-scenario baseline (MILP 413.62 vs cost-aware greedy 503.67 illustrative units, 12 wins / 18 ties / 0 worse) remains an invariant; code does not alter that generator.

## Acceptance / stop gates

1. All original optimizer and repository tests remain passing, including the overtaking regression.
2. Independently enumerated tiny examples agree with both optimizer variants and the recorded cheapest path per covered flight set.
3. No paired certified instance has a differing objective. **Any mismatch is a release blocker.**
4. Report all per-case `OPTIMAL`, `PATH_CAP`, `RAW_VISIT_CAP`, `COOPERATIVE_TIMEOUT`, `HARD_TIMEOUT`, and `UNCERTIFIED` statuses; do not omit censored results.
5. Report raw paths explored, retained columns, discarded paths, model time, solver time and peak memory; avoid claims of production performance or real financial savings.
6. Independently run the fixed study on GitHub Actions, retain only aggregate synthetic results for seven days, and document any negative result before contemplating another algorithm.

## Execution

```bash
python -m pytest -q tests/test_disruption_recovery_experiment.py \
  tests/test_recovery_scalability.py tests/test_recovery_column_dominance.py

python -m experiments.disruption_recovery.column_dominance \
  --path-cap 15000 --raw-visit-cap 250000 --wall-seconds 6 \
  --output /tmp/recovery_column_dominance.json
```

This is an educational, fictional finite MILP: no observed airline disruption, real fleet resources, crew legality, passenger connections, curfews or real costs. No dashboard or deployment is needed for this research question.
