# Network Lab — Tracked File Inventory

**Refreshed November 10, 2026.** Audited `main` snapshot: `b26e102406ab5f7466d9018819602b64b43b670a` · **255 tracked files**. This inventory includes the earlier comprehensive branch/research cleanup and the subsequent career-draft retirement. It is a point-in-time snapshot; later commits may add files.

**Current policy:** [Repository maintenance and privacy](../REPOSITORY_MAINTENANCE_POLICY.md) · [Branch retirement ledger](BRANCH_RETIREMENT_2026_11_09.md) · [Evidence scope](../FINAL_SCOPE_CONTRACT.md)

## What changed in employer-readiness cleanup

- Three former career-writing drafts (résumé bullet material, interview notes, and unpublished social posts) are no longer in the public working tree.
- Both `tests/test_consistency.py` and `replay/stage2r_gate.py` now enforce claims on **current published research surfaces**, not on private career-writing material.
- The publication-facing README and docs index lead directly to the verified case study, dashboard, independent review and limitations.
- No `data/parquet/outputs/`, model, warehouse, replay, or production application artifacts were moved or regenerated.
- Public Git history retains older versions of deleted files; this is **not** a history purge or security certification.

## Count by disposition

| Disposition | Files |
|---|---:|
| ARCHIVE LATER | 54 |
| EXTRACT LATER | 2 |
| KEEP — AGENT CONTRACT | 2 |
| KEEP — APPLICATION | 3 |
| KEEP — CI | 1 |
| KEEP — CORE | 39 |
| KEEP — DEPLOYMENT | 29 |
| KEEP — MAINTENANCE | 3 |
| KEEP — PUBLIC EVIDENCE | 13 |
| KEEP — RESEARCH | 6 |
| KEEP — ROOT | 6 |
| KEEP — SCIENTIFIC EVIDENCE | 25 |
| KEEP — TEST | 43 |
| REVIEW — OPTIONAL WORKFLOW | 6 |
| REVIEW — RESEARCH UTILITY | 23 |
| **Total** | **255** |

## Full tracked-file classification

