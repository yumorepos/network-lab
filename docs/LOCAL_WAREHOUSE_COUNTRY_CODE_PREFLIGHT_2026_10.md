# Mac warehouse source-country readback added to safe label preflight

**Research-only; never modifies the original warehouse.**

The first preserved Mac audit established 10 `dim_airport` city-market ID/name inconsistencies. Its country field, however, was not included in the returned report. An independent comparison against the **archived Drive OurAirports** country codes and the archived BTS Master Coordinate source finds that **7 of those 10** have country disagreements for the *selected numeric CityMarketID*: BDN PK/SA, BGN RU/PH, KMC SA/US, LAC MY/PG, LOM MX/ZA, NEU LA/US, SAW TR/US. The other three (BAT, ISL, TIC) have agreeing source countries for their selected IDs.

This is a **source-vintage country warning**, not yet an independently observed `dim_airport.iso_country` mismatch from the preserved Mac warehouse. Draft builder [PR #28](https://github.com/yumorepos/network-lab/pull/28) would ensure an ID and label come from the same source row **without changing numeric IDs**, leaving those seven geographic concerns unresolved. That is why PR #28 must remain unmerged until an identity review.

## Enhanced read-only preflight

`scripts.audit_airport_label_candidate` now also reads **actual stored `dim_airport.iso_country`** and the `AIRPORT_COUNTRY_CODE_ISO` field **from the exact source row that supplies the candidate numeric CityMarketID**. The returned small JSON provides:

- `original_warehouse_country_disagreements` — all observed source/warehouse country-code disagreements.
- `country_coding_conventions_to_verify` — provisional territory/administrative conventions (PR/US, GG/GB, etc), explicitly **not** certified equivalent or necessarily errors.
- `unresolved_original_warehouse_country_conflicts` and its count — source/warehouse disagreements not classed among those conventions.

The preflight's `PASS_DIMENSION_PROJECTION` status is now **blocked** when any unresolved country-code mismatch is present, even if the selected numeric IDs and all 10 label corrections pass. The launcher still produces a usable report with `REVIEW_REQUIRED` (exit 2) in this case. It must **not be interpreted as a broken audit** or reason to alter local data.

## Running without uploading DuckDB

Use the separately delivered `NetworkLab-Label-Preflight.command` on the user's Mac:

```bash
bash "$HOME/Downloads/NetworkLab-Label-Preflight.command"
```

The launcher shallow-clones the current default branch to a **separate** Desktop folder, uses the existing project Python environment, opens the preserved `warehouse.duckdb` **read_only=True**, and writes a **new small Desktop report ZIP**. The original project and data are not modified.

Upload only the small ZIP. **Do not** upload the 5.19 GB database, overwrite source data, run `make all` in the preserved project, or merge builder PR #28 solely because this diagnostic works.

## Acceptance boundary

Actual country readback and source-row consistency are necessary but not sufficient. Resolving code reuse requires source-published historical AirportID and per-year CityMarketID lookup at the appropriate time grain. The 200 published screening rows and 463 historical replay decisions require isolated fixed-source before/after model runs before production adoption. See [issue #7](https://github.com/yumorepos/network-lab/issues/7), [issue #30](https://github.com/yumorepos/network-lab/issues/30), [source-country audit](CROSS_SOURCE_COUNTRY_IDENTITY_AUDIT_2026_10.md).
