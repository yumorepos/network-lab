# Bounded sensitivity test — synthetic recovery MILP

**Purpose:** Test whether the existing small-scenario MILP's advantage over
the **cost-aware greedy**, not the weak fly-first policy, changes under
alternative *assumed* penalty and turnaround settings.

Same 30 seeded fictional five-flight/two-aircraft problems as the baseline
audit. Vary only one parameter family at a time:
- Reference (exactly reproduces the previously verified sample).
- Passenger-delay unit penalty ×0.5.
- Passenger-delay unit penalty ×2.
- Turnaround screen +20 minutes.
- Cancellation penalty ×2.

Use the original scenario generator, exact finite path enumeration and the
unchanged HiGHS MILP. Only independently feasible cost-aware greedy paths
are used as a comparator. No real flight schedules or prices.

The study must rerun identically byte-for-byte; all per-case scenario hashes
are recorded. Every variant reports wins, ties, mean modeled objective gap
and cancellation decisions. This is a limited **sensitivity check, not a
new optimization method or proof of generalization**.

Actual sensitivity numbers will be documented only after the GitHub Actions
real execution succeeds. Published website or investor-style savings
percentages are not appropriate for this toy model.
