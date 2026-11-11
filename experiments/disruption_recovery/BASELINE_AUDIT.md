# Synthetic recovery optimization — reproducible baseline audit

**Scope:** Educational five-flight, two-tail instances generated from fictional AAA/BBB/CCC airports and arbitrary unit penalties. No airline's schedules, passengers, crew, aircraft fleet or monetary savings are represented.

Run from the Network Lab repository root after installing SciPy, NumPy and pytest:

    python -m pytest -q tests/test_disruption_recovery_experiment.py tests/test_disruption_recovery_benchmark.py
    python -m experiments.disruption_recovery.benchmark --count 30 --seed 20261111 --output /tmp/recovery_baseline_30_synthetic.json

This implementation adds **no** changes to the frozen route-screening research or its original synthetic MILP optimizer. The benchmark records:
- The existing **chronological fly-first greedy** which operates whenever feasible; explicitly weak.
- A **cost-aware chronological greedy** which instead cancels if the immediate flight-delay cost meets/exceeds the cancellation penalty. It is only locally cost-aware, **not guaranteed globally better** than the fly-first baseline.
- A fully feasible **all-cancel** baseline, a trivial objective upper bound.
- The existing exact MILP on the same finite set of delays and enumerated tail paths.

All 30 input scenarios are deterministically regenerated from a fixed seed, generator version and scenario index. Individual SHA-256 hashes are stored in the result JSON with per-case objective and selected cancellation counts. The script fails if any resulting MILP objective exceeds a feasible comparator or the solver cannot certify optimality.

**Decision rule:** show exact per-baseline wins/ties, means and reproducible inputs; do not interpret the difference as operational cost reduction, predictive accuracy or real airline savings. The sample is intentionally small and educational. Crew assignments, legality, positioning, actual slots, maintenance, passenger misconnections, curfew and network recovery across days are omitted. A published portfolio claim requires an independently run benchmark and preserved results.

The previous README's 30-scenario numbers concern a different older local benchmark and are NOT verified as this version's output. Do not silently copy them into the new report.
