# Final project audit

Adversarial, not promotional. The question this document answers is not whether
Network Lab is impressive; it is whether any public statement in the repository
is stronger than the evidence behind it.

**This verdict is PROVISIONAL.** It was written by the same session that
performed the final packaging, which is the weakest possible arrangement for an
audit. It is not final until an independent read-only review of the final
candidate commit confirms it.

**Date.** 2026-08-17
**Branch.** `claude/network-lab-finalization`
**Scope contract.** [FINAL_SCOPE_CONTRACT.md](FINAL_SCOPE_CONTRACT.md)
**Evidence boundary.** [LIMITATIONS.md](LIMITATIONS.md)

---

## 1. What exactly does Network Lab do?

It screens candidate unserved airline routes for economic supportability
against a configured hub, carrier, aircraft gauge and schedule menu, using only
public government data.

Concretely: it ingests BTS T-100, DB1B and Form 41, StatCan, BEA, EIA, Census
delineations and OurAirports into a DuckDB warehouse that reconciles against
published totals within 1%; builds a candidate set by filtering metros the
carrier does not already serve nonstop from the hub; estimates market demand;
reconstructs the competitive set and estimates the proposed service's share;
runs truncated-normal spill into fully allocated route economics over a 3 fare
by 3 fuel grid; and emits LAUNCH, MONITOR or PASS with drivers, a top risk and
a confidence grade. A study is a YAML config, not a code change.

It also replays that entire chain at historical decision dates from
point-in-time data, which is how it tests itself.

## 2. What does it NOT do?

It does not perform fleet assignment, network design, frequency selection,
aircraft right-sizing, or validated prediction of route success. It does not
optimise anything. It does not cover Canadian domestic markets. It does not
select or recommend a schedule: it evaluates a fixed menu and reports the best
feasible option or, far more often, that none is feasible.

It has not been shown to rank candidates better than modelled demand alone.

## 3. Which datasets and grains are used?

| source | grain | use |
|---|---|---|
| BTS T-100 | carrier-segment-month | capacity, frequency, competitor reconstruction, corridor growth, served-market filter |
| BTS DB1B | origin-destination market, 10% ticket sample | US O&D demand, observed carrier shares, fare curve |
| BTS Form 41 P-5.2 / P-1.2 | carrier-quarter | direct operating cost, derived indirect burden |
| StatCan 23-10-0256 | city pair, annual, frozen at 2018 | transborder demand anchor |
| StatCan 23-10-0253 etc | airport-month | reconciliation |
| BEA CAINC1 / CAGDP2 | county-year | income and output covariates |
| EIA | weekly spot | jet fuel price |
| Census delineation | county to CBSA | metro rollup |

**T-100 is segment data and DB1B is O&D data**; they are never joined as though
they shared a grain. T-100 contains no Canadian domestic segments, which is the
root of two separate limitations.

## 4. Which important quantities are observed?

US domestic O&D demand and carrier shares (DB1B), US domestic fares (DB1B),
competitor nonstop service and frequency (T-100), the 2018 transborder anchor
where a market appears in the table (StatCan), comparator direct operating cost
(Form 41), fuel price (EIA), US per-capita personal income (BEA), and the
launch outcomes the backtest and replay are scored against.

## 5. Which are modeled?

Demand for markets without a usable observation (gravity, calibrated on 6,002
US city-market pairs, times a transfer factor); the proposed service's market
share (QSI-lite); spill and captured boardings (truncated normal); and every
economic quantity downstream of those.

## 6. Which are assumptions or proxies?

**Proxies:** competitor one-stop itineraries (reconstructed from T-100
frequencies, not observed); transborder fares (distance-matched US fares times
a premium assumption); BEA per-capita personal income standing in for ACS
median household income.

**Assumptions:** the transborder fare premium, the flat Canadian airport and
nav fee proxy (low confidence, plus or minus 30% sensitivity), the load-factor
feasibility floor, the margin hurdle, the break-even load-factor cap, the
survey ceiling threshold, the spill coefficient of variation, and the detour
bounds on the one-stop reconstruction. Each lives in `config/assumptions.yaml`
with a source, a confidence grade and a sensitivity range.

**Censored:** demand for Canada-US markets absent from the 2018 survey.

## 7. Which historical inputs contain accepted lookahead or revision?

Five, declared rather than eliminated, and generated from the provenance
records so the list cannot go stale: BEA revisions read at current vintage;
the StatCan anchor frozen at 2018 and used at every decision date; the EIA
weekly observation at the decision date itself; the 2023 Census CBSA
delineation applied at earlier dates; and the carrier operating-to-brand map,
which carries no effective dates.

The separate launch backtest carries a larger, disclosed lookahead: a single
pre-2022 model scores every launch.

**Revised historical values are described as revisions, never as
contemporaneously known information.**

