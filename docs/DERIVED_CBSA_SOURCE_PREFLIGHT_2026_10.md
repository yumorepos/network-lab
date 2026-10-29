# Source-side city-market to CBSA preflight (2026-10-29)

**Disposition: research/detection only.** No data-mart, route model, replay, input snapshot, committed output, or dashboard change is authorized by this document.

## Why this is important

The production rule in `warehouse/metro_map.py` joins a BTS `CITY_MARKET_ID` to Census CBSAs via city token and state, resolving ties by **largest CBSA population**. A single BTS city market may legitimately contain multiple CBSAs. An arbitrary one-to-one selection is not a proven spatial crosswalk and may change eligible metro anchor points, capacity and demand allocations.

The original 4.836 GiB DuckDB database cannot be transferred to Drive. **It is not required for the source preflight.** The archived input Parquet files are small (about 1.1 MB Master Coordinate and 37 KB metro population).

## Command on a local checkout with the archived inputs

```bash
python -m pytest -q tests/test_metro_source_preflight.py
python -m scripts.audit_metro_source_preflight \
  --lookup data/parquet/lookups/master_coord.parquet \
  --metros data/parquet/census/metro_pop_income.parquet \
  --source warehouse/metro_map.py \
  --output /tmp/networklab-metro-preflight.json
```

No warehouse writes or downloads. The script refuses to overwrite a prior report or write inside any input source directory. It loads the *literal current OVERRIDES dictionary* without executing warehouse code and reports all candidate CBSAs, source-name anomalies, override fallbacks and tie-break winners.

## Independently verified archived source evidence

The derived `metro_pop_income.parquet` was read and inspected independently from its Apache Parquet metadata, Snappy dictionaries and selected data pages. It contains **935 rows, 935 distinct CBSA codes and names**, all of whose code/name pairs agree with **935 of 935** entries in the official July 2023 Census `list1_2023.xlsx` used in the archive. The derived table **includes micropolitan areas**. Consequently, the correct source-universe warning is **13 token ambiguities**, not only the four found after restricting to the 393 metropolitan-only CBSAs.

From preserved T-100 ZIPs (2024, 2025, Jan-Apr 2026), these 13 names cover **9,217,264 U.S.-origin scheduled passenger-segment legs and 126,241 departures** across 10 traffic-bearing city markets. The traffic estimate explicitly omits 44 U.S.-origin source rows whose latest airport code was not uniquely linked to a city market; other historical code/identity errors remain possible. This is **exposure**, not count of misassigned or lost passengers.

| BTS market ID and name | Highest-population choice from exact derived table | Alternative | Segment legs in source periods |
|---|---|---|---:|
| 31871 Greenville/Spartanburg, SC | 24860 Greenville-Anderson-Greer (996,680) | 43900 Spartanburg (395,934) | 3,397,090 |
| 31003 Cedar Rapids/Iowa City, IA | 16300 Cedar Rapids (278,677) | 26980 Iowa City (182,711) | 1,835,437 |
| 33158 Midland/Odessa, TX | 33260 Midland (188,766) | 36220 Odessa (170,022) | 1,760,772 |
| 32448 Jackson/Vicksburg, MS | 27140 Jackson (606,178) | 46980 Vicksburg (42,105) | 1,416,646 |

These **selected CBSAs are reconstructions of the stated code rule from archived inputs**, not direct readback of the original `map_citymarket_cbsa` or an outcome counterfactual. All verified source CBSA titles match the official Census workbook; the workbook classification matters because `dim_metro_us` contains metro **and micro** entries.

`OVERRIDES['Aspen, CO']='Glenwood Springs'` has no match in this archived 2023 CBSA universe. The corresponding BTS city-market ID has 866,838 source passenger-segment legs in the same periods. This does not by itself demonstrate the corresponding airport was excluded from published routes.

### Source hashes (SHA-256)

- Census `list1_2023.xlsx`: `952c4b1e78acbb54e6ec9412434b7602fedacbf021736351a63c181bdb753629`
- Master Coordinate `master_coord.zip`: `3b429a4bc5950f6f16ff1796b204d10fcd5ad2e97ea39be5cb6476951ff3e6f1`
- T-100 2024/2025/2026 ZIPs: `a423f65baa9b4cc2a26e0742d3436888c24cca248f88a76eaecd4771054fa29d`, `83802dac25a7cdc6db55810fd642770913b94727a72ed4d8cc0a20c49c68fa53`, `3a050f1cc8c5daf9aa641f314c49cddbc25f875114113d6b02b803e9caea2c6f`.

## What remains blocked

1. Run the preflight on the **exact archived transformed inputs** and independently compare its reconstructed keyset and selected CBSA IDs with `map_citymarket_cbsa` on the preserved Mac warehouse or on a source-fixed isolated reproduction.
2. Investigate BTS city-market versus county-boundary meaning for all exposed IDs, rather than force an arbitrary geography merge or duplicate population.
3. Evaluate affected airport anchors, candidate served-market elimination, demand features, carrier competition, study rows and point-in-time replay by fixed snapshot; require *every changed decision and metric* to be recorded.
4. Keep DB1C and modern T-100 source vintages separate from the frozen baseline. Do not infer predictive improvements or new verdicts from mapping changes alone.

See [issue #14](https://github.com/yumorepos/network-lab/issues/14), [issue #7](https://github.com/yumorepos/network-lab/issues/7) and [publication readiness audit](PUBLICATION_READINESS_AUDIT_2026_10.md).
