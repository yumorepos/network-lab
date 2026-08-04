"""Phase 6A: log-OLS versus Poisson QMLE gravity, measured not assumed.

Emits the tables in docs/phase6a_poisson_comparison.md. Both estimators are
scored on the SAME 20% holdout (gravity.holdout_split, seed 7) so the comparison
is like for like.

Calibration is reported binned by PREDICTED value throughout. Binning by
observed value conditions on the outcome and manufactures a monotonic pattern
out of noise alone; that error is what the A5 correction was about.

Run: .venv/bin/python scripts/phase6a_compare.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from models import gravity, gravity_log_ols, gravity_poisson
from models.common import connect

BANDS = [(0, 10_000), (10_000, 25_000), (25_000, 50_000),
         (50_000, 100_000), (100_000, np.inf)]
BAND_LABELS = ["<10k", "10-25k", "25-50k", "50-100k", ">100k"]


def _band(v: np.ndarray) -> pd.Categorical:
    return pd.cut(v, [b[0] for b in BANDS] + [np.inf], labels=BAND_LABELS,
                  right=False)


def holdout_frame(vintage: str) -> pd.DataFrame:
    con = connect(read_only=True)
    df = gravity.build_market_frame(con, gravity.VINTAGE_YEARS[vintage])
    con.close()
    test = df[gravity.holdout_split(df)].copy()
    test["obs"] = test["pax_yr"].astype(float)
    for est in (gravity_log_ols.NAME, gravity_poisson.NAME):
        test[est] = gravity.predict(test, vintage, estimator=est)
    return test


def metrics(obs: np.ndarray, pred: np.ndarray) -> dict:
    err = pred - obs
    ape = np.abs(err) / obs
    logres = np.log(obs) - np.log(pred)
    return {
        "aggregate_pred_over_obs": pred.sum() / obs.sum(),
        "mape": ape.mean(),
        "median_ape": float(np.median(ape)),
        "rmse": float(np.sqrt((err ** 2).mean())),
        "rmsle": float(np.sqrt((logres ** 2).mean())),
        "log_resid_mean": float(logres.mean()),
        "log_resid_median": float(np.median(logres)),
        "log_resid_sd": float(logres.std(ddof=1)),
        # skew is undefined when every residual is identical (a perfect fit),
        # which happens in the metric's own unit test
        "log_resid_skew": (float(stats.skew(logres))
                           if logres.std() > 1e-12 else 0.0),
    }


def by_predicted_band(obs: np.ndarray, pred: np.ndarray) -> pd.DataFrame:
    d = pd.DataFrame({"obs": obs, "pred": pred, "band": _band(pred)})
    g = d.groupby("band", observed=True).apply(
        lambda x: pd.Series({
            "n": len(x),
            "mean_obs_over_mean_pred": x.obs.mean() / x.pred.mean(),
            "median_ape": float(np.median(np.abs(x.pred - x.obs) / x.obs)),
        }), include_groups=False)
    return g


def calibration_curve(obs: np.ndarray, pred: np.ndarray,
                      q: int = 10) -> pd.DataFrame:
    d = pd.DataFrame({"obs": obs, "pred": pred})
    d["decile"] = pd.qcut(d["pred"], q, labels=False, duplicates="drop")
    return d.groupby("decile").agg(n=("obs", "size"),
                                   mean_pred=("pred", "mean"),
                                   mean_obs=("obs", "mean")).assign(
        ratio=lambda x: x.mean_obs / x.mean_pred)


def main() -> int:
    for vintage in ("current", "pre2022"):
        t = holdout_frame(vintage)
        obs = t["obs"].to_numpy()
        print(f"\n{'=' * 72}\nVINTAGE {vintage}  (holdout n={len(t)})\n{'=' * 72}")
        rows = {}
        for est in (gravity_log_ols.NAME, gravity_poisson.NAME):
            rows[est] = metrics(obs, t[est].to_numpy())
        m = pd.DataFrame(rows).T
        print("\n-- headline metrics --")
        print(m[["aggregate_pred_over_obs", "mape", "median_ape", "rmse",
                 "rmsle"]].to_string(float_format=lambda v: f"{v:,.4g}"))
        print("\n-- log residual distribution (ln obs - ln pred) --")
        print(m[["log_resid_mean", "log_resid_median", "log_resid_sd",
                 "log_resid_skew"]].to_string(float_format=lambda v: f"{v:.4f}"))
        for est in rows:
            print(f"\n-- error by PREDICTED band, {est} "
                  "(mean_obs/mean_pred target 1.00) --")
            print(by_predicted_band(obs, t[est].to_numpy()).to_string(
                float_format=lambda v: f"{v:.3f}"))
        for est in rows:
            print(f"\n-- calibration curve by predicted decile, {est} --")
            print(calibration_curve(obs, t[est].to_numpy()).to_string(
                float_format=lambda v: f"{v:,.1f}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
