# Actual Mac warehouse country-conflict *fact* exposure audit

**2026-10-29 — read-only analysis gate.** The user's Mac country/label preflight established 140 actual stored `dim_airport.iso_country` vs selected BTS market-source-country disagreements: **28** provisional administrative/territorial coding conventions and **112** unresolved. Its ZIP SHA-256 is `7303ff6d6ec37f6fc0f1da72b66a6af2865a5ab1688475aea7eaad39108887b0`. The read-only actual Mac audit is evidence of dimension/source disagreement, **not proof of passenger loss or verdict changes**.

## Why this follows the first preflight

The preliminary deterministic label-only builder candidate in draft [PR #28](https://github.com/yumorepos/network-lab/pull/28) preserves all **8,802** numeric CityMarketIDs and alters exactly the ten expected labels, yet **seven of those ten** (BDN, BGN, KMC, LAC, LOM, NEU, SAW) have unresolved stored-country/source-market-country contradictions. These code strings can be associated with different physical airports in different vintages. Merging the label-only patch and rebuilding before checking traffic might conceal a *geographic* misjoin. PR #28 must remain **on hold**.

The independent archived source-only CBSA audit suggests 81/112 unresolved actual country conflict codes have a BTS-selected **US market** but a non-US stored airport country; **24** of these had a *source-reconstructed* CBSA selection. The actual Mac `map_citymarket_cbsa` and `fact_segment` consumers have NOT yet been interrogated for these 112 codes. Even among CBSA-mapped IDs, this is **source-code risk**, not 24 proven wrong route predictions. None of the 140 codes directly matches the published 200 screen `dest_airport` fields (verified with recovered CSVs). A one-stop or already-served market can nevertheless be affected indirectly.

## New Mac read-only query

```bash
python -m pytest -q tests/test_audit_country_conflict_fact_exposure.py
python -m scripts.audit_country_conflict_fact_exposure \
  --root "$HOME/Projects/network-lab" \
  --output-dir "$HOME/Desktop/NetworkLab-Country-Fact-Exposure-NEW"
```

**Run the command from a separate current GitHub checkout; do NOT replace or rebuild the original Mac project or DuckDB.** It opens `warehouse.duckdb` using `duckdb.connect(...,read_only=True)`, selects the code-only candidate market/country from the **same local archived lookup** and identifies unresolved versus provisional-convention code strings. Then it scans `fact_segment` *only for the code-specific source endpoints* with `service_class in ('F','L')` and positive performed departures. The report distinguishes:
- Historical per-code, source-year, endpoint role, and operated-segment source-country counts. Each flight may contribute two endpoint legs, so **not unique travelers or ticket O&D**.
- Latest-12-reported-month exposure under the current model's `latest_ym-100` cutoff.
- The narrow source path of flights leaving **YYC, SEA, YYZ** to a U.S.-reported destination that has a conflicting airport code in the current window; the actual stored `dim_airport.city_market_id` and mapped `cbsa` are included. This is potential served-market consumer exposure, **not a brand-resolved counterfactual**.
- Explicitly disjoint categories: historical administrative country-code conventions to verify vs unresolved country conflicts.

The script writes only `country_fact_exposure.json`, `country_endpoint_by_year.csv`, and a small `README.md` to a *new* Desktop folder and fails on missing warehouse tables or output collision. No `CREATE`, `DELETE`, `INSERT`, `UPDATE`, `COPY`, data-cache refresh or model invocation. It makes **no** assertion that an exposed record was lost, assigned to the wrong market, or changed a published route verdict.

## Next decision gates

1. Confirm actual `fact_segment` endpoint traffic and its original T-100 source-country tags for the 112 unresolved codes. Identify which report-backed conflict codes touch any current qualifying YYC/SEA/YYZ segments.
2. For traffic-bearing conflicts, reconcile **point-in-time published stable BTS AirportIDs**, country, and CityMarketIDs, not arbitrary country normalization or latest-code MAX. Preserve coding conventions (PR/US, etc.) separately.
3. Build a wholly separate candidate warehouse only after the exact source snapshot has been identified; then quantify numeric ID, CBSA/metro, served, competition, 200 screened rows and **463** historical replay decision deltas.
4. Merge a production correction only when its chosen IDs and geography are independently supported, and fixed-source output reproducibility gates pass. Keep [issue #7](https://github.com/yumorepos/network-lab/issues/7) and [issue #30](https://github.com/yumorepos/network-lab/issues/30) open.

This audit is a bounded evidence request, not permission to alter frozen published results.
