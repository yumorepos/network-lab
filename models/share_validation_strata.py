"""T3: the connection-only share validation.

Protocol frozen at `docs/change_reports/T3_connection_share_validation.md`
before this file existed. **Validation only.** Nothing here fits, refits or
tunes: not the detour bounds, the connect allowance, the minimum connecting
frequency, the QSI weights or either exponent. No new source is ingested.

`models/share_validation.py` is the published check and is not modified. It
anchors at a 50,000 passenger floor, which is why its zero-nonstop stratum
holds 2 of 66 markets: large markets have nonstops, so a high floor selects
the regime the WestJet study does **not** occupy. This module reuses the same
machinery at the floor the demand layer already uses for a thin DB1B market,
and splits the result by what the model reconstructs rather than by what the
market happens to contain.

The equal-share null is scored alongside on purpose. Identifying who competes
and sizing how much they carry are different claims, and only the second is
what a share model adds over a competitor list.

    .venv/bin/python -m models.share_validation_strata
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from .carriers import segment_brands
from .common import OUTPUTS, assumptions, connect
from .share_validation import HUB, MIN_SEGMENT_DEPS_YR, YEAR

# The floor `replay/snapshot.py:build_demand` uses to call a us_domestic DB1B
# market too thin to read observed, and `models/economics.py:fare_curve` uses
# to admit a market to the fare fit. Not a new constant; see protocol 0.3.
MIN_PAX = 4_000

# Reporting conventions, declared in protocol 0.6 and disclosed in the
# generated document. A market is the cluster, so both minimums bind.
MIN_ROWS = 30
MIN_MARKETS = 10

# The engine's own declared limit on a modelled share with no nonstop
# incumbent: `build_screen` caps such a verdict at MONITOR above this.
# Protocol 0.8 judges the share-1.0 default against it.
SHARE_UNCERTAINTY_LIMIT = 0.70

STRATA = ("A nonstop competition", "B one-stop competition only",
          "C sole reconstructed carrier")
VERDICTS = ("CONNECTION SHARE VALIDATED FOR FINAL SCOPE",
            "CONNECTION SHARE USABLE WITH MATERIAL LIMITATION",
            "CONNECTION SHARE NOT VALIDATED, DE-SCOPE OR REPAIR REQUIRED",
            "VALIDATION INSUFFICIENT")


def _reconstruct(min_pax: int = MIN_PAX) -> pd.DataFrame:
    """One row per market and ticketing carrier, with the modelled share, the
    equal-share null, and the stratum the market falls in.

    The itinerary construction is copied in behaviour from
    `models/share_validation.py:validate` and shares its assumptions object,
    so the two differ only in the sampling floor and in what is reported.
    """
    a = assumptions()
    w = a["qsi_weights"]
    t_exp = a["qsi_elapsed_time_exponent"]["value"]
    f_exp = w["frequency_exponent"]
    connect_h = a["connect_time_minutes"]["value"] / 60.0
    bt = a["block_time_model"]
    mph = bt["cruise_speed_kts"] * 1.15078
    fam = set(pd.read_csv("data/reference/carrier_families.csv")
              ["operating_carrier"])

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
        QUALIFY mkt_pax >= {min_pax}
    """).df()
    win = con.execute("""
        SELECT max(year::INT*100+month) FROM fact_segment
        WHERE service_class IN ('F','L')""").fetchone()[0]
    con.register("map_segment_brand", segment_brands(con, MIN_SEGMENT_DEPS_YR))
    seg = con.execute(f"""
        SELECT coalesce(b.brand, s.carrier) AS carrier,
               s.origin, s.dest, max(s.distance_mi) AS distance_mi,
               sum(s.departures)/52.0 AS freq_wk
        FROM fact_segment s
        LEFT JOIN map_segment_brand b
               ON b.op_carrier = s.carrier
              AND b.origin = s.origin AND b.dest = s.dest
        WHERE s.service_class IN ('F','L')
          AND (s.year::INT*100+s.month) > {win} - 100
          AND s.origin_country='US' AND s.dest_country='US'
        GROUP BY 1,2,3 HAVING sum(s.departures) >= {MIN_SEGMENT_DEPS_YR}
    """).df()
    cm_of = {k: int(v) for k, v in con.execute(
        "SELECT iata_code, city_market_id FROM dim_airport "
        "WHERE city_market_id IS NOT NULL").fetchall()}
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
        legs2 = seg[seg["d_cm"] == other_cm]
        os_ = from_hub.merge(legs2, left_on=["carrier", "dest"],
                             right_on=["carrier", "origin"],
                             suffixes=("_1", "_2"))
        if nonstop_dist is not None:
            os_ = os_[os_["distance_mi_1"] + os_["distance_mi_2"]
                      <= np.minimum(nonstop_dist + 700, 2.0 * nonstop_dist)]
        itins, elapsed_all = [], []
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
        prefs: dict[str, float] = {}
        unres_pref = 0.0
        for carrier, itype, f, e in itins:
            base = w["nonstop"] if itype == "nonstop" else w["single_connect"]
            p = base * f ** f_exp * (e / fastest) ** t_exp
            prefs[carrier] = prefs.get(carrier, 0.0) + p
            # Unresolved means the surviving code is still an operating
            # certificate from carrier_families, i.e. `coalesce` fell back.
            # A mainline carrier simply absent from the brand map is resolved,
            # not unresolved, which is the distinction Stage 2R.5 measured.
            if carrier in fam:
                unres_pref += p
        tot = sum(prefs.values())
        model_share = {c: p / tot for c, p in prefs.items()}
        null_share = {c: 1.0 / len(prefs) for c in prefs}
        n_ns = ns["carrier"].nunique()
        n_mod = len(prefs)
        if n_mod == 1:
            stratum = STRATA[2]
        elif n_ns > 0:
            stratum = STRATA[0]
        else:
            stratum = STRATA[1]
        for _, o in g.iterrows():
            rows.append({
                "other_cm": int(other_cm), "carrier": o["tk_carrier"],
                "obs_share": o["pax"] / o["mkt_pax"],
                "model_share": model_share.get(o["tk_carrier"], 0.0),
                "null_share": null_share.get(o["tk_carrier"], 0.0),
                "pax": float(o["pax"]), "mkt_pax": float(o["mkt_pax"]),
                "n_nonstop_carriers": int(n_ns),
                "n_modeled_carriers": int(n_mod),
                "stratum": stratum,
                "unresolved_pref_share": float(unres_pref / tot) if tot else 0.0,
            })
    df = pd.DataFrame(rows)
    df["abs_err"] = (df["model_share"] - df["obs_share"]).abs()
    df["null_abs_err"] = (df["null_share"] - df["obs_share"]).abs()
    df["bias"] = df["model_share"] - df["obs_share"]
    return df


