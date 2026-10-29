# Carrier-brand historical source audit — 2026-10-28

**Status:** Documentary correction and measured exposure, not a model re-estimate. Source counts are **T-100 operated scheduled passenger segment legs**. The marketing brands are **not** observable in T-100; do not interpret these as known brand attribution errors or changes in published Network Lab verdicts.

## Why this audit was necessary

`models/carriers.py` resolves static single-brand operators using `data/reference/carrier_families.csv` and multi-brand operators from a **fixed 2024 DB1B calendar year**, rather than effective-dated carrier agreements. The replay already discloses this exception in `replay/vintage.py::carrier_brand_vintage` and `docs/LIMITATIONS.md`.

However, its Air Wisconsin timeline was **reversed**. This audit corrects the factual description and makes the temporal evidence explicit; it does **not** fix production mapping or claim improved predictive performance.

## Verified company disclosures and scope boundaries

| Operator | Verified relationship dates | Relevance |
|---|---|---|
| Mesa (`YV`) | Mesa agreed to wind down American Eagle operations by **2023-04-03** while expanding United Express; it operated for both brands during the transition. | A static `YV -> UA` cannot correctly represent all pre-April 2023 activity. |
| Air Wisconsin (`ZW`) | Flew for United through **early June 2023**, began American Eagle flying **March 2023**, terminated American agreement **2025-04-03**. Later EAS/charter activity should not automatically inherit American/United branding. | Prior docs falsely described American through 2023, then United. The direction is the opposite. |
| Republic / Mesa corporate merger | Completed **2025-11-25**; subsidiary airline operating certificates continued. | Corporate group ownership is **not** a reliable marketing-carrier lookup key. |

SEC primary evidence:
- Mesa December 2022 announcement: https://www.sec.gov/Archives/edgar/data/810332/000156459022039477/mesa-ex991_6.htm
- Air Wisconsin FY2024/FY2025 filing: https://www.sec.gov/Archives/edgar/data/899394/000089939426000011/hrbr-20241231.htm
- Air Wisconsin FY2025 filing: https://www.sec.gov/Archives/edgar/data/899394/000089939426000033/hrbr-20251231.htm
- Republic/Mesa merger: https://www.sec.gov/Archives/edgar/data/810332/000119312525303961/d937766dex991.htm

## Real-data operator exposure from uploaded T-100 source ZIPs

Source: `data/raw/t100/t100_{year}.zip`, 2022–2026, filtered to `CLASS IN ('F','L')`, positive `DEPARTURES_PERFORMED`. **2026 is Jan–Apr only** in this uploaded source snapshot. These counts are operator traffic, not brand-specific traffic.

| Source year | Mesa YV departures | Mesa YV passenger-segment legs | Air Wisconsin ZW departures | Air Wisconsin ZW passenger-segment legs |
|---|---:|---:|---:|---:|
| 2022 | 120,233 | 7,825,703 | 68,523 | 2,858,071 |
| 2023 | 100,083 | 6,214,266 | 59,210 | 2,469,242 |
| 2024 | 92,762 | 5,675,597 | 52,587 | 2,154,891 |
| 2025 | 84,543 | 5,053,331 | 11,450 | 417,794 |
| 2026 Jan–Apr | 24,894 | 1,447,496 | 997 | 13,359 |

**Exposure ≠ erroneous assignment.** For example, the 2022 Mesa total includes both Mesa-operated American and United service. One cannot infer a marketing brand for each T-100 segment from `UNIQUE_CARRIER` alone. The 2023 transition contains overlap months and cannot be safely expressed as a single year-to-brand mapping.

A further source-vintage mismatch exists: the brand resolver defaults to the **2024 DB1B** year while the current T-100 source extends through April 2026. This is deliberately documented for historical replay as a residual lookahead, but it should not be described as point-in-time known evidence.

## Recommendation and safety gates

1. Preserve `replay/vintage.py` and `docs/LIMITATIONS.md` evidence disclosures. Correct factual chronology only, with the SEC URLs retained here.
2. Do not assign historical brand attribution simply from operated T-100 flights. Instead, require `operator, origin, destination, operating_month, brand, supporting_source, effective_start, effective_end`; allow **unresolved**.
3. Evaluate brand assignment at the **decision cutoff** when historical replay requires point-in-time inputs. Use a comparable DB1B source vintage (and avoid splicing DB1B into DB1C without a published methodological bridge).
4. Once the local `warehouse.duckdb` is accessible, run a side-by-side join: incumbent service, one-stop competition, route candidates, and published verdicts, using unchanged source snapshots.
5. If no previously published candidate/verdict changes, record a zero **measured** difference; do not infer no impact simply because current output rows look internally consistent.
6. Do not change the frozen model, data artifacts, historical replay or deployed app as part of this documentary correction.

**Disposition:** Documentation chronology error confirmed; source-exposed operators counted; downstream production impact **unmeasured**.
