"""Log-linear OLS gravity estimator: the Version 1 baseline.

`ln(pax) ~ ln(pop product) + ln(income product) + ln(dist) + ln(dist)^2`,
predicted back as `exp(Xb)`.

This is the estimator the frozen W1.4 baseline was computed with. It is kept
available for comparison and MUST continue to reproduce
`gravity_{vintage}.yaml` byte for byte; `tests/test_phase6a_poisson.py` asserts
it. Extracted from `models/gravity.py` unchanged in Phase 6A, so the arithmetic
here is deliberately identical to the pre-Phase-6A code including the order of
operations.

Its known defect, quantified in docs/phase6a_poisson_comparison.md: because
`E[y] = exp(Xb) x E[exp(e)]` and the log residual SD is near 1.0, `exp(Xb)`
recovers roughly the conditional MEDIAN, not the conditional mean. Summed over
the US calibration frame it accounts for 44% of the passengers that actually
flew.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

NAME = "log_ols"


def fit_one(train: pd.DataFrame, design: pd.DataFrame):
    """Fit on log passengers. `design` is the already-built covariate matrix."""
    return sm.OLS(np.log(train["pax_yr"]), design).fit()


def summarize(res) -> dict:
    return {"params": {k: float(v) for k, v in res.params.items()},
            "r2": float(res.rsquared)}


def predict_from_params(params: dict, pairs: pd.DataFrame) -> np.ndarray:
    ln_d = np.log(pairs["dist_mi"])
    ln = (params["const"]
          + params["ln_pop_product"] * np.log(pairs["pop_a"] * pairs["pop_b"])
          + params["ln_income_product"] * np.log(pairs["inc_a"] * pairs["inc_b"])
          + params["ln_dist"] * ln_d + params["ln_dist_sq"] * ln_d ** 2)
    return np.exp(ln)


def predict_from_fit(res, design: pd.DataFrame) -> np.ndarray:
    return np.exp(res.predict(design))
