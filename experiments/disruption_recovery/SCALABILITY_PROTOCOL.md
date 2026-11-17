# Disruption recovery — scalability and reliability protocol v1

**Purpose:** Measure whether the existing finite path-enumeration MILP remains computationally practical as synthetic flight counts increase. This is a new, separately evaluated experiment in the existing `experiments/disruption_recovery` package; it does **not** modify the frozen Network Lab route-ranking model or claim usable airline-scale recovery.

## Question and engineering value

Where does exact per-tail rotation enumeration become the dominant bottleneck? Can we quantify total wall time, enumeration time, model construction time, solver time, path count and process memory while preserving the original finite-universe optimality and independent solution validation?

A negative scalability result is valid. **Do not** change the MILP formulation until measurements identify a material bottleneck.

## Frozen baseline and experimental design

- Preserve the original `benchmark.py` scenario generator and its 30 five-flight / two-tail reference cases, seed **20261111**. The previously published means are **413.62** arbitrary units for the exact MILP and **503.67** for cost-aware chronological greedy, with **12 better, 18 tied, 0 worse**.
- New generator `recovery-scaling-v1`: start with the *same five flights*, then deterministically add flights up to 14 total. Two explicit fictional three-airport connectivity patterns: `connected` (repeating AAA↔BBB) and `distributed` (cyclic routes among AAA/BBB/CCC). Aircraft start positions and original five flights remain fixed in the default two-tail case.
- Primary diagnostic grid: **5, 8, 11 flights**, two seeded instances per connectivity pattern (five-flight reference is not duplicated across patterns). **10 distinct bounded cases**. Keep the original six delays and two aircraft in this initial test.
- Optional follow-up factors, **not part of the primary grid**: 3 aircraft versus 2, three delay options versus six, and 14 flights only if the primary grid is safely bounded.
- Identical synthetic assumptions and objective for the exact solver and **cost-aware greedy**. The older `savings_vs_greedy` field in `recovery.optimize()` refers to the *fly-first* comparator, **not** the cost-aware comparator; the scaling report separately names the cost-aware difference.

## Execution limits, failure states and acceptance

- Per-tail path cap **15,000**. If enumeration hits the cap, emit `PATH_CAP` and **never** present a partial enumeration as an optimum.
- **6-second hard wall deadline per case**, enforced by a separate worker process; termination returns `HARD_TIMEOUT` without any certified objective. The optimizer also receives a cooperative remaining-time budget, checked during enumeration, matrix building and after the solver.
- Successful solved cases are recorded as `OPTIMAL` **only** after HiGHS certifies the finite model and the selected schedule is independently revalidated and repriced. Uncertified solver status is `UNCERTIFIED`, cooperative total-budget exhaustion `COOPERATIVE_TIMEOUT`, and unexpected defects `ERROR`.
- Each row records SHA-256 of its canonical synthetic scenario, exact objective and cost-aware-greedy objective **only when certified**, timing by phase, path counts, cancellations, observed parent wall time and OS process peak RSS.
- Peak process RSS includes the Python interpreter and native numerical libraries. It is **not solver-only allocation**, and times and memory are host/hardware-dependent. Do **not** compare absolute times from local laptops and GitHub Actions as if they ran on the same hardware.
- Summaries **exclude censored cases** from medians and report every status and sample count. Do not infer a scaling law or extrapolate to real airlines from ten scenarios.

## Run locally

From repository root with the existing Python dependencies:

```bash
python -m pytest -q tests/test_disruption_recovery_experiment.py tests/test_recovery_scalability.py
python -m experiments.disruption_recovery.scalability \
  --cases 2 --sizes 5 8 11 --path-cap 15000 --wall-seconds 6 \
  --output /tmp/recovery_scalability_v1.json
```

Output files use exclusive creation (no overwrite) and contain only source-free synthetic hashes and aggregate results. The one-time PR workflow runs on `ubuntu-latest`, includes focused tests and archives the JSON for **7 days**. There is no schedule, deployment, or external data acquisition.

## Evaluation and next decision

1. Verify all existing optimizer tests and the fixed-reference 30-scenario result still agree.
2. Confirm independent feasibility/cost validation on every reported optimal schedule.
3. Record distributions **by topology and size**, including censored outcomes and the difference between solver-time and full-pipeline time.
4. If capped or time-limited cases appear, consider a targeted engineering experiment with dominance pruning, time-space networks or column generation **against this unchanged benchmark**.
5. Do not generalize to realistic crew, aircraft maintenance, passenger connections, curfews, positioning or airline savings.

**Release gate:** Source and experiment tests pass, benchmark provenance is inspectable, and any failed/censored cases remain visible rather than being omitted.
