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

## Second Mac audit: preserved-warehouse inventory and mapping (November 9)

This follows the country/source-endpoint audit above. The user ran `scripts.audit_preserved_warehouse` locally against the **same preserved original** via `duckdb.connect(..., read_only=True)`. Private input: `NetworkLab-Mapping-20261109-154617.zip`, SHA-256 `cdfc267b4f2d4997327dbb40f55d6e8ae5b998f8e83c6d036117079efcdea76e`. The ZIP contains only a summary and JSON diagnostics. **Do not commit the original private data or this ZIP.**

| Actual Mac warehouse check | Observed |
|---|---:|
| Warehouse bytes | 5,192,560,640 |
| Raw source tree | 218 files / 2,961,148,575 bytes |
| Parquet tree | 164 files / 1,142,110,808 bytes |
| T-100 `fact_segment` | 13,630,379 rows |
| DB1B `fact_od_market` | 173,741,663 rows |
| `dim_airport` / `dim_metro_us` / `map_citymarket_cbsa` | 8,802 / 935 / 815 rows |
| Duplicate airport codes / duplicate city-market-to-CBSA rows | 0 / 0 |
| Latest lookup codes with multiple stable AirportIDs or CityMarketIDs | 36 (17 multiple market IDs; 19 same market, multiple AirportIDs) |
| Actual stored CityMarketID/name disagreements | 10 |
| US-country airport rows lacking a city-market-to-CBSA join | 1,040 |
| Top-100 historical US airport endpoint gaps | 100 **returned records, capped by SQL LIMIT 100** |
| Top-100 historical unmapped US destination-metro traffic | 100 **returned records, capped by SQL LIMIT 100** |
| Internal T-100 month gaps | 12, **2020-01 through 2020-12 only** |

**Interpretation:** The 2020 exclusion is an existing documented scope choice, not proof of an ingestion failure. `map_citymarket_cbsa` has **no duplicate keys**, but its one-to-one value can still be *geographically wrong*: the builder uses hand-written overrides, token matching, then highest-population choice, so zero duplicate rows is not a correctness certificate. The 1,040 unmapped airport rows are **not 1,040 proven eligible candidate markets or dropped airline passengers**; nonmetropolitan, Alaska, territorial and historic code cases require separate treatment.

Examples worth triage: `GUM` (47,960,300), `STT` (20,824,041), `SPN` (19,360,859) and `STX` (7,771,495) have large **all-years** unmapped-destination segment-leg totals but are territorial or special-scope cases, not straightforward US CBSA failures. `ASE` has 7,760,885 historical unmapped destination segment legs and deserves a specific Aspen/CBSA mapping review. `PFN` is a large historical unmatched-code example; this diagnostic does not establish a current route verdict delta. The `PBI/DJT` diagnostic groups both code strings **together by year**, so it cannot establish which code has a valid, vintage-correct AirportID, and it cannot establish lost traffic or a changed verdict.

The ten label inconsistencies are `BAT, BDN, BGN, ISL, KMC, LAC, LOM, NEU, SAW, TIC`. `SAW`'s stored city name identifies Istanbul while the stored numeric market source identifies Marquette, illustrating why draft PR #28 is not safe to adopt as an identity repair. Both actual Mac audit reports explicitly say the warehouse was opened read-only and the original model outputs were not recomputed. The report's seven small SHA-256 output hashes are a **local fingerprint**, not independently compared to `main` here.

