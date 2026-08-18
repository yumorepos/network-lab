# Final independent release review

Adversarial read-only review of the candidate final commit. The reviewer did
not perform the finalization work and did not accept the implementation
session's provisional verdict as a premise.

**Candidate commit.** `1e8dafd` on `claude/network-lab-finalization`
**Working tree at start.** clean
**Review date.** 2026-08-17
**Constraint.** read-only. No implementation file, assumption, test or model was
changed. Every mutation described below was a temporary probe, reverted, with
`git status` proven clean afterwards.

---

## 1. Repository identity

| check | result |
|---|---|
| `pwd` | `/Users/yumo/Projects/network-lab` |
| branch | `claude/network-lab-finalization` |
| HEAD | `1e8dafd4eca90c62f0e637cf659ce87affb1e9fd` |
| working tree at start | clean |
| cited commits exist | yes: `039b83e`, `55e843d`, `ca251bf`, `1e8dafd`, `f38cf16`, `54155d7`, `531c95e`, `2131ff4`, `d514ec2`, `c889a3d`, `7b3a7db` |
| ancestry coherent | yes, all are ancestors of HEAD |
| source data unexpectedly modified | no |

### Packaging diff `039b83e..1e8dafd`, classified

40 files. Documentation and portfolio material (18), tests and consistency
guards (7), generated reports (6), presentation (1), generated-report code (1),
data artifacts (7).

Two files in the range are not documentation and were examined directly, since
an undisclosed analytical change here would be a P1:

- **`models/screen.py`** (28 lines): a rewritten `_select_service` docstring
  plus one output label, `"best schedule: "` to `"evaluated schedule: "`. The
  sort at `models/screen.py:159` is untouched.
- **`config/assumptions.yaml`** (10 lines): the `min_feasible_load_factor`
  *rationale* prose. The value is `0.50` on both sides.
- **`replay/stage2r_gate.py`** (56 lines): the claim scanner, widened.

**Verification that no analytical change hides in the artifact diff.** The
three `screen_*.csv` files were normalised by mapping the new label back to the
old and compared cell by cell against `039b83e`:

```
max relative numeric difference: 2.04e-14
non-numeric (string) differences: 0
```

Zero string differences means no verdict, no chosen frequency, no gauge, no
driver and no row ordering moved. The numeric drift is four orders of magnitude
inside the project's 1e-6 content contract and eight below any reader-facing
precision. **There is no undisclosed analytical or model change in the final
packaging range.**

---

## 2. Engineering gates, independently run

| gate | claimed | independently observed |
|---|---|---|
| `make all` | clean | **exit 0** |
| `make test` | 206 passed, 0 failed | **206 passed, 0 failed** (301 s) |
| `make reproducibility` run 1 | 29 artifacts identical | **29 artifacts identical**, exit 0 |
| `make reproducibility` run 2 | 29 artifacts identical | **29 artifacts identical**, exit 0 |
| CI-condition run | 65 / 141 / 0 | **65 passed, 141 skipped, 0 errors** |
| `git diff --check` | - | clean |
| `git status --short` after restore | - | clean |

**Tracked-output churn.** `make all` and the two reproducibility runs rewrote 14
tracked files under `data/parquet/outputs/`. Before restoring them, the
committed HEAD outputs were extracted to a temporary directory and compared
against the rebuilt tree with the project's own checker:

```
reproducible: 29 artifacts identical across a warehouse rebuild
```

All 14 differences are byte/float churn with no content difference under the
1e-6 key-merged contract. No file with a substantive difference was restored,
because there was none. `git checkout HEAD -- data/parquet/outputs/` was then
applied and the tree returned to clean at `1e8dafd`.

This same comparison independently discharges **P2-7**: the committed outputs
match a fresh build today.

---

## 3. The three late P1 fixes

These were treated as the highest-risk items because the session that found and
fixed them also issued the release verdict.

### P1-A: the consistency guard that had been red. CONFIRMED FIXED.

**The claim that it was red is true, and was verified rather than accepted.**
`039b83e` was extracted to an isolated directory and the guard run there:

