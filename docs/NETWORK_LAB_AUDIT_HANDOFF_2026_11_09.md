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

## Independent GSP/JAN geography verification — November 9

**Research result, no model correction:** The two BTS city markets **31871 Greenville/Spartanburg, SC** (GSP) and **32448 Jackson/Vicksburg, MS** (JAN) are broader commercial city-market labels, whereas the 2023 Census geography supplies distinct county-based CBSAs. An apparent choice between two CBSAs does **not** prove the current assignment is a wrong numeric ID; replacing it without a defensible catchment rule risks double-counting or relabeling unlike units.

- **GSP:** Current derived choice CBSA **24860 Greenville-Anderson-Greer** vs alternative **43900 Spartanburg**; both are separate units in **CSA 273**. Official [GSP airport master plan](https://gspairport.com/wp-content/uploads/2022/07/GSP-Executive-Summary-for-Web-Viewing.pdf) documents that airport property spans Greenville *and* Spartanburg counties. The [Census 2023 metro table](https://tigerweb.geo.census.gov/tigerwebmain/Files/bas25/tigerweb_bas25_metro_cbsa_2023_acs23_us.html) lists the separate core-based geographies, and the [Census county table](https://tigerweb.geo.census.gov/tigerwebmain/Files/acs25/tigerweb_acs25_county_2025_bas25_sc.html) labels Greenville County 24860 and Spartanburg County 43900. This is a genuine **cross-unit/coverage simplification**, not demonstrated wrong airline market passenger totals.
- **JAN:** Current published screen label **Jackson, MS / CBSA 27140**, alternative **Vicksburg 46980**. Official [Rankin County plan](https://www2.rankincounty.org/CommDev/rccp2024.pdf) places JAN in Rankin County, while the [Census 2024 county table](https://tigerweb.geo.census.gov/tigerwebmain/Files/bas25/tigerweb_bas25_county_2024_acs24_ms.html) assigns Rankin County **27140** and Warren County/Vicksburg **46980**. Jackson is therefore a geographically reasonable **airport-location** CBSA, even though BTS CityMarketID 32448 refers to the broader Jackson/Vicksburg city-market label. It does not automatically validate the modeled market-size proxy.
- **Actual direct study exposure already measured:** in the May 2025–April 2026 source-US hub diagnostic, `SEA→GSP` had 1 reported segment row / 189 passenger-segment legs; `YYZ→GSP` had 2 rows / 35 legs. No qualifying `YYC/SEA/YYZ→JAN` recent direct row appeared. These are source segments and **not** marketing-brand or historical replay coverage.
- **Published result exposure:** Both GSP and JAN are listed as screened `dest_airport` in **all three** frozen study screens (six candidate rows). Every verdict is `PASS`; margins remain the original computed values and **were not corrected/recomputed**.
- **Scope definitions:** BTS [AirportID and CityMarketID documentation](https://www.transtats.bts.gov/Fields.asp?gnoyr_VQ=FMF) distinguishes a stable AirportID from the commercial city market. Census [CBSA guidance](https://www.census.gov/programs-surveys/metro-micro/about.html) defines the county-based statistical areas. The units cannot safely be interchanged or assumed additively exhaustive for an airline catchment.
- **Implementation gate:** CI has now passed for an additional read-only **GSP/JAN diagnostic and synthetic tests** in draft [PR #35](https://github.com/yumorepos/network-lab/pull/35) (commit `2edd2c3bb3e6ea6dbff8c4858f5e06f6991b64b6`). It reads source AirportIDs, actual stored geography, recent segment exposure and six committed screen rows. The real original-Mac read-only run **completed on November 9, 2026**, with no warnings and the expected six screen rows; as designed, it does not produce a counterfactual verdict delta.

**Decision after local readback:** retain GSP and JAN's current mapped IDs as *documented source-backed proxies*, not as validated all-catchment demand geographies; no evidence-backed mapping change is justified. Keep the broader geography/candidate-consumer issue open. Any hypothetical source-supported correction requires an isolated warehouse and full 200+463 decision comparison; do not rewrite the original.

## Fourth Mac audit: GSP/JAN source-ID and actual stored CBSA gate COMPLETE

**Execution:** November 9, 2026, preserved original Mac DuckDB opened `read_only=True` by research-only `scripts/audit_gsp_jan_geography.py` (draft [PR #35](https://github.com/yumorepos/network-lab/pull/35), blob SHA `1b6295f8312973d662307e802fc24efb6a4e0388`; the user's uploaded script matches the exact Git blob). Local report folder `NetworkLab-GSP-JAN-20261109-173958`; private ZIP SHA-256 `e4f904e8d33fab2e32a7419f48b51531bbde1d5c3040298fa73f8bcfd7faf7b8`. **The ZIP, local path contents and original DuckDB are not committed.** The script read existing output CSVs; no data, model or replay files were written.

| Airport | Archive BTS AirportID | BTS CityMarketID (stored = source) | Actual mapped CBSA | Actual stored source name |
|---|---|---|---|---|
| GSP | `11996` | `31871` | `24860` Greenville-Anderson-Greer, SC | Greenville/Spartanburg, SC |
| JAN | `12448` | `32448` | `27140` Jackson, MS | Jackson/Vicksburg, MS |

The archived BTS Master Coordinate includes **two latest-flag variants of each airport code**, but **both variants agree on the same AirportID and CityMarketID for each airport**. All four reference component CBSAs are present: GSP 24860 population 996,680; Spartanburg 43900 population 395,934; Jackson 27140 population 606,178; Vicksburg 46980 population 42,105. The mapping method is `token` in both cases. **Zero script warnings**.

The May 2025–April 2026 source-US, scheduled F/L, positive-departure direct hub window contains exactly **three rows to GSP**: SEA→GSP May 2025 (189 passenger-segment legs; one departure), YYZ→GSP October 2025 (2 legs; one departure), YYZ→GSP November 2025 (33 legs; one departure): **224 passenger-segment legs / 3 departures in total**. No qualifying YYC/SEA/YYZ→JAN segment was present in that narrow window. These sparse rows may include reporting categories outside the regular airline study brand rules; neither passenger O&D nor forecast impacts follow from them.

The read-only report matched exactly **six published GSP/JAN candidate rows**, all `PASS`. Frozen base-case margin percentages:
- YYC: GSP **−1600.1%**, JAN **−1089.5%**
- SEA: GSP **−819.8%**, JAN **−784.2%**
- YYZ: GSP **−559.5%**, JAN **−1676.4%**

These extreme modeled negatives are reported as **existing screening estimates**, not independently validated route economics. No screens or 463 replay rows were recomputed, and there is **no measured hypothetical geographic correction**. The source's four explicit false certification flags (`source_stable_airport_id_snapshot_certified`, `bts_citymarket_cbsa_semantics_certified`, `brand_resolved_served_competition_recomputed`, `six_screen_verdicts_recomputed`) remain **false**.

**Interpretation:** Identity consistency is verified **for these two codes in this archived lookup and actual stored warehouse**. It does not establish source-stable ID correctness across every historical vintage, entire city-market population allocation, marketing-brand connections or a full production accuracy certificate. GSP is an airport whose broader region spans two CBSAs, and JAN sits in the Jackson CBSA despite the broader BTS market label. **No demonstrated production defect supports remapping either airport.**

## Updated stop/continue decision

1. **CLOSE THIS BOUNDED GSP/JAN READ-ONLY CHECK AS COMPLETED.** Keep GSP→24860 and JAN→27140 unmodified; clearly disclose cross-geography simplification instead of claiming catchment-wide population truth.
2. **DO NOT merge the label-only [draft PR #28](https://github.com/yumorepos/network-lab/pull/28)** or modify city-market IDs, frozen inputs, model results or 463 replay decisions. **Keep issues #7, #14 and #30 open** for unsolved general historical/cross-source identity cases.
3. Research [draft PR #35](https://github.com/yumorepos/network-lab/pull/35) contains synthetic-tested, locally exercised read-only tools and may be reviewed as a standalone research utility. The evidence is recorded here on [draft PR #34](https://github.com/yumorepos/network-lab/pull/34). **Neither needs to be merged automatically** to complete the immediate audit decision.
4. **Next priority: portfolio presentation**, not more diagnosis. Build one recruiter-friendly Network Lab case study using the locked 200-market study, point-in-time replay, fixes that worsened results, and the bounded negative predictive finding. Live Streamlit deployment verification and presentation review are still separate tasks.
5. **Only reopen a geography correction if new independent point-in-time source evidence identifies a material affected consumer path.** Before any production change, use a separate candidate warehouse and compare all 200 screens plus 463 historical decisions using fixed-source reproducibility gates. Do not auto-sum two CBSAs or infer a correction from a bigger candidate population.

## Near-term roadmap (approximately 5 focused hours per week)

- **Completed:** three broader source/warehouse audits plus the GSP/JAN source-ID/local-CBSA run; read-only reports retained privately; documentation/research draft CI passed.
- **Week 1 (3–5 hours):** finalize a one-page case study and three strong visuals: workflow, audited claim/method result, and replay-vs-demand comparison. Make limitations explicit.
- **Week 2 (2–4 hours):** verify the current Streamlit rendering and committed data/artifact parity, polish recruiter narrative and portfolio screenshots. No new model fitting.
- **Optional later, gated:** revisit DB1C compatibility, 2024 source-vintage rows and ambiguous CBSA city-market semantics only if practical job relevance or independent contradictory source evidence justifies the effort.

**Final recommendation: stabilize Network Lab as a credible research artifact and switch effort to the portfolio and the next distinct optimization project.** A cautious finding is a feature of the work, not a defect to optimize away.
