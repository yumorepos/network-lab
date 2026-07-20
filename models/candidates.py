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

    # nonstops from the hub in the latest 12 reported months, by carrier
    served = con.execute("""
        WITH latest AS (
          SELECT max(year::INT*100+month) AS ym FROM fact_segment
          WHERE service_class IN ('F','L')
        )
        SELECT s.dest AS airport, s.carrier,
               sum(s.departures) AS deps
        FROM fact_segment s, latest
        WHERE s.origin = ? AND s.service_class IN ('F','L')
          AND (s.year::INT*100+s.month) > latest.ym - 100
          AND s.departures >= 4
        GROUP BY 1, 2
    """, [hub]).df()
    served_by_study = set(served[served["carrier"] == carrier]["airport"])
    served_by_any = set(served["airport"])

    rows = []
    for _, m in metros.iterrows():
        if m["population"] is None or m["population"] < min_pop:
            continue
        dist = haversine_mi(hub_pt[0], hub_pt[1], m["lat"], m["lon"])
        if not (dmin <= dist <= dmax):
            continue
        if m["anchor_airport"] in served_by_study:
            continue
        rows.append({
            "study_id": study_id, "hub": hub, "carrier": carrier,
            "dest_airport": m["anchor_airport"], "cbsa": m["cbsa"],
            "metro_name": m["cbsa_name"], "dist_mi": dist,
            "pop": float(m["population"]), "income": float(m["income"]),
            "gdp_kusd": float(m["gdp_kusd"]) if m["gdp_kusd"] else None,
            "nonstop_by_others": m["anchor_airport"] in served_by_any,
        })
    con.close()
    df = pd.DataFrame(rows).sort_values("pop", ascending=False)
    return df.reset_index(drop=True)


if __name__ == "__main__":
    for s in ("westjet_yyc", "alaska_sea", "porter_yyz"):
        df = generate(s)
        print(f"{s}: {len(df)} candidates, top: "
              f"{df.head(3)['metro_name'].tolist()}")
