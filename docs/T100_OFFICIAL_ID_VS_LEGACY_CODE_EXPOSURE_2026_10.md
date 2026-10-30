# Official T-100 source AirportID vs archived latest-code warehouse rule

**2026-10-29, research only.** Independently reconciles official BTS full-field T-100 source AirportID/CityMarketID profiles with the archived Master Coordinate latest-code MAX(CITY_MARKET_ID) rule in `warehouse/build_marts.py`. The original Mac DuckDB was not opened and no frozen source or model was modified.

## Exact audited evidence

- BTS Master Coordinate archived ZIP SHA-256: `3b429a4bc5950f6f16ff1796b204d10fcd5ad2e97ea39be5cb6476951ff3e6f1`.
- Official full-field T-100 2024 SHA-256: `2e18f9491efecdad128887aea8e27fff27a78ceaf88469728a7fad3cc70c8e60`, 488,872 scheduled F/L positive-departure segment rows, January–December 2024.
- Official full-field T-100 Jan–Jul 2026 SHA-256: `469367f22db446f27c970b36ab06a7961b3624cccd785b9f8103646552c78b22`, 299,295 scheduled F/L positive-departure segment rows, January–July 2026.
- Both official source profiles had **zero missing published AirportID or CityMarketID endpoints**; see official [CI run 40947738178](https://github.com/yumorepos/network-lab/actions/runs/40947738178).

| Period | Source endpoints with matching latest-code MAX market | Source endpoints with *different* city-market | Source endpoints with no latest-code match |
|---|---:|---:|---:|
| 2024 | 977,740 | **4** / 86 endpoint passenger-segment legs | **0** |
| Jan–Jul 2026 | 598,584 | **4** / 14 endpoint passenger-segment legs | **2** / 8 endpoint passenger-segment legs |

Actual **source-verified** differences (not inferred from airport-code names):
- **2024 VZL**: BTS `CITY_MARKET_ID=35687` (source AirportID observed) versus latest-code `MAX=35853`: 1 endpoint record / 77 passenger-segment legs.
- **2024 SAW**: BTS `CITY_MARKET_ID=32395` versus latest-code `MAX=33459`: 3 endpoint records / 9 passenger-segment legs.
- **2026 SAW**: same market-ID disagreement: 4 endpoint records / 14 passenger-segment legs.
- **2026 W95**: missing latest-code row, 1 endpoint record / 6 passenger-segment legs.
- **2026 W29**: missing latest-code row, 1 endpoint record / 2 passenger-segment legs.

**Total different/missing source endpoint exposures:** 2024 = 4 rows / 86 legs; 2026 Jan–Jul = 6 rows / 22 legs. Each flight has both an origin and a destination endpoint; endpoint legs are not unique travelers, lost passengers or ticket O&D.

## Reproduce

Use a dated archived Master Coordinate ZIP and official-source summary JSONs from the full-field BTS research run. No network is needed to repeat the comparison:

```bash
python -m pytest -q tests/test_audit_t100_source_id_vs_latest_code.py
python -m scripts.audit_t100_source_id_vs_latest_code \
  --master-zip /private/master_coord.zip \
  --source-profile /private/research_t100_ids_2024.json \
  --source-profile /private/research_t100_ids_2026.json \
  --output /tmp/t100_source_ids_vs_latest_code.json
```

The script uses only standard-library Python, refuses to overwrite evidence, and separates **different published markets** from **absent code lookup**. Tests independently exercise reused SAW-like code, missing code, correct ID, missing published IDs, duplicate source-year and invalid endpoint counts.

## Acceptance and limits

This definitively demonstrates that a pure code-only MAX lookup does not preserve every BTS published city-market assignment **in the evaluated source vintages**. It does **not** show that these records reached the preserved DuckDB or changed source-derived candidate eligibility or any frozen model/replay verdict. Original `fact_segment` uses archived 14-field files, which have different source vintages from the fresh full-field files. No original Mac warehouse readback occurred.

**Next:** join source-fixed AirportIDs to historical archived facts by an independently verified row-grain bridge, quantify which actual airport/metro/candidate/competition consumers include affected endpoints, then run fixed-snapshot 200-screen/463-replay before/after comparison. Do not replace the frozen parquet or close [issue #7](https://github.com/yumorepos/network-lab/issues/7) based solely on this source-only diagnostic.
