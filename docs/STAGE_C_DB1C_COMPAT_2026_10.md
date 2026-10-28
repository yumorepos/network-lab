# Stage C - DB1C four-table compatibility spike (2026-10-28)

**Status: isolated schema and join-grain prototype, not production ingestion.**
The published Network Lab DB1B mart and all current route verdicts are frozen.
The pilot uses synthetic U.S. hub-month records to exercise the schema, and
separately verifies the official July 2025 ZIP URLs via metadata-only requests.
Actual DB1C Market/Coupon/Ticket/Segment rows have **not** yet been compared,
and no new prediction or fare observation is claimed.

## Published source, vintage and survey discontinuity

The U.S. BTS replaced DB1B (quarterly, 10% sample through June 2025) with
DB1C (monthly, 40% sample from July 2025). As of October 28, 2026, the official
DB1C product pages offer monthly files through **July 2026**. The reporting
carrier definition changed to issuing carrier, and reporting eligibility
expanded. Therefore raw ticket counts and carrier shares cannot be spliced.

Sources:
- [BTS OD-40 collection and definitions](https://www.bts.gov/OD-40)
- [Ticket](https://www.bts.gov/topics/airlines-and-airports/origin-and-destination-survey-data-ticket)
- [Market](https://www.bts.gov/topics/airlines-and-airports/origin-and-destination-survey-data-market)
- [Coupon](https://www.bts.gov/topics/airlines-and-airports/origin-and-destination-survey-data-coupon)
- [Segment](https://www.bts.gov/topics/airlines-and-airports/origin-and-destination-survey-data-segment)
- Official [DB1C Market field list](https://www.transtats.bts.gov/Fields.asp?gnoyr_VQ=GGF),
  [Coupon fields](https://www.transtats.bts.gov/Fields.asp?gnoyr_VQ=GGE),
  [Ticket fields](https://www.transtats.bts.gov/Fields.asp?gnoyr_VQ=GGG),
  [Segment fields](https://www.transtats.bts.gov/Fields.asp?gnoyr_VQ=GGH).

| Source object | Record grain | Canonical identifiers in published layout | Do not assume |
|---|---|---|---|
| Ticket | one passenger itinerary record | `ItinID`, `RpYear`, `RpMonth` | reporting carrier equals operating carrier |
| Market | directional trip market within itinerary | `ItinID`, `MktID`, source market IDs | unique fare is equivalent to DB1B fare |
| Coupon | ticket coupon, possibly containing intermediate via points | `ItinID`, `MktID`, `SeqNum` | one coupon always equals one flight leg |
| Segment | via-point expansion of a coupon only | `ItinID`, `MktID`, `SeqNum`, `SegmentID` | the segment table contains all flown legs |

**Critical segment trap:** BTS explicitly states that DB1C Segment only holds
segments made from coupons with Via Point values. Direct coupons with no via
point must be added from Coupon to obtain full leg records. But summing all leg
records counts flight legs traversed, **not unique passengers or ticket O&D**.
Every directional market must be counted once from Market and ticket revenue
must be read once from Ticket, not from a fanout Market-Coupon-Segment join.

## Field crosswalk and money handling

| Legacy DB1B in Network Lab | DB1C field(s) | Status |
|---|---|---|
| `Year`, `Quarter` | `RpYear`, `RpMonth` | Monthly, with separate scheduled-flight vintage; not a 1:1 quarter replacement |
| `OriginCityMarketID`, `DestCityMarketID` | same names in Market | Comparable location identifier semantics, but requires stable-ID and geographic checks |
| `TkCarrier` | `IssuingCarrier`, `MktCarrier`, `RpCarrier` | Not a direct carrier-code replacement; reporting definition changed |
| `Passengers` (10% DB1B sample) | `Passengers` (DB1C 40% sample) | Different sample and unit; no automatic x10 or x2.5 in prototype |
| `MktFare` | `MktAmout`, `MktTax`, `V_Yield` | Official Market field is spelled **MktAmout**. Gross amount including taxes differs from historical MktFare |
| separate ticket fare not imported | Ticket `TotalAmount`, `TaxAmount` and `RoundTrip` | Ticket fare is gross USD including taxes; round-trip fare not a one-way market fare |
| `MktCoupons` | `MktCoupons` | Coupon count, not leg count where via points exist |
| `OpCarrier` | `OpCarrier`, `MktCarrier`, `IssuingCarrier` | Don't silently infer brand or filing certificate from one code |

BTS calls the ticket gross amount `TotalAmount` and the corresponding tax
component `TaxAmount`. The Market layout names `MktAmout` and `MktTax`
with its original spelling. No fare conversion is safe until tax treatment,
allocation, ticket/market unit, trip-break changes, categories and outlier
filters are explicitly reconciled. The old `ingest/bts_db1b.py` fare filter
(`MktFare BETWEEN 25 AND 5000`) must **not** be copied over.

The 40% survey sampling fraction is a *study design*, not permission to treat
each reported record as precisely 2.5 real passengers for validation without
checking methodology and expansion policy. No sample expansion is applied.

## Offline demonstration and negative controls

`scripts/stage_c_db1c_compat.py` validates one explicitly **synthetic**
SEA-centered July 2025 fixture: two passenger itineraries, three directional
markets (round trip plus one-way), three coupons, and two extra segments from
one via-point coupon. The correct materialized leg count is four: two via
segments and two coupons without via points. The sample contains two itinerary
passengers, three market-passenger observations and four leg traversals.
These are different metrics and are deliberately NOT summed together.

Each join validates cardinality before use. Regression tests inject duplicate
itinerary IDs, orphan markets/coupons/segments, an illegal Segment row for a
direct coupon, an incorrect `MktFare` field, and a mixed reporting month.
The expected assertion failure is recorded by each `pytest.raises`.

The pilot also offers **HEAD-only** probes of the four BTS July 2025
download links. These check source availability without downloading
potentially large consumer-ticket archives. A HEAD success establishes a
reachable archive, not a validated row schema or comparability.

## Gate C and findings disposition

**Gate C remains OPEN.** This is a compatibility proof of concept, not a
successful observed-data ingestion. Before closing, inspect at least one actual
small, source-verified U.S. market/month subset (with the true field names,
record counts, joins, fare units, nulls, via-point rates and duplicate IDs)
and demonstrate comparability against an explicitly comparable DB1B metric.

No 2018 Canadian transborder anchors, baseline ranking, model defaults,
fare estimates, Streamlit artifacts, or replay will be overwritten. If a
reasonably bounded observed-data extract is not feasible, close with a
transparent standalone limitation rather than fabricate an empirical result.

**Prior Stage B finding carried forward:** BTS stable AirportID matched all
1,435 observed July T-100 airports while a current airport-code-only join
missed PBI records after the PBI to DJT code change. Any DB1C crosswalk should
use stable airport/city-market identifiers, not the latest IATA code. This
does not imply a validated cross-dataset join between T-100 and DB1C, which
have different observational grains.

[Stage B evidence](./STAGE_B_T100_2026_07.md) and
[airport join follow-up](https://github.com/yumorepos/network-lab/issues/7).