## 8. What correctness defects were found during development?

Found by audit and by replay, not by the model failing visibly:

1. Bidirectional demand divided by one-directional departures (P0).
2. One-stop competitors joined on operating certificate rather than marketing
   brand, making every mainline-plus-regional itinerary invisible (P0).
3. The incumbent cross-check was a dump of the code it was supposed to be
   checking (P0).
4. A candidate-filter leak at the metro level, letting regional-operated metros
   into the candidate set.
5. The backtest narrative was factually wrong about why routes ceased.
6. The transfer factor overrode market-specific evidence where an anchor
   existed.
7. **D1**, the corridor-growth vintage: the one vintage selection applying no
   exclusion set, so a declared structural break year could serve as a growth
   numerator. Only the point-in-time replay could expose it.
8. **D2**, the right-sizing claim: the component was effectively degenerate
   under the tested candidate universe.
9. **D3A / D3B**, survey censoring and the fixed historical floor.
10. A consistency guard that had been red since T3, and a fresh-checkout test
    run that errored rather than skipped. Both found during this packaging pass.

## 9. Which were fixed?

1 through 4, 6, 7 and 10 were fixed, each with a regression test
(`tests/test_p0_regressions.py`, `tests/test_d1_corridor_growth.py`). 5 was
corrected in the reports. **The fixes were kept when they made results worse:**
correcting the brand join moved median modelled share down 24 points at Porter
and 35 at Alaska, and Porter's headline fell from five LAUNCH markets to one.

D2 was **retired rather than repaired**, deliberately. D3A and D3B are
**documented limitations**, with D3A's disposition resting on a measurement
(no survey-ceiling row clears the feasibility floor) that is itself guarded by
a test.

## 10. Which limitations remain?

All fourteen numbered items in [LIMITATIONS.md](LIMITATIONS.md), of which the
load-bearing ones are: no public Canadian domestic O&D; the transborder anchor
frozen at 2018; no MIDT or OAG, so competitor connections are reconstructed;
Air Canada one-stops from Canadian hubs are structurally invisible; transborder
fares are proxied; costs are a fully allocated proxy with a low-confidence fee
component; the schedule step is a fixed menu evaluation with no validated
selection claim; and unanchored demand is censored at a survey ceiling.

## 11. What predictive evidence exists?

- The full verdict chain reconstructs at three historical decision dates from
  offline point-in-time data, guarded by leakage tests in which all ten
  injected leaks were demonstrated to fire, and by parity tests requiring the
  replay to reproduce every committed verdict market by market.
- On the only statistically full cell, WestJet launch agreement over 244 rows
  with 15 positives, the model places roughly two thirds of real launches in
  its top ten of about eighty candidates.
- The competition and share layer is validated against observed DB1B shares,
  including, since T3, in the zero-nonstop structural regime the flagship study
  actually occupies, where it beats an equal-share null.
- The demand and reconciliation layers check against published totals within
  1%.

## 12. What predictive evidence does NOT exist?

**There is no evidence that the full engine ranks better than modelled demand
alone.** Against a demand-only ranking on identical rows, every difference
interval spans zero, and the study's measured resolution means only large
effects were ever detectable: roughly 5 net launch events across at least two
of three vintages, against a largest observed difference of one event, with 15
positive rows resting on only 10 distinct launch events, and k=20
arithmetically saturated.

There is also **no evidence of equivalence**. The null is underpowered, not
empty. Smaller effects remain unresolved, and single-vintage effects cannot be
identified at any magnitude this sample permits.

No claim of validated predictive superiority is made anywhere in the
repository, and a guard fails the build if either forbidden shortening is
asserted.

## 13. Is competition and share adequately validated for the final scope?

**Yes, for the scoped use case, and the scope of that answer is stated.**

The layer materially reorders the candidate set, rests almost entirely on the
one-stop reconstruction, and was previously validated almost entirely outside
that regime because the published check's 50,000 passenger floor selected
against it. T3 re-ran the validation at the 4,000 floor the demand layer
already uses, at the same hub, adding no hub and refitting nothing, under a
protocol frozen before the check existed. The one-stop-only regime is now the
largest stratum and the model beats an equal-share null there.

It is **not** validated as a general account of airline connection behaviour,
as recovering real itineraries, or in regimes it was not tested in. The
overstatement of connectivity where banks do not align, and the invisibility of
Air Canada one-stops from Canadian hubs, are unaffected.

## 14. Is the final fixed-gauge screening claim supported?

Yes. Every element of it is either observed, validated, or disclosed as
modelled with its uncertainty. The claim is deliberately narrow: it asserts
that the engine constructs traceable screening inputs and screens candidates
against a configured gauge and schedule menu, not that its ordering has been
shown superior to a simpler one.

