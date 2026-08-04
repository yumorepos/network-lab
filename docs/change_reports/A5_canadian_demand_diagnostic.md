# A5: Canadian demand diagnostic (Milestone A exit gate)

**Task.** W3.1 from PHASE_5_6_PLAN.md. Diagnostic only.
**Date.** 2026-07-28
**Scope honoured.** No model code, `config/assumptions.yaml`, or model parameter
was modified. No dataset was added. The one counterfactual was run out of tree
against committed artifacts. This is a diagnosis, not a fix.

---

## Diagnosis

**Primary cause: (1) methodology and specification failure.** The gravity model
has a monotonic size bias that is present in the US calibration itself, with no
transfer factor involved. It over-predicts small markets and under-predicts
large ones. Everything downstream, including the cap binding on 52 of 76 WestJet
markets, follows from that.

**Contributing: (4) insufficient market segmentation.** One specification is fit
across a demand range spanning four orders of magnitude, and the error is
systematic by size band rather than random.

**Contributing but secondary: (2) missing explanatory variables.** Real, and
documented elsewhere (unmodeled leisure and business axis in the transfer
factor; Canadian hub income absent so `inc_a` is set to destination income).
Neither explains the size slope.

**Largely exonerated: (3) unrealistic calibration transfer from US markets.**
The transfer factor is a per-hub scalar. A scalar cannot create a bias that
varies monotonically with market size, and the identical bias shape appears in
US markets where no transfer is applied at all. The transfer contributes a level
shift, which is what it is designed to do.

---

---

## CORRECTION issued 2026-07-28, after this document was committed

The evidence table below bins gravity error by **observed** demand. That
conditions on the outcome: binning by the observed value sorts negative
residuals into the low bands and positive residuals into the high bands, so a
perfectly calibrated model with noise reproduces the monotonic pattern on its
own. The correct calibration test bins by **predicted** value.

Rebinned, same model and data:

| band | by observed (below) | by predicted (correct) |
|---|---|---|
| under 10k | 1.97 | 0.89 |
| 10k to 25k | 1.29 | 1.52 |
| 25k to 50k | 0.83 | 1.29 |
| 50k to 100k | 0.54 | 0.78 |
| over 100k | 0.30 | 0.42 |

**The conclusion of this document is unchanged**: the defect is specification,
not the transfer factor. The US and transborder columns were binned identically,
so the roughly constant offset between them still shows the transfer acting as a
level shift, and bias in the US column with no transfer applied is still
decisive.

**What changes** is the characterisation of the defect. On the conditional mean,
which is what a demand forecast must get right, it is worse than reported here:
`sum(predicted)/sum(observed) = 0.439`, so the model predicts 44% of the traffic
that actually flew. The median log residual is near zero, meaning the model
recovers the conditional median and not the mean. That is retransformation bias,
and this document under-stated it while over-stating the slope.

The same caveat applies to the "gravity exceeds the censoring bound on 100% of
capped markets" finding below: capped markets are selected by having low true
demand, so that comparison is also outcome-conditioned and some of the 4.5x
excess is expected from noise alone.

Full corrected analysis and the resulting migration plan:
`docs/phase6_demand_model_redesign.md` section 1.

---

## Evidence

### The decisive test: gravity bias where truth exists

Median predicted over observed, by market size. The US column applies **no
transfer factor whatsoever**; the transborder column is measured against the
observed 2018 StatCan anchor.

| market size | US domestic (no transfer), n=6,092 | transborder (with transfer), n=82 |
|---|---|---|
| under 10k | **1.97x** | 5.26x |
| 10k to 25k | 1.29x | 3.77x |
| 25k to 50k | 0.83x | 2.01x |
| 50k to 100k | 0.54x | 1.43x |
| over 100k | **0.30x** | 0.99x |

