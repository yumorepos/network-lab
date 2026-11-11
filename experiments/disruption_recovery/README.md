# Separate research experiment: airline disruption recovery MILP

This is an **educational, synthetic scheduling experiment**, separate from the
frozen route-screening model, its three published studies, historical replay,
and production data. No production result imports this package.

## What it solves

For a small set of synthetic flights and aircraft tail positions, choose which
flights operate and which cancel, allowing only specified delay options. The
objective is cancellation penalties plus passenger-delay penalties, in
**illustrative arbitrary cost units**. Aircraft paths enforce start location,
airport continuity, positive flight durations, turnaround time and no reuse of
the same flight. Every flight is flown exactly once or cancelled. The master
problem is a binary mixed-integer set-partitioning model using SciPy HiGHS.

**Critical correctness rule:** after disruption, actual departure order can
differ from original schedule order. The aircraft-path enumerator permits an
earlier-scheduled flight to operate after a later-scheduled one. A previous
prototype omitted those paths and falsely called a suboptimal solution
'optimal'. An independent permutation oracle in the tests detects that
counterexample.

## Use

Install the repository requirements (SciPy, NumPy, pytest) and run:

```bash
python -m pytest -q tests/test_disruption_recovery_experiment.py
```

From the project root, import:

```python
from experiments.disruption_recovery.recovery import optimize
result = optimize(synthetic_scenario_dict)
```

The example regression operates three flights:
- `F2` AAA -> CCC, scheduled at minute 20
- `F3` CCC -> AAA, scheduled at minute 60
- `F1` AAA -> BBB, originally scheduled at minute 0 but delayed 120 minutes

The corrected solution operates all flights for **12 illustrative units**.
The old sorted-schedule enumerator canceled `F1` for a cost of 1,000 units.
This is an **algorithm correctness** result, **not real airline savings**.

A **reproducible 30-scenario fixed-seed synthetic baseline study** is documented
in [BASELINE_AUDIT_RESULTS.md](BASELINE_AUDIT_RESULTS.md). It compares the exact
finite MILP against the original fly-first greedy, a more defensible **cost-aware
greedy**, and all-cancel. On these particular fictional instances, the MILP
averaged **413.62 illustrative units** against **503.67 for cost-aware greedy**,
improving in 12 scenarios and tying in 18. Two identical full generated reports
were independently rerun byte-for-byte. These are **not real airline savings**.
The prior ad-hoc benchmark's 30-instance numbers were not independently
reproduced on this generator and should not be mixed with the current results.

A separate [fixed-seed parameter sensitivity study](SENSITIVITY_RESULTS.md)
examines the same synthetic cases under alternative delay penalties,
cancellation penalties and turnaround screening assumptions. The MILP
outperformed cost-aware greedy in 11–13 of 30 cases per configuration,
but tied in the rest. These are illustrative costs, not airline savings.

## Stop / validity limits

- Exact only for the finite flight/tail/delay set and within enumerated path cap.
- The solver **fails loudly** if enumeration is too large or optimality is not
  certified; no silently truncated path set.
- Not airline dispatch software: no crew legality, passenger connections,
  airport slots, security, maintenance, rotations across days, recovery
  positioning, curfew, weather, or aircraft type compatibility.
- The **original fly-first greedy** always operates a feasible flight even when
  cancellation is cheaper; it is intentionally weak. The **new cost-aware
  greedy** uses an immediate cost check but cannot anticipate future aircraft
  positioning, so it is not an operationally complete dispatch policy.
- Synthetic improvements cannot be represented as practical operational savings.
- Before operational scale, use an expanded time-space network or column
  generation, scenario-specific constraint checks, and independent evaluation.

This experiment is a separate, explicitly labeled career portfolio exercise,
not an expanded claim of schedule optimization by Network Lab screening.
