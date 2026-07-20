"""Gravity model: log-log OLS on observed US domestic city-market pairs.

Two variants per vintage:
  - "predict": ln(pax) ~ ln(pop product) + ln(income product) + ln(distance).
    No service terms, so it can score unserved markets.
  - "diagnostic": adds nonstop presence and seat volume. It exists to show how
    much demand is service-driven; using it on unserved markets would be
    circular (you'd be assuming the service you're evaluating), so predict()
    refuses it.

Vintages: "current" fits on 2023-2024; "pre2022" fits on 2018-2019 and is the
only model the backtest is allowed to use (single fixed vintage, lookahead
disclosed in docs/validation.md).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
import yaml

from .common import OUTPUTS, connect

VINTAGE_YEARS = {"current": (2023, 2024), "pre2022": (2018, 2019)}
MIN_ANNUAL_PAX = 4000          # mirrors the StatCan >4000 city-pair threshold
DIST_RANGE = (150, 3500)
SIZE_BANDS = [(4_000, 25_000), (25_000, 100_000), (100_000, 500_000),
              (500_000, float("inf"))]


def build_market_frame(con, years: tuple[int, int]) -> pd.DataFrame:
    """Undirected US city-market pairs with demand, fare, covariates."""
    y0, y1 = years
    nyears = y1 - y0 + 1
    return con.execute(f"""
        WITH od AS (
          SELECT least(origin_cm, dest_cm) AS cm_a,
                 greatest(origin_cm, dest_cm) AS cm_b,
                 sum(passengers_est) / {nyears} AS pax_yr,
                 sum(mkt_fare * passengers_est) / sum(passengers_est) AS avg_fare,
                 median(nonstop_miles) AS dist_mi
          FROM fact_od_market
          WHERE year BETWEEN {y0} AND {y1} AND origin_cm != dest_cm
          GROUP BY 1, 2
        ),
        ns AS (   -- nonstop service between the two city markets, T-100
          SELECT least(ao.city_market_id, ad.city_market_id) AS cm_a,
                 greatest(ao.city_market_id, ad.city_market_id) AS cm_b,
                 sum(s.seats) / {nyears} AS nonstop_seats_yr
          FROM fact_segment s
          JOIN dim_airport ao ON ao.iata_code = s.origin
          JOIN dim_airport ad ON ad.iata_code = s.dest
          WHERE s.year BETWEEN {y0} AND {y1}
            AND s.origin_country = 'US' AND s.dest_country = 'US'
            AND s.service_class IN ('F','L')
          GROUP BY 1, 2
        )
        SELECT od.*, coalesce(ns.nonstop_seats_yr, 0) AS nonstop_seats_yr,
               ma.cbsa AS cbsa_a, mb.cbsa AS cbsa_b,
               da.population AS pop_a, db.population AS pop_b,
               da.income AS inc_a, db.income AS inc_b
        FROM od
        LEFT JOIN ns USING (cm_a, cm_b)
        JOIN map_citymarket_cbsa ma ON ma.city_market_id = od.cm_a
        JOIN map_citymarket_cbsa mb ON mb.city_market_id = od.cm_b
        JOIN dim_metro_us da ON da.cbsa = ma.cbsa
        JOIN dim_metro_us db ON db.cbsa = mb.cbsa
        WHERE od.pax_yr >= {MIN_ANNUAL_PAX}
          AND od.dist_mi BETWEEN {DIST_RANGE[0]} AND {DIST_RANGE[1]}
          AND da.population > 0 AND db.population > 0
          AND da.income > 0 AND db.income > 0
        ORDER BY od.cm_a, od.cm_b   -- stable row order => reproducible holdout split
    """).df()


def _design(df: pd.DataFrame, diagnostic: bool) -> pd.DataFrame:
    ln_d = np.log(df["dist_mi"])
    x = pd.DataFrame({
        "ln_pop_product": np.log(df["pop_a"] * df["pop_b"]),
        "ln_income_product": np.log(df["inc_a"] * df["inc_b"]),
        # quadratic in log distance: air O&D is hump-shaped in distance
        # (ground substitution kills short-haul, decay kills long-haul)
        "ln_dist": ln_d,
        "ln_dist_sq": ln_d ** 2,
    })
    if diagnostic:
        x["has_nonstop"] = (df["nonstop_seats_yr"] > 0).astype(float)
        x["ln_seats1p"] = np.log1p(df["nonstop_seats_yr"])
    return sm.add_constant(x)


def fit(vintage: str, seed: int = 7) -> dict:
    con = connect(read_only=True)
    df = build_market_frame(con, VINTAGE_YEARS[vintage])
    rng = np.random.default_rng(seed)
    holdout = rng.random(len(df)) < 0.2
    train, test = df[~holdout], df[holdout]
    y_tr = np.log(train["pax_yr"])

    models = {}
    for name, diag in (("predict", False), ("diagnostic", True)):
        res = sm.OLS(y_tr, _design(train, diag)).fit()
        models[name] = res

    res = models["predict"]
    pred = np.exp(res.predict(_design(test, False)))
    ape = np.abs(pred - test["pax_yr"]) / test["pax_yr"]
    bands = []
    for lo, hi in SIZE_BANDS:
        m = (test["pax_yr"] >= lo) & (test["pax_yr"] < hi)
        if m.sum() >= 5:
            bands.append({"band": f"{lo:,}-{'inf' if hi == float('inf') else f'{hi:,.0f}'}",
                          "n": int(m.sum()),
                          "median_ape": float(ape[m].median()),
                          "mean_ape": float(ape[m].mean())})
    out = {
        "vintage": vintage,
        "years": list(VINTAGE_YEARS[vintage]),
        "n_markets": int(len(df)),
        "n_train": int(len(train)), "n_test": int(len(test)),
        "predict": {
            "params": {k: float(v) for k, v in res.params.items()},
            "r2": float(res.rsquared),
        },
        "diagnostic": {
            "params": {k: float(v) for k, v in models["diagnostic"].params.items()},
            "r2": float(models["diagnostic"].rsquared),
        },
        "holdout": {
            "median_ape": float(ape.median()),
            "mean_ape": float(ape.mean()),
            "by_band": bands,
        },
    }
    path = OUTPUTS / f"gravity_{vintage}.yaml"
    path.write_text(yaml.safe_dump(out, sort_keys=False))
    con.close()
    return out


def load(vintage: str) -> dict:
    return yaml.safe_load((OUTPUTS / f"gravity_{vintage}.yaml").read_text())


def predict(pairs: pd.DataFrame, vintage: str) -> np.ndarray:
    """Score pairs with the no-service model. Requires columns pop_a, pop_b,
    inc_a, inc_b, dist_mi."""
    params = load(vintage)["predict"]["params"]
    ln_d = np.log(pairs["dist_mi"])
    ln = (params["const"]
          + params["ln_pop_product"] * np.log(pairs["pop_a"] * pairs["pop_b"])
          + params["ln_income_product"] * np.log(pairs["inc_a"] * pairs["inc_b"])
          + params["ln_dist"] * ln_d + params["ln_dist_sq"] * ln_d ** 2)
    return np.exp(ln)


if __name__ == "__main__":
    for v in ("current", "pre2022"):
        try:
            out = fit(v)
            print(f"{v}: n={out['n_markets']} r2={out['predict']['r2']:.3f} "
                  f"holdout median APE={out['holdout']['median_ape']:.3f}")
        except Exception as e:  # noqa: BLE001
            print(f"{v}: not fit ({e})")
