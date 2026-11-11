# Verified synthetic recovery optimization baseline audit — 2026-11-11

**Experiment:** 30 fictional five-flight, two-tail scheduling instances, seed 20261111, generator \`bounded-recovery-scenarios-v1\`. No airline data, real passengers, real fleet coverage, maintenance events, crew legality or currency-denominated savings.

Source: [one-time benchmark GitHub Actions run #43093837181](https://github.com/yumorepos/network-lab/actions/runs/43093837181); source code: \`experiments/disruption_recovery/benchmark.py\`. The workflow's six new offline baseline tests and five existing optimizer-oracle tests passed (11 focused passes), and the full Network Lab CI also passed.

## Measured mean objectives (lower is better)

| Method | Mean objective in arbitrary illustrative cost units |
|---|---:|
| Existing exact MILP (finite enumerated paths) | **413.62** |
| Cost-aware chronological greedy (locally cancels when cheaper) | 503.67 |
| All flights cancelled | 1,269.00 |
| Original fly-first chronological greedy | 2,109.03 |

| Comparison to MILP | MILP better | Tied | MILP worse | Mean illustrative-unit gap |
|---|---:|---:|---:|---:|
| Cost-aware greedy | 12 | 18 | 0 | **90.05** |
| All-cancel baseline | 30 | 0 | 0 | 855.38 |
| Fly-first greedy | 29 | 1 | 0 | 1,695.42 |

The naive fly-first greedy policy has weak economics (never considers cancelling a feasible but costly-to-delay flight), so the more credible comparator is the cost-aware greedy. That comparator is still intentionally myopic: it ignores how cancelling or operating an early flight changes downstream aircraft position and future feasibility. The all-cancel baseline confirms feasibility but is not an operationally credible dispatch policy.

## What was actually verified

- All 30 scenarios are regenerated from seed 20261111 and stable generator code; each carries an individual canonical SHA-256.
- Every baseline constructs a complete feasible assignment plus cancellations; full objective uses the same cancellation and passenger-delay penalty definitions.
- The existing SciPy HiGHS MILP certifies each solution optimal **within the finite delay choices and enumerated paths**.
- Code rejects scenarios too large for exact path enumeration rather than silently clipping them.
- No original Network Lab route-screening model, frozen demand-only baseline, 200-market screens, 463 historical replay choices or dashboard results changed.

**Reproducibility check:** The branch-only workflow also reruns the complete 30-scenario benchmark and checks byte-for-byte identical JSON output. The full rerun's pass/fail status must be checked before merging/publishing these benchmark results.

## Non-claims and weaknesses

The result is not an estimate of **real airline savings**, aircraft/crew productivity, operational recoverability or certified globally optimal airline dispatch. Only 30 small, highly structured fictional scenarios and three airport placeholders are represented. No real-world costs, time-zone effects, flight positioning, network passenger connections, maintenance, crew regulations, curfews, weather or day-long recovery are modeled. The outcome depends on synthetic penalty choices and allowed discrete delays. Replaying the same generator twice checks reproducibility, **not external validity**.

The previous README refers to a different historical local 30-case benchmark (greedy 7,276.77 vs MILP 6,335.10). It is not a reproduction of this new generator and must **not be compared, blended or substituted** for the results above.

## Recommendation

This supports a recruiter-facing *methodology and bounded decision tradeoff* demonstration: constraints, transparent baseline choice, exact finite optimization, reproducibility and principled limitations. It does **not** warrant new heuristics, a large app, or financial-impact claims. Keep the optimization case study concise and prioritize continued job applications alongside the portfolio.
