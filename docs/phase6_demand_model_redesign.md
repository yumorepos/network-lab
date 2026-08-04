# Phase 6: demand model redesign specification

**Status.** Specification only. Nothing implemented. `models/demand.py`,
`models/gravity.py`, `config/assumptions.yaml` and all model parameters are
untouched by this document.

**Baseline.** `docs/W1.4_baseline_freeze.md`, commit `bd7d4dd`.

---

## 1. A correction to the A5 diagnosis before anything else

A5 reported gravity bias as median predicted over observed by **observed**
demand band: 1.97x on sub-10k markets falling monotonically to 0.30x above 100k.

**That table is contaminated by conditioning on the outcome.** Binning by the
observed value selects markets with negative residuals into the low bands and
positive residuals into the high bands, so a perfectly calibrated model with
noise produces exactly that monotonic pattern. The honest calibration test bins
by **predicted** value and asks whether observed matches.

Both tables, same model, same data:

| band | binned by OBSERVED (A5) | binned by PREDICTED (correct) |
|---|---|---|
| under 10k | 1.97 | 0.89 |
| 10k to 25k | 1.29 | 1.52 |
| 25k to 50k | 0.83 | 1.29 |
| 50k to 100k | 0.54 | 0.78 |
| over 100k | 0.30 | 0.42 |

**What survives the correction.** A5's conclusion is unchanged: the problem is
specification, not the transfer factor. The US and transborder columns were
binned identically, so the roughly constant 2.4x to 3.3x offset between them is
still evidence that the transfer acts as a level shift, and the presence of bias
in the US column with no transfer applied is still the decisive point.

**What does not survive.** The clean monotonic "1.97 to 0.30 slope" as a
statement about model calibration. The real miscalibration is different in shape
and, on the mean, worse.

**What the corrected diagnosis is.** Measured on the conditional mean, which is
what a demand forecast must get right:

```
sum(predicted) / sum(observed) = 0.439
mean observed 83,202   mean predicted 36,513
log-residual: mean -0.006, sd 0.991
```

**The model predicts 44% of the traffic that actually flew.** Median log residual
is near zero, so it recovers the conditional *median* correctly and the
conditional *mean* not at all. That is textbook retransformation bias:
`E[y] = exp(Xb) x E[exp(e)]`, and with a residual SD near 1.0 the missing factor
is large. This is the primary defect and it was previously under-stated.

---

## 2. Evaluated alternatives

All fitted on the same `current` vintage frame (n=6,092 US city-market pairs,
pax at or above 4,000, 150 to 3,500 miles), same four covariates, no tuning.
"agg" is `sum(pred)/sum(obs)`, target 1.00. Bands are mean observed over mean
predicted **within predicted band**, target 1.00 in every cell.

| model | agg | <10k | 10-25k | 25-50k | 50-100k | >100k |
|---|---|---|---|---|---|---|
| **current log-linear OLS** | **0.439** | 2.11 | 1.22 | 1.42 | 2.12 | 3.48 |
| Duan smearing on the OLS fit | 0.810 | 2.72 | 0.74 | 0.65 | 0.79 | 1.63 |
| **Poisson GLM (log link)** | **1.000** | 2.39 | **0.98** | **0.85** | **0.82** | **1.03** |
| Negative Binomial (alpha=1) | 0.785 | 1.75 | 0.83 | 0.72 | 0.89 | 1.65 |
| Tweedie (p=1.5) | 0.930 | 2.25 | 0.85 | 0.75 | 0.79 | 1.21 |
| Gamma (log link) | failed to converge | | | | | |

Overdispersion, which decides how these are used rather than which is chosen:

```
Pearson chi2 / df = 223,598      (Poisson's own assumption is 1)
variance / mean   = 899,671
```

### 1. Poisson GLM

**Assumptions.** Log link, variance proportional to the mean. The variance
assumption is violated here by five orders of magnitude.

**Why that does not disqualify it.** Poisson quasi-maximum likelihood gives
consistent estimates of the conditional mean under *any* true variance function,
provided the mean is correctly specified. The score equations force
`sum(pred) = sum(obs)` exactly, which is why agg is 1.000 by construction rather
than by luck. This is the standard fix for exactly this problem in the gravity
literature: Santos Silva and Tenreyro, "The Log of Gravity" (2006), which shows
log-OLS gravity estimates are biased under heteroskedasticity and recommends
Poisson pseudo-ML.

**Aviation applicability.** High. Passenger counts are non-negative, skewed, and
heteroskedastic. Coefficients remain readable as elasticities, which the project
relies on. It also admits genuine zeros, which matters if the candidate universe
is ever widened below the current 4,000 floor.

**Complexity.** Low. `statsmodels` GLM, same design matrix, roughly a 20-line
change in `models/gravity.py`.

**Caveat.** Standard errors from the naive Poisson fit are meaningless at this
dispersion. **Robust (sandwich, HC1) covariance is mandatory**, not optional.

**Expected improvement.** Aggregate 0.439 to 1.000. Four of five bands land
between 0.82 and 1.03 against 1.22 to 3.48 today.

### 2. Negative Binomial GLM

**Assumptions.** Variance is mean plus alpha times mean squared. Models the
overdispersion explicitly rather than working around it.

**Result.** Worse than Poisson here on both aggregate (0.785) and the top band
(1.65). It is also numerically fragile: a naive method-of-moments alpha
overflowed and the fit failed outright, and alpha=1 was required to converge.
Because NB weights observations by an assumed variance function, a misspecified
alpha degrades the mean fit, whereas Poisson QMLE does not depend on getting the
variance right.

**Verdict.** Better for *inference* about dispersion; worse for *prediction*
here. Not recommended as the primary model. Worth revisiting only if prediction
intervals become a requirement.

