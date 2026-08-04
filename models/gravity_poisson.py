"""Poisson QMLE gravity estimator (Phase 6A).

## Why Poisson rather than a better log-linear model

The Version 1 estimator fits `ln(pax)` by OLS and predicts `exp(Xb)`. That is
not an estimate of expected passengers. Jensen's inequality gives

    E[y | X] = exp(Xb) * E[exp(e) | X]

and with a log-residual standard deviation of 0.99 the missing factor is large.
Measured on the US calibration frame, `sum(predicted) / sum(observed) = 0.439`:
the baseline accounts for 44% of the passengers that actually flew. The median
log residual is near zero, so the model recovers the conditional MEDIAN
correctly and the conditional MEAN not at all.

Poisson pseudo-maximum-likelihood with a log link estimates the conditional mean
directly. Its first-order condition is

    sum_i x_i * (y_i - exp(x_i'b)) = 0

so with a constant in the design the residuals sum to zero on the level scale
and `sum(fitted) = sum(observed)` holds exactly by construction, not by luck.

This is the standard correction for exactly this problem in the gravity
literature: Santos Silva and Tenreyro, "The Log of Gravity", Review of Economics
and Statistics 88(4), 2006, which shows log-OLS gravity estimates are
inconsistent under heteroskedastic errors and recommends Poisson PML.

## Why "quasi" and why robust covariance is mandatory

Poisson QMLE assumes only that the CONDITIONAL MEAN is correctly specified. It
does not require the data to be Poisson, or even to be counts. Under the
Gourieroux, Monfort and Trognon (1984) results for the linear exponential
family, the point estimates stay consistent under any true variance function.

That matters here because the Poisson variance assumption is violated by five
orders of magnitude:

    Pearson chi2 / df = 223,598      (Poisson's own assumption is 1)
    variance / mean   = 899,671

Consistency of the coefficients survives this. The standard errors do not: the
naive Poisson covariance is built from the false assumption `var = mean` and
understates the true sampling variability by roughly the square root of the
dispersion, which here is a factor in the hundreds. Reported standard errors
would be meaningless and every t-statistic would be inflated.

**Robust (Huber-White sandwich, HC1) covariance is therefore required, not
optional, and this module refuses to report naive standard errors.** The
dispersion ratio is written into the artifact so a reader can see why.

## What this does not fix

The fit sample is truncated at `MIN_ANNUAL_PAX`, mirroring the StatCan
publication floor. Poisson corrects the mean given the covariates but is still
fitted only on markets above the floor and then used below it, which is
extrapolation outside the fitted support. That is a separate defect and is
Phase 6B (censored estimation), not this module.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

NAME = "poisson_qmle"

# Huber-White sandwich with the small-sample correction n/(n-k). Named here so
# the artifact records which estimator produced the standard errors.
COV_TYPE = "HC1"


def fit_one(train: pd.DataFrame, design: pd.DataFrame):
    """Poisson QMLE on passenger LEVELS (not logs), log link, robust cov.

    `maxiter` is raised above the statsmodels default because the design spans
    ln(pop product) values around 30 and IRLS needs the headroom to converge
    from a cold start.
    """
    model = sm.GLM(train["pax_yr"].astype(float), design,
                   family=sm.families.Poisson())
    return model.fit(maxiter=200, cov_type=COV_TYPE)


def dispersion(res) -> float:
    """Pearson chi2 over residual df. Poisson assumes 1; this reports reality."""
    return float(res.pearson_chi2 / res.df_resid)


def summarize(res) -> dict:
    """Artifact payload. Standard errors are robust by construction; the naive
    ones are deliberately not exposed."""
    return {
        "params": {k: float(v) for k, v in res.params.items()},
        "robust_se": {k: float(v) for k, v in res.bse.items()},
        "cov_type": COV_TYPE,
        "dispersion_pearson_chi2_over_df": dispersion(res),
        "converged": bool(res.converged),
        "n_iter": int(getattr(res, "fit_history", {}).get("iteration", -1)),
        # Deviance and log-likelihood are reported for completeness but are
        # QUASI-likelihood quantities here: the Poisson variance assumption is
        # false, so they are not usable for likelihood-ratio testing.
        "quasi_deviance": float(res.deviance),
        "quasi_llf": float(res.llf),
    }


def predict_from_params(params: dict, pairs: pd.DataFrame) -> np.ndarray:
    """Same functional form as the OLS estimator; the difference is how the
    coefficients were estimated and that this is already a mean, so no
    retransformation correction is applied or needed."""
    ln_d = np.log(pairs["dist_mi"])
    eta = (params["const"]
           + params["ln_pop_product"] * np.log(pairs["pop_a"] * pairs["pop_b"])
           + params["ln_income_product"] * np.log(pairs["inc_a"] * pairs["inc_b"])
           + params["ln_dist"] * ln_d + params["ln_dist_sq"] * ln_d ** 2)
    return np.exp(eta)


def predict_from_fit(res, design: pd.DataFrame) -> np.ndarray:
    return np.asarray(res.predict(design))
