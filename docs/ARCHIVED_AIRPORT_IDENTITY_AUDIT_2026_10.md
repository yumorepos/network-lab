# Archived airport identity: reproducible source-only audit (2026-10-29)

**Status:** research evidence only. No production mapping, historical replay, study config, DuckDB warehouse or screened output was modified.

## Reproduce privately from archived ZIPs

Place `master_coord.zip`, `t100_2024.zip`, `t100_2025.zip`, and `t100_2026.zip` in a directory outside the repository. Then run:

```bash
python -m pytest tests/test_archived_airport_identity.py -q
python -m scripts.audit_archived_airport_identity --source-dir '/path/to/archives' --output-dir '/tmp/network-lab-identity-20261029'
```

The script checks ZIP CRCs, reads the archived 14-field T-100 passenger-service rows, records SHA-256 digests, and compares the legacy latest-code `max(CITY_MARKET_ID)` with a *candidate* inferred only where historical code/country/month validity produces a unique airport ID. It writes a bounded aggregate JSON outside the source directory, refusing to overwrite an existing output.

## Results on preserved user source files

| Period | Scheduled passenger-service rows | Candidate differing row mappings | Passenger-segment legs in differing rows |
|---|---:|---:|---:|
| 2024 | 488,806 | 4 | 86 |
| 2025 | 511,546 | 0 | 0 |
| 2026 Jan–Apr | 169,501 | 1 | 1 |
| **Total** | **1,169,853** | **5** | **87** |

Archived Master Coordinate contains **17** current/latest airport-code strings with more than one distinct `CITY_MARKET_ID`. The five differing rows involve `SAW` (historical Turkey versus US code reuse) and `VZL` (historical US metro ambiguity). These are source-level comparisons, **not measured production warehouse misjoins or changed verdicts**.

Verified file SHA-256:

- `master_coord.zip`: `3b429a4bc5950f6f16ff1796b204d10fcd5ad2e97ea39be5cb6476951ff3e6f1`
- `t100_2024.zip`: `a423f65baa9b4cc2a26e0742d3436888c24cca248f88a76eaecd4771054fa29d`
- `t100_2025.zip`: `83802dac25a7cdc6db55810fd642770913b94727a72ed4d8cc0a20c49c68fa53`
- `t100_2026.zip`: `3a050f1cc8c5daf9aa641f314c49cddbc25f875114113d6b02b803e9caea2c6f`

## Material limitations and stop conditions

1. These archived T-100 ZIPs omitted `OriginAirportID`, `DestAirportID`, `OriginCityMarketID`, and `DestCityMarketID`. Code/country/date matching **must never be substituted for the source-published stable IDs**.
2. T-100 passengers are operated segment legs, not unique travelers or ticket O&D. The 2026 archive covers January–April, not a full year.
3. An ambiguous historical match remains unresolved; do not select the largest city-market number or overwrite a model input.
4. This check does **not** read the preserved Mac warehouse, quantify consumer reach into candidate and competition joins, reconstruct a model, or compare frozen replay verdicts.
5. Official July 2026 T-100 stable IDs were checked separately in Stage B; never add their July row counts to these earlier, different-vintage source ZIP totals.

## Required next decisions

- **Issue #7:** Extract source-published stable AirportIDs in an isolated research-only vintage, then compare existing consumers side by side before implementing a production map correction.
- **Issue #14:** Independently resolve ambiguous BTS CityMarketID to Census CBSA mapping using appropriate Census geography; do not force a one-to-one map of multiple legitimate metros without evidence.
- **Issue #9:** Keep post-July-2025 DB1C entirely separate from legacy quarterly DB1B until actual multi-table ticket-market-coupon-segment key and sample reconciliation passes.
- **Freshness:** Audit partial-year T-100 cache (current ingest skips existing Parquet) using source-release-vintage metadata. Never refresh the historical frozen snapshot in place.
- **Full warehouse:** Only if warranted by measured consumer risk, build a *separate* candidate DuckDB from the same immutable source snapshots and run model, test, reproducibility, and 200-row screening plus 463-row replay before/after checks.

**Gate:** The source-only audit is reusable; **production correction remains blocked** without a sourced ID-level comparison and consumer-impact evidence. See [issue #7](https://github.com/yumorepos/network-lab/issues/7) and [publication audit](PUBLICATION_READINESS_AUDIT_2026_10.md).
