# incumbent_network_202604.csv companion notes

Purpose. An independently auditable record of each study carrier's current
nonstop network from its hub, so the "unserved candidate" claim in every screen
can be checked without re-running the T-100 join inside the model. A LAUNCH or
MONITOR verdict on a market the carrier already flies is the one error an
aviation reviewer will not read past; `tests/test_sanity.py` fails if any
screened metro appears in the matching carrier's list here.

Scope. One row per (study, served destination metro). A metro counts as served
when the study carrier operates at least ~weekly (26 departures over the
trailing twelve months) to any airport in the metro, rolled up to CBSA. This is
the same metro-level definition the candidate filter uses
(`served_market_min_deps_yr` = 26 in config/assumptions.yaml).

Provenance. Rows are derived from BTS T-100 (Domestic and International) for the
trailing twelve months to 2026-04, which is the newest complete reporting
window in the warehouse. The transborder carriers were spot-checked against
published schedules on 2026-07-23:

- Porter (PD, YYZ): the T-100 list (New York/LGA, Las Vegas, the Florida sun
  markets, the California and Arizona leisure markets) matches Porter's operating
  transborder routes in data/reference/launches.csv. Porter's Chicago and Boston
  history is Billy Bishop (YTZ) turboprop service, a different airport and gauge
  outside this YYZ mainline-jet study, and T-100 shows no Porter YYZ jet service
  to either, so neither is in this file and both remain valid candidates.
- WestJet (WS, YYC): the list matches WestJet's published YYC transborder map
  (the California/Nevada/Arizona leisure markets, the Florida sun routes, the
  Texas and Hawaii markets, New York, Chicago, Atlanta, Boston, Washington).

Regeneration. Rebuilt from the warehouse with the query in the git history for
this file; safe to regenerate after `make data`. If a future data vintage adds a
route, this file and the candidate filter move together because both read the
same fact_segment table, so the test guards against code regressions and stale
verdicts rather than against T-100 itself being wrong.
