# Official BTS stable airport-ID pilot — research only

**Purpose:** obtain `OriginAirportID`, `DestAirportID` and source-published `OriginCityMarketID`/`DestCityMarketID` from [TranStats T-100 Segment (All Carriers)](https://transtats.bts.gov/Fields.asp?gnoyr_VQ=FMG), because the existing archived 14-field T-100 extracts omit these essential identifiers.

This pilot **does not** change `ingest/bts_t100.py`, the frozen warehouse, source ZIP cache, route-screening decisions, historical replay, or dashboard. An independent repository CI job downloads a fresh **2026** full-field source ZIP to an ephemeral private runner directory, streams the CSV, removes the ZIP on process exit, and publishes only a small aggregate JSON artifact. It refuses to infer missing IDs from airport codes and exits nonzero if any scheduled passenger endpoint has missing published identifiers. The source SHA-256 and observed month coverage are recorded to prevent an undated `2026` claim.

Run locally:

```bash
python -m pytest -q tests/test_research_t100_source_ids.py
python -m scripts.research_t100_source_ids \
  --download-year 2026 --output /tmp/research_t100_source_ids_2026.json
```

Use `--zip PATH --year 2026` for an already downloaded **official all-field** source ZIP. The 14-field archived ZIP intentionally fails with a required-source-identifiers error.

## Outputs and definitions

- **Code reuse within a year:** one code associated with two published `AirportID` values.
- **Airport-code rename within a year:** one published `AirportID` associated with several airport-code strings.
- **Market reassignment:** one published `AirportID` associated with more than one source city-market identifier.
- **Endpoint passenger legs:** T-100 segment passenger field is counted separately for each affected endpoint. The same physical traveler may be counted more than once across segments; these are NOT ticket O&D or unique travelers.
- **No legacy-lookup impact claim:** the source-only script deliberately does not equate code changes with lost traffic or altered candidate choices.

The BTS source identity fields are explicitly intended for analysis across years when airport codes change or are reused. A versioned source-ID bridge remains the correct long-term route; a latest-code `max(CITY_MARKET_ID)` lookup is not an equivalent replacement.

## Production acceptance gate (still blocked)

To certify issue #7: (1) retain published stable IDs in a **separate source-fixed candidate vintage**; (2) compare those source IDs with code-only joins in each historical year; (3) join to actual airport, CBSA, carrier, candidate, competition and replay consumers; (4) report all changed rows/verdicts and verify output/readback parity; (5) run complete model and reproducibility gates before any migration. This pilot is data provenance, not production correction.

Source: https://www.transtats.bts.gov/Fields.asp?gnoyr_VQ=FMG