```
FAILED tests/test_consistency.py::test_handwritten_docs_match_generated_scalar_metrics
assert not ['PROGRESS.md states MAE 6.5, computed 5.7']
```

So the pre-existing "195 tests pass" statement was indeed inaccurate when
written. That is retracted at `PROGRESS.md:43` in a correction placed directly
above the inaccurate entry, with the original entry left standing. This is the
right disposition: the mistake is preserved rather than rewritten.

**The fix is not a weakening.** Each quantity is checked against its own
canonical artifact: the pooled MAE against `share_validation.parquet` and
`headline_metrics.yaml`, the stratum MAE against
`share_validation_by_stratum.parquet`, which the guard now *requires* rather
than treating as optional. Four probes:

| probe | result |
|---|---|
| pooled 5.7 to 5.9 in README | `test_share_mae_consistent` and the scalar guard both **FAIL** |
| stratum 6.5 to 6.9 in PROGRESS | scalar guard **FAILS** |
| stratum value 6.5 stated in the live region with no stratum named | scalar guard **FAILS**: "is not the pooled MAE and does not name a stratum" |
| unmutated tree | 16 passed |

All reverted; `git diff` clean after each.

### P1-B: fresh-checkout CI. CONFIRMED FIXED.

Reproduced in an isolated `git archive HEAD | tar -x` checkout with no
warehouse and no raw cache. `ROOT` resolves from the source file location, so
the probe provably cannot reach the real warehouse. The real warehouse and raw
cache were never renamed, moved, deleted or rebuilt.

```
65 passed, 141 skipped in 13.08s
```

Exactly the claimed figure, and 65 + 141 = 206 reconciles with the local suite.

**Every skip names a real missing prerequisite**, via `pytest.mark.skipif` or
`pytest.skip`, not a swallowed exception: 88 skips cite the uncommitted
warehouse (hard rule 3) by name; the remainder cite specific unbuilt
intermediate artifacts (`screen.parquet`, `decision_rows.parquet`,
`diag_wide.parquet`). `tests/conftest.py` also prints a report header stating
whether the warehouse is present. No test that can run without the warehouse is
skipped for convenience.

**On the harder release question.** 65 of 206 in public CI is acceptable here,
and the deciding fact is *which* 65 run. All 26 tests in
`tests/test_consistency.py` execute in the clean checkout, including the V2
freeze digest, the bounded-predictive-claim guard, the T3 verdict guard, the
scalar-metric guard and the degeneracy-count guard, as does the claim scan in
`tests/test_stage2r_decision.py`. Every guard that protects a reader-facing
claim runs in CI. What skips is the warehouse-dependent analytical suite, which
cannot run without committing data that hard rule 3 forbids, and which runs in
full under `make test`. README states this in plain terms rather than implying
away the gap. This is honest and portfolio-defensible; it is not a materially
misleading quality claim.

### P1-C: V2 immutability. CONFIRMED FIXED, AND THE DIGEST IS GENUINE.

The digest asserted in the test was not taken on trust. Recomputed against the
freeze commit:

```
digest asserted in test : 445d0284...2310a6
digest of current 1..6  : 445d0284...2310a6
digest of FULL d514ec2  : 445d0284...2310a6
current frozen region == full d514ec2 text? True
d514ec2 contains section 7? False
```

The frozen region is byte-identical to the **entire** document as it stood at
the freeze commit, so sections 7 and 8 are pure appends and no primary metric,
interval, universe or interpretation was silently changed. Three probes:

| probe | expected | result |
|---|---|---|
| mutate a frozen Family 1 value (`0.333` to `0.334`, section 4) | must fail | **FAILED** with digest mismatch |
| edit inside allowed addendum section 8 | must pass | **passed**: the guard covers the right region and is not over-broad |
| remove an addendum's "adds no number to the freeze and changes none" | must fail | **FAILED** |

The guard cannot trivially pass after changing a frozen number, and it does not
accidentally protect the mutable addenda.

---

## 4. Claim retirement

**The regex was not simply re-run.** The scanner was read first. It covers 16
surfaces, forbids `right-siz`, enumerated `optimi[sz]e/es/ed/ing/er/ation`,
`best-fit`, `best schedule`, `picks the frequency` and `maximi[sz]e`, and waives
a line only when a retirement token appears **on the same line**, with waived
lines reported through `claim_audit(exempt=True)`.

