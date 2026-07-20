"""Catchment: population reachable from an airport, with distance decay.

catchment_pop(airport) = sum over CBSAs/CMAs within the radius of
  population x 2^(-d / half_distance)
where d is the great-circle distance from the airport to the metro's anchor
point. The anchor point for a US CBSA is the coordinates of its largest
mapped airport (documented proxy; no shapefiles needed). Canadian CMAs use
the mapped airport itself.

When several same-country airports sit inside one metro's radius, the metro's
population is allocated across them in proportion to scheduled seats (T-100,
latest full year), so a metro is never double-counted across airports.
"""
from __future__ import annotations

import pandas as pd

from .common import assumptions, connect, haversine_mi

KM_PER_MI = 1.609344


def metro_anchor_points(con) -> pd.DataFrame:
    """One anchor coordinate per CBSA: its busiest mapped airport."""
    return con.execute("""
        WITH seats AS (
          SELECT origin AS iata, sum(seats) AS seats
          FROM fact_segment
          WHERE year = 2024 AND service_class IN ('F','L')
          GROUP BY origin
        ),
        us AS (
          SELECT m.cbsa, m.cbsa_name, a.iata_code, a.lat, a.lon,
                 coalesce(s.seats, 0) AS seats,
                 row_number() OVER (PARTITION BY m.cbsa
                                    ORDER BY coalesce(s.seats,0) DESC) AS rn
          FROM map_citymarket_cbsa m
          JOIN dim_airport a USING (city_market_id)
          LEFT JOIN seats s ON s.iata = a.iata_code
          WHERE a.iso_country = 'US'
        )
        SELECT u.cbsa, u.cbsa_name, u.iata_code AS anchor_airport,
               u.lat, u.lon, d.population, d.income, d.gdp_kusd
        FROM us u
        JOIN dim_metro_us d USING (cbsa)
        WHERE u.rn = 1 AND d.population IS NOT NULL
    """).df()


def catchment_for_airport(con, iata: str) -> dict:
    """Decayed catchment population around one airport (same country)."""
    a = assumptions()
    radius_km = float(a["catchment_radius_km"]["value"])
    half_km = float(a["catchment_decay"]["half_distance_km"])
    ap = con.execute(
        "SELECT lat, lon, iso_country FROM dim_airport WHERE iata_code=?",
        [iata]).fetchone()
    if ap is None:
        raise KeyError(f"airport {iata} not in dim_airport")
    lat0, lon0, country = ap
    if country == "US":
        metros = metro_anchor_points(con)
        pts = metros[["cbsa_name", "lat", "lon", "population"]].values
    else:
        # one row per CMA (its busiest mapped airport), or Toronto would be
        # counted once per airport that maps to it
        pts = con.execute("""
            WITH ranked AS (
              SELECT c.cma_name, a.lat, a.lon, m.population,
                     row_number() OVER (PARTITION BY c.cma_name
                                        ORDER BY a.iata_code) AS rn
              FROM ca_airport_cma c
              JOIN dim_airport a USING (iata_code)
              JOIN dim_metro_ca m ON m.cma LIKE c.cma_name || '%'
            )
            SELECT cma_name, lat, lon, population FROM ranked WHERE rn = 1
        """).fetchall()
    total, parts = 0.0, []
    for name, lat, lon, pop in pts:
        if pop is None:
            continue
        d_km = haversine_mi(lat0, lon0, lat, lon) * KM_PER_MI
        if d_km <= radius_km:
            w = 2 ** (-d_km / half_km)
            total += pop * w
            parts.append((name, pop, d_km, w))
    return {"airport": iata, "catchment_pop": total,
            "parts": sorted(parts, key=lambda x: -x[1] * x[3])[:8]}


def seat_share_allocation(con, country: str, year: int = 2024) -> pd.DataFrame:
    """Within-metro seat shares, used to split a metro across its airports."""
    key = "cbsa" if country == "US" else "cma_name"
    join = ("JOIN map_citymarket_cbsa m USING (city_market_id)"
            if country == "US" else
            "JOIN ca_airport_cma m ON m.iata_code = a.iata_code")
    return con.execute(f"""
        WITH seats AS (
          SELECT origin AS iata, sum(seats) AS seats
          FROM fact_segment
          WHERE year = {year} AND service_class IN ('F','L')
          GROUP BY origin
        )
        SELECT m.{key} AS metro, a.iata_code,
               coalesce(s.seats,0) AS seats,
               coalesce(s.seats,0) /
                 nullif(sum(coalesce(s.seats,0)) OVER (PARTITION BY m.{key}),0)
                 AS seat_share
        FROM dim_airport a
        {join}
        LEFT JOIN seats s ON s.iata = a.iata_code
        WHERE a.iso_country = '{country}'
        ORDER BY metro, seats DESC
    """).df()
