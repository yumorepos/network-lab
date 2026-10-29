# Independent airport ID / city-market label consistency diagnostic (2026-10-29)

**Research-only readback**. No warehouse rebuild or route/model change. Airport codes are NOT stable identity. This guard only determines whether a stored dimension market label is consistent with the stored market ID against the same latest lookup.

## New verified structural hazard

`warehouse/build_marts.py` builds the airport dimension using:

```sql
max(CITY_MARKET_ID) AS city_market_id,
any_value(DISPLAY_CITY_MARKET_NAME_FULL) AS city_market_name
```

These aggregates are **independent**. If the same airport code has multiple latest lookup rows, `max(id)` can choose one city market while `any_value(name)` chooses the name belonging to a different ID. This can mislabel a dimensional record **even when its numeric market ID remains unchanged**. No source data supports treating `any_value` as a name selected from the max-ID row.

Using the exact archived BTS Master Coordinate ZIP, 6,852 latest airport-code strings were inspected. For **16 codes**, the first published name (a plausible `any_value` outcome under source row order) differs from the name belonging to the max market ID. That is **potential** dimension mislabeling; we have not read the production `dim_airport` to establish its actual stored choice. Examples: `SAW` has a max-ID US market but a Turkey market label under the first-row rule; `ISL` has the reverse. The 16 codes are: A5K, BAT, BDN, BGN, ISL, KMC, LAC, LOM, NEU, NY3, SAW, T4X, TIC, TN5, VZL, WA3.

Across the archived 2024, 2025 and Jan-Apr 2026 T-100 ZIPs, **90 scheduled F/L records** with positive departures touch at least one of these 16 code strings; their passenger fields sum to **8,701 operated segment legs** (2024: 38 / 2,645; 2025: 39 / 4,208; Jan-Apr 2026: 13 / 1,848). These are *exposure counts*, not records or passengers proven wrong in the production warehouse. A row with one or both affected endpoints is counted once in these totals.

## Implemented non-mutating evidence gate

`scripts/audit_warehouse_mapping.py::examine` now emits
`airport_dim_market_label_mismatches` **only if** the lookup Parquet exists and the stored `dim_airport` table exposes `city_market_name`. It joins the stored `iata_code` and `city_market_id` to latest Master Coordinate rows with **exactly the same ID**; it reports a mismatch if *no* source label for that code/ID equals the stored label. This avoids guessing which order-sensitive `any_value` outcome materialized.

`scripts/audit_preserved_warehouse.py` includes the count in its small read-only local report. The negative control tests a deliberately mismatched source-code, market-ID and market-name combination and verifies that correcting the label eliminates the diagnostic. Full warehouse source-vintage, numeric feature and replay parity remain UNVERIFIED.

## Corrective acceptance gate

1. Run the preserved-Mac read-only auditor, obtain the small JSON and inspect actual stored `airport_dim_market_label_mismatches` by code/ID.
2. If nonempty, replace the paired aggregation with deterministic *row-consistent* selection (e.g. choose the max-ID row, assert a unique/expected label for that exact ID) in an isolated warehouse build branch.
3. Verify the selected numeric market IDs **do not change**, names now agree, and that published screen/replay outputs and dashboard labels are the expected fixed-snapshot before/after differences.
4. If resolving historic code collisions instead, use source-published stable AirportIDs from the separate official BTS pilot. Do not assume that repairing a label also repairs code identity or market geography.

No production model change is authorized by this check. See [issue #7](https://github.com/yumorepos/network-lab/issues/7).
