# Network Lab documentation index

This is the documentation set for Network Lab (repo root: one level up).

## Choose your path

- **Recruiters / hiring managers:** [short case study](https://yumorepos.github.io/network-lab.html) and [live route-screening dashboard](https://network-lab-tweqoqjxhfrhj7imgmuftl.streamlit.app/). Start with the *fixed-gauge scope* and bounded ranking result, not an implied production route recommendation.
- **Reviewers:** [final scope contract](FINAL_SCOPE_CONTRACT.md), [known limitations](LIMITATIONS.md), [historical replay resolution](STAGE_2R0_RESOLUTION.md), then [validation](validation.md) and [reconciliation](reconciliation.md).
- **Developers:** [repository README](../README.md), [Makefile](../Makefile), [CI workflow](../.github/workflows/ci.yml), and [AGENTS.md](../AGENTS.md). The Streamlit app reads the **tracked** precomputed output files and does not rebuild the Mac warehouse.
- **Maintainers:** [public/private file policy](REPOSITORY_MAINTENANCE_POLICY.md), [complete file-by-file inventory](maintenance/TRACKED_FILE_INVENTORY_2026_11_09.md), [34-branch retirement ledger](maintenance/BRANCH_RETIREMENT_2026_11_09.md), and [November Mac warehouse audit handoff](NETWORK_LAB_AUDIT_HANDOFF_2026_11_09.md).

**Status:** scientific sources and historical plans remain traceable. Personal résumé, interview and social-post drafts have been removed from the current public tree, and the reproducibility tests now validate research evidence directly. Git history can still contain prior versions; do not treat deletion as a privacy scrub.

## Start here

- [FINAL_SCOPE_CONTRACT.md](FINAL_SCOPE_CONTRACT.md) - what the project claims
  and what it does not, the full predictive claim with its evidence bounds, and
  the canonical source of record for every headline quantity
- [PORTFOLIO_NARRATIVE.md](PORTFOLIO_NARRATIVE.md) - the arc in eleven steps,
  including the components that were falsified and retired
- [LIMITATIONS.md](LIMITATIONS.md) - the evidence boundary: a status table for
  every quantity that carries weight in a verdict, fourteen numbered
  limitations, the disposition of every defect, the declared lookaheads, the
  predictive resolution bound, and the closed research
- [FINAL_PROJECT_AUDIT.md](FINAL_PROJECT_AUDIT.md) - the adversarial final
  audit and its severity table

## Validation and reconciliation

- [validation.md](validation.md) - gravity holdout by vintage and size band,
  transfer-factor distribution, share MAE vs observed DB1B by market
  structure
- [reconciliation.md](reconciliation.md) - computed vs published totals with
  the expected relationship derived from definitions first (14/14 in band)
- [backtest.md](backtest.md) - 48 launched-and-resolved routes vs the
  pre-2022 model; ceased-by-carrier breakdown; three-way separation

## The point-in-time replay

- [W1.4_REPLAY_PROTOCOL.md](W1.4_REPLAY_PROTOCOL.md) - frozen before results
- [W1.4_replay_results.md](W1.4_replay_results.md) - generated: per-date
  breakdown and the declared residual lookaheads
- [W1.4_predictive_baseline_v2.md](W1.4_predictive_baseline_v2.md) - the
  immutable pre-repair scoreboard. Sections 1 to 6 are frozen and guarded by a
  digest; sections 7 and 8 are append-only pointers that change no number
- [W1.4_POST_D1_COMPARISON.md](W1.4_POST_D1_COMPARISON.md) - the post-repair
  state compared against V2
- [W1.3_point_in_time_audit.md](W1.3_point_in_time_audit.md) - the leakage
  audit behind the replay

## Stage 2R: measure, attribute, decide

- [REMAINING_ROADMAP_REDESIGN.md](REMAINING_ROADMAP_REDESIGN.md) - Stage 2R,
  the diagnostic stage that replaced the automatic W2.1 to W2.5 sequence
- [STAGE_2R0_RESOLUTION.md](STAGE_2R0_RESOLUTION.md) - generated: what the
  frozen predictive comparison can and cannot distinguish, and the verdict
  that binds how the rest of Stage 2R may be read
- [STAGE_2R_DIAGNOSTICS.md](STAGE_2R_DIAGNOSTICS.md) - generated: score-layer
  attribution, the survey ceiling, the frequency degeneracy and D1's blast
  radius, all as mechanism rather than prediction
- [STAGE_2R_DECISION.md](STAGE_2R_DECISION.md) - generated: the product claim,
  the necessity gates and the final defect treatments. Its claim-audit table
  records the fifteen defective lines as they stood before T2 and is
  deliberately not regenerated, so the evidence of what was fixed survives

## Change reports

Every Phase 5 and Phase 6 change carries one; a change without one does not
merge. See [change_report_template.md](change_report_template.md).

- [change_reports/D1_corridor_growth_vintage.md](change_reports/D1_corridor_growth_vintage.md)
  - the one correctness defect found and repaired by the replay
- [change_reports/T3_connection_share_validation.md](change_reports/T3_connection_share_validation.md)
  - the stratified validation that closed W2.3 without a refit
- [change_reports/T2_scope_retirement.md](change_reports/T2_scope_retirement.md)
  - the right-sizing retirement, and a pre-existing red test found with it

## Employer-facing walkthrough and deployment

- [Portfolio case study](https://yumorepos.github.io/network-lab.html) - concise, evidence-backed overview
- [Live dashboard](https://network-lab-tweqoqjxhfrhj7imgmuftl.streamlit.app/) - read-only screening results and validation
- [demo_script.md](demo_script.md) - 2-3 minute technical walkthrough
- [deploy.md](deploy.md) - reproducible Streamlit deployment instructions

Personal résumé bullets, interview preparation and draft social posts are intentionally **not** project documentation.

## Archived research history

Older roadmap drafts, July independent audits, and the original agent instructions have moved to [docs/history/](history/README.md). The files are preserved for provenance; they do not authorize current model development. 

## Elsewhere in the repo

- `../reports/` - WestJet route evaluations, Alaska validation study, Porter
  portability table, and two route post-mortems (YYC-LAS: Flair route cut vs
  Lynx corporate shutdown, same market)
- [archived integrity report](history/INTEGRITY_REPORT.md) - what the correctness reviews changed, round by
  round, including the demotions
- [PROGRESS.md](../PROGRESS.md) - a guarded phase log; verified current claims come from data outputs. Its dated
  entries below record what was true at the time and are not rewritten
