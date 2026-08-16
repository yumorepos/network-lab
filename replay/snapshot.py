"""snapshot(t): the frozen model's full verdict chain, as of a decision date.

W1.3. Reconstructs candidates, demand, competition and share, economics,
right-sizing and verdict using only data a decision at `t` could have read.

**This measures the frozen model. It does not improve it.** Every scoring
function is imported from `models/` rather than reimplemented: spill, QSI
share, block hours, comparator rates, the fare curve, gravity prediction, the
service-selection rule and the verdict rule are all the production code. What
this module re-implements is the vintage-sensitive *queries*, and it is guarded
by `tests/test_replay_parity.py`, which asserts that a snapshot pinned to
production vintages reproduces all 200 committed verdicts exactly. A
reimplementation that cannot disagree with production is not a reimplementation
risk; that guard is the reason this design is safe, and it is the guard
`models/share_validation.py` lacked when it silently diverged (round 4).

Nothing here writes to the warehouse, to `data/parquet/outputs/`, or to any
tracked file.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import yaml

from models import carriers, gravity, spill
from models.catchment import metro_anchor_points
from models.common import OUTPUTS, assumptions, connect, haversine_mi, study
from models.competition import (DETOUR_ABS_MI, DETOUR_MAX, MIN_SEGMENT_DEPS_YR,
                                _block_hours, share_at_freq)
from models.demand import anchor_finder
from models.economics import (DIRECTIONS_PER_ROUTE, E2_FUEL_IMPROVEMENT,
                              block_hours, comparator_rates, fare_curve,
                              fuel_price_base)
from models.screen import BELF_MAX, _select_service, confidence, top_risk
from models.transfer import (CA_CITY_HUB, MIN_ANCHOR_PAX, US_STATE_CODE,
                             _cma_population, _match_us_metro, _parse_geo)
from replay import pit_metros
from replay.vintage import Cutoff, Provenance

# Gravity calibration windows, read from the frozen estimator's own vintages.
GRAVITY_WINDOWS = {"pre2022": (2018, 2019), "current": (2023, 2024)}


@dataclass
class Vintages:
    """Every vintage question, answered. Immutable input to the chain."""
    label: str
    t100_max_ym: int
    db1b_year: int
    form41_year: int
    bea_year: int
    ca_year: int
    anchor_year: int
    gravity_vintage: str
    seats_year: int
    growth_year: int
    fuel_as_of: str | None
    geography_vintage: str
    provenance: list[Provenance] = field(default_factory=list)

    def provenance_frame(self) -> pd.DataFrame:
        return pd.DataFrame([p.as_row() for p in self.provenance])


def cached_years(con) -> dict[str, set[int]]:
    q = lambda s: {int(r[0]) for r in con.execute(s).fetchall()}  # noqa: E731
    return {
        "db1b": q("SELECT DISTINCT year FROM fact_od_market"),
        "form41": q("SELECT DISTINCT YEAR FROM fact_costs"),
        "t100": q("SELECT DISTINCT year FROM fact_segment"),
        "bea": set(pit_metros.available_years()["us"]),
        "ca": set(pit_metros.available_years()["ca"]),
        "anchor": q("SELECT DISTINCT try_cast(REF_DATE AS INT) "
                    "FROM fact_od_transborder_2018 "
                    "WHERE try_cast(REF_DATE AS INT) IS NOT NULL"),
    }


def resolve_vintages(cutoff_ym: int, con) -> Vintages:
    """Every source resolved against a decision date. Fails closed."""
    c = Cutoff(cutoff_ym)
    cy = cached_years(con)
    t100_max = c.t100_max_ym()
    v = Vintages(
        label=c.label,
        t100_max_ym=t100_max,
        db1b_year=c.db1b_year(cy["db1b"]),
        form41_year=c.form41_year(cy["form41"]),
        bea_year=c.bea_year(cy["bea"]),
        ca_year=c.statcan_cma_year(cy["ca"]),
        anchor_year=c.statcan_transborder_year(cy["anchor"]),
        gravity_vintage=c.gravity_vintage(GRAVITY_WINDOWS),
        seats_year=c.t100_seats_year(cy["t100"], t100_max),
        growth_year=c.t100_corridor_growth_year(cy["t100"], t100_max),
        fuel_as_of=c.eia_fuel_as_of(),
        geography_vintage=c.geography_vintage(),
    )
    c.carrier_brand_vintage()
    v.provenance = list(c.provenance)
    return v


def production_vintages() -> Vintages:
    """The vintages the shipped pipeline actually uses. Parity target only.

    These are what `models/` hardcodes today, several of them stale relative to
    the data (seats_year 2024 against a panel running to 2026-04 is W1.3 audit
    vector L10). Reproduced here exactly so the parity test isolates
    pipeline-equivalence from vintage-selection.
    """
    return Vintages(
        label="production", t100_max_ym=0, db1b_year=2024, form41_year=2024,
        bea_year=2024, ca_year=0, anchor_year=2018, gravity_vintage="current",
        seats_year=2024, growth_year=0, fuel_as_of=None,
        geography_vintage="2023")


# --------------------------------------------------------------- layer 1
def build_candidates(study_id: str, con, v: Vintages) -> pd.DataFrame:
    """PIT candidate set. Mirrors models/candidates.generate() with the metro
    covariates, the seats year and the served-market window taken at vintage."""
    cfg = study(study_id)
    a = assumptions()
    hub, carrier = cfg["hub"], cfg["carrier"]
    dmin = cfg["candidates"]["distance_nm"]["min"] * 1.15078
    dmax = cfg["candidates"]["distance_nm"]["max"] * 1.15078
    min_pop = float(a["candidate_min_metro_pop"]["value"])
    min_seats = float(a["candidate_min_airport_seats_yr"]["value"])
    min_deps = float(a["served_market_min_deps_yr"]["value"])
    sat = a["satellite_airport_rule"]

    override = (None if v.label == "production"
                else pit_metros.us_at(v.bea_year)[
                    ["cbsa", "population", "income", "gdp_kusd"]])
    metros = metro_anchor_points(con, seats_year=v.seats_year,
                                 metro_override=override)
    hub_pt = con.execute(
        "SELECT lat, lon FROM dim_airport WHERE iata_code=?", [hub]).fetchone()

    carriers.register_segment_brands(con, min_deps=1)
    win_clause = ("(SELECT max(year::INT*100+month) - 100 FROM fact_segment "
                  " WHERE service_class IN ('F','L'))"
                  if v.label == "production" else str(v.t100_max_ym - 100))
    upper = ("" if v.label == "production"
             else f"AND (s.year::INT*100+s.month) <= {v.t100_max_ym}")
    served = con.execute(f"""
        SELECT m.cbsa AS cbsa, coalesce(b.brand, s.carrier) AS brand,
               sum(s.departures) AS deps
        FROM fact_segment s
        JOIN dim_airport a2 ON a2.iata_code = s.dest
        JOIN map_citymarket_cbsa m ON m.city_market_id = a2.city_market_id
        LEFT JOIN map_segment_brand b
               ON b.op_carrier = s.carrier
              AND b.origin = s.origin AND b.dest = s.dest
        WHERE s.origin = ? AND s.service_class IN ('F','L')
          AND s.dest_country = 'US'
          AND (s.year::INT*100+s.month) > {win_clause} {upper}
        GROUP BY 1, 2
    """, [hub]).df()
    served_by_study = set(served[(served["brand"] == carrier)
                                 & (served["deps"] >= min_deps)]["cbsa"])
    served_by_any = set(served[served["deps"] >= min_deps]["cbsa"])

    def is_satellite(m) -> bool:
        near = metros[(metros["cbsa"] != m["cbsa"])
                      & (metros["anchor_seats_yr"]
                         >= sat["seat_ratio"] * max(m["anchor_seats_yr"], 1))]
        return any(haversine_mi(m["lat"], m["lon"], n["lat"], n["lon"])
                   <= sat["radius_mi"] for _, n in near.iterrows())

    rows = []
    for _, m in metros.iterrows():
        if m["population"] is None or m["population"] < min_pop:
            continue
        dist = haversine_mi(hub_pt[0], hub_pt[1], m["lat"], m["lon"])
        if not (dmin <= dist <= dmax):
            continue
        if m["cbsa"] in served_by_study or m["anchor_seats_yr"] < min_seats:
            continue
        if is_satellite(m):
            continue
        rows.append({
            "study_id": study_id, "hub": hub, "carrier": carrier,
            "dest_airport": m["anchor_airport"], "cbsa": m["cbsa"],
            "metro_name": m["cbsa_name"], "dist_mi": dist,
            "pop": float(m["population"]), "income": float(m["income"]),
            "gdp_kusd": float(m["gdp_kusd"]) if m["gdp_kusd"] else None,
            "nonstop_by_others": m["cbsa"] in served_by_any,
        })
    return (pd.DataFrame(rows).sort_values("pop", ascending=False)
            .reset_index(drop=True))


# --------------------------------------------------------------- layer 2
def build_transfer(con, v: Vintages) -> dict:
    """Transfer factor at vintage. Same construction as models/transfer.py:
    observed anchor over gravity prediction, per-hub median where n >= 3."""
    if v.label == "production":
        return yaml.safe_load((OUTPUTS / "transfer_factor.yaml").read_text())

    # The corridor growth year is the largest single lever on transborder
    # demand: the ratio multiplies every anchored and every capped row. Taking
    # it from the panel end instead of the permitted window multiplies 2023-01
    # YYC demand by 5.73. Resolved and recorded in replay/vintage.py; this is
    # the use-site check, deliberate redundancy against a later edit handing
    # this layer a year the T-100 window does not permit.
    if v.growth_year * 100 + 12 > v.t100_max_ym:
        raise ValueError(
            f"corridor growth year {v.growth_year} is not a complete year "
            f"within the permitted T-100 window {v.t100_max_ym} at cutoff "
            f"{v.label}. The replay fails closed rather than applying a "
            "growth ratio the decision could not have computed.")

    metros = metro_anchor_points(
        con, seats_year=v.seats_year,
        metro_override=pit_metros.us_at(v.bea_year)[
            ["cbsa", "population", "income", "gdp_kusd"]])
    ca = pit_metros.ca_at(v.ca_year)
    cma = dict(zip(ca["cma"], ca["population"]))
    airports = dict((r[0], (r[1], r[2])) for r in con.execute(
        "SELECT iata_code, lat, lon FROM dim_airport").fetchall())
    anchor = con.execute("""
        SELECT GEO, try_cast(VALUE AS DOUBLE) AS pax
        FROM fact_od_transborder_2018
        WHERE REF_DATE = ?
          AND Estimates='Number of outbound and inbound passengers'
          AND GEO != 'Other cities' AND VALUE IS NOT NULL
    """, [str(v.anchor_year)]).df()

    rows = []
    for _, r in anchor.iterrows():
        parsed = _parse_geo(r["GEO"])
        if not parsed or r["pax"] < MIN_ANCHOR_PAX:
            continue
        (us_city, us_state), (ca_city, _) = parsed
        if ca_city not in CA_CITY_HUB:
            continue
        cma_key, hub = CA_CITY_HUB[ca_city]
        ca_pop = _cma_population(cma, cma_key)
        m = _match_us_metro(metros, us_city, US_STATE_CODE[us_state])
        if ca_pop is None or m is None or hub not in airports:
            continue
        hlat, hlon = airports[hub]
        rows.append({"hub": hub, "obs": r["pax"], "pop_a": ca_pop,
                     "pop_b": m["population"], "inc_a": m["income"],
                     "inc_b": m["income"],
                     "dist_mi": haversine_mi(hlat, hlon, m["lat"], m["lon"])})
    df = pd.DataFrame(rows)
    df["gravity_pred"] = gravity.predict(df, v.gravity_vintage)
    df["transfer"] = df["obs"] / df["gravity_pred"]

    # Resolved and recorded in replay/vintage.py, not recomputed here: this
    # line used to select the year itself, which is how the lever came to
    # carry no provenance record at all (P1-1). Same rule, same value, now
    # declared and guarded above.
    latest_full = v.growth_year
    growth = {}
    for hub in df["hub"].unique():
        g = con.execute("""
            WITH t AS (
              SELECT year, sum(passengers) AS pax FROM fact_segment
              WHERE service_class IN ('F','L')
                AND ((origin=? AND dest_country='US')
                  OR (dest=? AND origin_country='US'))
                AND year IN (?, ?)
              GROUP BY year
            )
            SELECT max(CASE WHEN year=? THEN pax END)
                 / max(CASE WHEN year=? THEN pax END) FROM t
        """, [hub, hub, v.anchor_year, latest_full,
              latest_full, v.anchor_year]).fetchone()[0]
        growth[hub] = float(g) if g else None
    return {
        "anchor_year": v.anchor_year,
        "growth_year": latest_full,
        "n_pairs": int(len(df)),
        "median": float(df["transfer"].median()),
        "per_hub_median": {h: float(g["transfer"].median())
                           for h, g in df.groupby("hub") if len(g) >= 3},
        "growth_t100": growth,
    }


def build_demand(study_id: str, con, v: Vintages, cand: pd.DataFrame,
                 tf: dict) -> pd.DataFrame:
    cfg = study(study_id)
    hub = cfg["hub"]
    cand = cand.copy()

    if cfg["market_scope"] == "us_domestic":
        obs = con.execute("""
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
        """, [hub, v.db1b_year]).df()
        cm_map = con.execute("""
            SELECT DISTINCT m.cbsa, a.city_market_id AS cm
            FROM map_citymarket_cbsa m JOIN dim_airport a USING (city_market_id)
        """).df()
        hub_metro = con.execute("""
            SELECT d.population, d.income FROM dim_airport a
            JOIN map_citymarket_cbsa m USING (city_market_id)
            JOIN dim_metro_us d USING (cbsa) WHERE a.iata_code = ?
        """, [hub]).fetchone()
        if v.label != "production":
            pit = pit_metros.us_at(v.bea_year)
            hub_cbsa = con.execute("""
                SELECT m.cbsa FROM dim_airport a
                JOIN map_citymarket_cbsa m USING (city_market_id)
                WHERE a.iata_code = ?
            """, [hub]).fetchone()[0]
            hr = pit[pit["cbsa"] == hub_cbsa]
            if len(hr):
                hub_metro = (float(hr["population"].iloc[0]),
                             float(hr["income"].iloc[0]))
        cand["pop_a"], cand["inc_a"] = hub_metro
        cand["pop_b"], cand["inc_b"] = cand["pop"], cand["income"]
        cm_map["cm"] = pd.to_numeric(cm_map["cm"], errors="coerce")
        obs_by_cbsa = (cm_map.dropna(subset=["cm"])
                       .merge(obs, left_on="cm", right_on="other_cm")
                       .groupby("cbsa")
                       .apply(lambda g: pd.Series({
                           "pax_yr": g["pax_yr"].sum(),
                           "avg_fare": (g["avg_fare"] * g["pax_yr"]).sum()
                                       / g["pax_yr"].sum()
                                       if g["pax_yr"].sum() else np.nan}),
                              include_groups=False)
                       .reset_index())
        merged = cand.merge(obs_by_cbsa, on="cbsa", how="left")
        thin = merged["pax_yr"].isna() | (merged["pax_yr"] < 4000)
        merged["demand_pax_yr"] = merged["pax_yr"]
        merged.loc[thin, "demand_pax_yr"] = gravity.predict(
            merged.loc[thin], v.gravity_vintage)
        merged["demand_source"] = np.where(thin, "modeled", "observed")
        merged["demand_method"] = np.where(thin, "gravity_thin",
                                           "observed_db1b")
        merged["fare_observed"] = merged["avg_fare"]
        out = merged
    else:
        factor = tf["per_hub_median"].get(hub, tf["median"])
        gkey = "growth_t100" if "growth_t100" in tf else "growth_t100_2018_to_2024"
        growth = tf[gkey].get(hub) or 1.0
        if v.label == "production":
            hub_pop = con.execute(
                "SELECT population FROM map_ca_airport_metro WHERE iata_code=?",
                [hub]).fetchone()[0]
        else:
            cma_key = {v2[1]: v2[0] for v2 in CA_CITY_HUB.values()}
            key = next(k for k, val in CA_CITY_HUB.items() if val[1] == hub)
            ca = pit_metros.ca_at(v.ca_year)
            hub_pop = _cma_population(
                dict(zip(ca["cma"], ca["population"])), CA_CITY_HUB[key][0])
        cand["pop_a"] = hub_pop
        cand["pop_b"] = cand["pop"]
        cand["inc_a"] = cand["income"]      # destination-income proxy
        cand["inc_b"] = cand["income"]
        gravity_est = (gravity.predict(cand, v.gravity_vintage)
                       * factor * growth)
        cand["anchor_2018_pax"] = cand["metro_name"].map(
            anchor_finder(con, hub, str(v.anchor_year)))
        has_anchor = cand["anchor_2018_pax"].notna()
        anchor_est = cand["anchor_2018_pax"] * growth
        # FROZEN MODEL PARAMETER. Stage 0 established the true StatCan
        # publication floor moves by vintage (280 to 3,090). That is recorded
        # as a baseline defect in docs/W1_REPLAY_FEASIBILITY.md section 5b and
        # is deliberately NOT fixed here: Milestone A measures the frozen
        # model. Do not replace this with a per-vintage floor.
        SURVEY_THRESHOLD = 4000.0
        ceiling = SURVEY_THRESHOLD * growth
        cand["demand_pax_yr"] = np.where(has_anchor, anchor_est,
                                         np.minimum(gravity_est, ceiling))
        cand["demand_method"] = np.where(
            has_anchor, "anchor_x_growth",
            np.where(gravity_est > ceiling, "unanchored_capped_at_ceiling",
                     "gravity_x_transfer"))
        cand["gravity_implied_pax"] = gravity_est
        cand["survey_ceiling_pax"] = ceiling
        cand["implied_vs_anchor_ratio"] = np.where(
            has_anchor, gravity_est / anchor_est, np.nan)
        cand["demand_source"] = "modeled"
        cand["fare_observed"] = np.nan
        out = cand
    return out


# --------------------------------------------------------------- layer 3
def build_share(study_id: str, con, v: Vintages,
                dem: pd.DataFrame) -> pd.DataFrame:
    cfg = study(study_id)
    a = assumptions()
    hub = cfg["hub"]
    w = a["qsi_weights"]
    f_exp, t_exp = w["frequency_exponent"], a["qsi_elapsed_time_exponent"]["value"]
    ref_freq = cfg["candidates"]["target_frequency_weekly"][1]

    con.register("cand_dest", dem[["cbsa", "dest_airport", "dist_mi"]])
    win = (con.execute("SELECT max(year::INT*100+month) FROM fact_segment "
                       "WHERE service_class IN ('F','L')").fetchone()[0]
           if v.label == "production" else v.t100_max_ym)
    carriers.register_segment_brands(con, MIN_SEGMENT_DEPS_YR)
    con.execute(f"""
        CREATE OR REPLACE TEMP VIEW seg12 AS
        SELECT coalesce(b.brand, s.carrier) AS carrier,
               s.origin, s.dest, max(s.distance_mi) AS distance_mi,
               sum(s.departures) / 52.0 AS freq_wk,
               string_agg(DISTINCT s.carrier, '+' ORDER BY s.carrier)
                 AS op_carriers
        FROM fact_segment s
        LEFT JOIN map_segment_brand b
               ON b.op_carrier = s.carrier
              AND b.origin = s.origin AND b.dest = s.dest
        WHERE s.service_class IN ('F','L')
          AND (s.year::INT*100+s.month) > {win} - 100
          AND (s.year::INT*100+s.month) <= {win}
          AND s.departures > 0 AND s.seats > 0
        GROUP BY 1,2,3
        HAVING sum(s.departures) >= {MIN_SEGMENT_DEPS_YR}
    """)
    con.execute("""
        CREATE OR REPLACE TEMP VIEW dest_airports AS
        SELECT DISTINCT c.cbsa, a.iata_code AS dest_ap
        FROM cand_dest c
        JOIN map_citymarket_cbsa m ON m.cbsa = c.cbsa
        JOIN dim_airport a ON a.city_market_id = m.city_market_id
    """)
    nonstop = con.execute(f"""
        SELECT c.cbsa, s.carrier, 'nonstop' AS itin_type, s.freq_wk,
               s.distance_mi AS total_dist
        FROM seg12 s JOIN dest_airports d ON d.dest_ap = s.dest
        JOIN cand_dest c ON c.cbsa = d.cbsa
        WHERE s.origin = '{hub}'
    """).df()
    onestop = con.execute(f"""
        SELECT c.cbsa, l1.carrier, 'onestop' AS itin_type,
               least(l1.freq_wk, l2.freq_wk) AS freq_wk,
               l1.distance_mi + l2.distance_mi AS total_dist
        FROM seg12 l1
        JOIN seg12 l2 ON l2.carrier = l1.carrier AND l2.origin = l1.dest
        JOIN dest_airports d ON d.dest_ap = l2.dest
        JOIN cand_dest c ON c.cbsa = d.cbsa
        WHERE l1.origin = '{hub}' AND l1.dest != '{hub}'
          AND l1.distance_mi + l2.distance_mi
              <= least(c.dist_mi + {DETOUR_ABS_MI}, {DETOUR_MAX} * c.dist_mi)
          AND least(l1.freq_wk, l2.freq_wk) >= 3
    """).df()
    connect_h = a["connect_time_minutes"]["value"] / 60.0
    over = a["block_time_model"]["taxi_climb_overhead_hours"]
    for df, extra in ((nonstop, 0.0), (onestop, connect_h + over)):
        if len(df):
            df["elapsed_h"] = _block_hours(df["total_dist"].astype(float)) + extra
    comp = pd.concat([nonstop, onestop], ignore_index=True)

    rows = []
    for _, c in dem.iterrows():
        mine = comp[comp["cbsa"] == c["cbsa"]]
        prop = float(_block_hours(c["dist_mi"]))
        fastest = min([prop] + mine["elapsed_h"].tolist())
        cps = sum(
            (w["nonstop"] if r["itin_type"] == "nonstop" else w["single_connect"])
            * r["freq_wk"] ** f_exp * (r["elapsed_h"] / fastest) ** t_exp
            for _, r in mine.iterrows())
        rows.append({
            "cbsa": c["cbsa"], "proposed_elapsed_h": prop,
            "fastest_elapsed_h": fastest, "comp_pref_sum": cps,
            "proposed_share": share_at_freq(ref_freq, prop, fastest, cps,
                                            w, f_exp, t_exp),
            "n_nonstop_incumbents": int((mine["itin_type"] == "nonstop").sum()),
            "n_onestop_carriers": int(mine[mine["itin_type"] == "onestop"]
                                      ["carrier"].nunique()),
            "top_competitor": (mine.sort_values("freq_wk", ascending=False)
                               ["carrier"].iloc[0] if len(mine) else None),
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------- layer 4/5
def build_economics(study_id: str, con, v: Vintages, dem: pd.DataFrame,
                    shr: pd.DataFrame) -> pd.DataFrame:
    cfg, a = study(study_id), assumptions()
    # fuel_price_base falls back to the panel end on None, which is future
    # information at every historical cutoff and moves the 2022-01 price by
    # +43.0% straight into margin_pct. Refuse the fallback rather than take it
    # silently. Recorded as a provenance entry in replay/vintage.py.
    if v.label != "production" and v.fuel_as_of is None:
        raise ValueError(
            f"no fuel vintage resolved at cutoff {v.label}; fuel_price_base "
            "would fall back to the latest observation in the panel.")
    comp_cfg = cfg["economics"]["cost_comparator"]
    if comp_cfg == "from_assumptions":
        if cfg["carrier"] == "PD":
            rates = comparator_rates(a["porter_cost_comparator_carrier"]["value"],
                                     year=v.form41_year, aircraft_like="%190%")
            rates["burn_gph"] *= (1 - E2_FUEL_IMPROVEMENT)
        else:
            rates = comparator_rates(a["cost_comparator_carrier"]["value"],
                                     year=v.form41_year)
    else:
        rates = comparator_rates(comp_cfg, year=v.form41_year)

    w = a["qsi_weights"]
    f_exp, t_exp = w["frequency_exponent"], a["qsi_elapsed_time_exponent"]["value"]
    freqs = cfg["candidates"]["target_frequency_weekly"]
    gauges = cfg.get("gauges") or [{"type": cfg["fleet"]["type"],
                                    "seats": cfg["fleet"]["seats"]}]
    fee = a["airport_fee_proxy"]
    premium = (a["transborder_fare_premium"]["value"]
               if cfg["market_scope"] == "transborder" else 1.0)
    p_base = fuel_price_base(con, v.fuel_as_of)
    curve = fare_curve(con, v.db1b_year)
    m = dem.merge(shr, on="cbsa")

    rows = []
    for _, r in m.iterrows():
        bh = block_hours(r["dist_mi"])
        fare_base = (r["fare_observed"]
                     if pd.notna(r.get("fare_observed", np.nan))
                     else float(curve(r["dist_mi"])) * premium)
        for g in gauges:
            seats = g["seats"]
            burn = rates["burn_gph"] * (seats / cfg["fleet"]["seats"])
            for freq_wk in freqs:
                shrv = share_at_freq(freq_wk, r["proposed_elapsed_h"],
                                     r["fastest_elapsed_h"], r["comp_pref_sum"],
                                     w, f_exp, t_exp)
                carried = r["demand_pax_yr"] * shrv
                deps_yr = freq_wk * 52 * DIRECTIONS_PER_ROUTE
                ppd = spill.expected_boardings(carried / deps_yr, seats)
                for f_pct in a["fare_scenario_grid_pct"]["value"]:
                    for g_pct in a["fuel_scenario_grid"]["value"]:
                        fare = fare_base * (1 + f_pct / 100)
                        gal = p_base * (1 + g_pct / 100)
                        doc = (rates["crew_ph"] + rates["maint_ph"]
                               + rates["own_ph"] + rates["other_ph"]) * bh
                        cost = ((burn * gal * bh + doc) * rates["indirect_mult"]
                                + fee["per_departure_usd"]
                                + fee["per_seat_usd"] * seats)
                        rev = fare * ppd
                        rows.append({
                            "study_id": study_id, "cbsa": r["cbsa"],
                            "metro_name": r["metro_name"],
                            "dest_airport": r["dest_airport"],
                            "dist_mi": r["dist_mi"],
                            "gauge_type": g["type"], "seats": seats,
                            "freq_wk": freq_wk,
                            "fare_scenario_pct": f_pct,
                            "fuel_scenario_pct": g_pct,
                            "pax_per_dep": ppd, "load_factor": ppd / seats,
                            "annual_contribution": deps_yr * (rev - cost),
                            "margin_pct": (100 * (rev - cost) / rev
                                           if rev else np.nan),
                            "belf": cost / (fare * seats) if fare else np.nan,
                            "demand_source": r["demand_source"],
                            "demand_method": r.get("demand_method",
                                                   "observed_db1b"),
                            "implied_vs_anchor_ratio":
                                r.get("implied_vs_anchor_ratio", np.nan),
                            "anchor_2018_pax": r.get("anchor_2018_pax", np.nan),
                            "proposed_share": shrv,
                            "demand_pax_yr": r["demand_pax_yr"],
                            "n_nonstop_incumbents": r["n_nonstop_incumbents"],
                            "top_competitor": r["top_competitor"],
                        })
    return pd.DataFrame(rows)


def build_screen(study_id: str, eco: pd.DataFrame) -> pd.DataFrame:
    """Verdict, using the production selection and verdict rules."""
    a = assumptions()
    hurdle = float(a["hurdle_margin_pct"]["value"])
    lf_floor = float(a["min_feasible_load_factor"]["value"])
    base_all = eco[(eco.fare_scenario_pct == 0) & (eco.fuel_scenario_pct == 0)]
    m = _select_service(base_all, lf_floor).rename(
        columns={"freq_wk": "chosen_freq_wk", "seats": "chosen_seats",
                 "gauge_type": "chosen_gauge"})
    key = ["cbsa", "chosen_freq_wk", "chosen_seats"]
    fare_dn = (eco[(eco.fare_scenario_pct == eco.fare_scenario_pct.min())
                   & (eco.fuel_scenario_pct == 0)]
               .rename(columns={"freq_wk": "chosen_freq_wk",
                                "seats": "chosen_seats",
                                "margin_pct": "fare_down_margin"}))
    fuel_up = (eco[(eco.fare_scenario_pct == 0)
                   & (eco.fuel_scenario_pct == eco.fuel_scenario_pct.max())]
               .rename(columns={"freq_wk": "chosen_freq_wk",
                                "seats": "chosen_seats",
                                "margin_pct": "fuel_down_margin"}))
    m = (m.merge(fare_dn[key + ["fare_down_margin"]], on=key)
          .merge(fuel_up[key + ["fuel_down_margin"]], on=key))

    def verdict(r):
        if pd.isna(r["margin_pct"]) or r["margin_pct"] < 0:
            return "PASS"
        if (r["margin_pct"] >= hurdle and r["fare_down_margin"] > 0
                and r["belf"] <= BELF_MAX):
            return "LAUNCH"
        return "MONITOR"

    m["verdict"] = m.apply(verdict, axis=1)
    m["share_uncertainty"] = ((m["proposed_share"] > 0.70)
                              & (m["n_nonstop_incumbents"] == 0))
    m.loc[m["share_uncertainty"] & (m["verdict"] == "LAUNCH"),
          "verdict"] = "MONITOR"
    m["confidence"] = m.apply(confidence, axis=1)
    m.loc[m["share_uncertainty"], "confidence"] = "low"
    m["top_risk"] = m.apply(top_risk, axis=1)
    return m.reset_index(drop=True)


# ------------------------------------------------------------------ driver
def snapshot(study_id: str, cutoff_ym: int | None = None,
             con=None) -> dict:
    """Full verdict chain as of `cutoff_ym`. None means production vintages."""
    own = con is None
    con = con or connect(read_only=True)
    try:
        v = (production_vintages() if cutoff_ym is None
             else resolve_vintages(cutoff_ym, con))
        cand = build_candidates(study_id, con, v)
        tf = build_transfer(con, v)
        dem = build_demand(study_id, con, v, cand, tf)
        shr = build_share(study_id, con, v, dem)
        eco = build_economics(study_id, con, v, dem, shr)
        scr = build_screen(study_id, eco)
        scr["study_id"] = study_id
        scr["cutoff"] = v.label
        return {"vintages": v, "candidates": cand, "transfer": tf,
                "demand": dem, "share": shr, "economics": eco, "screen": scr}
    finally:
        if own:
            con.close()


if __name__ == "__main__":
    import sys
    cut = int(sys.argv[1]) if len(sys.argv) > 1 else None
    for s in ("westjet_yyc", "alaska_sea", "porter_yyz"):
        r = snapshot(s, cut)
        v = r["vintages"]
        print(f"{s} @ {v.label}: {len(r['screen'])} candidates, "
              f"{r['screen']['verdict'].value_counts().to_dict()}")
        if cut:
            print(f"   vintages: t100<={v.t100_max_ym} db1b={v.db1b_year} "
                  f"f41={v.form41_year} bea={v.bea_year} ca={v.ca_year} "
                  f"anchor={v.anchor_year} gravity={v.gravity_vintage} "
                  f"seats={v.seats_year}")