The most common outcome, most routes failing, is a legitimate result under this
claim rather than a defect, because a thin transborder market genuinely cannot
support a 737 at three weekly frequencies.

## 15. Are any public statements stronger than the evidence?

**None found.** Sixteen reader-facing surfaces are scanned for
schedule-optimisation vocabulary and the scan returns zero violations, with
seven visible exemptions that are all explicit retractions. Verdict counts,
share MAE, transfer factor, backtest N, gravity counts, the D3A figures, the
resolution bounds and the T3 verdict string are each checked against a
computed artifact or a canonical document.

Two claims were corrected during this pass: `docs/linkedin_posts.md` stated a
share error of 7.0 points against a computed 5.7 and was outside every guard,
and `docs/README.md` described "thirteen limitations" and "the six tasks that
remain" when there are fourteen and none.

The residual exposure is qualitative, not numeric: the claim scan is a
vocabulary filter, so a sentence that implies optimisation without using the
scanned tokens would pass it. That is recorded as P2-3.

## 16. Are generated reports consistent with computed artifacts?

Yes. `reports/` regenerates from the outputs, and
`test_screen_reports_state_computed_verdict_counts` fails the build if any
generated report's prose disagrees with its study's verdict counts. No
generated markdown was hand-edited; the two generated reader-facing reports are
now inside the claim scan as well, so a regression in `reports/generate.py` is
caught in its output and not only in its source.

`docs/STAGE_2R_DECISION.md` is generated but deliberately **not** regenerated,
because doing so would empty the audit table that records the fifteen defective
lines T2 fixed. It is not part of `make all`, so a routine rebuild cannot empty
it by accident.

## 17. Are tests and regression guards adequate for all previously discovered P0/P1 failure modes?

Yes for the analytical P0s. Each Round 4 P0 has a named regression test that
was demonstrated to fail without its fix: bidirectional demand over
both-direction departures, brand-resolved competitor reconstruction, Air Canada
visible as one brand, and the incumbent reference proven independent of the
candidate filter. D1 has `tests/test_d1_corridor_growth.py`, and both review
mutations were re-run against the historical-chain suite and fail it.

Two gaps were closed during this pass. The V2 predictive baseline was asserted
immutable in prose by three generators, by PROGRESS.md and by the release
criteria, and **enforced by nothing**; its frozen sections are now pinned by a
digest that was verified equal to the same region at the freeze commit. And the
right-sizing retirement now has a permanent guard rather than resting on the
wording being correct once.

The honest limit: guards protect the failure modes that have already been
found. Every Round 4 P0 passed a full test suite before it was discovered.

## 18. Are V1, V2 and post-D1 states clearly distinguished?

Yes.

- **V1** is the artifact freeze, `docs/W1.4_baseline_freeze.md`.
- **V2** is the predictive scoreboard, `docs/W1.4_predictive_baseline_v2.md`,
  which states its own relationship to V1 in a table.
- **Post-D1** is `docs/W1.4_POST_D1_COMPARISON.md`, which compares against V2
  rather than replacing it.

V2 was verified during this audit to be substantively unmodified since its
freeze commit: sections 1 to 6 are byte-identical to `d514ec2`, and the two
later commits appended sections 7 and 8, each of which declares that it adds no
number and changes none. That convention is now enforced by two tests. The word
"immutable" is therefore accurate for the frozen figures and append-only for
the document, and this audit states it that way rather than loosely.

## 19. Are rejected and de-scoped research tasks documented honestly?

Yes, as completed research decisions rather than as a backlog. W2.1, W2.2, W2.4
and W2.5 are NOT JUSTIFIED with the reason attached to each; W2.3 is closed as
a validation with no refit; right-sizing expansion, additional airlines and
ADS-B are recorded as rejected, rejected and not triggered respectively.

The general rule is stated rather than left implicit: a calibration task must
address a measured bottleneck, and an expected improvement the study cannot
detect is not a justification.

Two rejections are settled by measurement rather than preference, which is what
makes them defensible: brand mapping, because unresolved regional flying is
under 0.15% of hub-origin departures at all three hubs, guarded by a test at a
1% threshold; and QSI fitting, because the frequency exponent sets a crossover
the candidate sets never approach.

## 20. Is there any remaining correctness-critical blocker?

**No.** No unresolved P0 or P1. Every finding at those severities was fixed
during this pass, with a regression guard, and none was reclassified downward.

---

## Severity table

### P0: unresolved correctness-critical

**None.**

### P1: resolved during this pass