Read the US column first. With no border, no transfer and no Canadian data
involved, the model over-predicts the smallest markets by roughly 2x and
under-predicts the largest by roughly 3x, monotonically. That is the signature of
fitting a log-linear model by OLS on a heavily skewed target: minimising
proportional error in logs compresses the predicted range toward the mean.

The transborder column is the same shape shifted upward by a roughly constant
factor of 2.4x to 3.3x across every band. A shift is what a scalar transfer
factor does. It does not change the slope, and the slope is the problem.

On the anchored transborder markets, gravity over-predicts in **89%** of cases,
median 3.00x. Broken out, the ratio falls from 5.26x on sub-10k markets to 0.99x
above 100k: essentially unbiased where markets are large.

### Capped market counts

By hub and carrier:

| hub | carrier | candidates | capped | rate |
|---|---|---|---|---|
| YYC | WS | 76 | 52 | 68.4% |
| YYZ | PD | 79 | 21 | 26.6% |

By metro population, where the clustering is sharpest:

| population | YYC capped / n | YYZ capped / n |
|---|---|---|
| under 500k | 14 / 15 (93%) | 12 / 14 (86%) |
| 500k to 1M | 28 / 32 (88%) | 9 / 28 (32%) |
| 1M to 2M | 10 / 17 (59%) | 0 / 16 |
| 2M to 5M | 0 / 10 | 0 / 15 |
| over 5M | 0 / 2 | 0 / 6 |

By distance:

| distance | YYC capped / n | YYZ capped / n |
|---|---|---|
| under 750 mi | 2 / 3 | 7 / 37 |
| 750 to 1250 | 8 / 12 | 6 / 20 |
| 1250 to 1750 | 11 / 24 | 4 / 11 |
| 1750 to 2500 | 31 / 37 (84%) | 4 / 11 |

By US region (capped rate): YYC South 79%, Northeast 70%, West 69%, Midwest 40%.
YYZ Northeast 40%, West 33%, South 26%, Midwest 19%.

### Do the caps cluster systematically?

Yes, and not by geography. **Population is the dominant axis**: capping is
monotonic in metro size and falls to zero above 2M at both hubs. Distance is a
secondary axis at YYC only, where 84% of markets beyond 1,750 miles are capped,
which is consistent with small distant metros rather than an independent
distance effect. Regional variation is weaker than the size effect and is
explained by which regions hold the small metros.

This clustering is exactly what the specification bias predicts. Small markets
are where gravity over-predicts, and they are the markets that fall below the
survey's publication floor and therefore lack an anchor.

### Distribution of capped versus uncapped estimates

| hub | capped | n | mean | median | min | max |
|---|---|---|---|---|---|---|
| YYC | no | 24 | 12,822 | 9,880 | 4,543 | 67,219 |
| YYC | **yes** | 52 | **4,659** | **4,659** | **4,659** | **4,659** |
| YYZ | no | 58 | 50,855 | 16,820 | 4,400 | 399,883 |
| YYZ | **yes** | 21 | **3,729** | **3,729** | **3,729** | **3,729** |

Standard deviation of the capped groups is exactly zero. **The model emits one
identical number per hub for every capped market**, collapsing metros spanning
412,339 to 1,760,548 population (a 4.3x spread) and 289 to 2,181 miles into a
single value. The uncapped gravity path would have spanned 4,699 to 36,132 at
YYC and 6,329 to 47,469 at YYZ.

### The cap is a valid bound, not an arbitrary patch

This is the part the earlier audit framing got wrong, and it matters. The
ceiling is `4,000 x t100_growth`: 4,659 at YYC (growth 1.1648) and 3,729 at YYZ
(growth 0.9323). StatCan published only city pairs above roughly 4,000
passengers, so a market's **absence from the survey is itself an observation**:
it was below that floor in 2018. Capping at the floor scaled by corridor growth
is a statistically defensible upper bound on a left-censored quantity.