| Path | Decision | Purpose / constraint |
|---|---|---|
| `.github/workflows/bts_tls_smoke.yml` | REVIEW — OPTIONAL WORKFLOW | Research or network-dependent job, not required for standard CI |
| `.github/workflows/ci.yml` | KEEP — CI | Primary test and artifact contract checks |
| `.github/workflows/research_t100_multivintage_identity.yml` | REVIEW — OPTIONAL WORKFLOW | Research or network-dependent job, not required for standard CI |
| `.github/workflows/research_t100_projection_snapshot.yml` | REVIEW — OPTIONAL WORKFLOW | Research or network-dependent job, not required for standard CI |
| `.github/workflows/research_t100_source_ids.yml` | REVIEW — OPTIONAL WORKFLOW | Research or network-dependent job, not required for standard CI |
| `.github/workflows/stage_b_t100_pilot.yml` | REVIEW — OPTIONAL WORKFLOW | Research or network-dependent job, not required for standard CI |
| `.github/workflows/stage_c_db1c_compat.yml` | REVIEW — OPTIONAL WORKFLOW | Research or network-dependent job, not required for standard CI |
| `.gitignore` | KEEP — ROOT | Project overview, license, runtime or build setting |
| `.streamlit/config.toml` | KEEP — APPLICATION | Live Streamlit code and presentation |
| `AGENTS.md` | KEEP — AGENT CONTRACT | Current machine-readable working rules |
| `app/streamlit_app.py` | KEEP — APPLICATION | Live Streamlit code and presentation |
| `app/theme.css` | KEEP — APPLICATION | Live Streamlit code and presentation |
| `AUDIT_2026-07-27_VERIFIED.md` | ARCHIVE LATER | Historical root progress/plan retained for provenance and tests |
| `AUDIT_2026-07-27.md` | ARCHIVE LATER | Historical root progress/plan retained for provenance and tests |
| `backtest/__init__.py` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `backtest/postmortem.py` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `backtest/run_backtest.py` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `CLAUDE.md` | KEEP — AGENT CONTRACT | Current machine-readable working rules |
| `config/assumptions.yaml` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `config/replay_protocol.yaml` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `config/studies/alaska_sea.yaml` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `config/studies/porter_yyz.yaml` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `config/studies/westjet_yyc.yaml` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `data/parquet/outputs/backtest_scores.parquet` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/competition_alaska_sea.parquet` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/competition_porter_yyz.parquet` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/competition_westjet_yyc.parquet` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/demand_alaska_sea.parquet` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/demand_porter_yyz.parquet` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/demand_westjet_yyc.parquet` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/economics_alaska_sea.parquet` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/economics_porter_yyz.parquet` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/economics_westjet_yyc.parquet` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/gravity_current_poisson.yaml` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/gravity_current.yaml` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/gravity_pre2022_poisson.yaml` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/gravity_pre2022.yaml` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/headline_metrics.yaml` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/screen_alaska_sea.csv` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/screen_alaska_sea.parquet` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/screen_porter_yyz.csv` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/screen_porter_yyz.parquet` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/screen_westjet_yyc.csv` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/screen_westjet_yyc.parquet` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/share_alaska_sea.parquet` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/share_porter_yyz.parquet` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/share_validation_by_stratum.parquet` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/share_validation_strata.parquet` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/share_validation.parquet` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/share_westjet_yyc.parquet` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/transfer_factor.yaml` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/parquet/outputs/transfer_pairs.parquet` | KEEP — DEPLOYMENT | Committed artifact required by the read-only Streamlit dashboard |
| `data/reference/carrier_codes.csv` | KEEP — RESEARCH | Source-vetted research reference/provenance |
| `data/reference/carrier_families.csv` | KEEP — RESEARCH | Source-vetted research reference/provenance |
| `data/reference/incumbent_network_202604.csv` | KEEP — RESEARCH | Source-vetted research reference/provenance |
| `data/reference/incumbent_network_NOTES.md` | KEEP — RESEARCH | Source-vetted research reference/provenance |
| `data/reference/launches_NOTES.md` | KEEP — RESEARCH | Source-vetted research reference/provenance |
| `data/reference/launches.csv` | KEEP — RESEARCH | Source-vetted research reference/provenance |
| `docs/ACTUAL_MAC_COUNTRY_CONFLICT_FACT_EXPOSURE_2026_10.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/AIRPORT_DIMENSION_LABEL_CONSISTENCY_2026_10.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/AIRPORT_IDENTITY_CONSUMER_AUDIT_2026_10.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/ARCHIVED_AIRPORT_IDENTITY_AUDIT_2026_10.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/backtest.md` | KEEP — PUBLIC EVIDENCE | Canonical scope, validation, technical navigation or audit |
| `docs/CARRIER_VINTAGE_AUDIT_2026_10.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/change_report_template.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/change_reports/A1_t100_full_history.md` | ARCHIVE LATER | Immutable research change explanation; don't delete |
| `docs/change_reports/A2_route_spell_register.md` | ARCHIVE LATER | Immutable research change explanation; don't delete |
| `docs/change_reports/A3_reproducibility_gate.md` | ARCHIVE LATER | Immutable research change explanation; don't delete |
| `docs/change_reports/A5_canadian_demand_diagnostic.md` | ARCHIVE LATER | Immutable research change explanation; don't delete |
| `docs/change_reports/D1_corridor_growth_vintage.md` | ARCHIVE LATER | Immutable research change explanation; don't delete |
| `docs/change_reports/T2_scope_retirement.md` | ARCHIVE LATER | Immutable research change explanation; don't delete |
| `docs/change_reports/T3_connection_share_validation.md` | ARCHIVE LATER | Immutable research change explanation; don't delete |
| `docs/CODEX_HANDOFF.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/CODEX_TRANSITION_AUDIT.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/CROSS_SOURCE_COUNTRY_IDENTITY_AUDIT_2026_10.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/demo_script.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/deploy.md` | KEEP — PUBLIC EVIDENCE | Canonical scope, validation, technical navigation or audit |
| `docs/DERIVED_CBSA_SOURCE_PREFLIGHT_2026_10.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/ECONOMICS_SANITY_AUDIT_2026_10.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/FINAL_INDEPENDENT_REVIEW.md` | KEEP — PUBLIC EVIDENCE | Canonical scope, validation, technical navigation or audit |
| `docs/FINAL_PROJECT_AUDIT.md` | KEEP — PUBLIC EVIDENCE | Canonical scope, validation, technical navigation or audit |
| `docs/FINAL_SCOPE_CONTRACT.md` | KEEP — PUBLIC EVIDENCE | Canonical scope, validation, technical navigation or audit |
| `docs/LIMITATIONS.md` | KEEP — PUBLIC EVIDENCE | Canonical scope, validation, technical navigation or audit |
| `docs/LOCAL_AIRPORT_LABEL_CANDIDATE_PREFLIGHT_2026_10.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/LOCAL_WAREHOUSE_AUDIT_HANDOFF_2026_10.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/LOCAL_WAREHOUSE_COUNTRY_CODE_PREFLIGHT_2026_10.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/maintenance/BRANCH_RETIREMENT_2026_11_09.md` | KEEP — MAINTENANCE | Historical branch ledger, current file inventory and governance policy |
| `docs/maintenance/TRACKED_FILE_INVENTORY_2026_11_09.md` | KEEP — MAINTENANCE | Historical branch ledger, current file inventory and governance policy |
| `docs/MILESTONE_A_COMPLETION.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/MILESTONE_A_INDEPENDENT_REVIEW.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/NETWORK_LAB_AUDIT_HANDOFF_2026_11_09.md` | KEEP — PUBLIC EVIDENCE | Canonical scope, validation, technical navigation or audit |
| `docs/phase6_demand_model_redesign.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/phase6a_implementation_report.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/phase6a_poisson_comparison.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/PORTFOLIO_NARRATIVE.md` | KEEP — PUBLIC EVIDENCE | Canonical scope, validation, technical navigation or audit |
| `docs/PUBLICATION_READINESS_AUDIT_2026_10.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/README.md` | KEEP — PUBLIC EVIDENCE | Canonical scope, validation, technical navigation or audit |
| `docs/reconciliation.md` | KEEP — PUBLIC EVIDENCE | Canonical scope, validation, technical navigation or audit |
| `docs/REMAINING_ROADMAP_REDESIGN.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/REPOSITORY_MAINTENANCE_POLICY.md` | KEEP — MAINTENANCE | Historical branch ledger, current file inventory and governance policy |
| `docs/STAGE_2R_DECISION.md` | KEEP — PUBLIC EVIDENCE | Canonical scope, validation, technical navigation or audit |
| `docs/STAGE_2R_DIAGNOSTICS.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/STAGE_2R0_RESOLUTION.md` | KEEP — PUBLIC EVIDENCE | Canonical scope, validation, technical navigation or audit |
| `docs/STAGE_B_T100_2026_07.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/STAGE_C_DB1C_COMPAT_2026_10.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/T100_2024_CANDIDATE_CONSUMER_ENVELOPE_2026_10.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/T100_2024_EXACT_FIELD_SOURCE_RECONCILIATION_2026_10.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/T100_CACHE_FRESHNESS_AUDIT_2026_10.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/T100_CROSS_VINTAGE_SOURCE_ID_RESULT_2026_10.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/T100_OFFICIAL_ID_VS_LEGACY_CODE_EXPOSURE_2026_10.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/T100_OFFICIAL_SOURCE_ID_PILOT_2026_10.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/T100_SAMPLED_HISTORICAL_AIRPORT_ID_AUDIT_2026_10.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/UPGRADE_2026_ROADMAP.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/validation.md` | KEEP — PUBLIC EVIDENCE | Canonical scope, validation, technical navigation or audit |
| `docs/W1_OFFLINE_CACHE_INVENTORY.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/W1_REPLAY_FEASIBILITY.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/W1.3_point_in_time_audit.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/W1.4_baseline_freeze.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/W1.4_POST_D1_COMPARISON.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/W1.4_predictive_baseline_v2.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/W1.4_REPLAY_PROTOCOL.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `docs/W1.4_replay_results.md` | ARCHIVE LATER | Older plan or handoff; keep link stable until tested migration |
| `experiments/disruption_recovery/README.md` | EXTRACT LATER | Synthetic optimizer for future standalone project |
| `experiments/disruption_recovery/recovery.py` | EXTRACT LATER | Synthetic optimizer for future standalone project |
| `ingest/__init__.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `ingest/bts_db1b.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `ingest/bts_form41.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `ingest/bts_lookups.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `ingest/bts_t100.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `ingest/census_bea_eia.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `ingest/common.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `ingest/ourairports.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `ingest/run_all.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `ingest/statcan.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `ingest/transtats.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `INTEGRITY_REPORT.md` | ARCHIVE LATER | Historical root progress/plan retained for provenance and tests |
| `LICENSE` | KEEP — ROOT | Project overview, license, runtime or build setting |
| `Makefile` | KEEP — ROOT | Project overview, license, runtime or build setting |
| `models/__init__.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `models/candidates.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `models/carriers.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `models/catchment.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `models/common.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `models/competition.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `models/demand.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `models/economics.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `models/gravity_log_ols.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `models/gravity_poisson.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `models/gravity.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `models/run_all.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `models/screen.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `models/share_validation_strata.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `models/share_validation.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `models/spill.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `models/transfer.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `PHASE_5_6_PLAN.md` | ARCHIVE LATER | Historical root progress/plan retained for provenance and tests |
| `PLAN.md` | ARCHIVE LATER | Historical root progress/plan retained for provenance and tests |
| `PROGRESS.md` | ARCHIVE LATER | Historical root progress/plan retained for provenance and tests |
| `pytest.ini` | KEEP — ROOT | Project overview, license, runtime or build setting |
| `README.md` | KEEP — ROOT | Project overview, license, runtime or build setting |
| `replay/__init__.py` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `replay/diagnostics.py` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `replay/pit_metros.py` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `replay/post_d1_comparison.py` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `replay/report.py` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `replay/resolution.py` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `replay/run_replay.py` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `replay/snapshot.py` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `replay/stage2r_gate_report.py` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `replay/stage2r_gate.py` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `replay/stage2r_report.py` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `replay/stage2r_snapshots.py` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `replay/stage2r.py` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `replay/vintage.py` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `reports/alaska_sea_validation.md` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `reports/generate.py` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `reports/porter_yyz_portability.md` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `reports/postmortem_f8_yyc_las.md` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `reports/postmortem_y9_yyc_las.md` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `reports/westjet_yyc_dallas_fort_worth_arlington.md` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `reports/westjet_yyc_philadelphia_camden_wilmington.md` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `reports/westjet_yyc_salt_lake_city_murray.md` | KEEP — SCIENTIFIC EVIDENCE | History, replay, or generated research outputs |
| `requirements.txt` | KEEP — ROOT | Project overview, license, runtime or build setting |
| `scripts/__init__.py` | REVIEW — RESEARCH UTILITY | Retain until callers, imports and offline behavior are audited |
| `scripts/audit_airport_join_exposure.py` | REVIEW — RESEARCH UTILITY | Retain until callers, imports and offline behavior are audited |
| `scripts/audit_airport_label_candidate.py` | REVIEW — RESEARCH UTILITY | Retain until callers, imports and offline behavior are audited |
| `scripts/audit_archived_airport_identity.py` | REVIEW — RESEARCH UTILITY | Retain until callers, imports and offline behavior are audited |
| `scripts/audit_country_conflict_fact_exposure.py` | REVIEW — RESEARCH UTILITY | Retain until callers, imports and offline behavior are audited |
| `scripts/audit_cross_source_country_exposure.py` | REVIEW — RESEARCH UTILITY | Retain until callers, imports and offline behavior are audited |
| `scripts/audit_metro_source_preflight.py` | REVIEW — RESEARCH UTILITY | Retain until callers, imports and offline behavior are audited |
| `scripts/audit_preserved_warehouse.py` | REVIEW — RESEARCH UTILITY | Retain until callers, imports and offline behavior are audited |
| `scripts/audit_publication_readiness.py` | REVIEW — RESEARCH UTILITY | Retain until callers, imports and offline behavior are audited |
| `scripts/audit_t100_2024_candidate_envelope.py` | REVIEW — RESEARCH UTILITY | Retain until callers, imports and offline behavior are audited |
| `scripts/audit_t100_2024_vintage_diff.py` | REVIEW — RESEARCH UTILITY | Retain until callers, imports and offline behavior are audited |
| `scripts/audit_t100_freshness.py` | REVIEW — RESEARCH UTILITY | Retain until callers, imports and offline behavior are audited |
| `scripts/audit_t100_source_id_vs_latest_code.py` | REVIEW — RESEARCH UTILITY | Retain until callers, imports and offline behavior are audited |
| `scripts/audit_warehouse_mapping.py` | REVIEW — RESEARCH UTILITY | Retain until callers, imports and offline behavior are audited |
| `scripts/check_reproducible.py` | REVIEW — RESEARCH UTILITY | Retain until callers, imports and offline behavior are audited |
| `scripts/compare_t100_source_ids.py` | REVIEW — RESEARCH UTILITY | Retain until callers, imports and offline behavior are audited |
| `scripts/demo_leakage_tests.py` | REVIEW — RESEARCH UTILITY | Retain until callers, imports and offline behavior are audited |
| `scripts/phase6a_compare.py` | REVIEW — RESEARCH UTILITY | Retain until callers, imports and offline behavior are audited |
| `scripts/research_t100_multivintage_identity.py` | REVIEW — RESEARCH UTILITY | Retain until callers, imports and offline behavior are audited |
| `scripts/research_t100_projection_snapshot.py` | REVIEW — RESEARCH UTILITY | Retain until callers, imports and offline behavior are audited |
| `scripts/research_t100_source_ids.py` | REVIEW — RESEARCH UTILITY | Retain until callers, imports and offline behavior are audited |
| `scripts/stage_b_t100_pilot.py` | REVIEW — RESEARCH UTILITY | Retain until callers, imports and offline behavior are audited |
| `scripts/stage_c_db1c_compat.py` | REVIEW — RESEARCH UTILITY | Retain until callers, imports and offline behavior are audited |
| `tests/__init__.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/conftest.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_airport_join_exposure.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_airport_label_candidate.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_archived_airport_identity.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_audit_country_conflict_fact_exposure.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_audit_cross_source_country_exposure.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_audit_t100_2024_candidate_envelope.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_audit_t100_2024_vintage_diff.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_audit_t100_source_id_vs_latest_code.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_compare_t100_source_ids.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_consistency.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_d1_corridor_growth.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_dashboard_artifact_contract.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_dashboard_desktop_qa.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_dashboard_portfolio_theme.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_disruption_recovery_experiment.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_economics_sanity_audit.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_ingest_common_tls.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_live_output_artifact_parity.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_metro_source_preflight.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_p0_regressions.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_phase6a_poisson.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_preserved_warehouse_audit.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_public_tree_hygiene.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_publication_readiness_audit.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_replay_historical_chain.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_replay_leakage.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_replay_parity.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_research_t100_multivintage_identity.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_research_t100_projection_snapshot.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_research_t100_source_ids.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_sanity.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_share_validation_strata.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_stage_b_t100_pilot.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_stage_c_db1c_compat.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_stage_c_db1c_small_segment.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_stage2r_decision.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_stage2r_diagnostics.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_stage2r0_resolution.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_t100_freshness.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_transtats_tls.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `tests/test_warehouse_mapping_audit.py` | KEEP — TEST | Automated consistency, contract, unit or audit test |
| `warehouse/__init__.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `warehouse/build_marts.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `warehouse/incumbent_reference.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `warehouse/metro_map.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `warehouse/reconcile.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |
| `warehouse/route_spells.py` | KEEP — CORE | Model, source, warehouse build or assumptions; maintain existing imports |

## Decisions for next review

1. **Do not remove** tracked live Streamlit outputs or the fixed-gauge pipeline without verifying new deployment artifacts and all reproducibility tests.
2. **Do not erase** historical scientific failures or negative results merely to shorten public documentation.
3. Older plans and agent handoffs can be moved into a history folder in a later, tested link migration. They are not current work authorizations.
4. The synthetic disruption recovery experiment may become a separate repository after independent evaluation and provenance checks.
5. To truly remove confidential content from an old public commit, assess credential revocation and history-remediation separately; simple file deletion does not suffice.
