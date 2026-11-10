# Public Network Lab tracked-file inventory

**Snapshot:** November 9, 2026 (America/Toronto), `main` commit `4706f07523fc1955545b3af791271a697da7bb71`. **260 tracked files** (includes this inventory document). This is an inventory of the *current* public branch, not of old Git history, forks or local private files.

The pre-cleanup branch retirement ledger remains at [BRANCH_RETIREMENT_2026_11_09.md](BRANCH_RETIREMENT_2026_11_09.md). Current publication/privacy decisions are at [PUBLICATION_PRIVACY_REVIEW_2026_11_09.md](PUBLICATION_PRIVACY_REVIEW_2026_11_09.md). The five historical root reports and former verbose agent guide now live under [docs/history/](../history/README.md). The `PROGRESS.md` phase log remains in root because current tests use it.

**No claim of full secrecy:** a public repository cannot hide specific subdirectories. Deleting/moving a tracked file from `main` leaves historical commits reachable. The new current-tree privacy guard checks obvious credential and personally identifying file patterns, but the history is not yet exhaustively audited.

## Count by disposition

| Decision | Files |
|---|---:|
| EXTRACT LATER | 2 |
| KEEP: canonical public docs | 14 |
| KEEP: change provenance | 7 |
| KEEP: coding agent contract | 2 |
| KEEP: core model/source | 39 |
| KEEP: dashboard | 3 |
| KEEP: deployment artifact | 29 |
| KEEP: guarded phase log | 1 |
| KEEP: historical archive | 7 |
| KEEP: maintenance evidence | 3 |
| KEEP: primary CI | 1 |
| KEEP: project root | 6 |
| KEEP: research appendix | 41 |
| KEEP: research tool | 23 |
| KEEP: scientific evidence | 25 |
| KEEP: source reference | 6 |
| KEEP: test | 45 |
| REVIEW: optional research workflow | 6 |
| **Total** | **260** |

## Every currently tracked file

