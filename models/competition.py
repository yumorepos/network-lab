"""Competition reconstruction and QSI-lite share.

A proposed nonstop is never scored against an empty market. For each candidate
metro pair we reconstruct what passengers can already fly:

- Incumbent nonstops: T-100 latest 12 reported months, any carrier, hub
  airport to any airport in the destination metro.
- Incumbent one-stops: same-carrier segment pairs hub->X and X->dest with a
  plausible corridor (total distance <= 1.30x nonstop), weekly frequency =
  min of the two legs, elapsed = leg blocks + connect allowance. This is a
  reconstruction from segment frequencies, not observed itineraries — MIDT
  would be the real source and is priced out of a portfolio project; the
  approximation and its direction of error are documented in LIMITATIONS.

QSI-lite preference per itinerary:
  weight(type) x weekly_freq^freq_exponent x (elapsed/fastest)^time_exponent
Share(proposed) = pref(proposed) / sum(all prefs).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .common import OUTPUTS, assumptions, connect, study

DETOUR_MAX = 1.30
MPH_CRUISE_FACTOR = 1.15078   # kts -> mph


def _block_hours(dist_mi: np.ndarray | float) -> np.ndarray | float:
    a = assumptions()["block_time_model"]
    mph = a["cruise_speed_kts"] * MPH_CRUISE_FACTOR
    return dist_mi / mph + a["taxi_climb_overhead_hours"]


def build_competition(study_id: str) -> pd.DataFrame:
    """Per candidate metro: incumbent nonstop and one-stop itineraries."""
    cfg = study(study_id)
    hub = cfg["hub"]
    con = connect(read_only=True)

    cand = pd.read_parquet(OUTPUTS / f"demand_{study_id}.parquet")
    dest_metros = cand[["cbsa", "dest_airport", "dist_mi"]].copy()
    con.register("cand_dest", dest_metros)

    # latest 12 reported months of scheduled service
    win = con.execute("""
        SELECT max(year::INT*100+month) AS ym FROM fact_segment
        WHERE service_class IN ('F','L')
    """).fetchone()[0]

    con.execute(f"""
        CREATE OR REPLACE TEMP VIEW seg12 AS
        SELECT s.carrier, s.origin, s.dest, s.distance_mi,
               sum(s.departures) / 52.0 AS freq_wk
        FROM fact_segment s
        WHERE s.service_class IN ('F','L')
          AND (s.year::INT*100+s.month) > {win} - 100
          AND s.departures > 0 AND s.seats > 0
        GROUP BY 1,2,3,4
        HAVING sum(s.departures) >= 26   -- at least ~weekly over the window
    """)

    # airports belonging to each candidate destination metro
    con.execute("""
        CREATE OR REPLACE TEMP VIEW dest_airports AS
        SELECT DISTINCT c.cbsa, a.iata_code AS dest_ap
        FROM cand_dest c
        JOIN map_citymarket_cbsa m ON m.cbsa = c.cbsa
        JOIN dim_airport a ON a.city_market_id = m.city_market_id
    """)

    nonstop = con.execute(f"""
        SELECT c.cbsa, s.carrier, 'nonstop' AS itin_type,
               s.freq_wk, s.distance_mi AS total_dist,
               NULL AS connect_ap
        FROM seg12 s
        JOIN dest_airports d ON d.dest_ap = s.dest
        JOIN cand_dest c ON c.cbsa = d.cbsa
        WHERE s.origin = '{hub}'
    """).df()

    onestop = con.execute(f"""
        SELECT c.cbsa, l1.carrier, 'onestop' AS itin_type,
               least(l1.freq_wk, l2.freq_wk) AS freq_wk,
               l1.distance_mi + l2.distance_mi AS total_dist,
               l1.dest AS connect_ap
        FROM seg12 l1
        JOIN seg12 l2 ON l2.carrier = l1.carrier AND l2.origin = l1.dest
        JOIN dest_airports d ON d.dest_ap = l2.dest
        JOIN cand_dest c ON c.cbsa = d.cbsa
        WHERE l1.origin = '{hub}'
          AND l1.dest != '{hub}'
          AND l1.distance_mi + l2.distance_mi <= {DETOUR_MAX} * c.dist_mi
          AND least(l1.freq_wk, l2.freq_wk) >= 3
    """).df()
    con.close()

    a = assumptions()
    connect_h = a["connect_time_minutes"]["value"] / 60.0
    for df, extra in ((nonstop, 0.0), (onestop, connect_h)):
        if len(df):
            df["elapsed_h"] = _block_hours(df["total_dist"].astype(float)) + extra
            # one-stop block time is two legs' worth of overhead
            if extra > 0:
                df["elapsed_h"] += a["block_time_model"]["taxi_climb_overhead_hours"]
    comp = pd.concat([nonstop, onestop], ignore_index=True)
    comp["study_id"] = study_id
    return comp


def qsi_share(study_id: str) -> pd.DataFrame:
    """Proposed-service share per candidate metro under QSI-lite."""
    cfg = study(study_id)
    a = assumptions()
    w = a["qsi_weights"]
    t_exp = a["qsi_elapsed_time_exponent"]["value"]
    f_exp = w["frequency_exponent"]
    prop_freq = cfg["candidates"]["proposed_weekly_frequency"]

    cand = pd.read_parquet(OUTPUTS / f"demand_{study_id}.parquet")
    comp = build_competition(study_id)

    rows = []
    for _, c in cand.iterrows():
        mine = comp[comp["cbsa"] == c["cbsa"]]
        prop_elapsed = float(_block_hours(c["dist_mi"]))
        fastest = min([prop_elapsed] + mine["elapsed_h"].tolist())
        def pref(itype, freq, elapsed):
            base = w["nonstop"] if itype == "nonstop" else w["single_connect"]
            return (base * freq ** f_exp
                    * (elapsed / fastest) ** t_exp)
        prop_pref = pref("nonstop", prop_freq, prop_elapsed)
        comp_pref = sum(pref(r["itin_type"], r["freq_wk"], r["elapsed_h"])
                        for _, r in mine.iterrows())
        share = prop_pref / (prop_pref + comp_pref) if prop_pref else 0.0
        n_ns = (mine["itin_type"] == "nonstop").sum()
        rows.append({
            "study_id": study_id, "cbsa": c["cbsa"],
            "metro_name": c["metro_name"],
            "proposed_share": share,
            "n_nonstop_incumbents": int(n_ns),
            "n_onestop_carriers": int(mine[mine["itin_type"] == "onestop"]
                                      ["carrier"].nunique()),
            "top_competitor": (mine.sort_values("freq_wk", ascending=False)
                               ["carrier"].iloc[0] if len(mine) else None),
        })
    out = pd.DataFrame(rows)
    comp.to_parquet(OUTPUTS / f"competition_{study_id}.parquet", index=False)
    out.to_parquet(OUTPUTS / f"share_{study_id}.parquet", index=False)
    return out


if __name__ == "__main__":
    for s in ("westjet_yyc", "alaska_sea", "porter_yyz"):
        try:
            df = qsi_share(s)
            print(f"{s}: {len(df)} markets, median share "
                  f"{df['proposed_share'].median():.3f}, "
                  f"served-by-others share "
                  f"{df[df['n_nonstop_incumbents']>0]['proposed_share'].median():.3f}")
        except Exception as e:  # noqa: BLE001
            print(f"{s}: {e}")
