# Exact completed-column dominance — verified synthetic study

**Verified November 16–17, 2026.** [Independent GitHub Actions benchmark #43989372221](https://github.com/yumorepos/network-lab/actions/runs/43989372221) passed the paired research workflow and archived the entire 12-pair aggregate JSON. A separate [repository-wide test run #43989372182](https://github.com/yumorepos/network-lab/actions/runs/43989372182) and the preexisting [scalability workflow #43989372248](https://github.com/yumorepos/network-lab/actions/runs/43989372248) also passed for that same implementation commit. Later regression-only tests further exercise all 30 historical reference scenarios and a crafted cheaper-later-order counterexample; check the PR's final CI head for those additional gates.

This is a **finite, educational, synthetic aircraft-rotation MILP**, not airline disruption recovery software or an estimate of real monetary savings. The original Network Lab frozen route-ranking findings are unchanged.

## Mathematical method

The [predeclared protocol](COLUMN_DOMINANCE_PROTOCOL.md) contains the full condition and proof. In the current master problem, two *complete* rotations of the *same aircraft* that cover the *same set of flight IDs* have identical row coefficients, regardless of operating order, allowed delay choices or final airport. The master charges only additive delay penalties, and has **no final aircraft location or end-of-day obligation**. Thus only the cheapest complete rotation for each `(tail, flight-set)` is required. All raw feasible paths are still visited by the DFS.

This is **not partial-state pruning**. A future extension involving crew, onward rotations, aircraft end positioning or connections invalidates the simple terminal-column dominance condition unless the relevant state is added to the column identity.

## Paired study design and verification

Both versions were executed on the same 12 fixed-seed `recovery-scaling-v1` scenarios (`seed=20261111`): 5 flights (2 cases), 8 flights (4), 11 flights (4), and a 14-flight stress pair (2). All scenarios used two fictional tails, the original six discrete delay choices and the same artificial airports and passenger/cancellation penalties.

For each separate worker process:
- **15,000 retained columns per tail maximum**. The original method caps generated paths; the pruned method caps distinct retained flight-set columns.
- The pruned method additionally limits **raw DFS visits to 250,000 per tail**; a smaller MILP does not hide unbounded search.
- A **6-second hard parent-process wall deadline** (including spawn startup); any cap or timeout is censored rather than an objective.
- Independent feasibility and objective arithmetic verification on every certified solution.
- Objective equality required to `1e-6` whenever **both** methods certify. No assertion of empirical objective parity on a capped control.
- File/protocol source, seed, scenario SHA-256, all per-case statuses, phase times and RSS are recorded. Timing applies only to the Linux Python 3.11.18 GitHub Actions runner used, not generally to other machines.

## Summary results

| Metric | Original exact enumeration | Exactly dominated complete columns |
| --- | ---: | ---: |
| Paired scenarios attempted | 12 | 12 |
| Finite MILP optima certified | **11** | **12** |
| Per-tail path-cap stops | **1** | **0** |
| Paired certified objectives with equality | **11/11** | **11/11** |
| Median columns across 11 both-certified cases | 1,777 | 53 |
| Median total optimizer time across those 11 cases | 0.036805 s | 0.006904 s |
| Median OS process peak RSS across those 11 cases | 94.176 MiB | 91.164 MiB |

**Median reduction in retained MILP columns: 96.132%.** The observed paired median optimizer times are approximately **5.3× apart on this one CI host**. They exclude Python child-process startup and baseline calculation and are not a guarantee of future performance; the sample is small and repeated trials/host variance are not characterized.

The primary reduction is in stored completed rotations and the resulting sparse set-partitioning matrix. Every raw feasible path is still traversed: the faster solved instances do **not** prove a reduction in combinatorial enumeration complexity. The paired run recorded median construction times **0.008872 s original vs 0.000581 s pruned**, and median HiGHS times **0.024694 s original vs 0.004586 s pruned**, conditional on both methods certifying.

### Selected case evidence

| Flights | Network pattern / case | Original retained columns | Pruned retained columns | Objective parity |
| --- | --- | ---: | ---: | --- |
| 5 | Connected / 0 | 81 | 11 | 755.00 = 755.00 |
| 8 | Connected / 1 | 1,777 | 53 | 824.50 = 824.50 |
| 11 | Connected / 0 | 5,910 | 165 | 1,340.00 = 1,340.00 |
| 11 | Connected / 1 | 17,572 total (each tail below cap) | 239 | 955.00 = 955.00 |
| 11 | Distributed / 1 | 7,984 | 163 | 1,070.00 = 1,070.00 |
| 14 | Distributed / 0 | 12,986 | 240 | 1,478.00 = 1,478.00 |

All these values are **illustrative penalty units**, not dollars or actual flight disruption effects. Full 12-pair details and scenario hashes remain in the short-lived Actions artifact.

### The previously capped 14-flight connected case

| Measure | Original enumerator | Exact terminal-column pruning |
| --- | --- | --- |
| Outcome | **PATH_CAP** (15,001st path within one tail) | **OPTIMAL** with certified HiGHS status |
| Raw feasible paths visited | Censored at cap | **68,989** (58,518 tail A, 10,471 tail B) |
| Retained columns | Not a complete model | **792** (579 tail A, 213 tail B) |
| Certified MILP objective | **Unavailable** | **1,271.50** illustrative units |
| Full internal optimizer time | N/A | **0.224 s** |
| Process peak RSS | Partial process (not comparable) | **94.004 MiB** |

This is a **real improvement for the exact synthetic problem**: the treatment explores all complete paths under its raw-visit guard and then solves the dramatically smaller equivalent master. However, because the original **failed** to construct a complete MILP, there is **no directly observed original objective** to compare. The equivalence claim rests on the proof for identical terminal flight-set columns, the unchanged finite decision universe and the independently certified treatment result.

## Counterexamples, failure gates and limitations

- The original delayed-flight **overtaking oracle** continues to pass; no ordering assumption was added.
- A separate four-flight permutation oracle and a synthetic case in which DFS first finds a costly complete rotation and only later discovers a cheaper one confirm that the method keeps the **minimum-cost** representative, not simply the first path.
- Every original five-flight reference case is regression-compared against the pruned method; the original 30-case baseline still measures **413.62 vs 503.67** illustrative units (MILP versus cost-aware greedy).
- `PATH_CAP`, `RAW_VISIT_CAP`, timeout, `UNCERTIFIED` and unexpected `ERROR` remain distinct failure states. Censored results have no invented MILP objective.
- This is a tiny, highly structured fictional benchmark on one CI host. The apparent runtime or memory gains may change with network topology, delay menus, fleet size, or different HiGHS/Python versions. Enumeration remains exponential in the general case.
- No aircraft turnaround realism beyond the original toy rule, real crew feasibility, passenger connections, positioning, airport slots, maintenance or operational cost data are represented.

**Engineering decision:** In this existing restricted model, exact completed-column pruning is justified by its mathematical equivalence and observed material reduction in columns and matrix workload. It should remain an **opt-in research flag**, not an automatic default for unknown extensions. A future time-space or column-generation experiment needs a new defined research question, independent oracle, and approval, not an automatic rewrite.
