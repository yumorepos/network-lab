"""Transfer factor: anchors the US-calibrated gravity model to Canada-US truth.

Construction, stated precisely because each piece covers a different thing:
- The gravity model (pre2022 vintage, US-calibrated) gives the cross-sectional
  SHAPE of demand across destination metros, evaluated with current covariates.
- StatCan 23-10-0256 (frozen 2018) gives the last observed LEVEL for each
  transborder city pair: transfer_i = observed_2018_i / gravity_i.
- T-100 gives corridor GROWTH since the anchor froze:
  growth(hub) = T-100 transborder pax(hub, latest) / (hub, 2018).
Modeled demand for a pair is then gravity x transfer x growth. The covariate
vintage mismatch (2024 covariates against a 2018 anchor) cancels through the
ratio; what does not cancel is dispersion across pairs, which is exactly why
the factor is reported as median with IQR, min/max, and leave-one-out medians
rather than as a single confident number. The factor absorbs border effects,
currency, definitional mismatch between surveys, and model error; no attempt
is made to attribute it.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd
import yaml

from . import gravity
from .catchment import metro_anchor_points
from .common import OUTPUTS, connect, haversine_mi

CA_PROVINCES = {"Ontario", "Quebec", "British Columbia", "Alberta",
                "Manitoba", "Saskatchewan", "Nova Scotia", "New Brunswick",
                "Newfoundland and Labrador", "Prince Edward Island"}

US_STATE_CODE = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT",
    "Delaware": "DE", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI",
    "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME",
    "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI",
    "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO", "Montana": "MT",
    "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH",
    "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
    "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA",
    "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD",
    "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
    "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY", "District of Columbia": "DC",
}

# Canadian anchor cities we can resolve to a CMA population and a hub airport.
CA_CITY_HUB = {
    "Toronto": ("Toronto", "YYZ"),
    "Montréal": ("Montréal", "YUL"),
    "Vancouver": ("Vancouver", "YVR"),
    "Calgary": ("Calgary", "YYC"),
    "Edmonton": ("Edmonton", "YEG"),
    "Ottawa": ("Ottawa - Gatineau", "YOW"),
    "Winnipeg": ("Winnipeg", "YWG"),
    "Halifax": ("Halifax", "YHZ"),
}

ANCHOR_YEAR = "2018"
MIN_ANCHOR_PAX = 40_000     # thin anchor pairs are survey-noisy


def _parse_geo(geo: str):
    """'Albany, New York - Toronto, Ontario' -> (us_city, state), (ca_city, prov).
    Either side may be the Canadian one."""
    parts = [p.strip() for p in geo.split(" - ")]
    if len(parts) != 2:
        return None
    sides = []
    for p in parts:
        if "," not in p:
            return None
        city, region = [s.strip() for s in p.rsplit(",", 1)]
        sides.append((city, region))
    ca = [s for s in sides if s[1] in CA_PROVINCES]
    us = [s for s in sides if s[1] in US_STATE_CODE]
    if len(ca) != 1 or len(us) != 1:
        return None
    return us[0], ca[0]


def _match_us_metro(metros: pd.DataFrame, city: str, state_code: str):
    toks = metros["cbsa_name"].str.lower()
    cand = metros[(metros["cbsa_name"].str.contains(state_code, regex=False))
                  & (toks.str.contains(re.escape(city.lower())))]
    if len(cand) == 0:
        return None
    return cand.sort_values("population", ascending=False).iloc[0]


def estimate() -> dict:
    con = connect(read_only=True)
    metros = metro_anchor_points(con)
    cma = dict(con.execute(
        "SELECT cma, population FROM dim_metro_ca").fetchall())
    airports = dict(
        (r[0], (r[1], r[2])) for r in con.execute(
            "SELECT iata_code, lat, lon FROM dim_airport").fetchall())

    anchor = con.execute(f"""
        SELECT GEO, try_cast(VALUE AS DOUBLE) AS pax
        FROM fact_od_transborder_2018
        WHERE REF_DATE='{ANCHOR_YEAR}'
          AND Estimates='Number of outbound and inbound passengers'
          AND GEO != 'Other cities' AND VALUE IS NOT NULL
    """).df()

    rows, skipped = [], []
    for _, r in anchor.iterrows():
        parsed = _parse_geo(r["GEO"])
        if not parsed or r["pax"] < MIN_ANCHOR_PAX:
            continue
        (us_city, us_state), (ca_city, _) = parsed
        if ca_city not in CA_CITY_HUB:
            skipped.append(r["GEO"])
            continue
        cma_key, hub = CA_CITY_HUB[ca_city]
        ca_pop = next((v for k, v in cma.items()
                       if k.startswith(cma_key)), None)
        m = _match_us_metro(metros, us_city, US_STATE_CODE[us_state])
        if ca_pop is None or m is None or hub not in airports:
            skipped.append(r["GEO"])
            continue
        hlat, hlon = airports[hub]
        dist = haversine_mi(hlat, hlon, m["lat"], m["lon"])
        rows.append({
            "geo": r["GEO"], "hub": hub, "obs_2018": r["pax"],
            "pop_a": ca_pop, "pop_b": m["population"],
            "inc_a": m["income"],   # CA income proxy: matched US metro income;
                                    # constant-ish per hub, absorbed by factor
            "inc_b": m["income"], "dist_mi": dist,
        })
    df = pd.DataFrame(rows)
    df["gravity_pred"] = gravity.predict(df, "pre2022")
    df["transfer"] = df["obs_2018"] / df["gravity_pred"]

    # per-hub growth from T-100 (anchor year -> latest full year)
    growth = {}
    for hub in df["hub"].unique():
        g = con.execute("""
            WITH t AS (
              SELECT year, sum(passengers) AS pax FROM fact_segment
              WHERE service_class IN ('F','L')
                AND ((origin=? AND dest_country='US')
                  OR (dest=? AND origin_country='US'))
                AND year IN (2018, 2024)
              GROUP BY year
            )
            SELECT max(CASE WHEN year=2024 THEN pax END)
                 / max(CASE WHEN year=2018 THEN pax END) FROM t
        """, [hub, hub]).fetchone()[0]
        growth[hub] = float(g) if g else None

    med = float(df["transfer"].median())
    loo = [float(df.drop(i)["transfer"].median()) for i in df.index[:50]]
    out = {
        "anchor_year": int(ANCHOR_YEAR),
        "n_pairs": int(len(df)),
        "n_skipped": len(skipped),
        "median": med,
        "iqr": [float(df["transfer"].quantile(0.25)),
                float(df["transfer"].quantile(0.75))],
        "min": float(df["transfer"].min()),
        "max": float(df["transfer"].max()),
        "leave_one_out_median_range": [min(loo), max(loo)] if loo else None,
        "per_hub_median": {h: float(g["transfer"].median())
                           for h, g in df.groupby("hub") if len(g) >= 3},
        "growth_t100_2018_to_2024": growth,
        "note": "factor absorbs border, currency, survey-definition and model "
                "error; reported as a distribution, applied as per-hub median "
                "where n>=3 else national median",
    }
    (OUTPUTS / "transfer_factor.yaml").write_text(
        yaml.safe_dump(out, sort_keys=False))
    df.to_parquet(OUTPUTS / "transfer_pairs.parquet", index=False)
    con.close()
    return out


if __name__ == "__main__":
    o = estimate()
    print(f"pairs={o['n_pairs']} median={o['median']:.3f} "
          f"IQR={o['iqr']} hub medians={o['per_hub_median']}")
