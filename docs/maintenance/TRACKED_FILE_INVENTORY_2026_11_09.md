# Network Lab tracked-file inventory (post-cleanup snapshot)

Snapshot commit: `760eb9ca7de8a1245e98f3a0b5966f427beead6b` (GitHub `main`), 256 **tracked blob files**, full tree **not truncated**. Classification reflects operational need and public presentation value, **not** a full secret-history scan, copyright determination or assertion of source completeness. This snapshot does not count this inventory document itself, which is committed afterward.

**Permanent branches:** `main` only, following successful owner-approved retirement of 34 old remote branches. [Exact retired-head ledger](BRANCH_RETIREMENT_2026_11_09.md); PR #28 and #35 were closed without merging.

**Principle:** keep stable modules, evidence and Streamlit dependencies public; archive outdated claims without rewriting history; only put truly private content in a separately private repository/storage. Do not relocate code, generated reports, test-guarded documents or `data/parquet/outputs/` without verifying all consumers, artifact parity and full CI.

## Status totals for this snapshot

| Disposition | Number of tracked files |
|---|---:|
| ARCHIVE CANDIDATE | 54 |
| EXTRACT LATER | 2 |
| KEEP—AGENT RULES | 2 |
| KEEP—APP | 3 |
| KEEP—CI | 1 |
| KEEP—CORE | 39 |
| KEEP—DEPLOYMENT | 29 |
| KEEP—EVIDENCE | 25 |
| KEEP—POLICY | 2 |
| KEEP—RESEARCH | 6 |
| KEEP—ROOT | 6 |
| KEEP—SOURCE/INDEX | 13 |
| KEEP—TEST | 42 |
| PRIVATE CANDIDATE | 3 |
| REVIEW—OPTIONAL JOB | 6 |
| REVIEW—RESEARCH TOOL | 23 |
| **Total** | **256** |

## Highest-value cleanup actions

1. **Completed:** one `main` branch; preserved exact old SHA ledger; two unmerged PRs closed with comments.
2. **Completed:** navigation pointers in root README and docs index; credential/local ZIP ignore rules; two pre-final screenshot PNGs removed from active tree (still in Git history).
3. **Keep in place:** 29 tracked precomputed `data/parquet/outputs/` files required by Streamlit and artifact parity; `data/reference/`, config, model, replay, generated reports, test suite.
4. **Conditional migration:** career-writing drafts marked PRIVATE CANDIDATE only after removing hardcoded `tests/test_consistency.py` dependencies, updating docs links, and creating an actual private destination. Note: `git rm` leaves public history.
5. **Conditional archive:** old planning/agent handoff docs can move into `docs/history/` with GitHub link redirects or replacement pointers and a full test run. Keep historical analytical claims discoverable.
6. **Later:** separate the existing synthetic disruption recovery experiment, alongside its independent-oracle test and limitations, into its own repository. Do **not** conflate with Network Lab's route-screening engine.

## Every tracked file (snapshot at `760eb9ca7de8`)

