# Change report: retire the right-sizing claim

**Task.** T2, final packaging. Stage 2R decision `D2 RETIRE / DE-SCOPE
RIGHT-SIZING`, recorded in `docs/STAGE_2R_DECISION.md` section 1.
**Date.** 2026-08-17
**Baseline.** Checkpoint A, `039b83e`.

This is a scope and wording change. No model behaviour, assumption, threshold or
numeric result moved, and the selector implementation is untouched.

## 1. Metric impact

None. No metric family from W1.4 is touched.

| metric | before | after | delta |
|---|---|---|---|
| all Family 1 to Family 4 metrics | not recomputed | not recomputed | none |

The only computed artifact content that changed is one label string. Measured
by rebuilding under HEAD's `models/screen.py` and under the new one and
comparing with `scripts/check_reproducible.py`, which merges on keys rather than
row position:

```
screen_{alaska_sea,porter_yyz,westjet_yyc}.{parquet,csv}: driver_service moved
on 45, 79 and 76 rows
```

`driver_service` is a reader-facing sentence emitted into the screen artifact
and the downloadable CSV. It read `best schedule: 3x weekly x 174 seats
(737-8)` and now reads `evaluated schedule: ...`. No other column in any of the
29 artifacts differs, at any tolerance.

## 2. Verdict changes

None, in any study.

| study | LAUNCH | MONITOR | PASS |
|---|---|---|---|
| westjet_yyc | 0 (unchanged) | 0 (unchanged) | 76 (unchanged) |
| alaska_sea | 0 (unchanged) | 0 (unchanged) | 45 (unchanged) |
| porter_yyz | 1 (unchanged) | 1 (unchanged) | 77 (unchanged) |

Markets that changed category: none.

## 3. Regression risk

- **Guarded by:** `tests/test_stage2r_decision.py::
  test_no_public_surface_claims_schedule_optimisation`, which fails if the
  retired vocabulary reappears on any of the 15 public surfaces;
  `test_claim_audit_reads_the_working_tree`, which proves the scan reads the
  tree rather than a cached frame; `test_the_scope_contract_still_states_every_
  retired_claim`, which stops the scope contract quietly losing its retractions;
  `test_every_claim_audit_exemption_is_an_explicit_retraction`, which keeps the
  retirement carve-out honest. The existing `test_the_decision_stage_changed_
  nothing` continues to pin the menu, the gauge count and the floor.
- **Would still slip through:** wording that claims optimisation without using
  any of the scanned tokens, for example "the engine finds the schedule that
  works best". The scan is a vocabulary filter, not a semantic one. It also
  does not read the frozen Stage 2R and W1.4 research records, which are
  excluded deliberately (section 6), so a reader who takes a dated record as
  current state is not protected by a test.

## 4. Statistical meaningfulness

Not applicable. Nothing was estimated, fitted or compared.

- Sample size: not applicable
- Interval or test: not applicable
- Verdict: no detectable change, by construction

## 5. Assumptions touched

None. `config/assumptions.yaml` `min_feasible_load_factor` keeps its value of
0.50, its source, its confidence and its sensitivity range; only the free-text
`rationale` was reworded and given a pointer to the Stage 2R measurement. No
constant was added, removed, fitted or moved.

---

## 6. Surfaces audited

The Stage 2R audit named 15 lines across 7 surfaces. That count was recomputed
from the working tree at the start of this task and reproduced exactly, so no
drift had occurred since the gate. It was also **not** trusted as complete, and
searching the tree directly found more:

| surface | in Stage 2R audit | additional found | disposition |
|---|---|---|---|
| `README.md` | 4 | 0 | changed |
| `app/streamlit_app.py` | 3 | 0 | changed |
| `reports/generate.py` | 2 | 5 | changed |
| `docs/LIMITATIONS.md` | 3 | 0 | rewritten as the retirement |
| `docs/interview_story.md` | 1 | 0 | changed |
| `docs/resume_material.md` | 1 | 0 | changed |
| `docs/demo_script.md` | 1 | 0 | changed |
| `docs/linkedin_posts.md` | 0 | 1 | changed |
| `config/assumptions.yaml` | 0 | 1 | rationale reworded |
| `CLAUDE.md`, `AGENTS.md` | 0 | 3 | changed |
| `models/screen.py` | 0 | 2 | docstring and one label |
| `reports/*.md` (generated) | 0 | 2 | regenerated from the fixed generator |