Live result: **0 violations, 10 exemptions**, each of which I read individually
and confirmed to be an explicit retraction.

**Probe.** Appending `The engine right-sizes each market to its optimal
frequency.` to README caused
`test_no_public_surface_claims_schedule_optimisation` to **FAIL** naming the
file and line. Reverted; README byte-clean.

**Manual semantic review** of README, the Streamlit UI, all seven generated
reports, PORTFOLIO_NARRATIVE, resume_material, interview_story, demo_script,
linkedin_posts, LIMITATIONS, INTEGRITY_REPORT, docs/README and the PROGRESS
current-state block, searching for synonyms a lexical scan cannot see
(right-sizing optimizer, optimal schedule, best frequency, frequency
optimization, validated predictor, predictive superiority, route/network
optimizer, best-fit schedule). **No current surface makes any of these claims.**
Every hit was inside an explicit denial or a dated historical record. The three
generated WestJet market reports, which are outside the scanner, are clean.

The product is described consistently as **fixed-gauge route screening**.
README's schedule row, the Streamlit caption, `models/screen.py`'s docstring and
the assumptions rationale all now describe a fixed-menu evaluation, and README
states plainly that the step "is not a frequency selector".

Two gaps in the mechanism, both nonblocking, are recorded as P2-3a and P3-5
below.

---

## 5. Canonical numeric sources (Rule 6)

Load-bearing figures are generated or guarded (category A or B):

| figure | disposition |
|---|---|
| verdict counts, all three studies | B, against `headline_metrics.yaml` |
| pooled share MAE 5.7 | B, six surfaces against `share_validation.parquet` |
| stratum MAE 6.5 | B, against `share_validation_by_stratum.parquet` |
| backtest N 48 | B, matched in context on four surfaces |
| fallback count 445 of 463 | B, against `STAGE_2R_DECISION.md` |
| D3A 0 of 172 and LF 0.078 | B, against `STAGE_2R_DECISION.md` |
| resolution bounds 15 / 10 / 5 | B, against `STAGE_2R0_RESOLUTION.md` |
| T3 verdict string | B, against the T3 change report |
| transfer factor median and IQR | B, plus explicit stale-value assertions |
| gravity 6,002 / 6,092 | B on README and validation.md |

Four category-C copies survive on live portfolio surfaces, all correct today.
Recorded as P3-7.

---

## 6. The final predictive claim

Every element verified against the canonical Stage 2R artifacts, not against
prose:

| element | claimed | artifact |
|---|---|---|
| distinct launch events | 10 | `STAGE_2R0_RESOLUTION.md:68`, 15 rows, 5 scored twice |
| positive rows | 15 | `resolution_events.parquet`, 7+5+3 |
| decision vintages | 3 | 202201, 202301, 202401 |
| detectability floor | ~5 net events across >=2 vintages | `resolution_mde_grid.parquet`: minimum detectable = **5 events**, and every detectable configuration has `n_dates_moved` in {2,3} |
| largest observed difference | 1 event | `max abs net_events = 1` |
| single-vintage effects unidentifiable | yes | **0** detectable configurations with `n_dates_moved == 1` |
| k=20 saturated | yes | agreement_model == agreement_demand at all three dates (0.35/0.25/0.15) |
| metro bootstrap misses vintage uncertainty | disclosed | LIMITATIONS, stated explicitly |

