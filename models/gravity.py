"""Gravity model: public interface and estimator dispatch.

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

## Estimators (Phase 6A)

The functional form above is shared; how its coefficients are estimated is now
selectable, because the two answer different questions:

  log_ols       models/gravity_log_ols.py. Fits ln(pax) by OLS and predicts
                exp(Xb), which recovers the conditional MEDIAN. The Version 1
                frozen baseline. Artifact: gravity_{vintage}.yaml
  poisson_qmle  models/gravity_poisson.py. Fits passenger levels by Poisson
                pseudo-ML with a log link and robust covariance, which targets
                the conditional MEAN. Artifact:
                gravity_{vintage}_poisson.yaml

`DEFAULT_ESTIMATOR` decides what `predict()` uses when a caller does not say.
It is deliberately still `log_ols`: Phase 6A implements and measures the
Poisson estimator without moving the frozen baseline, so that the switch is an
evidence-gated decision with its own change report rather than a side effect of
landing the code. See docs/phase6a_implementation_report.md.

Every downstream consumer (models/demand.py, models/transfer.py,
backtest/run_backtest.py) is unchanged and keeps calling
`gravity.predict(pairs, vintage)`.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
import statsmodels.api as sm
import yaml

from . import gravity_log_ols, gravity_poisson
from .common import OUTPUTS, connect

ESTIMATORS = {gravity_log_ols.NAME: gravity_log_ols,
              gravity_poisson.NAME: gravity_poisson}

# Model version selection. The default is the frozen Version 1 baseline; the
# environment override exists so the Phase 6A counterfactual (what would the
# verdicts be if ONLY the demand estimator changed?) can be run through the real
# pipeline instead of a reimplementation of it. Set to a key of ESTIMATORS.
DEFAULT_ESTIMATOR = os.environ.get("NETWORK_LAB_GRAVITY_ESTIMATOR",
                                   gravity_log_ols.NAME)
if DEFAULT_ESTIMATOR not in ESTIMATORS:
    raise ValueError(f"NETWORK_LAB_GRAVITY_ESTIMATOR={DEFAULT_ESTIMATOR!r} is "
                     f"not one of {sorted(ESTIMATORS)}")

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


def artifact_path(vintage: str, estimator: str = DEFAULT_ESTIMATOR):
    """The log_ols artifact keeps its original unsuffixed name so the frozen
    baseline stays byte-identical; other estimators are suffixed."""
    suffix = "" if estimator == gravity_log_ols.NAME else f"_{estimator.split('_')[0]}"
    return OUTPUTS / f"gravity_{vintage}{suffix}.yaml"


def holdout_split(df: pd.DataFrame, seed: int = 7) -> np.ndarray:
    """Shared 20% holdout mask. Every estimator must be scored on the SAME
    split or the comparison is meaningless, so this is computed once here from
    the stable row order guaranteed by build_market_frame's ORDER BY."""
    return np.random.default_rng(seed).random(len(df)) < 0.2


def fit(vintage: str, seed: int = 7,
        estimator: str = DEFAULT_ESTIMATOR) -> dict:
    est = ESTIMATORS[estimator]
    con = connect(read_only=True)
    df = build_market_frame(con, VINTAGE_YEARS[vintage])
    holdout = holdout_split(df, seed)
    train, test = df[~holdout], df[holdout]

    models = {name: est.fit_one(train, _design(train, diag))
              for name, diag in (("predict", False), ("diagnostic", True))}

    res = models["predict"]
    pred = est.predict_from_fit(res, _design(test, False))
    obs = test["pax_yr"].to_numpy(dtype=float)
    ape = np.abs(pred - obs) / obs
    bands = []
    for lo, hi in SIZE_BANDS:
        m = (obs >= lo) & (obs < hi)
        if m.sum() >= 5:
            bands.append({"band": f"{lo:,}-{'inf' if hi == float('inf') else f'{hi:,.0f}'}",
                          "n": int(m.sum()),
                          "median_ape": float(np.median(ape[m])),
                          "mean_ape": float(ape[m].mean())})
    out = {
        "vintage": vintage,
        "years": list(VINTAGE_YEARS[vintage]),
        "n_markets": int(len(df)),
        "n_train": int(len(train)), "n_test": int(len(test)),
        "predict": est.summarize(res),
        "diagnostic": est.summarize(models["diagnostic"]),
        "holdout": {
            "median_ape": float(np.median(ape)),
            "mean_ape": float(ape.mean()),
            "by_band": bands,
        },
    }
    if estimator != gravity_log_ols.NAME:
        # Level-scale calibration, which is the whole point of the change and
        # is not visible in APE. Only emitted for non-baseline estimators so
        # the frozen gravity_{vintage}.yaml is unchanged.
        out["estimator"] = estimator
        out["holdout"]["aggregate_pred_over_obs"] = float(pred.sum() / obs.sum())
    path = artifact_path(vintage, estimator)
    path.write_text(yaml.safe_dump(out, sort_keys=False))
    con.close()
    return out


def load(vintage: str, estimator: str = DEFAULT_ESTIMATOR) -> dict:
    return yaml.safe_load(artifact_path(vintage, estimator).read_text())


def predict(pairs: pd.DataFrame, vintage: str,
            estimator: str | None = None) -> np.ndarray:
    """Score pairs with the no-service model. Requires columns pop_a, pop_b,
    inc_a, inc_b, dist_mi."""
    estimator = estimator or DEFAULT_ESTIMATOR
    params = load(vintage, estimator)["predict"]["params"]
    return ESTIMATORS[estimator].predict_from_params(params, pairs)


if __name__ == "__main__":
    for est in (gravity_log_ols.NAME, gravity_poisson.NAME):
        for v in ("current", "pre2022"):
            try:
                out = fit(v, estimator=est)
                extra = out["holdout"].get("aggregate_pred_over_obs")
                print(f"{est:14s} {v:8s} n={out['n_markets']} "
                      f"holdout median APE={out['holdout']['median_ape']:.3f}"
                      + (f" agg pred/obs={extra:.3f}" if extra else ""))
            except Exception as e:  # noqa: BLE001
                print(f"{est} {v}: not fit ({e})")
