"""Share model validation: QSI-lite carrier shares vs observed DB1B shares.

On US domestic markets the truth exists: DB1B ticketing-carrier shares. For a
sample of markets from the validation hub (SEA), we score every incumbent's
itineraries with the same QSI-lite used for proposals, convert preferences to
carrier shares, and report mean absolute error in share points, split by
market structure. This is the honesty check on the exact machinery that
scores unserved candidates.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .common import OUTPUTS, assumptions, connect

HUB = "SEA"
YEAR = 2024
MIN_PAX = 50_000


def validate() -> dict:
    a = assumptions()
    w = a["qsi_weights"]
    t_exp = a["qsi_elapsed_time_exponent"]["value"]
    f_exp = w["frequency_exponent"]
    connect_h = a["connect_time_minutes"]["value"] / 60.0
    bt = a["block_time_model"]
    mph = bt["cruise_speed_kts"] * 1.15078

    con = connect(read_only=True)
    obs = con.execute(f"""
        WITH hub_cm AS (SELECT city_market_id FROM dim_airport
                        WHERE iata_code = '{HUB}'),
        mkts AS (
          SELECT CASE WHEN origin_cm = h.city_market_id THEN dest_cm
                      ELSE origin_cm END AS other_cm,
                 tk_carrier, sum(passengers_est) AS pax
          FROM fact_od_market, hub_cm h
          WHERE (origin_cm = h.city_market_id OR dest_cm = h.city_market_id)
            AND year = {YEAR}
          GROUP BY 1, 2
        )
        SELECT m.other_cm, m.tk_carrier, m.pax,
               sum(m.pax) OVER (PARTITION BY m.other_cm) AS mkt_pax
        FROM mkts m
        QUALIFY mkt_pax >= {MIN_PAX}
    """).df()

    win = con.execute("""
        SELECT max(year::INT*100+month) FROM fact_segment
        WHERE service_class IN ('F','L')""").fetchone()[0]
    seg = con.execute(f"""
        SELECT s.carrier, s.origin, s.dest, s.distance_mi,
               sum(s.departures)/52.0 AS freq_wk
        FROM fact_segment s
        WHERE s.service_class IN ('F','L')
          AND (s.year::INT*100+s.month) > {win} - 100
          AND s.origin_country='US' AND s.dest_country='US'
        GROUP BY 1,2,3,4 HAVING sum(s.departures) >= 26
    """).df()
    cm_of = dict(con.execute(
        "SELECT iata_code, city_market_id FROM dim_airport "
        "WHERE city_market_id IS NOT NULL").fetchall())
    con.close()

    seg["o_cm"] = seg["origin"].map(cm_of)
    seg["d_cm"] = seg["dest"].map(cm_of)
    hub_cm = cm_of[HUB]
    from_hub = seg[seg["o_cm"] == hub_cm]

    def block_h(d):
        return d / mph + bt["taxi_climb_overhead_hours"]

    rows = []
    for other_cm, g in obs.groupby("other_cm"):
        ns = from_hub[from_hub["d_cm"] == other_cm]
        nonstop_dist = ns["distance_mi"].min() if len(ns) else None
        # one-stops: hub->X->dest same carrier
        legs2 = seg[seg["d_cm"] == other_cm]
        os_ = from_hub.merge(legs2, left_on=["carrier", "dest"],
                             right_on=["carrier", "origin"],
                             suffixes=("_1", "_2"))
        if nonstop_dist is not None:
            os_ = os_[os_["distance_mi_1"] + os_["distance_mi_2"]
                      <= 1.30 * nonstop_dist]
        prefs: dict[str, float] = {}
        elapsed_all = []
        itins = []
        for _, r in ns.iterrows():
            e = block_h(r["distance_mi"])
            itins.append((r["carrier"], "nonstop", r["freq_wk"], e))
            elapsed_all.append(e)
        for _, r in os_.iterrows():
            e = (block_h(r["distance_mi_1"]) + block_h(r["distance_mi_2"])
                 + connect_h)
            f = min(r["freq_wk_1"], r["freq_wk_2"])
            if f >= 3:
                itins.append((r["carrier"], "onestop", f, e))
                elapsed_all.append(e)
        if not itins:
            continue
        fastest = min(elapsed_all)
        for carrier, itype, f, e in itins:
            base = w["nonstop"] if itype == "nonstop" else w["single_connect"]
            prefs[carrier] = prefs.get(carrier, 0) + (
                base * f ** f_exp * (e / fastest) ** t_exp)
        tot = sum(prefs.values())
        model_share = {c: p / tot for c, p in prefs.items()}
        n_ns_carriers = ns["carrier"].nunique()
        for _, o in g.iterrows():
            rows.append({
                "other_cm": other_cm, "carrier": o["tk_carrier"],
                "obs_share": o["pax"] / o["mkt_pax"],
                "model_share": model_share.get(o["tk_carrier"], 0.0),
                "n_nonstop_carriers": n_ns_carriers,
            })
    df = pd.DataFrame(rows)
    df["abs_err"] = (df["model_share"] - df["obs_share"]).abs()
    by_struct = (df.groupby(pd.cut(df["n_nonstop_carriers"], [-1, 0, 1, 2, 99],
                                   labels=["0 nonstop", "1 nonstop",
                                           "2 nonstop", "3+ nonstop"]),
                            observed=True)["abs_err"]
                 .agg(["mean", "count"]))
    out = {
        "hub": HUB, "year": YEAR, "n_market_carrier_rows": int(len(df)),
        "mae_share_points": float(100 * df["abs_err"].mean()),
        "by_structure": {str(k): {"mae_pts": float(100 * v["mean"]),
                                  "n": int(v["count"])}
                         for k, v in by_struct.iterrows()},
    }
    df.to_parquet(OUTPUTS / "share_validation.parquet", index=False)
    return out


if __name__ == "__main__":
    import json
    print(json.dumps(validate(), indent=2))
