# Network Lab — November 9, 2026 audit handoff (draft)

**Scope:** Documentation-only handoff based on the user's privately run, read-only November 9 Mac warehouse diagnostic. **No warehouse, ingestion, mapping, model, replay, generated screen output, or deployed application was changed.** The private ZIP/JSON/CSV and 5.19 GB DuckDB are not committed.

## Source and verification boundaries

- Base repository: `main` at `41c67f61f5ce65902ca67976b032ae963a62a91e`, latest main CI successful ([run #93](https://github.com/yumorepos/network-lab/actions/runs/40998912096)).
- Executed script: `scripts/audit_country_conflict_fact_exposure.py` (merged [PR #33](https://github.com/yumorepos/network-lab/pull/33)); original Mac DuckDB was opened by the local script with `read_only=True`.
- Local evidence: privately supplied `NetworkLab-Audit-20261109-142012.zip`, SHA-256 `dd21f0533763995dadfb414a2bf79669f1bd6d1484836ccc6377f6a004d1793c`. JSON and CSV were cross-checked for all 1,583 grouped endpoint records and summary aggregations.
- **Not verified:** independent original warehouse hash before and after; source-stable historic AirportID completeness; corrected 200 screen decisions; corrected 463 replay decisions; live Streamlit deployment state.

## Evidence established

| Property | Measured value |
|---|---:|
| Stored airport dimension rows | 8,802 |
| Stored-country / selected BTS market-country disagreements | 140 |
| Provisional administrative or territory conventions | 28 |
| Unresolved country conflicts | 112 |
| Unresolved conflicts with historical operated-segment endpoint rows | 51 codes |
| Historical unresolved endpoint rows / passenger-segment legs | 3,830 / 147,323 |
| Latest-12 unresolved endpoint rows / passenger-segment legs | 97 / 286 (9 codes) |
| Latest-12 provisional-convention endpoint rows / passenger-segment legs | 8,827 / 18,776,134 |

Latest reporting month was **2026-04**, and the latest-12 window is **2025-05 through 2026-04**. The only direct `YYC/SEA/YYZ` origin -> `US`-reported conflicting destination in that window was **YYZ -> SJU**: 18 segment rows, 65 departures, 9,652 passenger-segment legs. SJU is in the provisional PR/US country-convention class; **zero unresolved conflicts appeared in this limited direct hub-to-U.S. path**.

This is exposure, **not** passenger loss, ticket O&D, a proven wrong CBSA/city-market assignment, forecast error, or route-verdict delta. The nine traffic-bearing recent unresolved codes are PTL, SKJ, MHM, CAT, LSR, MQJ, NAD, DWA and SAW. SAW has both historical Turkey- and US-reported source rows, illustrating the risk of an IATA code-only join across vintages.

## Decision

1. **Close the bounded source-endpoint fact-exposure evidence request as measured**, but do not certify historical identity or downstream accuracy. Keep [#7](https://github.com/yumorepos/network-lab/issues/7), [#14](https://github.com/yumorepos/network-lab/issues/14) and [#30](https://github.com/yumorepos/network-lab/issues/30) open.
2. Keep [draft PR #28](https://github.com/yumorepos/network-lab/pull/28) **unmerged**. Its label-only fix cannot reconcile source-vintage airport identity or geographically ambiguous numeric CityMarketIDs.
3. Next bounded check: use the existing `scripts.audit_preserved_warehouse` **read-only** against the preserved local warehouse, with a new output folder **outside** the project. Assess real `map_citymarket_cbsa` cardinality, source airport-code gaps, monthly coverage and PBI/DJT. [#14](https://github.com/yumorepos/network-lab/issues/14) has much larger **source-side** ambiguous-CBSA exposure (9.22M segment-passenger legs across 10 markets), but production misassignment is **not yet demonstrated**.
4. If and only if a consumer path and official point-in-time stable identifiers support a correction, compare an **isolated candidate** warehouse against all 200 screens and 463 replay decisions under fixed source snapshots and the full gates. Never overwrite the original DuckDB or hand-edit generated reports.
5. Prioritize an evidence-first portfolio case study and live dashboard visual review over further model tuning. The [final scope contract](FINAL_SCOPE_CONTRACT.md) remains controlling: **fixed-gauge route screening**, not optimized network design, validated frequency selection or demonstrated predictive superiority.

## Short work plan (5 hours/week)

- **Now, 0.5–1 hour:** record this result, preserve the audit archive privately, leave model defaults/outputs unchanged.
- **Next, 2–4 hours:** targeted existing read-only preserved-warehouse/mapping audit, review join/candidate consumer pathways and determine stop/continue.
- **Conditional, 2–6 hours:** official historic AirportID/CBSA source validation and isolated counterfactual only if impact evidence exists.
- **Portfolio, 3–5 hours:** demonstrate clear problem → data → model → validation → bounded negative result → stop decision; confirm live Streamlit rendering. Do not publish the private career website without explicit approval.
- **Deferred:** DB1C full migration [#9](https://github.com/yumorepos/network-lab/issues/9), source-vintage backfill [#23](https://github.com/yumorepos/network-lab/issues/23), major model expansion and separate optimization/history products.

**Do not run** `make data`, `make marts`, `make reproducibility` or `make clean-data` against the preserved production directory during audit work. Some of these commands modify or delete local data.

Related canonical documents: [Final scope](FINAL_SCOPE_CONTRACT.md), [Publication readiness](PUBLICATION_READINESS_AUDIT_2026_10.md), [October fact-exposure diagnostic](ACTUAL_MAC_COUNTRY_CONFLICT_FACT_EXPOSURE_2026_10.md), [2026 gated research roadmap](UPGRADE_2026_ROADMAP.md).
