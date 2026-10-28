# Airport identity consumer-exposure audit (2026-10-28)

**Disposition:** Risk confirmed in code, final-market direct-name check completed,
**production outcome impact not measured**. No airport mapping, model, candidate,
historical replay or computed artifact was changed. Issue
[#7](https://github.com/yumorepos/network-lab/issues/7) remains open for a
warehouse-backed consumer-impact comparison.

## Why this matters

The isolated July 2026 BTS T-100 pilot downloaded and compared source airport
identifiers. All 1,435 observed AirportID / CityMarketID pairs matched current
BTS Master Coordinate, with no disagreements. A latest *airport-code* lookup
instead missed PBI (280 July segment rows, 587,101 segment passengers),
after the **August 18, 2026** PBI to DJT code change. These counts describe
the **separate Stage B research extract**, not lost passengers in Network Lab's
production warehouse or a measured verdict difference.

Source: [Stage B evidence](STAGE_B_T100_2026_07.md).

## Consumer exposure - actual repository trace

| Surface | Static finding | What this establishes |
|---|---|---|
| `ingest/bts_t100.py` | Persists `origin` and `dest` airport *codes* without the source stable AirportIDs | Historical airport identity cannot be recovered directly from the slim T-100 mart |
| `warehouse/build_marts.py` | Latest lookup groups by `AIRPORT` code, takes `max(CITY_MARKET_ID)`, and joins OurAirports by IATA code | Reused codes and changed codes can map to wrong or missing markets after a refresh |
| `warehouse/metro_map.py` | Builds metro traffic through `fact_segment.origin = dim_airport.iata_code` | Incomplete code joins can affect metro evidence and warning coverage |
| `models/catchment.py` | Joins `dim_airport.city_market_id` to metro map | Potential anchor and seat-share exposure, depending on vintage |
| `models/candidates.py` | Excludes already-served markets through `fact_segment.dest` to code-based `dim_airport` | Potential served-market classification exposure |
| `models/competition.py` | Reconstructs destination-metro airports through code-derived city markets | Potential service/competition exposure |
| `data/parquet/outputs/screen_*.csv` | All 200 currently published rows searched; **0** name `PBI` or `DJT` as `dest_airport` | No direct PBI/DJT destination display, **not proof** of zero indirect effect |
| `data/reference/incumbent_network_202604.csv` | Porter YYZ's Miami-Fort Lauderdale-West Palm Beach metro has a `PBI` sample-airport row | Independent historical service evidence touches the affected airport code |

The committed headlined market totals remain exactly as recorded by
`data/parquet/outputs/headline_metrics.yaml`: WestJet YYC 76 PASS, Alaska SEA
45 PASS, Porter YYZ 1 LAUNCH / 1 MONITOR / 77 PASS. **They were not
recomputed**, so this audit **cannot** assert these results would remain
unchanged under a corrected production identifier path.

The positive and negative tests in
`tests/test_airport_join_exposure.py` reproduce only (a) committed screen
and reference exposure, and (b) how a deliberately code-only lookup loses a
historical code when the newest label changes. These are not replay tests.

## Controlled next decision

**Do not auto-replace PBI with DJT or substitute `max(CITY_MARKET_ID)`**.
Any proposed production fix must first:

1. Identify current warehouse vintages for all historical source snapshots and
   describe every PBI/DJT source and `dim_airport` row. Audit all actual
   joins to stable IDs and historic codes, including `fact_segment` and
   `dim_airport`.
2. Run old code-only and proposed time-aware/stable-ID mapping side by side,
   reporting affected rows and passenger/seat totals by vintage, study, and
   carrier. Preserve original codes and the full source lineage.
3. Re-run the full warehouse, `make all`, `make test`, and
   `make reproducibility` using same source snapshots. File a before/after
   report with *every* changed market, model metric, and verdict, or explicitly
   state that no effect was measured.
4. Never use the July 2026 Stage B 587,101 count as an estimated production
   error without this independent test.

The project-wide predictive claim remains frozen. A changed match count is
a data quality correction, not evidence of better forecast skill.

**Stop rule:** With only committed screening outputs and without the archived
full production warehouse and stable-ID inputs, no defensible verdict delta
can be calculated. This pass is closed as a **bounded exposure audit**; the
consumer-impact question in issue #7 is **still OPEN**.