The five extra lines in `reports/generate.py` used **best-fit** ("best-fit
schedule", "best-fit frequency", "best-fit margin"), which the Stage 2R pattern
did not match. The pattern now does. This is the concrete reason the task was
told to re-search rather than work from the stored count.

Two categories of false positive in the old pattern were also corrected:
`optimi[sz]` matched **optimistic**, which is a statement about a share estimate
and not an optimisation claim.

## 7. Statements changed

The substantive ones, beyond direct word substitution:

- `README.md` gained a short section stating what the schedule step is and is
  not, including that the historical replay found it effectively degenerate
  under the tested candidate universe, with 445 of 463 decisions reaching no
  comparison. This is the one place the exact count is restated outside its
  canonical source, because it is the single fact that makes the de-scope
  legible; it is covered by `test_readme_degeneracy_count_matches_the_decision_
  document`, which checks it against `docs/STAGE_2R_DECISION.md`.
- `docs/LIMITATIONS.md` item 11 was rewritten from "right-sizing is over
  frequency and gauge" into an explicit retirement: what the step does, that
  each shipped study configures one gauge so no gauge comparison ever occurs,
  that the fallback branch is arithmetically the smallest frequency, and that a
  reported frequency is therefore not evidence a comparison happened.
- `app/streamlit_app.py` now names the product as fixed-gauge route screening
  on the route screen, marks each row feasible or not against the configured
  floor, and warns on the market detail page when the frequency shown is the
  infeasibility fallback rather than a selected schedule.
- `reports/generate.py` emits a per-market sentence stating whether any tested
  option cleared the floor, generated from the artifact rather than asserted.
- `models/screen.py` docstring records that the function is a fixed-menu
  evaluation and that its behaviour is deliberately unchanged by the decision.

## 8. Terminology adopted

Following the replacement table in `docs/STAGE_2R_DECISION.md`:

| retired | adopted |
|---|---|
| right-sizing, right-sized | fixed-gauge schedule evaluation |
| picks the frequency and gauge that maximize annual contribution | evaluates a fixed schedule menu on the study gauge and reports the best feasible option, or that none is feasible |
| best schedule, best-fit schedule | evaluated schedule |
| best-fit margin | margin at the evaluated schedule |
| optimisation, optimizer | screening, evaluation |

The artifact column keeps the name `chosen_freq_wk`. Renaming a column to make
a documentation point would have changed every consumer for no gain, and the
Stage 2R decision explicitly permitted the name to stay.

## 9. Statements intentionally retained

- **Every dated research record.** `docs/STAGE_2R_DECISION.md`,
  `docs/STAGE_2R_DIAGNOSTICS.md`, `docs/STAGE_2R0_RESOLUTION.md`, the W1.4
  documents, `INTEGRITY_REPORT.md` Round 3 and the dated sections of
  `PROGRESS.md` still contain the old vocabulary. They are records of what was
  true and decided at a point in time. Rewriting them would destroy the trail
  that shows the claim was found wrong and withdrawn, which is the part worth
  keeping. `INTEGRITY_REPORT.md` Round 3 carries a pointer to this retirement so
  a reader cannot mistake it for current scope.
- **The Stage 2R audit table itself.** It lists the 15 defective lines and the
  document promises it "empties itself when the wording is corrected". It is not
  regenerated here: emptying it would erase the evidence of what T2 fixed. The
  promise is kept by a test instead, which asserts the live audit is empty. The
  document is generated but is not part of `make all`, so it will not empty on
  a routine rebuild.
- **The implementation.** `_select_service` is unchanged. The 3x/7x/14x
  evaluation still runs and is described accurately rather than hidden.

## 10. The test that changed, and why that is not a relaxation

`tests/test_stage2r_decision.py::test_claim_audit_reads_the_working_tree`
asserted `len(df)` was non-zero, that is, that defective wording was still
present. T2 exists to make that false, so the assertion could not survive the
task it was written to enable.

The property it protected, that the audit reads the working tree and not a
stored snapshot, is unchanged and is now demonstrated positively: a violation is
planted in a temporary surface and the audit must find it at the right line.

The old assertion is replaced by a strictly stronger one in
`test_no_public_surface_claims_schedule_optimisation`: the audit must be
**empty**. At the same commit the surface list grew from 8 files to 15 and the
pattern gained three claim forms. No tolerance was widened and no expected value
was edited to make a test pass.

## 11. A pre-existing test failure found and fixed

`make test` was **not** green at the baseline. At `039b83e`,
`tests/test_consistency.py::test_handwritten_docs_match_generated_scalar_metrics`
failed with:

```
PROGRESS.md states MAE 6.5, computed 5.7
```

Verified by stashing this task's changes and running the test at HEAD. The
Checkpoint A entry in `PROGRESS.md` claims "195 tests pass", which was not
accurate when written.

PROGRESS.md was right and the guard was wrong. 6.5 is the one-stop-only stratum
MAE from `share_validation_by_stratum.parquet`, a legitimately different
quantity from the pooled 5.7, and the guard compared every "MAE x.y" in a
document against the pooled value alone. It went red when T3 (`531c95e`)
published the stratum result and stayed red through Checkpoint A.

Fixed by teaching the guard both quantities, each against its own artifact. A
stratum value is accepted only where the surrounding text identifies the
stratum, so a pooled figure still cannot hide behind one. Both failure
directions were demonstrated before the fix was accepted:

```
PROGRESS.md states MAE 7.9, which is not the pooled MAE and does not name a
  stratum (pooled 5.7, strata [5.5, 6.5, 5.9])
PROGRESS.md states MAE 8.8, which does not match any computed stratum MAE
  (pooled 5.7, strata [5.5, 6.5, 5.9])
```

Two T3 artifacts, `share_validation_by_stratum.parquet` and
`share_validation_strata.parquet`, were also never force-added to git while
their 27 siblings were. CI checks out the repository and runs pytest without
building outputs, so the corrected guard would have passed locally and failed in
CI on a missing file. Both are now tracked, bringing the tracked set to the same
29 artifacts the reproducibility gate compares.

## 12. Artifact churn

`make all` rewrites every output. Eight artifacts came back byte-different but
value-identical, which is row ordering and container metadata rather than
content; they were restored to their committed state rather than committed as
noise. The commit carries only the six screen artifacts whose `driver_service`
label genuinely changed, plus the two newly tracked stratum artifacts.
