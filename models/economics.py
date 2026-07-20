"""Route economics: decomposed cost build and revenue on a 3 fare x 3 fuel grid.

Costs come from the comparator carrier's Form 41 P-5.2 filings (direct
aircraft operating expense). Fuel is stripped and rebuilt: the comparator's
own gallons-per-air-hour (AIR_FUELS_ISSUED / TOTAL_AIR_HOURS) x the EIA
scenario price, so fuel burn is derived from filings, not assumed. The one
adjustment is Porter's E195-E2 vs the B6 E190 proxy (assumption, Embraer
public efficiency claims). Crew, maintenance, ownership, and other direct
costs are per-air-hour rates applied to modeled block hours (slightly
conservative: block > air hours).

Scope note, stated everywhere the numbers appear: margins are a
FULLY-ALLOCATED PROXY - direct operating cost times the comparator's own
indirect burden (P-1.2 total opex / P-5.2 direct opex, derived not assumed),
plus the incremental Canadian airport/nav fee proxy. Without the burden,
every decent market clears an 8% hurdle and the screen stops discriminating;
with it, the hurdle means what a planner expects it to mean. Possible modest
double-count between the burden and the fee proxy is inside the fee's +/-30%
sensitivity band and noted in LIMITATIONS.

Fares: US domestic markets use observed DB1B fares. Transborder markets use a
distance-matched fare curve fit on DB1B x the documented transborder premium.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import yaml

from . import spill
from .common import OUTPUTS, assumptions, connect, study

E2_FUEL_IMPROVEMENT = 0.12   # E195-E2 vs E190, Embraer public claims; assumption

CREW_COLS = ["PILOT_FLY_OPS", "OTH_FLT_FLY_OPS", "TRAIN_FLY_OPS",
             "PERS_EXP_FLY_OPS", "BENEFITS_FLY_OPS", "PAY_TAX_FLY_OPS"]
MAINT_COLS = ["TOT_DIR_MAINT", "AP_MT_BURDEN"]
OWN_COLS = ["RENTAL_FLY_OPS", "INS_FLY_OPS", "AIRFRAME_DEP", "ENGINE_DEP",
            "PARTS_DEP", "ENG_PARTS_DEP", "OTH_FLT_EQUIP_DEP"]


def comparator_rates(carrier: str, year: int = 2024,
                     aircraft_like: str | None = None) -> dict:
    """Per-air-hour direct cost rates and fuel burn for a comparator carrier."""
    con = connect(read_only=True)
    where = f"UNIQUE_CARRIER = '{carrier}' AND YEAR = {year}"
    if aircraft_like:
        ats = con.execute(f"""
            SELECT AC_TYPEID FROM read_parquet(
              'data/parquet/lookups/aircraft_types.parquet')
            WHERE SHORT_NAME LIKE '{aircraft_like}'
        """).df()["AC_TYPEID"].tolist()
        codes = ",".join(f"'{c}'" for c in ats)
        where += f" AND AIRCRAFT_TYPE IN ({codes})"
    cols = ", ".join(f"sum(try_cast({c} AS DOUBLE)) AS {c}"
                     for c in CREW_COLS + MAINT_COLS + OWN_COLS
                     + ["FUEL_FLY_OPS", "TOT_FLY_OPS", "TOTAL_AIR_HOURS",
                        "AIR_FUELS_ISSUED"])
    r = con.execute(f"SELECT {cols} FROM fact_costs WHERE {where}").df().iloc[0]
    con.close()
    hours = r["TOTAL_AIR_HOURS"]
    assert hours and hours > 0, f"no P-5.2 hours for {carrier} {year}"
    crew = sum(r[c] or 0 for c in CREW_COLS) / hours
    maint = sum(r[c] or 0 for c in MAINT_COLS) / hours
    own = sum(r[c] or 0 for c in OWN_COLS) / hours
    other = max(0.0, (r["TOT_FLY_OPS"] or 0) / hours
                - crew - (r["FUEL_FLY_OPS"] or 0) / hours
                - ((r["RENTAL_FLY_OPS"] or 0) + (r["INS_FLY_OPS"] or 0)) / hours)
    burn_gph = r["AIR_FUELS_ISSUED"] / hours
    # sanity: narrowbody burn should land in a physical range
    assert 400 < burn_gph < 1400, f"implausible burn {burn_gph:.0f} gal/h"
    # indirect burden derived from the same carrier's filings: P-1.2 total
    # operating expense over P-5.2 total direct aircraft operating expense.
    # This converts direct-cost margins into a fully-allocated proxy.
    con2 = connect(read_only=True)
    mult = con2.execute(f"""
        WITH direct AS (
          SELECT sum(try_cast(TOT_AIR_OP_EXPENSES AS DOUBLE)) AS d
          FROM fact_costs
          WHERE UNIQUE_CARRIER = '{carrier}' AND YEAR = {year}
        ),
        total AS (
          SELECT sum(try_cast(OP_EXPENSES AS DOUBLE)) AS t
          FROM fact_income_p12
          WHERE UNIQUE_CARRIER = '{carrier}' AND YEAR = {year}
        )
        SELECT t / d FROM direct, total
    """).fetchone()[0]
    con2.close()
    assert mult and 1.2 < mult < 3.0, f"implausible indirect mult {mult}"
    return {"carrier": carrier, "year": year,
            "crew_ph": float(crew), "maint_ph": float(maint),
            "own_ph": float(own), "other_ph": float(other),
            "burn_gph": float(burn_gph), "indirect_mult": float(mult)}


def fuel_price_base(con) -> float:
    return con.execute("""
        SELECT avg(usd_per_gal) FROM fact_fuel
        WHERE date >= (SELECT max(date) FROM fact_fuel) - INTERVAL 365 DAY
    """).fetchone()[0]


def fare_curve(con, year: int = 2024) -> np.poly1d:
    """DB1B one-way fare vs distance (for markets without observed fare)."""
    df = con.execute(f"""
        SELECT median(nonstop_miles) AS dist,
               sum(mkt_fare*passengers_est)/sum(passengers_est) AS fare
        FROM fact_od_market WHERE year = {year}
        GROUP BY least(origin_cm,dest_cm), greatest(origin_cm,dest_cm)
        HAVING sum(passengers_est) > 4000
    """).df().dropna()
    coef = np.polyfit(df["dist"], df["fare"], 1)
    return np.poly1d(coef)


def block_hours(dist_mi) -> float:
    a = assumptions()["block_time_model"]
    return dist_mi / (a["cruise_speed_kts"] * 1.15078) \
        + a["taxi_climb_overhead_hours"]


def scenario_grid(study_id: str) -> pd.DataFrame:
    cfg = study(study_id)
    a = assumptions()
    con = connect(read_only=True)

    comp_cfg = cfg["economics"]["cost_comparator"]
    if comp_cfg == "from_assumptions":
        if cfg["carrier"] == "PD":
            rates = comparator_rates(
                a["porter_cost_comparator_carrier"]["value"],
                aircraft_like="%190%")
            rates["burn_gph"] *= (1 - E2_FUEL_IMPROVEMENT)
        else:
            rates = comparator_rates(a["cost_comparator_carrier"]["value"])
    else:
        rates = comparator_rates(comp_cfg)

    seats = cfg["fleet"]["seats"]
    freq_wk = cfg["candidates"]["proposed_weekly_frequency"]
    fee = a["airport_fee_proxy"]
    fee_dep = fee["per_departure_usd"]
    fee_seat = fee["per_seat_usd"]
    premium = (a["transborder_fare_premium"]["value"]
               if cfg["market_scope"] == "transborder" else 1.0)
    p_base = fuel_price_base(con)
    curve = fare_curve(con)

    demand = pd.read_parquet(OUTPUTS / f"demand_{study_id}.parquet")
    share = pd.read_parquet(OUTPUTS / f"share_{study_id}.parquet")
    m = demand.merge(share[["cbsa", "proposed_share", "n_nonstop_incumbents",
                            "n_onestop_carriers", "top_competitor"]],
                     on="cbsa")

    rows = []
    for _, r in m.iterrows():
        bh = block_hours(r["dist_mi"])
        fare_base = (r["fare_observed"]
                     if pd.notna(r.get("fare_observed", np.nan))
                     else float(curve(r["dist_mi"])) * premium)
        carried = r["demand_pax_yr"] * r["proposed_share"]
        deps_yr = freq_wk * 52
        pax_per_dep = spill.expected_boardings(carried / deps_yr, seats)
        for f_pct in a["fare_scenario_grid_pct"]["value"]:
            for g_pct in a["fuel_scenario_grid"]["value"]:
                fare = fare_base * (1 + f_pct / 100)
                gal = p_base * (1 + g_pct / 100)
                fuel_cost = rates["burn_gph"] * gal * bh
                doc = (rates["crew_ph"] + rates["maint_ph"] + rates["own_ph"]
                       + rates["other_ph"]) * bh
                fees = fee_dep + fee_seat * seats
                # fully-allocated proxy: comparator's own indirect burden on
                # direct cost, plus the incremental Canadian fee proxy
                cost = (fuel_cost + doc) * rates["indirect_mult"] + fees
                rev = fare * pax_per_dep
                asm = seats * r["dist_mi"]
                rows.append({
                    "study_id": study_id, "cbsa": r["cbsa"],
                    "metro_name": r["metro_name"],
                    "dest_airport": r["dest_airport"],
                    "dist_mi": r["dist_mi"], "block_h": bh,
                    "fare_scenario_pct": f_pct, "fuel_scenario_pct": g_pct,
                    "fare_used": fare, "fuel_usd_gal": gal,
                    "pax_per_dep": pax_per_dep,
                    "load_factor": pax_per_dep / seats,
                    "revenue_dep": rev, "cost_dep": cost,
                    "casm_c": 100 * cost / asm, "rasm_c": 100 * rev / asm,
                    "margin_pct": 100 * (rev - cost) / rev if rev else np.nan,
                    "belf": cost / (fare * seats) if fare else np.nan,
                    "demand_source": r["demand_source"],
                    "demand_method": r.get("demand_method", "observed_db1b"),
                    "implied_vs_anchor_ratio":
                        r.get("implied_vs_anchor_ratio", np.nan),
                    "anchor_2018_pax": r.get("anchor_2018_pax", np.nan),
                    "proposed_share": r["proposed_share"],
                    "demand_pax_yr": r["demand_pax_yr"],
                    "n_nonstop_incumbents": r["n_nonstop_incumbents"],
                    "top_competitor": r["top_competitor"],
                })
    con.close()
    out = pd.DataFrame(rows)
    out.to_parquet(OUTPUTS / f"economics_{study_id}.parquet", index=False)
    return out


if __name__ == "__main__":
    for s in ("westjet_yyc", "alaska_sea", "porter_yyz"):
        try:
            df = scenario_grid(s)
            base = df[(df.fare_scenario_pct == 0) & (df.fuel_scenario_pct == 0)]
            print(f"{s}: {base.shape[0]} candidates, median margin "
                  f"{base['margin_pct'].median():.1f}%, median LF "
                  f"{base['load_factor'].median():.2f}")
        except Exception as e:  # noqa: BLE001
            print(f"{s}: {e}")
