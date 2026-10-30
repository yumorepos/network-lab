# OurAirports / BTS legacy country-code conflicts — source-only audit (2026-10-29)

**Scope:** archived source comparison only. This analysis is **NOT** a read of original Mac `dim_airport` country values and does not certify a production mapping error, lost passenger, incorrect itinerary, or changed Network Lab result.

## Inputs and comparison

The original source ZIPs were inspected directly without DuckDB. Match OurAirports `iata_code` to archived BTS Master Coordinate `AIRPORT`; among `AIRPORT_IS_LATEST` rows, select the **maximum stored VARCHAR `CITY_MARKET_ID`** to match the legacy numeric selection rule in `warehouse/build_marts.py`. Compare its published `AIRPORT_COUNTRY_CODE_ISO` with OurAirports `iso_country`. One archived OurAirports code corresponds to one archived source row; duplicate-code source conditions fail closed.

- **5,402** code strings match both source tables and have latest CityMarketIDs.
- **151** source-code pairs have different raw country strings.
- **31** are tentatively classed as **administrative or territory-country coding conventions requiring verification**, e.g. `SJU` OurAirports `PR` vs BTS `US`, `GUM` `GU` vs `US`, `JER` `JE` vs `GB`. `EH`/`MA` is a contested administrative coding convention, not a claim of political sovereignty or acceptance as an equivalent country.
- The other **120** are **unresolved cross-source disagreements**, often explained by airport-code reuse or mismatched reference vintages, *not yet proven production mapping errors*. Examples include `SAW` OurAirports Türkiye vs BTS-selected U.S./Marquette; `BDN` Pakistan vs BTS Saudi Arabia; `KMC` Saudi Arabia vs BTS U.S./Alaska; `SKJ` Indonesia vs BTS U.S.; `PTL` Peru vs BTS U.S.

## Actual archived T-100 source endpoint exposure

Filtered to F/L service classes with positive performed departures. The same source segment can contribute two endpoint observations. Values below are **endpoint passenger-segment legs, not unique travelers, ticket O&D, or production traffic lost**.

| Frozen source period | 31 coding-convention codes: endpoints / legs | 120 unresolved codes: endpoints / legs |
|---|---:|---:|
| 2024 | **8,461 / 18,816,697** | **133 / 429** |
| 2025 | **9,005 / 18,992,417** | **103 / 282** |
| 2026 Jan–Apr | **3,041 / 6,463,714** | **20 / 46** |

The large raw source totals are dominated by legitimate administrative/territory country-code conventions. Treating all 151 source mismatches as an equivalent class of lost traffic would be misleading. **None of the 120 unresolved codes appears as a direct destination** among the three published 200-route screen CSVs; this says nothing about indirect candidate, competition or historical replay consumers.

Input hashes are embedded in the machine JSON. Archived BTS Master Coordinate ZIP SHA-256: `3b429a4bc5950f6f16ff1796b204d10fcd5ad2e97ea39be5cb6476951ff3e6f1`.

## Reproduce

```bash
python -m pytest -q tests/test_audit_cross_source_country_exposure.py

python -m scripts.audit_cross_source_country_exposure \
  --ourairports /private/ourairports/airports.csv \
  --master-zip /private/master_coord.zip \
  --t100-zip /private/t100_2024.zip \
  --t100-zip /private/t100_2025.zip \
  --t100-zip /private/t100_2026.zip \
  --screen-csv data/parquet/outputs/screen_westjet_yyc.csv \
  --screen-csv data/parquet/outputs/screen_alaska_sea.csv \
  --screen-csv data/parquet/outputs/screen_porter_yyz.csv \
  --output /tmp/network-lab-country-exposure.json
```

The script uses only the standard library; it refuses to overwrite source inputs or existing reports and never opens or mutates `warehouse.duckdb`.

## Acceptance gate before any production remediation

1. Run the existing **read-only original Mac warehouse label preflight** for all 8,802 `dim_airport` rows. Its draft label-pair fix [PR #28](https://github.com/yumorepos/network-lab/pull/28) is **not** a geographic identity fix.
2. Measure actual `dim_airport.iso_country`, numeric CityMarketID and source-country agreement at the same source vintage, with administrative exceptions explicitly documented and reviewed. Country differences alone do not prove incorrect market assignments.
3. Reconcile historical airport codes to **source-published AirportIDs** for relevant source years, then identify affected airport/metro/candidate/competition/replay consumers; don't impute historical AirportIDs from present codes.
4. Rebuild only an isolated candidate warehouse if the consumer impact justifies it, and check 200 published screening rows plus 463 historical replay decisions before proposing adoption.

**Do not automatically normalize country codes, select a country by maximum ID, backfill historic geography, or replace frozen historical snapshots.** See [issue #30](https://github.com/yumorepos/network-lab/issues/30), [issue #7](https://github.com/yumorepos/network-lab/issues/7), [issue #14](https://github.com/yumorepos/network-lab/issues/14).