Gravity exceeds that known bound on **100%** of capped markets, by a median
factor of 4.5x. That is independent confirmation of the specification bias: the
model systematically predicts above a ceiling that the source data proves cannot
have been exceeded.

Caveat on exactness: the smallest observed anchor is 3,900 passengers, slightly
below the stated 4,000 floor, so the threshold is approximate rather than a hard
cut. It does not change the direction or magnitude of the finding.

### Is the cap decision-relevant?

Yes, which is the answer that determines Phase 6 priority.

As shipped, every capped market is a decisive PASS: best margin -354% at YYC and
-622% at YYZ, maximum load factor 0.09. None is near a boundary.

But an out-of-tree counterfactual removing the cap and substituting the full
uncapped gravity estimate (median scale 3.8x at YYC, 5.8x at YYZ):

| | YYC | YYZ |
|---|---|---|
| best margin, capped to uncapped | -354% to **+11%** | -622% to **+41%** |
| median margin | -1,146% to -104% | -1,575% to -61% |
| markets clearing the 8% hurdle | **1** | **3** |
| markets clearing the 0.50 LF floor | 11 | 11 |

So the choice between the cap and the raw gravity estimate moves up to four
markets across the two studies between PASS and LAUNCH-eligible. Neither end of
that range is trustworthy: the cap is a bound reported as a point estimate, and
the uncapped value comes from the size class where the model is provably worst.

---

## Answering the framing question

**Is this methodology or missing data?** Methodology, primarily. The size bias is
measurable in the US calibration where no Canadian data is involved and no
transfer is applied. No amount of Canadian data fixes a specification that
compresses the predicted range.

The genuine data constraint is narrower than it looks and is one of censoring
rather than absence. For the 73 capped markets we do have information: an upper
bound of roughly 4,000 passengers in 2018, plus corridor growth. The model
currently discards the informative part of that and reports the bound itself.

**No dataset is recommended for addition on this evidence.** The one previously
identified candidate, StatCan CMA income, remains justified on separate grounds
(it removes the doubled destination-income elasticity in `models/demand.py`) but
it will not address the size bias and should not be sold as doing so.

---

## Recommended Phase 6 path, in priority order

1. **Correct the gravity specification for small markets.** The bias is
   measurable, monotonic and therefore correctable. Candidate approaches, to be
   tested against the frozen W1.4 baseline rather than chosen in advance: a
   Poisson or negative-binomial GLM with a log link, which handles skewed count
   data without the retransformation bias OLS-in-logs introduces; or a smearing
   or Duan-style retransformation correction on the existing fit. Success is
   measured as the median predicted-over-observed ratio approaching 1.0 across
   all five size bands, not as a better R2.

2. **Use the censoring instead of discarding it.** Once the specification is
   fixed, the 73 capped markets should receive a point estimate below their known
   bound, from a censored regression (Tobit or equivalent) that treats "below
   4,000 in 2018" as left-censored information. That replaces one constant per
   hub with per-market estimates that still respect the bound.

3. **Then, and only then, revisit segmentation** (cause 4). Once the range
   compression is corrected, measure how much systematic error remains by market
   type. Segmenting before fixing the specification would fit separate models
   that each carry the same retransformation bias.

4. **Deprioritise transfer-factor work as a fix for this problem.** Modelling the
   transfer factor on a leisure indicator remains the highest value-per-hour item
   in the plan for reducing reported *uncertainty*, and W3.2 should still happen.
   But this diagnostic shows it is not the cause of the capping, and it should
   not be scheduled as though it were.

Every step above is a Phase 6 change and none should start before the W1.4
baseline is frozen, so that the before and after is measurable.

---

## Gate status

Milestone A exit criteria: baseline foundation reproducible (`make
reproducibility` passes, 25 artifacts) and the Canadian demand question answered
in writing. **This document closes the second.** W1.3 point-in-time snapshots and
W1.4 the frozen baseline remain open before Milestone B may begin.
