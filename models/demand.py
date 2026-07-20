"""Demand resolution: observed where it exists, modeled where it does not.

US domestic candidate markets -> DB1B observed city-market O&D (flag
'observed'); pairs too thin for DB1B fall back to the gravity model (flag
'modeled'). Transborder candidate markets -> gravity x transfer x growth
(flag 'modeled'), with the 2018 StatCan anchor value reported alongside when
the pair existed then. No exceptions: every row carries demand_source.

Consistency note: the Canadian endpoint's income covariate is proxied by the
destination metro's income, exactly as in transfer-factor estimation, so the
proxy's level error cancels through the ratio.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import yaml

from . import candidates, gravity
from .common import OUTPUTS, connect, study


def _observed_us(con, hub: str, year: int = 2024) -> pd.DataFrame:
    """DB1B city-market O&D pax/fare from the hub's city market, by dest cm."""
    return con.execute("""
        WITH hub_cm AS (
          SELECT city_market_id FROM dim_airport WHERE iata_code = ?
        )
        SELECT CASE WHEN origin_cm = h.city_market_id THEN dest_cm
                    ELSE origin_cm END AS other_cm,
               sum(passengers_est) AS pax_yr,
               sum(mkt_fare*passengers_est)/sum(passengers_est) AS avg_fare
        FROM fact_od_market, hub_cm h
        WHERE (origin_cm = h.city_market_id OR dest_cm = h.city_market_id)
          AND year = ?
        GROUP BY 1
    """, [hub, year]).df()


def resolve(study_id: str) -> pd.DataFrame:
    cfg = study(study_id)
    cand = candidates.generate(study_id)
    con = connect(read_only=True)

    if cfg["market_scope"] == "us_domestic":
        obs = _observed_us(con, cfg["hub"])
        cm_of = dict(con.execute("""
            SELECT m.cbsa, a.city_market_id
            FROM map_citymarket_cbsa m JOIN dim_airport a USING (city_market_id)
        """).fetchall())
        hub_metro = con.execute("""
            SELECT d.population, d.income FROM dim_airport a
            JOIN map_citymarket_cbsa m USING (city_market_id)
            JOIN dim_metro_us d USING (cbsa)
            WHERE a.iata_code = ?
        """, [cfg["hub"]]).fetchone()
        cand["pop_a"], cand["inc_a"] = hub_metro
        cand["pop_b"], cand["inc_b"] = cand["pop"], cand["income"]
        cand["cm"] = cand["cbsa"].map(cm_of)
        merged = cand.merge(obs, left_on="cm", right_on="other_cm", how="left")
        thin = merged["pax_yr"].isna() | (merged["pax_yr"] < 4000)
        merged["demand_pax_yr"] = merged["pax_yr"]
        merged.loc[thin, "demand_pax_yr"] = gravity.predict(
            merged.loc[thin], "current")
        merged["demand_source"] = np.where(thin, "modeled", "observed")
        merged["fare_observed"] = merged["avg_fare"]
        out = merged
    else:   # transborder
        tf = yaml.safe_load((OUTPUTS / "transfer_factor.yaml").read_text())
        hub = cfg["hub"]
        factor = tf["per_hub_median"].get(hub, tf["median"])
        growth = tf["growth_t100_2018_to_2024"].get(hub) or 1.0
        hub_pop = con.execute("""
            SELECT m.population FROM ca_airport_cma c
            JOIN dim_metro_ca m ON m.cma LIKE c.cma_name || '%'
            WHERE c.iata_code = ?
        """, [hub]).fetchone()[0]
        cand["pop_a"] = hub_pop
        cand["pop_b"] = cand["pop"]
        cand["inc_a"] = cand["income"]     # destination-income proxy, see doc
        cand["inc_b"] = cand["income"]
        cand["demand_pax_yr"] = (gravity.predict(cand, "current")
                                 * factor * growth)
        cand["demand_source"] = "modeled"
        cand["transfer_factor"] = factor
        cand["t100_growth"] = growth
        cand["fare_observed"] = np.nan
        # report the frozen anchor value alongside where the pair existed
        anchor = con.execute("""
            SELECT GEO, try_cast(VALUE AS DOUBLE) AS pax
            FROM fact_od_transborder_2018
            WHERE REF_DATE='2018'
              AND Estimates='Number of outbound and inbound passengers'
        """).df()
        city = {"YYC": "Calgary", "YYZ": "Toronto", "YUL": "Montréal",
                "YVR": "Vancouver", "YEG": "Edmonton"}.get(hub, "")
        sub = anchor[anchor["GEO"].str.contains(city, na=False)]
        def find_anchor(name):
            us_city = name.split("-")[0].split(",")[0].strip()
            hit = sub[sub["GEO"].str.contains(us_city, na=False, regex=False)]
            return float(hit["pax"].iloc[0]) if len(hit) else np.nan
        cand["anchor_2018_pax"] = cand["metro_name"].map(find_anchor)
        out = cand
    con.close()

    keep = [c for c in ["study_id", "hub", "carrier", "dest_airport", "cbsa",
                        "metro_name", "dist_mi", "pop", "income",
                        "nonstop_by_others", "demand_pax_yr", "demand_source",
                        "fare_observed", "transfer_factor", "t100_growth",
                        "anchor_2018_pax"] if c in out.columns]
    res = out[keep].copy()
    res.to_parquet(OUTPUTS / f"demand_{study_id}.parquet", index=False)
    return res


if __name__ == "__main__":
    for s in ("westjet_yyc", "alaska_sea", "porter_yyz"):
        try:
            df = resolve(s)
            src = df["demand_source"].value_counts().to_dict()
            print(f"{s}: {len(df)} markets, {src}")
        except Exception as e:  # noqa: BLE001
            print(f"{s}: {e}")
