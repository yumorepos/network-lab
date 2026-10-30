# Research: sampled historical BTS airport identity trajectories (2026-10-29)

**Research-only.** This is a preproduction source-integrity gate for [issue #7](https://github.com/yumorepos/network-lab/issues/7). It does not rebuild the warehouse, change archived T-100 extracts, touch the frozen screening model, or certify historical replay outcomes.

## Why this gate exists

The frozen T-100 Parquets contain airport *codes* but omit source-published BTS AirportIDs, while the latest-code reference lookup can attach a CityMarketID to an airport code whose historical meaning may have changed. The direct official-source 2024-vs-Jan–Jul 2026 comparison passed on 1,570 shared AirportIDs, but that two-year negative result says nothing about older airport-code reuse.

A standalone CI job therefore downloads **official, all-field** T-100 segment rows for the *sampled* study-relevant years **1990, 2018, 2022, 2024 and January–July 2026**, to isolated temporary locations. It records the full source ZIP SHA-256 and observed monthly coverage, and streams only F/L passenger-service rows with positive departures. Codes never substitute for `OriginAirportID`/`DestAirportID` or source `CityMarketID`. Any missing stable identifier, unexpected vintage, nonintegral identity, incomplete required month range, or malformed source pair fails the gate.

The cross-vintage report flags:
- Same code associated with different **official AirportIDs** in sampled years (potential historical code reuse).
- Same **official AirportID** associated with different airport code strings (potential airport code rename).
- Same AirportID associated with different source CityMarketIDs or countries.
- Per-year endpoint segment passenger legs and departures for flagged code strings (context, **not lost production passengers**).

## Reproduce privately

```bash
python -m pytest -q tests/test_research_t100_multivintage_identity.py
# Use official source-published full-field data profiles, e.g.:
python -m scripts.research_t100_multivintage_identity \
  --profile /tmp/t100_ids_1990.json \
  --profile /tmp/t100_ids_2018.json \
  --profile /tmp/t100_ids_2022.json \
  --profile /tmp/t100_ids_2024.json \
  --profile /tmp/t100_ids_2026.json \
  --output /tmp/t100_multivintage_summary.json
```

The GitHub workflow supplies the full source-provenance profiles and stores a bounded, expiring **aggregate JSON** artifact. Original source ZIPs are discarded on the ephemeral CI runner; no user-private Mac data is uploaded.

## Stop conditions and limits

- The **five sampled years are not the complete 1990–2026 history**. A code reused and retired between sample years may be undetected. A negative source sample is not a universal history certificate.
- A code reused historically is not necessarily an active misjoin in the 200 published screens or the 463 historical replay decisions. Quantifying actual impact requires an independent source-fixed consumer reconstruction and readback from the original DuckDB warehouse.
- T-100 passenger fields are **operated segment legs**, not unique travelers or ticket O&D.
- The archived 2024 14-field source and the currently released 2024 source are known to have nonidentical row multisets. Preserve both vintages with hashes; do not silently replace the frozen data to make this gate pass.
- **Do not close #7** or alter the model until source-verified and same-snapshot warehouse consumer/parity gates pass.

See [original stable-ID source pilot](T100_OFFICIAL_SOURCE_ID_PILOT_2026_10.md) and [2024/2026 matched-ID review](T100_CROSS_VINTAGE_SOURCE_ID_RESULT_2026_10.md).
