"""Rebuild the incumbent-network reference file from sources INDEPENDENT of the
candidate filter.

Why this module exists. The previous version of
`data/reference/incumbent_network_202604.csv` was a dump of the same T-100 query
that `models/candidates.py` runs to decide which metros are already served. It
was described as an independent cross-check, but the test that reads it
(`test_no_screened_market_is_already_served`) could not fail: both sides shared
one query, one table and one carrier concept, so both shared the same bug. Four
Seattle metros flown by Horizon as Alaska (El Paso, Wichita, Monterey, Tulsa)
were absent from both sides and leaked into the Alaska candidate set.

A cross-check is only worth having if it can disagree. So each row here records
which source produced it and how independent that source actually is:

  db1b_nonstop_ticket_sales   fully independent. A different BTS survey (the
                              10% ticket sample, not the segment census), a
                              different grain (origin and destination, not
                              segment), and a different carrier concept (who
                              SOLD the ticket, not who flew the metal). This is
                              what catches an operating-versus-marketing carrier
                              error. US origins only.
  t100_inbound_seats          partially independent. DB1B does not cover
                              Canadian origins, and no public source gives
                              carrier-level Canadian transborder service, so the
                              transborder hubs fall back to T-100. Independence
                              is bought by reading a DIFFERENT SET OF FILED
                              RECORDS (the inbound direction, US airport to hub,
                              which the candidate filter never touches) and a
                              DIFFERENT MEASURE (seats flown, not departures
                              from the hub). This catches query, brand-mapping
                              and metro-rollup errors. It cannot catch T-100
                              itself being wrong, and the notes say so.

Both tiers resolve the operating certificate to its marketing brand through
models.carriers, because the question the file answers is commercial: can a
passenger already buy this city pair from this airline.

Run with `python -m warehouse.incumbent_reference`. Regenerate after `make data`.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from models.carriers import register_segment_brands
from models.common import assumptions, connect, study

REF = Path("data/reference/incumbent_network_202604.csv")
STUDIES = ("westjet_yyc", "alaska_sea", "porter_yyz")
DB1B_YEAR = 2024


def _db1b_served(con, hub: str, brand: str) -> pd.DataFrame:
    """Metros where the brand SELLS a nonstop from the hub, per the DB1B ticket
    sample. Independent of T-100 in survey, grain and carrier concept."""
    return con.execute(f"""
        SELECT m.cbsa AS dest_cbsa,
               max(a.iata_code) AS sample_airport,
               sum(o.passengers_est) AS evidence_value
        FROM fact_od_market o
        JOIN dim_airport a ON a.iata_code = o.dest
        JOIN map_citymarket_cbsa m ON m.city_market_id = a.city_market_id
        WHERE o.year = {DB1B_YEAR} AND o.coupons = 1
          AND o.origin = '{hub}' AND o.tk_carrier = '{brand}'
        GROUP BY 1
    """).df()


def _t100_inbound_served(con, hub: str, brand: str,
                         min_deps: float) -> pd.DataFrame:
    """Metros the brand flies INTO the hub from.

    Deliberately the mirror image of the candidate filter, which reads only
    records with the hub as origin. The service threshold is the study's own
    (`served_market_min_deps_yr`): independence has to come from the source and
    the record set, not from quietly using a looser definition of "served".
    Without it a seasonal experiment reads as a served market, and WestJet's
    21-flight summer 2025 Calgary to Anchorage run would wrongly disqualify a
    live candidate.
    """
    win = con.execute("""
        SELECT max(year::INT*100+month) FROM fact_segment
        WHERE service_class IN ('F','L')
    """).fetchone()[0]
    return con.execute(f"""
        SELECT m.cbsa AS dest_cbsa,
               max(s.origin) AS sample_airport,
               sum(s.departures) AS evidence_value,
               sum(s.seats) AS inbound_seats
        FROM fact_segment s
        JOIN dim_airport a ON a.iata_code = s.origin
        JOIN map_citymarket_cbsa m ON m.city_market_id = a.city_market_id
        LEFT JOIN map_segment_brand b
               ON b.op_carrier = s.carrier
              AND b.origin = s.origin AND b.dest = s.dest
        WHERE s.dest = '{hub}' AND s.service_class IN ('F','L')
          AND s.origin_country = 'US'
          AND (s.year::INT*100+s.month) > {win} - 100
          AND coalesce(b.brand, s.carrier) = '{brand}'
          AND s.departures > 0 AND s.seats > 0
        GROUP BY 1
        HAVING sum(s.departures) >= {min_deps}
    """).df()


def build() -> pd.DataFrame:
    con = connect(read_only=True)
    register_segment_brands(con, min_deps=1)
    min_deps = float(assumptions()["served_market_min_deps_yr"]["value"])
    names = con.execute(
        "SELECT cbsa, name FROM dim_metro_us").df().set_index("cbsa")["name"]

    frames = []
    for sid in STUDIES:
        cfg = study(sid)
        hub, brand = cfg["hub"], cfg["carrier"]
        if cfg["hub_country"] == "US":
            df = _db1b_served(con, hub, brand)
            df["verification_source"] = "db1b_nonstop_ticket_sales"
            df["evidence_unit"] = f"db1b_nonstop_pax_{DB1B_YEAR}"
            df["independent_of_candidate_filter"] = "full"
            df["source"] = (
                f"BTS DB1B Market {DB1B_YEAR}, single-coupon itineraries "
                f"ticketed by {brand} from {hub}, rolled to CBSA. Independent "
                "of T-100 in survey, grain and carrier concept.")
        else:
            df = _t100_inbound_served(con, hub, brand, min_deps)
            df["verification_source"] = "t100_inbound_direction"
            df["evidence_unit"] = "t100_inbound_departures_trailing_12mo"
            df["independent_of_candidate_filter"] = "partial"
            df["source"] = (
                "BTS T-100 trailing 12mo to 2026-04, INBOUND records "
                f"(US origin to {hub}) resolved to the {brand} brand. DB1B "
                "does not cover Canadian origins; this is a different record "
                "set from the candidate filter, not a different source.")
        df["study_id"] = sid
        df["carrier"] = brand
        df["hub"] = hub
        frames.append(df)

    con.close()
    out = pd.concat(frames, ignore_index=True)
    out["dest_metro_name"] = out["dest_cbsa"].map(names)
    out = out[out["dest_metro_name"].notna()]
    cols = ["study_id", "carrier", "hub", "dest_cbsa", "dest_metro_name",
            "sample_airport", "evidence_value", "evidence_unit",
            "inbound_seats", "verification_source",
            "independent_of_candidate_filter", "source"]
    out = (out[cols].sort_values(["study_id", "evidence_value"],
                                ascending=[True, False])
           .reset_index(drop=True))
    out.to_csv(REF, index=False)
    return out


if __name__ == "__main__":
    df = build()
    for sid, g in df.groupby("study_id"):
        print(f"{sid}: {len(g)} served metros "
              f"({g['verification_source'].iloc[0]})")
    print(f"wrote {REF}")
