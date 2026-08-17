# Network Lab: what this project is, and what it demonstrates

The short version, in the order the work actually happened. The claims here are
bounded by [FINAL_SCOPE_CONTRACT.md](FINAL_SCOPE_CONTRACT.md) and the evidence
behind them is in [LIMITATIONS.md](LIMITATIONS.md).

## The arc

**1. Built a route-screening engine from public government data.** BTS T-100,
DB1B, Form 41, StatCan, BEA, EIA, Census and OurAirports, ingested into a
DuckDB warehouse that reconciles against published totals within 1%. One
config-driven pipeline, three hub studies, no proprietary inputs.

**2. Built the layers a planner would expect.** Catchment, demand (observed
where DB1B exists, anchor-scaled or gravity plus transfer where it does not,
with the path recorded per row), competition reconstructed from T-100
frequencies, a QSI-lite share model, truncated-normal spill, and fully
allocated route economics on a 3 fare by 3 fuel grid.

**3. Audited it, and found serious defects.** The audit was adversarial and it
found real problems, not cosmetic ones. Bidirectional demand was being divided
by one-directional departures. Competitors were reconstructed by operating
certificate rather than marketing brand, which made every
mainline-plus-regional itinerary invisible. The incumbent cross-check was a
dump of the code it was supposed to be checking.

**4. Fixed them, and let the results get worse.** Correcting the brand join
moved the median modelled share down 24 points at Porter and 35 at Alaska.
Porter's headline fell from five LAUNCH markets to one. The fixes were kept and
the demotion was published, because a correctness fix that is only accepted
when it flatters the result is not a correctness process.

**5. Built a point-in-time historical replay to test the model honestly.**
Rather than scoring the current model against current outcomes, the full
verdict chain is reconstructed at three historical decision dates from offline
point-in-time data, guarded by leakage tests in which all ten injected leaks
were demonstrated to fire, and by parity tests requiring the replay to
reproduce every committed verdict market by market.

**6. Measured the instrument before reading it, and found the resolution
limited.** Agreement and recall at top k are lattice-valued on this sample, and
the smallest difference the design can resolve is roughly five net launch
events spread across two vintages. Every non-zero number in the headline
comparison was a single launch label changing at a single date. At k=20 the
demand comparator already contains every positive, so no ranking can beat it
there by any amount.

**7. Reported the bounded negative.** Against a demand-only ranking on
identical rows, the full engine showed no detectable incremental value at
effects larger than that resolution. Smaller effects remain unresolved. This is
published as the finding, per a protocol frozen before the results existed. It
is not a claim of equivalence, which the design cannot support, and it is not a
failure.

**8. Found that a headline component was effectively degenerate.** The
frequency and gauge step was described as right-sizing, a claim now retired.
Measured against the
tested candidate universe, each study configures one gauge, the schedule menu
starts at 3x weekly, and 445 of 463 decisions never reach a schedule comparison
at all because nothing is feasible. The fallback branch returns the highest
load factor, which on this menu is arithmetically the smallest frequency.

**9. Narrowed the product claim instead of adding complexity to rescue it.**
The retired right-sizing claim would have needed gauges the studied
carriers do not fly, schedules below a real operation, and a fleet-assignment
layer to support it. The claim was withdrawn rather than the model expanded.
The code path is unchanged and honestly described; only the claim moved.

**10. Investigated which layers had real mechanistic evidence, and validated
one.** The null did not license deleting everything. Layer attribution showed
share and economics materially reorder the candidate set while the schedule
step does not, and that the share layer rested almost entirely on the one-stop
reconstruction while being validated almost entirely outside that regime. That
gap was closed by a stratified validation, frozen as a protocol before the
check existed: the one-stop-only regime is now the largest stratum and the
layer beats an equal-share null there. **CONNECTION SHARE VALIDATED FOR FINAL
SCOPE.**

**11. Stopped when the evidence stopped justifying more.** Four of the five
queued calibration tasks were closed as not justified, on measurement rather
than preference: brand mapping because unresolved regional flying is under
0.15% of hub-origin departures, QSI fitting because the frequency exponent sets
a crossover the candidate sets never approach. No calibration could be
justified by an expected gain in a metric already shown unable to resolve it.

## What it demonstrates

The engineering is the entry fee: a reproducible warehouse, config-driven
studies, provenance on every demand row, every constant in one file with a
source and a sensitivity, and a test suite that fails the build when a
reader-facing number drifts from the artifact that produced it.

The part worth reading is the discipline. This project falsified its own
headline component, published a negative result against its own engine, refused
to rescue either with complexity it could not justify, and then declined to
over-correct by deleting layers that did have evidence. The final claim is
narrow, bounded, and supported.

Knowing which parts of your own model to stop defending is the skill this
demonstrates.

## What it is not

This project does not claim aircraft right-sizing, fleet assignment, network
design, validated frequency selection, or predictive superiority over demand
ranking. Each is enumerated with its reason in
[FINAL_SCOPE_CONTRACT.md](FINAL_SCOPE_CONTRACT.md).