The approved wording appears intact on every surface that states it, and the
bound travels with it. A search for the forbidden stronger readings ("no better
than demand", "equivalent to demand", "predicts launches", "validated
predictive model", "beats demand") returned **only** denials and retirement
lists. The claim is stated as a bounded negative everywhere, including in the
Streamlit Backtest page, which now separates the launch backtest from the
point-in-time replay.

---

## 7. T3 connection-share validation

**Verdict CONNECTION SHARE VALIDATED FOR FINAL SCOPE is correctly issued.**

Recomputed from `share_validation_by_stratum.parquet`:

| stratum | markets | rows | MAE | null MAE | beats null |
|---|---|---|---|---|---|
| A nonstop competition | 66 | 503 | 5.49 | 12.79 | yes |
| B one-stop competition only | 87 | 482 | 6.54 | 9.35 | yes |
| C sole reconstructed carrier | 23 | 62 | 5.87 | 5.87 | no, by construction |

All match the reader-facing rounded values.

**The 0.987 figure was traced to its own field and recomputed independently**,
not compared against the stratum-level `median_obs_share`. Restricting stratum C
to the 23 rows where the model assigns share 1.0, that carrier's observed share
has median **0.9868**, mean 0.9209, IQR 0.8788 to 0.9910, with **95.7% (22 of
23)** at or above 0.70 and 2.70 carriers actually selling per market. Every
number in the T3 report's stratum-C table reproduces. The stratum-level
`median_obs_share` is 0.0369, a different quantity over all 62 rows, and the
report does not conflate them.

**Protocol precedence is real, not asserted.** `c889a3d` precedes `531c95e`;
`models/share_validation_strata.py` is **absent** at the protocol commit; and
all **150 lines** of the protocol section are byte-identical between the frozen
commit and HEAD, with results appended below. The decision rule could not have
been chosen to fit the outcome.

**The 4,000 floor was not chosen to flatter the result.** It is pre-existing and
independently used at `models/demand.py:137,180`, `replay/snapshot.py:341,379`
and `models/economics.py:144`. The frozen rule 0.7 mechanically yields VALIDATED
(B has 482 rows >= 30, 87 markets >= 10, MAE 6.54 < null 9.35), and rule 0.8
mechanically yields "defensible" for stratum C (0.987 >= 0.70, the engine's own
pre-existing guard threshold, not a new one).

**Not circular.** The null shares the reconstruction's identification, so the
comparison isolates sizing given identification, which the protocol states
outright. Carriers that sell but are not reconstructed enter the panel with
model share 0 and are penalised, so missed identification is scored rather than
hidden. Unresolved-brand contribution is computed against the operating
certificate set and is genuinely 0.000 at this hub.

The scope limit is stated in LIMITATIONS: validated for the scoped screening
use case and the flagship structural regime, **not** as a general account of
airline connection behaviour, not as recovering real itineraries, and not in
untested regimes.

---

## 8. D1 final state

| requirement | result |
|---|---|
| protocol preceded the repair | yes, `7b3a7db` precedes `54155d7`, and `structural_break_years` is absent at the freeze |
| adopted rule excludes break years from the growth-ratio endpoint | yes, `replay/vintage.py:245` |
| level inputs not changed under the same exclusion | yes, `t100_seats_year` deliberately still admits a break year, documented in its docstring |
| regression tests enforce it | yes, `tests/test_d1_corridor_growth.py`, 8 tests |
| point-in-time provenance intact | yes, `_record(Provenance(...))` preserved on both resolvers |
| post-D1 comparison uses V2 as an immutable before-state | yes, and V2 was proven unmodified in section 3 |
| no new numeric constant | yes, same `[2020, 2021]` and same source as `excluded_decision_vintages`, declared separately with a distinct documented use |

Documented outcome confirmed in `W1.4_POST_D1_COMPARISON.md`: 2 of 6 growth
terms moved, both at 202301; identical decision universe; WestJet demand and
economics moved materially at that one cell (median 783 to 4,227); **zero
verdict changes in 463 rows**; both rankings identical everywhere; Families 1, 3
and 4 unchanged including bootstrap intervals; **Porter entirely unchanged**;
and the divergence from the broader Stage 2R.4 counterfactual is disclosed in
the change report, LIMITATIONS and PROGRESS rather than dropped.

**Probe E.** Removing the exclusion at `replay/vintage.py:245`, the smallest
mutation that reinstates the rejected behaviour, failed exactly the intended
guards:

```
FAILED test_corridor_growth_year_is_never_a_structural_break_year
FAILED test_resolver_skips_a_break_year_at_any_constructed_cutoff
FAILED test_growth_and_seats_years_are_now_two_rules
```

Restored from backup; md5 identical before and after; `git diff -- replay/vintage.py` empty; the 8 tests pass again. No historical rebuild was run.

D1 was not reopened on the grounds that a different growth model could be
designed. The accepted repair is correct for the defect it addresses.

---

## 9. D2 and fixed-gauge scope

Recomputed independently from `diag_wide.parquet`:

```
decision rows: 463                          (doc: 463)
rows where NO option clears the floor: 445  (doc: 445)
rows selecting 3x: 461                      (doc: 461)
selection distribution: {3: 461, 7: 2}
```

Every figure reproduces. One gauge per configured study, menu begins at 3x,
fallback returns the maximum-load-factor option which on a monotone menu is
arithmetically the smallest frequency. Fixed-gauge screening is the defensible
narrower claim, and it is the claim made.

**No live reader-facing surface presents the selected frequency as a validated
optimal schedule.** The Streamlit market detail warns when the reported
frequency is the infeasibility fallback; the route-screen caption names the
product and disclaims frequency selection; the generated reports say "evaluated
schedule". Historical documents retain the old vocabulary only where marked
(see P2-4 and P3-6).

---

## 10. D3A / D3B separation

Kept properly distinct in LIMITATIONS. D3A is survey censoring, the tied demand
blocks (51/50/49 rows) and the downstream asymmetry where margin promotes
capped rows into its own top 10 and top 20 while demand never does. D3B is the
fixed historical floor.

The project **does not** claim that changing the floor removes the tie
structure; it states the opposite explicitly, that the tie group is the same
size at every floor from 280 to 4,000 and grows as the floor falls.

Stage 2R evidence is stated and guarded: **0 of 172 survey-ceiling rows clear
the feasibility floor**, highest load factor 0.078, enforced by
`test_no_survey_ceiling_row_clears_the_feasibility_floor` (verified passing
against the warehouse). The Porter exception to the WestJet no-capped-launch
observation is disclosed as a correction rather than dropped. Both are correctly
nonblocking under fixed-gauge screening.

---

## 11. Streamlit and product semantics

`models/screen.py:159` sorts `["verdict", "margin_pct"]` and **was not touched**
in the packaging range. Confirmed against the artifacts: all three studies are
verdict-ordered with margin descending inside each verdict.

- no new score was invented; `feasible` is `load_factor >= min_feasible_load_factor`, read from `config/assumptions.yaml` rather than restated
- no model ranking changed
- no analytical artifact changed for presentation
- verdict and feasibility are conspicuous
- ordering is described accurately as a research comparator, not an opportunity ranking

The warning is load-bearing and correct. WestJet has **0 of 76** and Alaska **0
of 45** candidates clearing the floor, so both raise "the row at the top is not a
recommendation" - important, because WestJet's top row is a PASS at load factor
0.277. Porter has 4 of 79 and its top row is the genuine LAUNCH at 0.919. Deeply
infeasible PASS markets are not presented as top opportunities.

---

## 12. Generated reports versus generators

All six modified generated reports changed only through `reports/generate.py`.
Re-running `make all` left **every generated markdown byte-identical**, so
nothing was hand-edited and nothing would disappear on the next rebuild.
Reader-facing claims survive regeneration intact. `docs/STAGE_2R_DECISION.md` is
deliberately outside `make all`, with the reason stated.

---

## 13. V1 / V2 / post-D1 separation

Distinguishable, and the distinction is enforced rather than asserted. V1 is the
artifact freeze; V2 is the frozen pre-D1 predictive scoreboard, now digest-
pinned; post-D1 is a separate comparison document that reads *against* V2 rather
than replacing it. No post-D1 finding is written back into V2's primary
sections, which section 3 proves byte-identical to the freeze commit. V2 is
retained as the honest before-state and is labelled that way, not as the current
model state.

---

## 14. The hiring-manager reading

Reading only README, the portfolio narrative, the demo script, the Streamlit app
and the resume material, a hiring manager would believe:

> This person built an airline route-screening engine on open government data
> that turns raw federal and Canadian statistical files into LAUNCH/MONITOR/PASS
> verdicts for candidate new routes, with demand, competition, share and route
> economics as separate traceable layers. They then tested it honestly: they
> replayed it at historical decision dates, found it could not be shown to rank
> better than a demand-only baseline at any effect the study could resolve,
> found one headline component was doing no work, retired that component's claim
> rather than adding complexity to rescue it, validated the one layer that had
> mechanistic evidence, and stopped. The deliverable is fixed-gauge route
> screening with a bounded negative predictive result.

Compared against what the code and artifacts support, **this belief is accurate
and is not stronger than the evidence.** It is not stronger than "fixed-gauge
route screening using public data, with validated competition/share inputs and
historically bounded evaluation". No overclaim identified.

The flagship result is a recommendation of nothing, published as the finding.
That is a harder thing to put on a portfolio than a list of opportunities, and
it is presented without inflation.

---

## 15. Findings

### P0: release-invalidating correctness

**None.**

### P1: material correctness, evidence or public-claim blocker

**None.** All three P1 items claimed resolved were independently verified as
genuinely resolved, by recomputation and by mutation, not by reading their
descriptions. No finding at this severity was discovered during this review, and
none was reclassified downward to reach approval.

### P2: meaningful but disclosed and nonblocking

I concur with all seven disclosed items. Two need a correction to their stated
scope; neither changes the severity.

| id | finding | reviewer position |
|---|---|---|
| P2-1 | CI exercises 65 of 206 tests | **Concur, nonblocking.** Decisive mitigation independently verified: every reader-facing claim guard runs in CI; only the warehouse-dependent analytical suite skips, and committing that data would violate hard rule 3. Disclosed in README. |
| P2-2 | CI badge tracks `main` | **Concur.** Structural to GitHub badges; resolves on merge. |
| P2-3 | claim scan is lexical, not semantic | **Concur, and the disclosure understates the escape by one route.** See P2-3a. |
| P2-4 | frozen research records retain retired vocabulary | **Concur, but the coverage statement is optimistic.** See P2-4a. |
| P2-5 | `top_competitor` ranks by raw frequency | **Concur.** Verified reporting-only: the column is a passthrough in `models/economics.py` and `models/screen.py` and enters no computation. No verdict is affected. |
| P2-6 | ~1e-15 float noise defeats byte-equality | **Concur.** Measured 2.04e-14 maximum relative drift against a 1e-6 content contract. |
| P2-7 | nothing enforces committed outputs match a fresh build | **Concur.** Independently verified equal today (29 artifacts identical). Exposure is a stale demo, not a wrong analysis. |

**P2-3a (new, refines P2-3).** The disclosure says wording that avoids a scanned
token would pass. There is a second route it does not name: a line that *does*
use a scanned token is waived whenever a `RETIREMENT_PATTERN` token appears on
the same line, and `test_every_claim_audit_exemption_is_an_explicit_retraction`
cannot catch this because it re-applies the same pattern that granted the
waiver. Demonstrated: appending `Although the old label was retired, the engine
still selects the optimal frequency for every market.` to README left **both**
guards passing. Reverted. Nonblocking: all 10 current exemptions were read and
are genuine retractions, and no such wording exists today.

**P2-4a (new, refines P2-4).** The audit cites Round 3's superseding banner.
Round 3 does carry one. **Round 4 does not**, and it retains the vocabulary in
current tense at `INTEGRITY_REPORT.md:446` ("best-fit margin"), `:462` ("The
model right-sizes it to 3x weekly") and `:467` ("Right-sizing scope is a known
limitation"). Mitigated by the document being a dated round-structured
correctness-review history, and by the cross-reference pointing at LIMITATIONS
item 11, which is the retirement itself. Nonblocking, but the audit's coverage
claim is broader than the banners actually are.

### P3: minor cleanup

P3-1 through P3-3 as recorded by the implementation audit, plus:

| id | finding |
|---|---|
| P3-4 | `docs/FINAL_PROJECT_AUDIT.md` P1-2 states "64 passed, 141 skipped"; the correct figure is **65**, as PROGRESS.md and P2-1 both state, and as measured. 64 + 141 also fails to reconcile to 206. |
| P3-5 | `docs/FINAL_PROJECT_AUDIT.md` section 15 states "seven visible exemptions"; the live count is **10**. All 10 are genuine retractions, so the substance holds and only the count is stale. |
| P3-6 | The claim scan's surface list omits reader-facing files: `PROGRESS.md`, `INTEGRITY_REPORT.md`, `docs/README.md` and the three generated WestJet market reports. `test_claim_audit_covers_every_public_surface_that_exists` only asserts listed surfaces exist, not that all surfaces are listed. Verified clean today by manual scan. |
| P3-7 | Rule 6 says any repeated figure is generated or guarded. Four hand-maintained copies sit outside every guard: backtest N 48 at `docs/demo_script.md:47` and `docs/linkedin_posts.md:70`; gravity 6,002 at `docs/resume_material.md:9` and `docs/linkedin_posts.md:63`. All four are correct today against the computed artifacts. |
| P3-8 | README states `make test` takes ~4 s; the measured runtime is **301 s**. |

None of P3-4 through P3-8 affects a screening conclusion, the predictive claim,
the validation, or a reader's understanding of scope.

---

## 16. Audit of the audit

`docs/FINAL_PROJECT_AUDIT.md` was read line by line and its major conclusions
traced to a computed artifact, a test, source code or an explicit limitation.
The three items it nominated as least self-judgeable were taken first, and all
three survived: the packaging prose does not overstate; the right-sizing
retirement did go far enough; and the bounded negative is stated as a bounded
negative everywhere it appears, in spirit as well as in words.

The document is adversarial rather than promotional. It records that its own
project-progress claims were previously inaccurate, names the commit at which
the guard went red, and does not rewrite the entries that were wrong. Its
severity labels were not accepted automatically and, on independent
enumeration, none required promotion.

Two stale counts were found inside it (P3-4, P3-5) and one coverage statement is
broader than the evidence (P2-4a). Its verdict line is `PORTFOLIO READY`,
guarded by `test_final_audit_ends_with_exactly_one_verdict`, and the document
opens by declaring itself provisional pending exactly this review.

---

## 17. Probe register

Every probe was reverted and the tree proven clean.

| probe | target | expected | result |
|---|---|---|---|
| A1 | pooled MAE 5.7 in README | guard fails | **FAILED** as required |
| A2 | stratum MAE 6.5 in PROGRESS | guard fails | **FAILED** as required |
| A3 | stratum value with no stratum named | guard fails | **FAILED** as required |
| B1 | frozen V2 primary value | freeze guard fails | **FAILED** as required |
| B2 | allowed addendum edit | freeze guard passes | **passed**, correct region |
| B3 | addendum loses its declaration | addendum guard fails | **FAILED** as required |
| C1 | unsupported right-sizing claim in README | claim guard fails | **FAILED** as required |
| C2 | claim shielded by a same-line retirement token | - | **passed**: escape route, logged as P2-3a |
| D | clean-checkout CI, isolated `git archive` | 65 / 141 / 0 | **65 passed, 141 skipped, 0 errors** |
| E | remove D1 break-year exclusion | D1 guards fail | **3 FAILED** as required |
| - | `039b83e` guard replay | was red | **red**, confirming P1-A |

Final state: `git status --short` empty, `git diff --check` clean, HEAD
`1e8dafd` before this review document was committed. The real warehouse and raw
cache were never modified; both temporary checkouts were deleted.

---

## 18. Release decision

No unresolved P0 and no unresolved P1. The engineering gates reproduce exactly
as claimed. The three late P1 fixes are genuine, verified by recomputation and
by mutation rather than by description. The analytical evidence, D1, D2, D3, T3
and the predictive resolution bound, reproduces from the computed artifacts. The
public claim is narrower than the evidence supports rather than broader.

The residual findings are five minor documentation items and two refinements to
already-disclosed P2 limitations. None is a release blocker.

No additional model development is justified by this review. The project's own
stopping rule, that a calibration task must address a measured bottleneck and
that an expected improvement the study cannot detect is not a justification, is
correctly applied, and nothing found here reopens it.

**Nonblocking limitations carried into release:** P2-1 through P2-7 as
disclosed, refined by P2-3a and P2-4a, plus P3-1 through P3-8.

INDEPENDENT RELEASE VERDICT: APPROVE WITH NONBLOCKING FINDINGS

PORTFOLIO READY CONFIRMED
