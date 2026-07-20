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
        cand["cm"] = pd.to_numeric(cand["cbsa"].map(cm_of), errors="coerce")
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
        gravity_est = gravity.predict(cand, "current") * factor * growth
        anchor = con.execute("""
            SELECT GEO, try_cast(VALUE AS DOUBLE) AS pax
            FROM fact_od_transborder_2018
            WHERE REF_DATE='2018'
              AND Estimates='Number of outbound and inbound passengers'
        """).df()
        # Parse anchor pairs properly (city tokens AND state), not by raw
        # substring: "Columbia, SC" must not match "District of Columbia",
        # Portland ME must not match Portland OR, and StatCan's compound
        # names ("Dallas-Fort Worth, Texas", "Washington/Baltimore") must
        # still match their metros. City names are split into tokens on
        # both sides and compared exactly, gated on state.
        import re as _re
        from .transfer import CA_CITY_HUB, US_STATE_CODE, _parse_geo
        hub_city = {v[1]: k for k, v in CA_CITY_HUB.items()}.get(hub, "")
        def _tokens(city_str):
            return [t.strip().lower() for t in _re.split(r"[-/]", city_str)
                    if t.strip()]
        by_token_state: dict[tuple[str, str], float] = {}
        for _, ar in anchor.iterrows():
            parsed = _parse_geo(ar["GEO"])
            if not parsed:
                continue
            (us_city, us_state), (ca_city, _) = parsed
            if ca_city != hub_city or pd.isna(ar["pax"]):
                continue
            for tok in _tokens(us_city):
                key = (tok, US_STATE_CODE[us_state])
                by_token_state[key] = max(by_token_state.get(key, 0.0),
                                          float(ar["pax"]))
        def find_anchor(name):
            city_part, _, state_part = name.rpartition(",")
            states = [s.strip() for s in state_part.split("-")]
            for tok in _tokens(city_part):
                for st in states:
                    if (tok, st) in by_token_state:
                        return by_token_state[(tok, st)]
            return np.nan
        cand["anchor_2018_pax"] = cand["metro_name"].map(find_anchor)

        # Market-specific evidence beats the hub median: where the pair has
        # its own 2018 anchor, demand = anchor x T-100 corridor growth.
        # Gravity x hub-median transfer is the fallback for unanchored pairs
        # only. No shrinkage applied: every anchor already clears the
        # survey's own >4,000 pax floor (documented choice).
        has_anchor = cand["anchor_2018_pax"].notna()
        anchor_est = cand["anchor_2018_pax"] * growth

        # Negative-space cap: a market ABSENT from the 2018 StatCan >4,000
        # city-pair table had at most 4,000 transborder O&D that year, by
        # construction (the table is O&D, so even latent connect demand would
        # have registered). Absence is therefore evidence of a small market,
        # and the US-calibrated gravity model routinely over-predicts these
        # (4,700-36,000 pax for markets known to be <4,000). We cap the
        # unanchored estimate at the survey threshold scaled by corridor
        # growth: a generous upper bound (~4,660 for YYC) that keeps a real
        # opportunity from being missed while stopping right-sizing from
        # manufacturing LAUNCHes out of gravity noise on tiny markets.
        SURVEY_THRESHOLD = 4000.0
        ceiling = SURVEY_THRESHOLD * growth
        unanchored_est = np.minimum(gravity_est, ceiling)
        cand["demand_pax_yr"] = np.where(has_anchor, anchor_est,
                                         unanchored_est)
        cand["demand_method"] = np.where(
            has_anchor, "anchor_x_growth",
            np.where(gravity_est > ceiling, "unanchored_capped_at_ceiling",
                     "gravity_x_transfer"))
        cand["survey_ceiling_pax"] = ceiling
        cand["gravity_implied_pax"] = gravity_est
        # diagnostic: what the gravity path would have said, relative to the
        # market's own last observed actual. Visible on every screen row.
        cand["implied_vs_anchor_ratio"] = np.where(
            has_anchor, gravity_est / anchor_est, np.nan)
        cand["demand_source"] = "modeled"
        cand["transfer_factor"] = factor
        cand["t100_growth"] = growth
        cand["fare_observed"] = np.nan
        out = cand
    con.close()

    keep = [c for c in ["study_id", "hub", "carrier", "dest_airport", "cbsa",
                        "metro_name", "dist_mi", "pop", "income",
                        "nonstop_by_others", "demand_pax_yr", "demand_source",
                        "demand_method", "gravity_implied_pax",
                        "survey_ceiling_pax", "implied_vs_anchor_ratio",
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