| Path | Disposition | Reason |
|---|---|---|
| `.github/workflows/bts_tls_smoke.yml` | REVIEW: optional research workflow | Research-only network-dependent job; don't delete without review |
| `.github/workflows/ci.yml` | KEEP: primary CI | Required verification workflow |
| `.github/workflows/research_t100_multivintage_identity.yml` | REVIEW: optional research workflow | Research-only network-dependent job; don't delete without review |
| `.github/workflows/research_t100_projection_snapshot.yml` | REVIEW: optional research workflow | Research-only network-dependent job; don't delete without review |
| `.github/workflows/research_t100_source_ids.yml` | REVIEW: optional research workflow | Research-only network-dependent job; don't delete without review |
| `.github/workflows/stage_b_t100_pilot.yml` | REVIEW: optional research workflow | Research-only network-dependent job; don't delete without review |
| `.github/workflows/stage_c_db1c_compat.yml` | REVIEW: optional research workflow | Research-only network-dependent job; don't delete without review |
| `.gitignore` | KEEP: project root | Employer overview, license or build configuration |
| `.streamlit/config.toml` | KEEP: dashboard | Public read-only Streamlit app and styling |
| `AGENTS.md` | KEEP: coding agent contract | Tool-discoverable current coding rules |
| `app/streamlit_app.py` | KEEP: dashboard | Public read-only Streamlit app and styling |
| `app/theme.css` | KEEP: dashboard | Public read-only Streamlit app and styling |
| `backtest/__init__.py` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `backtest/postmortem.py` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `backtest/run_backtest.py` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `CLAUDE.md` | KEEP: coding agent contract | Tool-discoverable current coding rules |
| `config/assumptions.yaml` | KEEP: core model/source | Stable config, source and analytical implementation |
| `config/replay_protocol.yaml` | KEEP: core model/source | Stable config, source and analytical implementation |
| `config/studies/alaska_sea.yaml` | KEEP: core model/source | Stable config, source and analytical implementation |
| `config/studies/porter_yyz.yaml` | KEEP: core model/source | Stable config, source and analytical implementation |
| `config/studies/westjet_yyc.yaml` | KEEP: core model/source | Stable config, source and analytical implementation |
| `data/parquet/outputs/backtest_scores.parquet` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/competition_alaska_sea.parquet` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/competition_porter_yyz.parquet` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/competition_westjet_yyc.parquet` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/demand_alaska_sea.parquet` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/demand_porter_yyz.parquet` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/demand_westjet_yyc.parquet` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/economics_alaska_sea.parquet` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/economics_porter_yyz.parquet` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/economics_westjet_yyc.parquet` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/gravity_current_poisson.yaml` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/gravity_current.yaml` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/gravity_pre2022_poisson.yaml` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/gravity_pre2022.yaml` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/headline_metrics.yaml` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/screen_alaska_sea.csv` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/screen_alaska_sea.parquet` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/screen_porter_yyz.csv` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/screen_porter_yyz.parquet` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/screen_westjet_yyc.csv` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/screen_westjet_yyc.parquet` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/share_alaska_sea.parquet` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/share_porter_yyz.parquet` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/share_validation_by_stratum.parquet` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/share_validation_strata.parquet` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/share_validation.parquet` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/share_westjet_yyc.parquet` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/transfer_factor.yaml` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/parquet/outputs/transfer_pairs.parquet` | KEEP: deployment artifact | Canonical small tracked output needed by Streamlit |
| `data/reference/carrier_codes.csv` | KEEP: source reference | Research source reference/provenance |
| `data/reference/carrier_families.csv` | KEEP: source reference | Research source reference/provenance |
| `data/reference/incumbent_network_202604.csv` | KEEP: source reference | Research source reference/provenance |
| `data/reference/incumbent_network_NOTES.md` | KEEP: source reference | Research source reference/provenance |
| `data/reference/launches_NOTES.md` | KEEP: source reference | Research source reference/provenance |
| `data/reference/launches.csv` | KEEP: source reference | Research source reference/provenance |
| `docs/ACTUAL_MAC_COUNTRY_CONFLICT_FACT_EXPOSURE_2026_10.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/AIRPORT_DIMENSION_LABEL_CONSISTENCY_2026_10.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/AIRPORT_IDENTITY_CONSUMER_AUDIT_2026_10.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/ARCHIVED_AIRPORT_IDENTITY_AUDIT_2026_10.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/backtest.md` | KEEP: canonical public docs | Reader-first methods, boundaries, deployment and scope |
| `docs/CARRIER_VINTAGE_AUDIT_2026_10.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/change_report_template.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/change_reports/A1_t100_full_history.md` | KEEP: change provenance | Auditable closed research change report |
| `docs/change_reports/A2_route_spell_register.md` | KEEP: change provenance | Auditable closed research change report |
| `docs/change_reports/A3_reproducibility_gate.md` | KEEP: change provenance | Auditable closed research change report |
| `docs/change_reports/A5_canadian_demand_diagnostic.md` | KEEP: change provenance | Auditable closed research change report |
| `docs/change_reports/D1_corridor_growth_vintage.md` | KEEP: change provenance | Auditable closed research change report |
| `docs/change_reports/T2_scope_retirement.md` | KEEP: change provenance | Auditable closed research change report |
| `docs/change_reports/T3_connection_share_validation.md` | KEEP: change provenance | Auditable closed research change report |
| `docs/CODEX_HANDOFF.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/CODEX_TRANSITION_AUDIT.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/CROSS_SOURCE_COUNTRY_IDENTITY_AUDIT_2026_10.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/demo_script.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/deploy.md` | KEEP: canonical public docs | Reader-first methods, boundaries, deployment and scope |
| `docs/DERIVED_CBSA_SOURCE_PREFLIGHT_2026_10.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/ECONOMICS_SANITY_AUDIT_2026_10.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/FINAL_INDEPENDENT_REVIEW.md` | KEEP: canonical public docs | Reader-first methods, boundaries, deployment and scope |
| `docs/FINAL_PROJECT_AUDIT.md` | KEEP: canonical public docs | Reader-first methods, boundaries, deployment and scope |
| `docs/FINAL_SCOPE_CONTRACT.md` | KEEP: canonical public docs | Reader-first methods, boundaries, deployment and scope |
| `docs/history/AGENTS_legacy_2026.md` | KEEP: historical archive | Superseded audit, agent guide or plan; no longer root-level |
| `docs/history/AUDIT_2026-07-27_VERIFIED.md` | KEEP: historical archive | Superseded audit, agent guide or plan; no longer root-level |
| `docs/history/AUDIT_2026-07-27.md` | KEEP: historical archive | Superseded audit, agent guide or plan; no longer root-level |
| `docs/history/INTEGRITY_REPORT.md` | KEEP: historical archive | Superseded audit, agent guide or plan; no longer root-level |
| `docs/history/PHASE_5_6_PLAN.md` | KEEP: historical archive | Superseded audit, agent guide or plan; no longer root-level |
| `docs/history/PLAN.md` | KEEP: historical archive | Superseded audit, agent guide or plan; no longer root-level |
| `docs/history/README.md` | KEEP: historical archive | Superseded audit, agent guide or plan; no longer root-level |
| `docs/LIMITATIONS.md` | KEEP: canonical public docs | Reader-first methods, boundaries, deployment and scope |
| `docs/LOCAL_AIRPORT_LABEL_CANDIDATE_PREFLIGHT_2026_10.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/LOCAL_WAREHOUSE_AUDIT_HANDOFF_2026_10.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/LOCAL_WAREHOUSE_COUNTRY_CODE_PREFLIGHT_2026_10.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/maintenance/BRANCH_RETIREMENT_2026_11_09.md` | KEEP: maintenance evidence | Branch ledger, privacy review and tracked inventory |
| `docs/maintenance/PUBLICATION_PRIVACY_REVIEW_2026_11_09.md` | KEEP: maintenance evidence | Branch ledger, privacy review and tracked inventory |
| `docs/maintenance/TRACKED_FILE_INVENTORY_2026_11_09.md` | KEEP: maintenance evidence | Branch ledger, privacy review and tracked inventory |
| `docs/MILESTONE_A_COMPLETION.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/MILESTONE_A_INDEPENDENT_REVIEW.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/NETWORK_LAB_AUDIT_HANDOFF_2026_11_09.md` | KEEP: canonical public docs | Reader-first methods, boundaries, deployment and scope |
| `docs/phase6_demand_model_redesign.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/phase6a_implementation_report.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/phase6a_poisson_comparison.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/PORTFOLIO_NARRATIVE.md` | KEEP: canonical public docs | Reader-first methods, boundaries, deployment and scope |
| `docs/PUBLICATION_READINESS_AUDIT_2026_10.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/README.md` | KEEP: canonical public docs | Reader-first methods, boundaries, deployment and scope |
| `docs/reconciliation.md` | KEEP: canonical public docs | Reader-first methods, boundaries, deployment and scope |
| `docs/REMAINING_ROADMAP_REDESIGN.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/REPOSITORY_MAINTENANCE_POLICY.md` | KEEP: canonical public docs | Reader-first methods, boundaries, deployment and scope |
| `docs/STAGE_2R_DECISION.md` | KEEP: canonical public docs | Reader-first methods, boundaries, deployment and scope |
| `docs/STAGE_2R_DIAGNOSTICS.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/STAGE_2R0_RESOLUTION.md` | KEEP: canonical public docs | Reader-first methods, boundaries, deployment and scope |
| `docs/STAGE_B_T100_2026_07.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/STAGE_C_DB1C_COMPAT_2026_10.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/T100_2024_CANDIDATE_CONSUMER_ENVELOPE_2026_10.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/T100_2024_EXACT_FIELD_SOURCE_RECONCILIATION_2026_10.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/T100_CACHE_FRESHNESS_AUDIT_2026_10.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/T100_CROSS_VINTAGE_SOURCE_ID_RESULT_2026_10.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/T100_OFFICIAL_ID_VS_LEGACY_CODE_EXPOSURE_2026_10.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/T100_OFFICIAL_SOURCE_ID_PILOT_2026_10.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/T100_SAMPLED_HISTORICAL_AIRPORT_ID_AUDIT_2026_10.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/UPGRADE_2026_ROADMAP.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/validation.md` | KEEP: canonical public docs | Reader-first methods, boundaries, deployment and scope |
| `docs/W1_OFFLINE_CACHE_INVENTORY.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/W1_REPLAY_FEASIBILITY.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/W1.3_point_in_time_audit.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/W1.4_baseline_freeze.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/W1.4_POST_D1_COMPARISON.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/W1.4_predictive_baseline_v2.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/W1.4_REPLAY_PROTOCOL.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `docs/W1.4_replay_results.md` | KEEP: research appendix | Detailed historical or reproducibility source appendix; archive further only with tests |
| `experiments/disruption_recovery/README.md` | EXTRACT LATER | Synthetic separate recovery project; keep until migration tested |
| `experiments/disruption_recovery/recovery.py` | EXTRACT LATER | Synthetic separate recovery project; keep until migration tested |
| `ingest/__init__.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `ingest/bts_db1b.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `ingest/bts_form41.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `ingest/bts_lookups.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `ingest/bts_t100.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `ingest/census_bea_eia.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `ingest/common.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `ingest/ourairports.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `ingest/run_all.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `ingest/statcan.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `ingest/transtats.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `LICENSE` | KEEP: project root | Employer overview, license or build configuration |
| `Makefile` | KEEP: project root | Employer overview, license or build configuration |
| `models/__init__.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `models/candidates.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `models/carriers.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `models/catchment.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `models/common.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `models/competition.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `models/demand.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `models/economics.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `models/gravity_log_ols.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `models/gravity_poisson.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `models/gravity.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `models/run_all.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `models/screen.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `models/share_validation_strata.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `models/share_validation.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `models/spill.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `models/transfer.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `PROGRESS.md` | KEEP: guarded phase log | Test dependencies still reference root path |
| `pytest.ini` | KEEP: project root | Employer overview, license or build configuration |
| `README.md` | KEEP: project root | Employer overview, license or build configuration |
| `replay/__init__.py` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `replay/diagnostics.py` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `replay/pit_metros.py` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `replay/post_d1_comparison.py` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `replay/report.py` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `replay/resolution.py` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `replay/run_replay.py` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `replay/snapshot.py` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `replay/stage2r_gate_report.py` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `replay/stage2r_gate.py` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `replay/stage2r_report.py` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `replay/stage2r_snapshots.py` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `replay/stage2r.py` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `replay/vintage.py` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `reports/alaska_sea_validation.md` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `reports/generate.py` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `reports/porter_yyz_portability.md` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `reports/postmortem_f8_yyc_las.md` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `reports/postmortem_y9_yyc_las.md` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `reports/westjet_yyc_dallas_fort_worth_arlington.md` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `reports/westjet_yyc_philadelphia_camden_wilmington.md` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `reports/westjet_yyc_salt_lake_city_murray.md` | KEEP: scientific evidence | Replay, reports and bounded source findings |
| `requirements.txt` | KEEP: project root | Employer overview, license or build configuration |
| `scripts/__init__.py` | KEEP: research tool | Source verification, traceability or reproducibility CLI |
| `scripts/audit_airport_join_exposure.py` | KEEP: research tool | Source verification, traceability or reproducibility CLI |
| `scripts/audit_airport_label_candidate.py` | KEEP: research tool | Source verification, traceability or reproducibility CLI |
| `scripts/audit_archived_airport_identity.py` | KEEP: research tool | Source verification, traceability or reproducibility CLI |
| `scripts/audit_country_conflict_fact_exposure.py` | KEEP: research tool | Source verification, traceability or reproducibility CLI |
| `scripts/audit_cross_source_country_exposure.py` | KEEP: research tool | Source verification, traceability or reproducibility CLI |
| `scripts/audit_metro_source_preflight.py` | KEEP: research tool | Source verification, traceability or reproducibility CLI |
| `scripts/audit_preserved_warehouse.py` | KEEP: research tool | Source verification, traceability or reproducibility CLI |
| `scripts/audit_publication_readiness.py` | KEEP: research tool | Source verification, traceability or reproducibility CLI |
| `scripts/audit_t100_2024_candidate_envelope.py` | KEEP: research tool | Source verification, traceability or reproducibility CLI |
| `scripts/audit_t100_2024_vintage_diff.py` | KEEP: research tool | Source verification, traceability or reproducibility CLI |
| `scripts/audit_t100_freshness.py` | KEEP: research tool | Source verification, traceability or reproducibility CLI |
| `scripts/audit_t100_source_id_vs_latest_code.py` | KEEP: research tool | Source verification, traceability or reproducibility CLI |
| `scripts/audit_warehouse_mapping.py` | KEEP: research tool | Source verification, traceability or reproducibility CLI |
| `scripts/check_reproducible.py` | KEEP: research tool | Source verification, traceability or reproducibility CLI |
| `scripts/compare_t100_source_ids.py` | KEEP: research tool | Source verification, traceability or reproducibility CLI |
| `scripts/demo_leakage_tests.py` | KEEP: research tool | Source verification, traceability or reproducibility CLI |
| `scripts/phase6a_compare.py` | KEEP: research tool | Source verification, traceability or reproducibility CLI |
| `scripts/research_t100_multivintage_identity.py` | KEEP: research tool | Source verification, traceability or reproducibility CLI |
| `scripts/research_t100_projection_snapshot.py` | KEEP: research tool | Source verification, traceability or reproducibility CLI |
| `scripts/research_t100_source_ids.py` | KEEP: research tool | Source verification, traceability or reproducibility CLI |
| `scripts/stage_b_t100_pilot.py` | KEEP: research tool | Source verification, traceability or reproducibility CLI |
| `scripts/stage_c_db1c_compat.py` | KEEP: research tool | Source verification, traceability or reproducibility CLI |
| `tests/__init__.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/conftest.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_airport_join_exposure.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_airport_label_candidate.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_archived_airport_identity.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_audit_country_conflict_fact_exposure.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_audit_cross_source_country_exposure.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_audit_t100_2024_candidate_envelope.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_audit_t100_2024_vintage_diff.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_audit_t100_source_id_vs_latest_code.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_compare_t100_source_ids.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_consistency.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_d1_corridor_growth.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_dashboard_artifact_contract.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_dashboard_desktop_qa.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_dashboard_portfolio_theme.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_disruption_recovery_experiment.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_economics_sanity_audit.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_ingest_common_tls.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_live_output_artifact_parity.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_metro_source_preflight.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_p0_regressions.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_phase6a_poisson.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_preserved_warehouse_audit.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_public_document_links.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_public_privacy_guard.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_public_tree_hygiene.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_publication_readiness_audit.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_replay_historical_chain.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_replay_leakage.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_replay_parity.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_research_t100_multivintage_identity.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_research_t100_projection_snapshot.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_research_t100_source_ids.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_sanity.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_share_validation_strata.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_stage_b_t100_pilot.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_stage_c_db1c_compat.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_stage_c_db1c_small_segment.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_stage2r_decision.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_stage2r_diagnostics.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_stage2r0_resolution.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_t100_freshness.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_transtats_tls.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `tests/test_warehouse_mapping_audit.py` | KEEP: test | Automated correctness, documentation or privacy check |
| `warehouse/__init__.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `warehouse/build_marts.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `warehouse/incumbent_reference.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `warehouse/metro_map.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `warehouse/reconcile.py` | KEEP: core model/source | Stable config, source and analytical implementation |
| `warehouse/route_spells.py` | KEEP: core model/source | Stable config, source and analytical implementation |

## Outstanding governance decisions

1. Keep `data/parquet/outputs/` tracked while the deployed Streamlit app depends on it.
2. Do not move `PROGRESS.md` or generated model outputs without an independent reproducibility and link test.
3. Preserve `AGENTS.md` and `CLAUDE.md` as concise tool-discoverable files, and retain older instructions as clearly historical.
4. The original Mac DuckDB warehouse and raw data remain private. Career-writing and employer/client documents are private-workspace content, not public repo content.
5. Review old Git author metadata, removed career documents and committed history separately if any true privacy-remediation need arises.
6. Enable a protected `main` ruleset with required CI and no forced pushes/deletion in GitHub repository settings.
