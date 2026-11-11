# Verified synthetic recovery sensitivity — November 11, 2026

Study: the **unchanged** SciPy/HiGHS finite path MILP and cost-aware greedy,
on the same 30 fictional five-flight/two-tail generated scenarios
(seed **20261111**, generator \`bounded-recovery-scenarios-v1\`).
No airline source operations or actual financial figures.

**Verification:** [GitHub Actions run #43104762481](https://github.com/yumorepos/network-lab/actions/runs/43104762481) passed 15 focused tests and the full benchmark was re-run **byte-for-byte identically**. The reference variant exactly preserves the original scenario SHA-256 checksums and 413.62 vs 503.67 baseline means. An earlier code defect changed integer penalty values to floating-point representation under the no-op reference multiplier, breaking checksum identity; it was fixed before these results were accepted.

## Paired scenarios by hypothetical assumption

| Changed input | MILP better / tied / worse vs cost-aware greedy | Mean MILP objective | Mean greedy objective | Mean gap | Mean MILP cancellations |
|---|---|---:|---:|---:|---:|
| Reference | **12 / 18 / 0** | 413.62 | 503.67 | 90.05 | 1.97 |
| Passenger-delay unit penalty ×0.5 | **13 / 17 / 0** | 317.03 | 440.66 | 123.63 | 1.30 |
| Passenger-delay unit penalty ×2 | **13 / 17 / 0** | 454.17 | 563.35 | 109.18 | 2.30 |
| Ground-turn screen +20 minutes | **11 / 19 / 0** | 456.98 | 555.44 | 98.46 | 2.23 |
| Cancellation penalty ×2 | **13 / 17 / 0** | 634.06 | 881.32 | 247.26 | 1.30 |

**All objectives and gaps are arbitrary illustrative penalty units, NOT
currency or real airline savings.** Each row is a different model parameter
setting. Do not directly interpret cross-row cost differences as business
savings when the objective function itself has changed.

The exact finite MILP cannot cost more than a feasible greedy schedule in
its own enumerated decision universe; zero losses are thus an expected
internal optimizer property, not external validation. Most cases (17–19 of
30) **tie** cost-aware greedy despite the additional MILP complexity.
Changing fictitious penalties changes cancellation choices and the
numerical objective gap. The scenarios are too small and stylized to
establish scaling, statistical generality or airline operational usefulness.

## Reproducibility and unresolved realism

- Code: \`experiments/disruption_recovery/sensitivity.py\`
- Scenario hashes per case/variant and two identical complete JSON runs
- Existing exact optimizer and separate 3-flight overtaking correctness
  oracle unchanged
- Finite delay options and path enumeration; abort if infeasible to prove
  solver status rather than implying global network optimality
- No realistic crew schedules, aircraft types, recovery positioning,
  aircraft maintenance, passenger connections, airport slots, real curfews,
  real disruption costs, real passenger numbers or weather controls

**Decision:** sufficient for a compact synthetic model-sensitivity exhibit
in the existing optimization case study; insufficient for real savings,
operational dispatch or industry-wide robustness claims. Do not build a
new optimizer or dashboard for this narrow experiment.