| Path | Public-tree decision | Reason/constraint |
|---|---|---|
| `.github/workflows/bts_tls_smoke.yml` | REVIEW—OPTIONAL JOB | Historical research or network-dependent workflow; keep until deliberate workflow audit |
| `.github/workflows/ci.yml` | KEEP—CI | Required unit/artifact tests |
| `.github/workflows/research_t100_multivintage_identity.yml` | REVIEW—OPTIONAL JOB | Historical research or network-dependent workflow; keep until deliberate workflow audit |
| `.github/workflows/research_t100_projection_snapshot.yml` | REVIEW—OPTIONAL JOB | Historical research or network-dependent workflow; keep until deliberate workflow audit |
| `.github/workflows/research_t100_source_ids.yml` | REVIEW—OPTIONAL JOB | Historical research or network-dependent workflow; keep until deliberate workflow audit |
| `.github/workflows/stage_b_t100_pilot.yml` | REVIEW—OPTIONAL JOB | Historical research or network-dependent workflow; keep until deliberate workflow audit |
| `.github/workflows/stage_c_db1c_compat.yml` | REVIEW—OPTIONAL JOB | Historical research or network-dependent workflow; keep until deliberate workflow audit |
| `.gitignore` | KEEP—ROOT | Operational project entrypoint |
| `.streamlit/config.toml` | KEEP—APP | Streamlit deployment, visual theme |
| `AGENTS.md` | KEEP—AGENT RULES | Current hard rules; wording review needed |
| `app/streamlit_app.py` | KEEP—APP | Streamlit deployment, visual theme |
| `app/theme.css` | KEEP—APP | Streamlit deployment, visual theme |
| `AUDIT_2026-07-27_VERIFIED.md` | ARCHIVE CANDIDATE | Root historical audit/plan/progress document; test references may require current path |
| `AUDIT_2026-07-27.md` | ARCHIVE CANDIDATE | Root historical audit/plan/progress document; test references may require current path |
| `backtest/__init__.py` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `backtest/postmortem.py` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `backtest/run_backtest.py` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `CLAUDE.md` | KEEP—AGENT RULES | Current hard rules; wording review needed |
| `config/assumptions.yaml` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `config/replay_protocol.yaml` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `config/studies/alaska_sea.yaml` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `config/studies/porter_yyz.yaml` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `config/studies/westjet_yyc.yaml` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `data/parquet/outputs/backtest_scores.parquet` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/competition_alaska_sea.parquet` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/competition_porter_yyz.parquet` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/competition_westjet_yyc.parquet` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/demand_alaska_sea.parquet` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/demand_porter_yyz.parquet` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/demand_westjet_yyc.parquet` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/economics_alaska_sea.parquet` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/economics_porter_yyz.parquet` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/economics_westjet_yyc.parquet` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/gravity_current_poisson.yaml` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/gravity_current.yaml` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/gravity_pre2022_poisson.yaml` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/gravity_pre2022.yaml` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/headline_metrics.yaml` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/screen_alaska_sea.csv` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/screen_alaska_sea.parquet` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/screen_porter_yyz.csv` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/screen_porter_yyz.parquet` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/screen_westjet_yyc.csv` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/screen_westjet_yyc.parquet` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/share_alaska_sea.parquet` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/share_porter_yyz.parquet` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/share_validation_by_stratum.parquet` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/share_validation_strata.parquet` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/share_validation.parquet` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/share_westjet_yyc.parquet` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/transfer_factor.yaml` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/parquet/outputs/transfer_pairs.parquet` | KEEP—DEPLOYMENT | App reads committed outputs; parity tests guard values |
| `data/reference/carrier_codes.csv` | KEEP—RESEARCH | Published vetted reference datasets and provenance |
| `data/reference/carrier_families.csv` | KEEP—RESEARCH | Published vetted reference datasets and provenance |
| `data/reference/incumbent_network_202604.csv` | KEEP—RESEARCH | Published vetted reference datasets and provenance |
| `data/reference/incumbent_network_NOTES.md` | KEEP—RESEARCH | Published vetted reference datasets and provenance |
| `data/reference/launches_NOTES.md` | KEEP—RESEARCH | Published vetted reference datasets and provenance |
| `data/reference/launches.csv` | KEEP—RESEARCH | Published vetted reference datasets and provenance |
| `docs/ACTUAL_MAC_COUNTRY_CONFLICT_FACT_EXPOSURE_2026_10.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/AIRPORT_DIMENSION_LABEL_CONSISTENCY_2026_10.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/AIRPORT_IDENTITY_CONSUMER_AUDIT_2026_10.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/ARCHIVED_AIRPORT_IDENTITY_AUDIT_2026_10.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/backtest.md` | KEEP—SOURCE/INDEX | Published scope, method, limitations, audit or deployment |
| `docs/CARRIER_VINTAGE_AUDIT_2026_10.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/change_report_template.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/change_reports/A1_t100_full_history.md` | ARCHIVE CANDIDATE | Immutable correction history, do not delete without migration |
| `docs/change_reports/A2_route_spell_register.md` | ARCHIVE CANDIDATE | Immutable correction history, do not delete without migration |
| `docs/change_reports/A3_reproducibility_gate.md` | ARCHIVE CANDIDATE | Immutable correction history, do not delete without migration |
| `docs/change_reports/A5_canadian_demand_diagnostic.md` | ARCHIVE CANDIDATE | Immutable correction history, do not delete without migration |
| `docs/change_reports/D1_corridor_growth_vintage.md` | ARCHIVE CANDIDATE | Immutable correction history, do not delete without migration |
| `docs/change_reports/T2_scope_retirement.md` | ARCHIVE CANDIDATE | Immutable correction history, do not delete without migration |
| `docs/change_reports/T3_connection_share_validation.md` | ARCHIVE CANDIDATE | Immutable correction history, do not delete without migration |
| `docs/CODEX_HANDOFF.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/CODEX_TRANSITION_AUDIT.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/CROSS_SOURCE_COUNTRY_IDENTITY_AUDIT_2026_10.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/demo_script.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/deploy.md` | KEEP—SOURCE/INDEX | Published scope, method, limitations, audit or deployment |
| `docs/DERIVED_CBSA_SOURCE_PREFLIGHT_2026_10.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/ECONOMICS_SANITY_AUDIT_2026_10.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/FINAL_INDEPENDENT_REVIEW.md` | KEEP—SOURCE/INDEX | Published scope, method, limitations, audit or deployment |
| `docs/FINAL_PROJECT_AUDIT.md` | KEEP—SOURCE/INDEX | Published scope, method, limitations, audit or deployment |
| `docs/FINAL_SCOPE_CONTRACT.md` | KEEP—SOURCE/INDEX | Published scope, method, limitations, audit or deployment |
| `docs/interview_story.md` | PRIVATE CANDIDATE | Career draft; tests/test_consistency.py presently depends on path |
| `docs/LIMITATIONS.md` | KEEP—SOURCE/INDEX | Published scope, method, limitations, audit or deployment |
| `docs/linkedin_posts.md` | PRIVATE CANDIDATE | Career draft; tests/test_consistency.py presently depends on path |
| `docs/LOCAL_AIRPORT_LABEL_CANDIDATE_PREFLIGHT_2026_10.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/LOCAL_WAREHOUSE_AUDIT_HANDOFF_2026_10.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/LOCAL_WAREHOUSE_COUNTRY_CODE_PREFLIGHT_2026_10.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/maintenance/BRANCH_RETIREMENT_2026_11_09.md` | KEEP—POLICY | One-branch retirement, privacy and repository architecture |
| `docs/MILESTONE_A_COMPLETION.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/MILESTONE_A_INDEPENDENT_REVIEW.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/NETWORK_LAB_AUDIT_HANDOFF_2026_11_09.md` | KEEP—SOURCE/INDEX | Published scope, method, limitations, audit or deployment |
| `docs/phase6_demand_model_redesign.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/phase6a_implementation_report.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/phase6a_poisson_comparison.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/PORTFOLIO_NARRATIVE.md` | KEEP—SOURCE/INDEX | Published scope, method, limitations, audit or deployment |
| `docs/PUBLICATION_READINESS_AUDIT_2026_10.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/README.md` | KEEP—SOURCE/INDEX | Published scope, method, limitations, audit or deployment |
| `docs/reconciliation.md` | KEEP—SOURCE/INDEX | Published scope, method, limitations, audit or deployment |
| `docs/REMAINING_ROADMAP_REDESIGN.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/REPOSITORY_MAINTENANCE_POLICY.md` | KEEP—POLICY | One-branch retirement, privacy and repository architecture |
| `docs/resume_material.md` | PRIVATE CANDIDATE | Career draft; tests/test_consistency.py presently depends on path |
| `docs/STAGE_2R_DECISION.md` | KEEP—SOURCE/INDEX | Published scope, method, limitations, audit or deployment |
| `docs/STAGE_2R_DIAGNOSTICS.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/STAGE_2R0_RESOLUTION.md` | KEEP—SOURCE/INDEX | Published scope, method, limitations, audit or deployment |
| `docs/STAGE_B_T100_2026_07.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/STAGE_C_DB1C_COMPAT_2026_10.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/T100_2024_CANDIDATE_CONSUMER_ENVELOPE_2026_10.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/T100_2024_EXACT_FIELD_SOURCE_RECONCILIATION_2026_10.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/T100_CACHE_FRESHNESS_AUDIT_2026_10.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/T100_CROSS_VINTAGE_SOURCE_ID_RESULT_2026_10.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/T100_OFFICIAL_ID_VS_LEGACY_CODE_EXPOSURE_2026_10.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/T100_OFFICIAL_SOURCE_ID_PILOT_2026_10.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/T100_SAMPLED_HISTORICAL_AIRPORT_ID_AUDIT_2026_10.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/UPGRADE_2026_ROADMAP.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/validation.md` | KEEP—SOURCE/INDEX | Published scope, method, limitations, audit or deployment |
| `docs/W1_OFFLINE_CACHE_INVENTORY.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/W1_REPLAY_FEASIBILITY.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/W1.3_point_in_time_audit.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/W1.4_baseline_freeze.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/W1.4_POST_D1_COMPARISON.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/W1.4_predictive_baseline_v2.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/W1.4_REPLAY_PROTOCOL.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `docs/W1.4_replay_results.md` | ARCHIVE CANDIDATE | Historical research/agent handoff; check links and tests before moving |
| `experiments/disruption_recovery/README.md` | EXTRACT LATER | Synthetic optimization belongs in separate future project; preserve test |
| `experiments/disruption_recovery/recovery.py` | EXTRACT LATER | Synthetic optimization belongs in separate future project; preserve test |
| `ingest/__init__.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `ingest/bts_db1b.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `ingest/bts_form41.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `ingest/bts_lookups.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `ingest/bts_t100.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `ingest/census_bea_eia.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `ingest/common.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `ingest/ourairports.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `ingest/run_all.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `ingest/statcan.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `ingest/transtats.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `INTEGRITY_REPORT.md` | ARCHIVE CANDIDATE | Root historical audit/plan/progress document; test references may require current path |
| `LICENSE` | KEEP—ROOT | Operational project entrypoint |
| `Makefile` | KEEP—ROOT | Operational project entrypoint |
| `models/__init__.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `models/candidates.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `models/carriers.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `models/catchment.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `models/common.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `models/competition.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `models/demand.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `models/economics.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `models/gravity_log_ols.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `models/gravity_poisson.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `models/gravity.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `models/run_all.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `models/screen.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `models/share_validation_strata.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `models/share_validation.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `models/spill.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `models/transfer.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `PHASE_5_6_PLAN.md` | ARCHIVE CANDIDATE | Root historical audit/plan/progress document; test references may require current path |
| `PLAN.md` | ARCHIVE CANDIDATE | Root historical audit/plan/progress document; test references may require current path |
| `PROGRESS.md` | ARCHIVE CANDIDATE | Root historical audit/plan/progress document; test references may require current path |
| `pytest.ini` | KEEP—ROOT | Operational project entrypoint |
| `README.md` | KEEP—ROOT | Operational project entrypoint |
| `replay/__init__.py` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `replay/diagnostics.py` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `replay/pit_metros.py` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `replay/post_d1_comparison.py` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `replay/report.py` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `replay/resolution.py` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `replay/run_replay.py` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `replay/snapshot.py` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `replay/stage2r_gate_report.py` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `replay/stage2r_gate.py` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `replay/stage2r_report.py` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `replay/stage2r_snapshots.py` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `replay/stage2r.py` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `replay/vintage.py` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `reports/alaska_sea_validation.md` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `reports/generate.py` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `reports/porter_yyz_portability.md` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `reports/postmortem_f8_yyc_las.md` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `reports/postmortem_y9_yyc_las.md` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `reports/westjet_yyc_dallas_fort_worth_arlington.md` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `reports/westjet_yyc_philadelphia_camden_wilmington.md` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `reports/westjet_yyc_salt_lake_city_murray.md` | KEEP—EVIDENCE | Historical replay, postmortem or output generation |
| `requirements.txt` | KEEP—ROOT | Operational project entrypoint |
| `scripts/__init__.py` | REVIEW—RESEARCH TOOL | Keep available; group/archive later after caller/test audit |
| `scripts/audit_airport_join_exposure.py` | REVIEW—RESEARCH TOOL | Keep available; group/archive later after caller/test audit |
| `scripts/audit_airport_label_candidate.py` | REVIEW—RESEARCH TOOL | Keep available; group/archive later after caller/test audit |
| `scripts/audit_archived_airport_identity.py` | REVIEW—RESEARCH TOOL | Keep available; group/archive later after caller/test audit |
| `scripts/audit_country_conflict_fact_exposure.py` | REVIEW—RESEARCH TOOL | Keep available; group/archive later after caller/test audit |
| `scripts/audit_cross_source_country_exposure.py` | REVIEW—RESEARCH TOOL | Keep available; group/archive later after caller/test audit |
| `scripts/audit_metro_source_preflight.py` | REVIEW—RESEARCH TOOL | Keep available; group/archive later after caller/test audit |
| `scripts/audit_preserved_warehouse.py` | REVIEW—RESEARCH TOOL | Keep available; group/archive later after caller/test audit |
| `scripts/audit_publication_readiness.py` | REVIEW—RESEARCH TOOL | Keep available; group/archive later after caller/test audit |
| `scripts/audit_t100_2024_candidate_envelope.py` | REVIEW—RESEARCH TOOL | Keep available; group/archive later after caller/test audit |
| `scripts/audit_t100_2024_vintage_diff.py` | REVIEW—RESEARCH TOOL | Keep available; group/archive later after caller/test audit |
| `scripts/audit_t100_freshness.py` | REVIEW—RESEARCH TOOL | Keep available; group/archive later after caller/test audit |
| `scripts/audit_t100_source_id_vs_latest_code.py` | REVIEW—RESEARCH TOOL | Keep available; group/archive later after caller/test audit |
| `scripts/audit_warehouse_mapping.py` | REVIEW—RESEARCH TOOL | Keep available; group/archive later after caller/test audit |
| `scripts/check_reproducible.py` | REVIEW—RESEARCH TOOL | Keep available; group/archive later after caller/test audit |
| `scripts/compare_t100_source_ids.py` | REVIEW—RESEARCH TOOL | Keep available; group/archive later after caller/test audit |
| `scripts/demo_leakage_tests.py` | REVIEW—RESEARCH TOOL | Keep available; group/archive later after caller/test audit |
| `scripts/phase6a_compare.py` | REVIEW—RESEARCH TOOL | Keep available; group/archive later after caller/test audit |
| `scripts/research_t100_multivintage_identity.py` | REVIEW—RESEARCH TOOL | Keep available; group/archive later after caller/test audit |
| `scripts/research_t100_projection_snapshot.py` | REVIEW—RESEARCH TOOL | Keep available; group/archive later after caller/test audit |
| `scripts/research_t100_source_ids.py` | REVIEW—RESEARCH TOOL | Keep available; group/archive later after caller/test audit |
| `scripts/stage_b_t100_pilot.py` | REVIEW—RESEARCH TOOL | Keep available; group/archive later after caller/test audit |
| `scripts/stage_c_db1c_compat.py` | REVIEW—RESEARCH TOOL | Keep available; group/archive later after caller/test audit |
| `tests/__init__.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/conftest.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_airport_join_exposure.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_airport_label_candidate.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_archived_airport_identity.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_audit_country_conflict_fact_exposure.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_audit_cross_source_country_exposure.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_audit_t100_2024_candidate_envelope.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_audit_t100_2024_vintage_diff.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_audit_t100_source_id_vs_latest_code.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_compare_t100_source_ids.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_consistency.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_d1_corridor_growth.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_dashboard_artifact_contract.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_dashboard_desktop_qa.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_dashboard_portfolio_theme.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_disruption_recovery_experiment.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_economics_sanity_audit.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_ingest_common_tls.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_live_output_artifact_parity.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_metro_source_preflight.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_p0_regressions.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_phase6a_poisson.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_preserved_warehouse_audit.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_publication_readiness_audit.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_replay_historical_chain.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_replay_leakage.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_replay_parity.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_research_t100_multivintage_identity.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_research_t100_projection_snapshot.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_research_t100_source_ids.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_sanity.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_share_validation_strata.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_stage_b_t100_pilot.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_stage_c_db1c_compat.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_stage_c_db1c_small_segment.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_stage2r_decision.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_stage2r_diagnostics.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_stage2r0_resolution.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_t100_freshness.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_transtats_tls.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `tests/test_warehouse_mapping_audit.py` | KEEP—TEST | Guarded by CI or local tests; may require preserved warehouse |
| `warehouse/__init__.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `warehouse/build_marts.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `warehouse/incumbent_reference.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `warehouse/metro_map.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `warehouse/reconcile.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
| `warehouse/route_spells.py` | KEEP—CORE | Source/assumptions/model execution; stable imports |