**Next narrow gate (issue #14, then #7):** (a) report **latest-12** operated-segment traffic, by hub and destination, where the current CBSA join fails or maps ambiguously; separate territorial/rural/retired codes; (b) test source-vintage `ASE`, `PFN` and `PBI/DJT` mapping provenance, and the 10 source-ambiguous high-traffic markets from issue #14; (c) trace only evidence-backed cases through actual candidate, served-market and competition consumers. The present all-years top-100 lists are **not exhaustive** and should never be added as if they were a complete error count. Conditional source-stable-ID validation and isolated counterfactual come **after** this consumer evidence. Freeze the original 200 screens and 463 historical replay decisions until that gate.

### Follow-up implementation status

A separate *draft, unmerged* [PR #35](https://github.com/yumorepos/network-lab/pull/35) now contains the narrow **read-only** `scripts.audit_hub_cbsa_consumer_exposure` runner plus synthetic tests. [GitHub CI passed](https://github.com/yumorepos/network-lab/actions/runs/42698825568) on commit `706335980eb106e35c2c1d9483b6dac83e4c7a18`. The script has **not** been run against the actual original Mac warehouse at the time of this handoff; the real consumer result remains unknown. This runner only measures recent source endpoint mapping, not full candidate eligibility, brand reconstruction or counterfactual changes.

## Third Mac audit: actual recent YYC/SEA/YYZ CBSA source-consumer exposure

The user independently executed the **read-only** `scripts.audit_hub_cbsa_consumer_exposure.py` from research [draft PR #35](https://github.com/yumorepos/network-lab/pull/35) on the preserved Mac warehouse on November 9, 2026. Private upload: `NetworkLab-Hub-CBSA-20261109-161909.zip` (SHA-256 `48484f3ca48cf300b7eb4f7c9fba9bfb2ce32f3d1d0efc7d47dce707449f5857`). **Do not commit the ZIP or original warehouse.** The JSON and CSV agree across all **383 distinct hub/destination/status groups** and numerical source sums; six hub/status aggregates reconcile.

**Latest 12 reported months:** May 2025–April 2026 (`latest_reported_month = 202604`, exclusive cutoff `202504`); direct flights from YYC/SEA/YYZ to source-reported U.S. destinations; scheduled `F/L` categories with positive operated departures. This is *not* an airline-brand, candidate eligibility, ticket O&D, one-stop reconstruction, or replay query.

| Hub | Direct hub/destination groups | No CBSA | No-CBSA segment-passenger legs | All source segment legs | % |
|---|---:|---:|---:|---:|---:|
| YYC | 67 | 1 | 786 | 1,814,314 | 0.043% |
| SEA | 161 | 7 | 30,288 | 21,951,725 | 0.138% |
| YYZ | 155 | 14 | 1,443 | 5,510,043 | 0.026% |
| **Total** | **383** | **22** | **32,517** | **29,276,082** | **0.111%** |

The **22** missing-CBSA hub groups represent **20 distinct destination codes**, 168 source segment rows and 475 departures. SEA→SIT (Sitka, AK) contributes **28,730** of 32,517 unmapped source passenger-segment legs; other cases include SEA/YYC/YYZ→IFP and YYZ→BED/TEB. Several reflect small, rural/Alaska/specialized airport services; do not assume they are eligible metros under the model's 400k population rule. None of these 20 codes appears as a direct `dest_airport` in the **200 published screening rows**, verified against the three canonical committed screen CSVs, but **indirect competitive, already-served, and geographic effects are still unmeasured**.

**Focused source mappings:** `PBI` is currently CBSA-mapped (33100) in the stored warehouse; the report does not establish point-in-time `PBI/DJT` AirportID correctness. `SJU` is CBSA-key-mapped (41980) and is a PR/US convention, yet its focus lookup records **null census population**; mapped key is not identical to complete demographic eligibility. `ASE` lacks CBSA mapping, but **no current qualifying direct hub→ASE destination** appears in this window. Historical PFN and territorial GUM/SPN/STT/STX exposures cannot automatically be treated as current eligible U.S. metros.

**Direct published candidate overlap with wrong-but-present geography:** the earlier source-ambiguous markets Greenville/Spartanburg (selected CBSA Greenville-Anderson-Greer, airport GSP) and Jackson/Vicksburg (selected Jackson, MS, airport JAN) each appear as `dest_airport` in **all three** canonical published study screens. Thus **six source-ambiguous candidate rows** are already visible, despite zero overlap between the 20 *missing*-CBSA codes and published destination codes. All six currently say PASS under frozen assumptions; **no corrected geographic counterfactual has been measured**. The source audit's other named ambiguous markets CID and MAF appear in recent hub flight segments, though they do not appear as the published `dest_airport` under those code strings. This is a reason to prioritize **issue #14's geographic semantics** before publishing a full data-accuracy certification, not a reason to change a verdict directly.

**Decision:** This closes the narrow *direct missing-CBSA source-endpoint measurement only*, **not** the broader CBSA geography/consumer-impact issue #14. The higher-value next check is a scoped read-only **wrong-but-present CBSA** audit for the ten source-ambiguous traffic-bearing markets in #14, plus the Aspen override, using original source geography/IDs. Before considering any fix, trace those markets into eligible 3-study candidates, brand-resolved served exclusion and reconstructed one-stop competition; stop if no credible material impact. Do not rebuild, update the original warehouse or change 200 screens/463 replay decisions. On the current evidence, **prioritize portfolio readiness over broad model work**.

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
