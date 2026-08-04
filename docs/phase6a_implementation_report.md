# Phase 6A implementation report: Poisson QMLE gravity

**Date.** 2026-07-28
**Baseline.** `docs/W1.4_baseline_freeze.md`, commit `bd7d4dd`
**Evidence.** `docs/phase6a_poisson_comparison.md`, produced by
`scripts/phase6a_compare.py`

**Recommendation in one line: implement and keep, do not adopt as default yet.
Bundle adoption with Phase 6B.** Reasoning in section 6.

---

## 1. Methodology

### The defect

The Version 1 estimator fits `ln(pax)` by OLS and predicts `exp(Xb)`. By
Jensen's inequality that is not an estimate of expected passengers:

```
E[y | X] = exp(Xb) * E[exp(e) | X]
```

With a log-residual standard deviation of 0.99 the omitted factor is large.
Measured on the US calibration frame, `sum(predicted) / sum(observed) = 0.439`.
The median log residual is near zero, so the baseline recovers the conditional
**median** correctly and the conditional **mean** not at all.

### The estimator

Poisson pseudo-maximum-likelihood with a log link, same covariates, same
functional form:

```
E[y_i | x_i] = exp(b0 + b1*ln(pop_a*pop_b) + b2*ln(inc_a*inc_b)
                      + b3*ln(dist) + b4*ln(dist)^2)
```

First-order condition:

```
sum_i x_i * (y_i - exp(x_i'b)) = 0
```

With a constant in the design this forces `sum(fitted) = sum(observed)` exactly
on the fitting sample, by construction rather than by luck. That is the property
the baseline lacks.

Poisson QMLE requires only that the **conditional mean** be correctly specified.
Under Gourieroux, Monfort and Trognon (1984) the point estimates are consistent
under any true variance function, so the data need not be Poisson or even be
counts. The canonical application to gravity models is Santos Silva and
Tenreyro, "The Log of Gravity", Review of Economics and Statistics 88(4), 2006,
which shows log-OLS gravity estimates are inconsistent under heteroskedastic
errors and recommends Poisson PML.

### Why robust covariance is mandatory

The Poisson variance assumption is violated by five orders of magnitude:

```
Pearson chi2 / df = 223,598      (Poisson assumes 1)
variance / mean   = 899,671
```

Coefficient consistency survives this; standard errors do not. The naive Poisson
covariance is built from the false assumption `var = mean` and would understate
sampling variability by roughly the square root of the dispersion, inflating
every t-statistic by a factor in the hundreds. **`models/gravity_poisson.py`
fits with `cov_type="HC1"` and deliberately does not expose naive standard
errors.** The dispersion ratio is written into the artifact so a reader can see
the justification without rerunning anything.

## 2. Implementation

Estimator selection, not a rewrite. Every downstream consumer
(`models/demand.py`, `models/transfer.py`, `backtest/run_backtest.py`) is
unchanged and still calls `gravity.predict(pairs, vintage)`.

| file | role |
|---|---|
| `models/gravity.py` | public interface and dispatch; unchanged signatures |
| `models/gravity_log_ols.py` | Version 1 baseline estimator, extracted intact |
| `models/gravity_poisson.py` | Poisson QMLE with HC1 robust covariance |
| `scripts/phase6a_compare.py` | comparison framework |
| `tests/test_phase6a_poisson.py` | 7 tests |

**A note on the requested layout.** The plan specified `models/demand/`. That is
not constructible: `models/demand.py` already exists, and a module and a package
of the same name cannot coexist in one package. The estimators sit alongside
`gravity.py` instead, which also keeps the diff smaller.

Artifacts: `gravity_{vintage}.yaml` keeps its original unsuffixed name and
contents so the frozen baseline is untouched; Poisson writes
`gravity_{vintage}_poisson.yaml`. Both are inside the reproducibility gate,
which now covers **27** artifacts.

Model version selection is via `NETWORK_LAB_GRAVITY_ESTIMATOR`, which exists so
the counterfactual could be run through the real pipeline rather than a
reimplementation of it. Default remains `log_ols`.

## 3. Validation results

Both estimators on the same holdout (seed 7).

| metric | log_ols | poisson_qmle | better |
|---|---|---|---|
| aggregate pred/obs, `current` | 0.4352 | **0.9481** | Poisson |
| aggregate pred/obs, `pre2022` | 0.4508 | **1.046** | Poisson |
| RMSE, `current` | 233,700 | **168,100** | Poisson, -28% |
| calibration, top predicted decile | **3.4x off** | **1.1x** | Poisson |
| bands within [0.8, 1.15] | 0 of 5 | **4 of 5** | Poisson |
| median APE, `current` | **0.6153** | 0.7402 | OLS |
| MAPE, `current` | **1.050** | 1.849 | OLS |
| RMSLE, `current` | **1.001** | 1.128 | OLS |