def by_stratum(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for s in STRATA:
        g = df[df["stratum"] == s]
        if not len(g):
            rows.append({"stratum": s, "rows": 0, "markets": 0})
            continue
        rho = spearmanr(g["model_share"], g["obs_share"])
        rows.append({
            "stratum": s, "rows": len(g),
            "markets": int(g["other_cm"].nunique()),
            "pax": float(g["pax"].sum()),
            "median_obs_share": float(g["obs_share"].median()),
            "median_model_share": float(g["model_share"].median()),
            "mae": float(100 * g["abs_err"].mean()),
            "pax_weighted_mae": float(
                100 * np.average(g["abs_err"], weights=g["pax"])
                if g["pax"].sum() else np.nan),
            "null_mae": float(100 * g["null_abs_err"].mean()),
            "beats_null": bool(g["abs_err"].mean() < g["null_abs_err"].mean()),
            "bias": float(100 * g["bias"].mean()),
            "spearman": float(rho.statistic) if len(g) > 2 else np.nan,
            "spearman_p": float(rho.pvalue) if len(g) > 2 else np.nan,
            "max_abs_err": float(100 * g["abs_err"].max()),
            "mean_unresolved_pref_share": float(
                g["unresolved_pref_share"].mean()),
        })
    return pd.DataFrame(rows)


def verdict(st: pd.DataFrame) -> tuple[str, list[str]]:
    """Protocol 0.7, applied to stratum B."""
    b = st[st["stratum"] == STRATA[1]]
    reasons = []
    if not len(b) or b["rows"].iloc[0] < MIN_ROWS \
            or b["markets"].iloc[0] < MIN_MARKETS:
        n = int(b["rows"].iloc[0]) if len(b) else 0
        m = int(b["markets"].iloc[0]) if len(b) else 0
        reasons.append(
            f"stratum B has {n} rows across {m} markets, below the declared "
            f"minimum of {MIN_ROWS} rows and {MIN_MARKETS} markets.")
        return VERDICTS[3], reasons
    r = b.iloc[0]
    reasons.append(
        f"stratum B: {int(r['rows'])} rows across {int(r['markets'])} "
        f"markets, MAE {r['mae']:.1f} share points against an equal-share "
        f"null of {r['null_mae']:.1f}.")
    if r["beats_null"]:
        reasons.append("QSI-lite beats the null, so the layer contributes "
                       "sizing and not only identification.")
        return VERDICTS[0], reasons
    reasons.append("QSI-lite does not beat the equal-share null on MAE.")
    if r["spearman"] > 0:
        reasons.append(
            f"modelled and observed shares remain positively rank-correlated "
            f"(Spearman {r['spearman']:.3f}, p={r['spearman_p']:.3g}), so the "
            "layer identifies the leader without sizing the gap.")
        return VERDICTS[1], reasons
    reasons.append("modelled and observed shares are not positively "
                   "rank-correlated.")
    return VERDICTS[2], reasons


def stratum_c_detail(df: pd.DataFrame) -> dict:
    """Protocol 0.8, and the one place the protocol left a minimum unstated.

    Section 0.6 fixed a minimum for stratum B in market-carrier rows. Stratum C
    yields exactly one relevant observation per market, the sole reconstructed
    carrier, so the row minimum does not transfer and the **declared market
    minimum of 10** is applied instead. That is disclosed rather than chosen:
    the full distribution is reported below, so the classification is not
    load-bearing for a reader who would set the bar elsewhere.
    """
    c = df[(df["stratum"] == STRATA[2]) & (df["model_share"] == 1.0)]
    n_mkt = int(c["other_cm"].nunique())
    if n_mkt < MIN_MARKETS:
        return {"classification": "unsupported", "n_markets": n_mkt,
                "n": len(c)}
    obs = c["obs_share"]
    all_c = df[df["stratum"] == STRATA[2]]
    return {
        "classification": ("defensible"
                           if float(obs.median()) >= SHARE_UNCERTAINTY_LIMIT
                           else "aggressive"),
        "n": int(len(c)), "n_markets": n_mkt,
        "median_obs_share": float(obs.median()),
        "mean_obs_share": float(obs.mean()),
        "p25_obs_share": float(obs.quantile(0.25)),
        "p75_obs_share": float(obs.quantile(0.75)),
        "share_at_or_above_limit": float((obs >= SHARE_UNCERTAINTY_LIMIT).mean()),
        "mean_observed_carriers_per_market": float(
            all_c.groupby("other_cm").size().mean()),
        "limit": SHARE_UNCERTAINTY_LIMIT,
    }


def validate_strata() -> dict:
    df = _reconstruct()
    st = by_stratum(df)
    v, reasons = verdict(st)
    c = stratum_c_detail(df)
    df.to_parquet(OUTPUTS / "share_validation_strata.parquet", index=False)
    st.to_parquet(OUTPUTS / "share_validation_by_stratum.parquet", index=False)
    return {"hub": HUB, "year": YEAR, "min_pax": MIN_PAX,
            "rows": int(len(df)), "markets": int(df["other_cm"].nunique()),
            "verdict": v, "reasons": reasons,
            "stratum_c": c,
            "by_stratum": st.to_dict(orient="records")}


if __name__ == "__main__":
    import json
    print(json.dumps(validate_strata(), indent=2, default=str))
