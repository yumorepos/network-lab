"""Candidate generation: which unserved (by the study carrier) US metros are
worth evaluating from the hub. Rules come from the study config; thresholds
from assumptions.yaml.
"""
from __future__ import annotations

import pandas as pd

from .catchment import metro_anchor_points
from .common import assumptions, connect, haversine_mi, study


def generate(study_id: str) -> pd.DataFrame:
    cfg = study(study_id)
    a = assumptions()
    con = connect(read_only=True)
    hub = cfg["hub"]
    carrier = cfg["carrier"]
    dmin = cfg["candidates"]["distance_nm"]["min"] * 1.15078  # nm -> mi
    dmax = cfg["candidates"]["distance_nm"]["max"] * 1.15078
    min_pop = float(a["candidate_min_metro_pop"]["value"])

    hub_pt = con.execute(
        "SELECT lat, lon FROM dim_airport WHERE iata_code=?", [hub]).fetchone()
    metros = metro_anchor_points(con)
    min_deps = float(a["served_market_min_deps_yr"]["value"])

    # Nonstops from the hub in the trailing 12 reported months, rolled up to
    # the METRO (via city market -> CBSA) so that service to a secondary
    # airport still counts as the metro being served. Airport-level rollup was
    # the leak: WS flies YYC-IAD ~1x weekly, but the DC metro's busiest airport
    # is BWI, so an airport match missed it.
    served = con.execute("""
        WITH latest AS (
          SELECT max(year::INT*100+month) AS ym FROM fact_segment
          WHERE service_class IN ('F','L')
        )
        SELECT m.cbsa AS cbsa, s.carrier,
               sum(s.departures) AS deps
        FROM fact_segment s, latest
        JOIN dim_airport a2 ON a2.iata_code = s.dest
        JOIN map_citymarket_cbsa m ON m.city_market_id = a2.city_market_id
        WHERE s.origin = ? AND s.service_class IN ('F','L')
          AND s.dest_country = 'US'
          AND (s.year::INT*100+s.month) > latest.ym - 100
        GROUP BY 1, 2
    """, [hub]).df()
    served_by_study = set(
        served[(served["carrier"] == carrier) & (served["deps"] >= min_deps)]
        ["cbsa"])
    served_by_any = set(served[served["deps"] >= min_deps]["cbsa"])

    min_seats = float(a["candidate_min_airport_seats_yr"]["value"])
    sat = a["satellite_airport_rule"]

    def is_satellite(m) -> bool:
        near = metros[(metros["cbsa"] != m["cbsa"])
                      & (metros["anchor_seats_yr"]
                         >= sat["seat_ratio"] * max(m["anchor_seats_yr"], 1))]
        return any(haversine_mi(m["lat"], m["lon"], n["lat"], n["lon"])
                   <= sat["radius_mi"] for _, n in near.iterrows())

    rows, dropped = [], {"seats_floor": 0, "satellite": 0, "already_served": 0}
    for _, m in metros.iterrows():
        if m["population"] is None or m["population"] < min_pop:
            continue
        dist = haversine_mi(hub_pt[0], hub_pt[1], m["lat"], m["lon"])
        if not (dmin <= dist <= dmax):
            continue
        if m["cbsa"] in served_by_study:   # metro-level exclusion (fixed leak)
            dropped["already_served"] += 1
            continue
        if m["anchor_seats_yr"] < min_seats:
            dropped["seats_floor"] += 1
            continue
        if is_satellite(m):
            dropped["satellite"] += 1
            continue
        rows.append({
            "study_id": study_id, "hub": hub, "carrier": carrier,
            "dest_airport": m["anchor_airport"], "cbsa": m["cbsa"],
            "metro_name": m["cbsa_name"], "dist_mi": dist,
            "pop": float(m["population"]), "income": float(m["income"]),
            "gdp_kusd": float(m["gdp_kusd"]) if m["gdp_kusd"] else None,
            "nonstop_by_others": m["cbsa"] in served_by_any,
        })
    con.close()
    print(f"[candidates] {study_id}: {len(rows)} kept; dropped "
          f"{dropped['already_served']} already served by {carrier}, "
          f"{dropped['seats_floor']} below seat floor, "
          f"{dropped['satellite']} satellites of larger airports")
    df = pd.DataFrame(rows).sort_values("pop", ascending=False)
    return df.reset_index(drop=True)


if __name__ == "__main__":
    for s in ("westjet_yyc", "alaska_sea", "porter_yyz"):
        df = generate(s)
        print(f"{s}: {len(df)} candidates, top: "
              f"{df.head(3)['metro_name'].tolist()}")
