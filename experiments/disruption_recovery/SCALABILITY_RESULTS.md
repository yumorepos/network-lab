# Verified bounded recovery MILP scaling experiment — 2026-11-16

**Status:** Reproducible *synthetic* performance audit, **not** an airline-scale optimizer claim. Source and CI evidence: [GitHub Actions recovery scaling run #43988045914](https://github.com/yumorepos/network-lab/actions/runs/43988045914) (ten primary cases, two 14-flight stress cases, and six controlled aircraft/delay factor cases all passed their execution/validation gates). The benchmark keeps timeout and capped outcomes **visible rather than recoding them as solutions**. The repo-wide test workflow for the same research commit also passed. The final PR may include one additional test-only regression commit.

## Baseline preservation

The first five flights of each new benchmark scenario exactly reproduce the original fixed-seed `benchmark.py` generator. The existing 30-scenario reference remains **413.62 versus 503.67** illustrative units (exact finite MILP vs cost-aware chronological greedy), with **12 improved, 18 tied, none worse**, as independently reproduced before this change. This is a reference-invariance check, not evidence of external generality.

## Environment and measured resource limits

Primary benchmark: seed **20261111**, generator `recovery-scaling-v1`, original two fictional tails and six discrete delay options, 5/8/11 flights, connected or distributed 3-airport synthetic route motifs. The 5-flight case uses the unmodified base generator without duplicating topology cells. Two seeded cases per cell; **10 total**.

Experimental host from the CI artifact: **Ubuntu Linux x86_64, Python 3.11.18, SciPy 1.17.1, NumPy 2.4.6, four reported logical CPUs**. Runtime and RSS results are specific to this CI host/software environment; they are not hardware-independent benchmarks.

- Hard process wall limit: **6 s per case**, including process startup; shared cooperative budget within the worker and HiGHS.
- Path cap: **15,000 generated paths per tail**, *not* a cap of 15,000 summed over all tails.
- Memory: **OS high-water RSS for the process**, including Python interpreter and native numerical libraries; not a pure MILP allocation measurement.
- Phase time: inside the worker, from `optimize()` entry to validated result, **excluding** child process startup and separately measured cost-aware greedy construction.
- Exact status `OPTIMAL` requires certified HiGHS result, schedule feasibility and independent recalculation of objective. `PATH_CAP`, `UNCERTIFIED`, `COOPERATIVE_TIMEOUT` and `HARD_TIMEOUT` never imply an optimum.

## Primary 10-case results

| Synthetic flights | Attempted | Certified optimal | Other statuses | Median enumerated paths, solved only | Median full optimizer time, solved only | Median process peak RSS, solved only |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| 5 | 2 | 2 | None | **131.5** | **0.0057 s** | **91.0 MiB** |
| 8 | 4 | 4 | None | **768** | **0.0169 s** | **92.3 MiB** |
| 11 | 4 | 4 | None | **6,947** | **0.1300 s** | **104.8 MiB** |

**Important:** only 2 or 4 samples per size are available. These are descriptive benchmark medians, not estimates of a growth rate, confidence intervals, or typical performance at arbitrary scale.

### Topology-specific evidence

| Flights | Pattern | Case | Enumerated paths, all tails | Exact objective | Cost-aware greedy objective | Interpretation |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 8 | Connected | 0 | 356 | 1,040.00 | 1,235.00 | MILP lower |
| 8 | Connected | 1 | 1,777 | 824.50 | 824.50 | Tie |
| 8 | Distributed | 0 | 586 | 805.00 | 1,155.00 | MILP lower |
| 8 | Distributed | 1 | 950 | 310.00 | 835.00 | MILP lower |
| 11 | Connected | 0 | 5,910 | 1,340.00 | 1,965.00 | MILP lower |
| 11 | Connected | 1 | **17,572** | 955.00 | 1,155.00 | MILP lower |
| 11 | Distributed | 0 | 2,637 | 1,063.00 | 1,093.00 | MILP lower |
| 11 | Distributed | 1 | 7,984 | 1,070.00 | 1,930.00 | MILP lower |

All objectives are **arbitrary fictional penalty units**, not dollars, real passenger impacts, or operational savings. The complete report retains the SHA-256 of every generated case and the exact time splits by stage.

## Additional 14-flight stress exercise

A second bounded run used **one** fixed-seed scenario in each topology, otherwise retaining the same resource caps:

| Synthetic scenario | Outcome | Paths / evidence | Interpretation |
| --- | --- | --- | --- |
| 14 flights, connected motif | **PATH_CAP** | 15,001st path generated for a single tail | Exact enumeration **aborted intentionally**; no certified optimization objective or solver comparison |
| 14 flights, distributed motif | **OPTIMAL** | 12,986 paths across tails; ~0.239 s inside optimizer | Feasible certified finite-model optimum, with cost-aware greedy 1,634.50 vs MILP 1,478.00 illustrative units |

This is a *constructive failure-mode result*. Different graph connectivity, timing, and delay choices produce different feasible path growth. **It is not a universal 14-flight threshold**, and the ceiling of 14 flights is still an explicit model input bound.

## Controlled aircraft-count and delay-menu factor audit (8 flights)

The benchmark also exercises the originally approved sensitivity axes instead of merely making them configurable. These are **six additional** fixed-seed `case_index=0` runs plus the two matching primary-grid baselines. Both artificial connectivity patterns use **exactly the same eight generated flights, departures and penalties** within each topology; only the number of available aircraft or the discrete delay-choice menu changes.

| Network pattern | Two tails, six delays (primary baseline) | Three tails, six delays | Two tails, three delays | Three tails, three delays |
| --- | ---: | ---: | ---: | ---: |
| Connected routes | 356 paths | 686 paths | 66 paths | 114 paths |
| Distributed routes | 586 paths | 1,088 paths | 96 paths | 155 paths |

All eight factor scenarios (including the two already in the primary grid) returned **certified finite optima**. On these fixed inputs, adding an aircraft increased the number of feasible tail paths while reducing the delay menu from six to three reduced that path count substantially. This is a controlled diagnostic of **search-space sensitivity**, not a general scaling law.

The new three-tail scenarios may have very different cancellation and objective values because an additional aircraft changes feasibility. The three-delay scenarios use a **different finite decision menu**. Therefore costs across factor cells are **not a measure of algorithmic speedup, monetary savings, or an operational intervention**. Each cell's MILP and cost-aware greedy are compared only *within* that cell, under identical assumptions.

## What the timings do and do not establish

The path count rises sharply within this particular case family. However, **path enumeration is not yet demonstrated to be the dominant *time* bottleneck on solved cases**. For example, in the 11-flight connected case with 17,572 paths, GitHub Actions measured approximately:

- Enumeration: **0.028 s**
- Sparse model construction: **0.106 s**
- HiGHS solution: **0.201 s**
- Full instrumented optimization: **0.342 s**

Thus solver time was largest in that measured instance, construction was material, and enumeration produced the combinatorial work that feeds both. In a 14-flight connected case the path cap prevented construction/solving entirely. Both observations matter.

The 6-second worker deadline prevents unbounded benchmark hangs and explicitly handles censored results. It does **not** turn a solver with a 14-flight input ceiling and enumerated discrete paths into production airline recovery software.

## Validity and next decision

Validated against [the preregistered protocol](SCALABILITY_PROTOCOL.md), [the instrumented optimizer](recovery.py), [the independent benchmark and scenario hashes](scalability.py), and [regression tests](../../tests/test_recovery_scalability.py). The benchmark result ZIP is short-lived (7-day retention) by design; the summary and verification links remain permanently versioned here.

**Next engineering research question:** Would dominance pruning or a time-space formulation reduce model construction and the path-cap failure on exactly these synthetic, version-pinned cases, *without* changing finite-universe objectives or losing the overtaking counterexample? Any such technique must be tested against unchanged benchmark scenarios and independent feasibility/objective validation. No broad rewrite has been approved or performed.
