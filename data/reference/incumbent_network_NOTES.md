# incumbent_network_202604.csv companion notes

Purpose. A record of each study carrier's current nonstop network from its hub,
built so the "unserved candidate" claim in every screen can be checked against
something the model did not produce itself. A LAUNCH or MONITOR verdict on a
market the carrier already flies is the one error an aviation reviewer will not
read past; `tests/test_sanity.py` fails if any screened metro appears in the
matching carrier's list here.

## What was wrong with the previous version

Through Round 3 this file was a dump of the same T-100 query that
`models/candidates.py` runs. All 99 rows matched that query on CBSA with a
maximum departure delta of 0.0. It was described as an independently auditable
record, but the two sides shared one query, one table and one carrier concept,
so they also shared one bug: both counted the OPERATING carrier, so four Seattle
metros that Horizon flies as Alaska (El Paso, Wichita, Monterey, Tulsa) were
invisible to both and leaked into the Alaska candidate set. The test could not
fail. A cross-check that cannot disagree is not a cross-check.

The old note's closing paragraph came close to admitting this ("both read the
same fact_segment table"), which made it a documented limitation rather than a
hidden one, but it still did not stop the leak.

## How it is built now

Rebuilt by `python -m warehouse.incumbent_reference`. Every row records which
source produced it and how independent that source actually is, in the
`verification_source` and `independent_of_candidate_filter` columns.

**`db1b_nonstop_ticket_sales` (alaska_sea, 81 metros, fully independent).**
BTS DB1B Market 2024, single-coupon itineraries ticketed by the study carrier
from the hub, rolled up to CBSA. A different survey from T-100 (a 10% ticket
sample, not the segment census), a different grain (origin and destination, not
segment), and a different carrier concept (who sold the ticket, not who flew the
metal). That last difference is the one that matters: DB1B is what catches an
operating-versus-marketing carrier error, and it independently identified three
of the four leaked Alaska metros. Its blind spot is time. Alaska launched
Seattle to Tulsa in March 2026, after the 2024 DB1B year, so DB1B cannot see it;
the brand-aware T-100 filter catches that one instead. The two sources have
complementary blind spots, which is the point of having two.

No passenger floor is applied. The candidate universe starts at 400,000 metro
population and every marginal DB1B row here is a sub-100,000 ski market
(Edwards, Steamboat Springs, Jackson), so a floor would buy nothing and risks
re-hiding the leaks it exists to catch. Raw passenger counts sit in
`evidence_value` so any future collision can be inspected directly.

**`t100_inbound_direction` (westjet_yyc 26 metros, porter_yyz 11 metros,
partially independent).** DB1B does not cover Canadian origins and no open
source gives carrier-level Canadian transborder service, so the transborder hubs
fall back to T-100. Independence is bought where it can be: these rows read the
INBOUND record set (US origin to hub), which the candidate filter never touches,
and resolve the operating certificate to its marketing brand. That catches
query, brand-mapping and metro-rollup errors. It cannot catch T-100 itself being
wrong, and the `independent_of_candidate_filter` column says `partial` rather
than pretending otherwise.

## Scope

One row per (study, served destination metro). A metro counts as served when the
study carrier's brand operates at least ~weekly (26 departures over the trailing
twelve months, `served_market_min_deps_yr` in config/assumptions.yaml) to any
airport in the metro. The threshold is deliberately the study's own: independence
has to come from the source, not from quietly using a looser definition of
"served". Without it WestJet's 21-flight summer 2025 Calgary to Anchorage
experiment reads as a served market and wrongly disqualifies a live candidate.

Porter's Chicago and Boston history is Billy Bishop (YTZ) turboprop service, a
different airport and gauge outside this YYZ mainline-jet study, so neither is in
this file. Note for future vintages: Porter began YYZ to Boston on 2026-05-14 at
14x weekly, after the close of this data window, so Boston is correctly a
candidate at this vintage and will correctly stop being one at the next.

## Carrier brands

Operating certificate to marketing brand comes from
`data/reference/carrier_families.csv`, which cites the ownership or capacity
purchase relationship per row and records how strongly DB1B corroborates it. See
`models/carriers.py` for how multi-brand operators such as SkyWest are resolved
segment by segment.

## Regeneration

Safe to regenerate after `make data`. The DB1B tier moves with the DB1B vintage
and the T-100 tier with the segment window, so a new data vintage can legitimately
change this file. That is a signal to re-read the screens, not a test to relax.