| id | finding | disposition |
|---|---|---|
| P1-1 | `test_handwritten_docs_match_generated_scalar_metrics` had been failing since T3 (`531c95e`), because it compared every "MAE x.y" against the pooled 5.7 while T3 legitimately published the stratum 6.5. PROGRESS.md's "195 tests pass" was therefore inaccurate when written. | **FIXED** in T2. The guard now checks both quantities against their own artifacts and accepts a stratum figure only where the text names the stratum. Both failure directions demonstrated before acceptance. |
| P1-2 | A fresh checkout produced roughly 100 errors instead of skips, because the chain, leakage and parity suites need a warehouse that is deliberately not committed. CI had last run green on 2026-07-23, before the replay machinery existed, while README displayed a passing badge. | **FIXED** in T6. `tests/conftest.py` adds a warehouse precondition; under CI conditions the suite is now 64 passed, 141 skipped, zero errors. README states what CI covers. |
| P1-3 | V2's immutability, a release criterion and a claim in five places, was enforced by nothing. | **FIXED** in T6. Frozen region pinned by a digest verified against the freeze commit; addenda required to declare that they change no number. |

### P2: open, disclosed, non-blocking

| id | finding | why non-blocking |
|---|---|---|
| P2-1 | CI exercises 65 of 206 tests. The point-in-time chain, leakage and parity suites cannot run without the warehouse, and committing raw data would violate hard rule 3. | Disclosed in README rather than implied away. The skipped tests run in full under `make test`, which is the gate this project actually uses. |
| P2-2 | The CI badge tracks `main`. This branch is unmerged, so the badge does not describe the audited tree until it is merged. | Structural to GitHub badges. Resolves on merge. |
| P2-3 | The claim scan is a vocabulary filter, not a semantic one. Wording that implies optimisation without using a scanned token would pass. | Stated in the T2 change report as the known escape. No such wording exists today; the scan is a regression guard, not a proof. |
| P2-4 | Frozen research records retain pre-retirement vocabulary by design. A reader who mistakes a dated record for current scope is protected by a banner and by document conventions, not by a test. | Rewriting them would destroy the trail showing the claim was made, tested and withdrawn, which is worth more than the tidiness. INTEGRITY_REPORT Round 3 carries an explicit superseding banner. |
| P2-5 | `top_competitor` ranks by raw frequency and ignores itinerary type, so Air Canada under-reports as top competitor at Porter. | Pre-existing and recorded since Round 4. The share model itself weights nonstop against connecting correctly, so **no verdict is affected**; only a reporting field is misleading. |
| P2-6 | Run-to-run float noise of about 1e-15 relative means artifact byte-equality is not a valid reproducibility check. | Handled: the gate merges on keys and compares at 1e-6, and ran green twice. Verdicts, chosen frequencies, demand and share are bit-identical across runs. |
| P2-7 | Nothing enforces that the committed `data/parquet/outputs/` match a fresh build, so they could drift between commits. | Verified equal during this audit by key-merged comparison. The exposure is a stale live demo, not a wrong analysis. |

### P3: cosmetic or structural

| id | finding |
|---|---|
| P3-1 | `diag_wide.parquet` is untracked, so the D3A guard that recomputes from it skips in CI. A document-based guard against `STAGE_2R_DECISION.md` covers the same figures there. |
| P3-2 | LIMITATIONS item numbers cannot be made sequential because `PHASE_5_6_PLAN.md` cites them by number. Items 13 and 14 were reordered for reading without renumbering. |
| P3-3 | `PHASE_5_6_PLAN.md` and `PLAN.md` remain in the tree as superseded plans and still use pre-retirement vocabulary. They are historical planning records, marked superseded in PROGRESS.md. |

---

## Release criteria

| criterion | status |
|---|---|
| no unresolved P0 or P1 | met |
| 100% clean required tests | met: 206 passed, 0 failed |
| reproducibility green twice | met: 29 artifacts identical, both runs |
| no reader-facing contradiction with final model scope | met: claim scan returns 0 violations across 16 surfaces |
| V2 preserved | met, and now enforced by digest |
| post-D1 results documented | met: `docs/W1.4_POST_D1_COMPARISON.md` |
| connection-share validation published | met, with its scope limited |
| right-sizing claim retired | met, with a permanent regression guard |
| predictive-resolution bound disclosed | met, and guarded against its source document |
| D3 limitations disclosed | met, D3A and D3B separately |
| generated reports internally consistent | met |

## What would change this verdict

An independent reviewer should look hardest at the three things this session is
least able to judge about its own work:

1. **Whether the packaging prose overstates anything the guards cannot catch.**
   The scan is lexical. Read the README, the portfolio narrative and the
   interview story as a skeptic and ask whether the impression they leave is
   narrower than the evidence.
2. **Whether retiring the right-sizing claim went far enough**, or whether the
   engine still reads as though a schedule decision means something.
3. **Whether the bounded negative is stated as a bounded negative** everywhere
   it appears, rather than sliding into either of the two forbidden
   shortenings in spirit while avoiding them in words.

---

PORTFOLIO READY