Poisson wins every level metric; OLS wins every relative-error metric. That is
the expected consequence of the two estimators targeting different functionals
of the same conditional distribution, not evidence that one is broken.

## 4. Downstream impact

**Zero of 200 markets change verdict.** Ranking Spearman 0.88 to 1.00 by study;
backtest percentile Spearman 0.9878, and the null separation result is
unchanged.

**Why**, and this is the most important finding in Phase 6A: the transfer factor
is estimated as `observed_2018 / gravity_pred`. Raising `gravity_pred` lowers the
fitted transfer factor by the same proportion (national median 0.802 to 0.306,
0.38x), and transborder demand is their product, so the change cancels almost
exactly. **Transborder demand is structurally invariant to any uniform rescaling
of the gravity model.** Improving gravity's level calibration cannot improve
transborder estimates while the transfer factor remains a ratio to that same
model. Separately, `alaska_sea` is 45 of 45 observed DB1B, so gravity never fires
there at all.

**One genuine gain.** `gravity_x_transfer` fires for the first time: 14 markets
(12 WestJet, 2 Porter) move off the constant cap onto real per-market estimates,
all downward, from -0.0% to -72.5%.

**One genuine regression.** Transfer-factor dispersion worsens: sd of
ln(transfer) 0.915 to 1.130, IQR ratio 3.70 to 4.56. This is a published metric.

## 5. Limitations

1. **The truncation is untouched.** The frame is floored at
   `MIN_ANNUAL_PAX = 4,000`; both estimators are fitted above it and used below
   it. Both miss the smallest predicted band and Poisson misses it by more
   (1.98 against 1.56). Phase 6B.
2. **Per-market relative accuracy degrades.** Median APE 0.615 to 0.740 is a
   real cost, not an artifact.
3. **Quasi-likelihood quantities are not usable for testing.** Deviance and
   log-likelihood are reported but the variance assumption is false, so
   likelihood-ratio tests are invalid.
4. **Point-in-time leakage is unchanged.** All 11 vectors in
   `docs/W1.3_point_in_time_audit.md` still apply.
5. **The 4,000 threshold is approximate.** The smallest observed anchor is
   3,900.

## 6. Recommendation: implement and keep, do not adopt as default yet

The evidence supports Poisson being the better **model**. It does not yet
support Poisson being the better **default**, and those are different claims.

**For adoption.** It fixes a real, severe, quantified defect. Systematic 3.4x
under-prediction of the largest markets is exactly the wrong failure mode for a
system whose job is sizing markets it has never served, because large markets
are where launch decisions get made. Aggregate calibration 0.44 to 0.95 and RMSE
down 28% are large improvements on the criteria that matter for that job.

**Against adopting it today, as a standalone change.**

1. **Zero decision benefit.** Not one of 200 verdicts moves, and the backtest is
   unchanged. Nothing downstream improves.
2. **The benefit is structurally blocked.** The transfer factor absorbs the
   entire level correction by construction. Until that ratio-to-model
   construction is addressed, the transborder studies cannot benefit however
   good the gravity model becomes.
3. **It would degrade two published metrics** for that zero benefit: transfer
   dispersion (sd 0.915 to 1.130) and median APE (0.615 to 0.740).
4. **It would move a reader-facing headline number**, transfer median 0.80 to
   0.31, which appears in the README and the validation docs, with no analytic
   gain to justify explaining it.

**Recommended sequencing.** Adopt Poisson as the default **together with Phase
6B**, not before. 6B's censored estimation is what lets the gravity path
actually drive transborder demand instead of being bypassed by the cap, and it
is the point at which Poisson's calibration starts doing real work. Adopting
both at once also means the transfer-factor dispersion change is evaluated
against a transfer factor that is no longer a pure ratio to an uncalibrated
model.

**What would change this recommendation.** If Phase 6B is deferred
indefinitely, adopt Poisson standalone anyway: shipping a demand model that
recovers 44% of actual passengers is worse than shipping one with a 20% higher
median APE, and the current default should not be defended on the strength of
metrics that reward median-targeting.

## 7. Phase 6A completion against its success criteria

| criterion | status |
|---|---|
| Poisson model implemented | done, with robust covariance |
| Existing baseline preserved | `gravity_{vintage}.yaml` byte-identical; test asserts it |
| Comparison report produced | `docs/phase6a_poisson_comparison.md` |
| Calibration improvement demonstrated or rejected honestly | demonstrated on level metrics, rejected on relative metrics, both reported |
| Backtest impact documented | zero verdict changes, Spearman 0.9878, mechanism explained |
| Tests remain green | `make test` 45 passed, up from 38 |
| Reproducibility intact | `make reproducibility` 27 artifacts identical, up from 25 |
