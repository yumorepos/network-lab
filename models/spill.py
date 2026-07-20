"""Truncated-normal spill: expected boardings when demand meets a finite cabin.

Daily demand D ~ Normal(mu, sigma = cov x mu). With capacity C:
  E[boardings] = E[min(D, C)] = mu - sigma*phi(z) - (mu - C)*(1 - Phi(z)),
  z = (C - mu) / sigma.
One formula, one test (tests/test_spill.py): capacity -> infinity recovers mu,
and E[boardings] never exceeds C or mu.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import norm

from .common import assumptions


def expected_boardings(mean_demand: float, capacity: float,
                       cov: float | None = None) -> float:
    if cov is None:
        cov = float(assumptions()["spill_cov"]["value"])
    if mean_demand <= 0:
        return 0.0
    sigma = cov * mean_demand
    if sigma == 0:
        return min(mean_demand, capacity)
    z = (capacity - mean_demand) / sigma
    return float(mean_demand - sigma * norm.pdf(z)
                 - (mean_demand - capacity) * (1 - norm.cdf(z)))