### 3. Gamma and Tweedie

**Gamma** (log link) failed to converge on this data. It also cannot represent
zeros, which forecloses widening the candidate universe.

**Tweedie** (p=1.5) sits between Poisson and Gamma: agg 0.930, bands 0.75 to
2.25. Respectable, strictly dominated by Poisson on every metric measured, and it
adds a power parameter that must itself be estimated and defended. Rule 1 would
require sourcing `var_power` and there is no external source for it.

**Verdict.** Neither recommended.

### 4. Duan smearing retransformation

**Assumptions.** Multiply the exponentiated prediction by `mean(exp(residual))`,
here **1.847**. Non-parametric, requires no distributional assumption.

**Result.** Aggregate 0.439 to 0.810, a real improvement. But smearing applies
one constant factor to every prediction, so **it corrects the level and cannot
correct the shape**: bands go from 2.11/1.22/1.42/2.12/3.48 to
2.72/0.74/0.65/0.79/1.63, over-correcting the middle while still missing the top.

**Verdict.** The cheapest possible intervention and a reasonable fallback if the
GLM migration is deferred. Strictly worse than Poisson. Not recommended as the
destination.

### 5. Tobit and censored regression

This addresses a **different defect** from the four above, and the two must not
be conflated.

The fit sample is truncated at `MIN_ANNUAL_PAX = 4,000`, mirroring the StatCan
publication floor. Two consequences:

- Every model above is fitted only on markets above 4,000 and then used to
  predict markets known to be below it. That is extrapolation outside the fitted
  support, and it explains the one band where Poisson still misses badly (<10k
  predicted, obs/pred 2.39): the observed values there are themselves
  floor-censored.
- The 73 capped transborder markets have real information attached, namely "below
  roughly 4,000 in 2018", which the current pipeline discards in favour of
  reporting the bound itself as a point estimate for all of them.

A censored specification (Tobit, or a Poisson/NB likelihood with a left-censored
contribution) uses that bound as data. It is the only approach here that can give
73 capped markets **distinct** estimates that still respect the ceiling.

**Complexity.** Moderate to high. Requires assembling the sub-4,000 US markets
currently excluded by `MIN_ANNUAL_PAX`, and the censoring threshold is
approximate (the smallest observed anchor is 3,900, not 4,000).

**Verdict.** Recommended, but strictly after the mean specification is fixed.
Censoring a mis-specified mean model propagates the mis-specification into the
bound.

### 6. Hierarchical market segmentation

**Assumptions.** Separate coefficients (or random effects) by market type,
distance band, or hub.

**Why not first.** Every segment would inherit the same retransformation bias,
so segmentation before the link-function fix multiplies the defect rather than
removing it. It also fragments an already thin transborder sample: 87 anchor
pairs across 8 hubs.

**Where it genuinely applies.** The audit found real unmodelled structure in the
transfer factor, a leisure and business axis (LAS 8.78, PHX 3.68, MCO 3.26
against BOS 0.44, DFW 0.63, ORD 0.73). That is a segmentation finding and it is
tracked as W3.2. It is about *level by market type*, not about the size bias.

**Verdict.** Phase 6c at the earliest, and only on measured residual structure.

---

## 3. Recommended phased migration

Each phase is a separate change with its own report against the frozen baseline.
No phase begins before the previous one is measured.

### Phase 6a. Poisson QMLE with robust standard errors

Replace the log-OLS `predict` variant with a Poisson GLM on the identical design
matrix. Keep the diagnostic variant untouched. Report robust HC1 covariance.

- **Fixes.** Retransformation bias, the primary defect. Aggregate 0.439 to 1.000.
- **Effort.** 2 to 3 days including the change report.
- **Success.** `sum(pred)/sum(obs)` within 0.02 of 1.00; at least four of five
  predicted bands within [0.85, 1.15]; holdout median APE no worse than the
  current 0.62; every verdict change named.
- **Risk.** Demand estimates rise materially, so verdict counts will move. The
  A5 counterfactual suggests the direction: up to 4 markets could become
  LAUNCH-eligible. **This is the change most likely to alter the headline
  result, and it must be reported as such rather than buried.**

### Phase 6b. Censored treatment of the sub-threshold markets

Extend the fit sample below 4,000 and add a left-censored likelihood
contribution. Replace the constant-per-hub cap with per-market estimates
respecting the bound.

- **Fixes.** The bound-as-point-estimate defect; the residual <10k band miss.
- **Effort.** 5 to 8 days.
- **Success.** The 73 capped markets receive distinct estimates, all at or below
  their ceiling; the <10k predicted band moves toward 1.00; no capped market
  exceeds its 2018 bound scaled by growth.

### Phase 6c. Residual structure and segmentation

Only if 6a and 6b leave measured systematic residual structure. Test the leisure
and business axis (W3.2) as the first candidate.

- **Effort.** 3 to 5 days.
- **Success.** Reduction in residual dispersion that survives a holdout, not an
  in-sample R2 gain.

### Explicitly out of scope for Phase 6

Adding Canadian datasets. A5 established the defect is specification, not data.
The one justified addition, StatCan CMA income, is tracked separately as W3.3
because it fixes the doubled destination-income elasticity, and it should not be
presented as addressing the size bias.

---

## 4. What must not regress

From the frozen baseline: `make test` 38 passing, `make reproducibility` 25
artifacts identical, reconciliation 14 of 14 in band, route-spell reproduction at
or above 90%.

And one methodological guardrail carried from section 1: **calibration is
reported binned by predicted value, never by observed.** The old table format is
what let a regression-to-the-mean artifact read as a specification finding.
