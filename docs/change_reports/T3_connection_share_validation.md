# Change report: T3, the connection-only share validation

**Task.** T3 of the six-task finish plan in `docs/STAGE_2R_DECISION.md`
section 6. The required form of old task W2.3.
**Date.** 2026-08-17
**Baseline.** The existing share validation, `models/share_validation.py`,
published as MAE 5.7 share points in `docs/validation.md`. That check is
**not modified**.

---

## 0. Protocol, frozen before any expanded result was computed

**Section 0 was written and committed before the stratified validation
existed.** The strata, the sample minimums and the decision rule below could
not have been chosen to match an outcome.

### 0.1 What is being validated, and why it is the only required task

Stage 2R.5 classified W2.3 REQUIRED on three measurements:

- reconstructed one-stops carry **95.2%** of WestJet competitor preference;
- **85 of 88** WestJet candidates have no nonstop incumbent;
- the existing share check covers that structural regime with **2 of 66**
  markets.

The competition and share layer is one of only two that materially reorder the
candidate ranking. It is therefore a claimed component of the final
fixed-gauge screening product, and it is validated almost entirely outside the
regime the flagship study occupies. T3 closes that gap.

### 0.2 Validation only

Nothing is fitted, refitted or tuned. Specifically **not** touched: detour
bounds (`DETOUR_MAX`, `DETOUR_ABS_MI`), the minimum connecting frequency, the
connect-time allowance, `MIN_SEGMENT_DEPS_YR`, the QSI weights, the frequency
exponent, the elapsed-time exponent, and every carrier preference. No new
source is ingested. If the result is poor, the finding is recorded and the
repair is a separate decision, not part of this task.

### 0.3 Data, and the one sampling change

Existing cached inputs only: `fact_od_market` at the year the current check
uses, and `fact_segment` over the same trailing window, both already in the
warehouse.

The current check is anchored at hub **SEA** with a floor of **50,000** annual
O&D passengers. That floor is why the zero-nonstop stratum is nearly empty:
large markets have nonstops, so a high floor selects the regime the flagship
study does not occupy.

The stratified validation keeps the hub and lowers the floor to **4,000**
annual O&D passengers. This is not a new constant. It is the same threshold
`replay/snapshot.py:build_demand` already uses to decide a `us_domestic` DB1B
market is too thin to read observed, and the same one
`models/economics.py:fare_curve` uses to admit a market to the fare fit. At
that floor the SEA panel holds 178 markets against 66 today.

**No hub is added.** Selecting hubs until a stratum fills would be sampling to
a result. If the minimums in 0.6 are not met at SEA, the verdict is
`VALIDATION INSUFFICIENT` and the protocol does not permit widening.

**The existing check is untouched.** `validate()` keeps its 50,000 floor, so
`headline_metrics.yaml`, `docs/validation.md` and the consistency tests do not
move. T3 adds a separate function and a separate artifact.

### 0.4 The strata

Defined on what the model reconstructs, because that is the thing under test.

| stratum | definition | why it matters |
|---|---|---|
| **A** | at least one nonstop carrier in the reconstruction | the regime the existing check covers |
| **B** | no nonstop carrier, two or more carriers reconstructed from one-stops | **the regime the WestJet study occupies**, and the one under test |
| **C** | exactly one carrier reconstructed, so its modelled share is 1.0 | the analogue of the candidate-side default that gives a proposed service share 1.0 when no competitor is found |

Stratum C is the validation analogue of the 33 WestJet candidates at 2022-01
that receive share 1.0 because the reconstruction found no competitor. On the
validation side the same condition is observable against truth: if the sole
reconstructed carrier really does carry the market, the default is defensible;
if it does not, the default overstates share.

### 0.5 Metrics

Per stratum: rows, markets, passenger weight, observed and modelled share
distributions, MAE in share points, passenger-weighted MAE, signed bias
(modelled minus observed), Spearman correlation between modelled and observed
share, the largest absolute errors named, and the share of each stratum's
preference that rests on an unresolved operating certificate.

Each stratum is also reported as a fraction of the actual Stage 2R candidate
universe, so a stratum that is well validated but rare is not mistaken for
one that matters.

**A null model is scored alongside.** For every market the null assigns equal
share to each carrier the reconstruction identifies. This separates two
claims that are otherwise conflated: that the reconstruction identifies the
right competitors, and that QSI-lite weights them correctly. Only the second
is what a share model adds.

### 0.6 Sample minimums, declared in advance

Stratum B is evaluable only with at least **30 market-carrier rows across at
least 10 distinct markets**. A market is the cluster, so both matter. These
are reporting conventions, not fitted values, and they are disclosed here for
that reason. Below either minimum the verdict is `VALIDATION INSUFFICIENT`
regardless of what the errors look like.

### 0.7 The decision rule, fixed in advance

Anchored on falsification rather than on a tolerance, so that no threshold has
to be invented and none can be chosen afterwards.

| verdict | condition |
|---|---|
| **CONNECTION SHARE VALIDATED FOR FINAL SCOPE** | stratum B meets 0.6, and QSI-lite's MAE in stratum B is **lower than the equal-share null's** |
| **CONNECTION SHARE USABLE WITH MATERIAL LIMITATION** | stratum B meets 0.6, QSI-lite does not beat the null on MAE, but modelled and observed shares are **positively rank-correlated**: it identifies who leads without sizing the gap |
| **CONNECTION SHARE NOT VALIDATED, DE-SCOPE OR REPAIR REQUIRED** | stratum B meets 0.6, and neither holds |
| **VALIDATION INSUFFICIENT** | stratum B fails 0.6 |

Beating the null is the meaningful bar. A share model that cannot outperform
"split the market evenly among the carriers you found" is contributing
identification, not sizing, and the final document should say so.

### 0.8 Stratum C, classified separately

The share-1.0 default is judged against a threshold the model already
declares, not a new one. `build_screen` caps a verdict at MONITOR when
`proposed_share > 0.70` with no nonstop incumbent, so the engine itself
declares 0.70 the point beyond which such a share is untrustworthy.

- **defensible** if the median observed share of the sole reconstructed
  carrier is at or above 0.70: the reconstruction's monopoly finding is
  broadly right, and the existing guard is correctly placed;
- **aggressive** if it is below 0.70: the reconstruction misses real
  competitors and the default overstates the proposed service's share, in
  which case the existing `share_uncertainty` guard is load-bearing rather
  than precautionary and must be described that way;
- **unsupported** if stratum C is too small to say.

### 0.9 What a failure would mean

If stratum B returns `NOT VALIDATED`, the competition and share layer cannot
be carried as a claimed component of the final product. The options at that
point, none of which is taken in T3, would be to de-scope the layer to a
documented heuristic, or to repair the reconstruction. Either is a separate
decision and would make T3 an analytical blocker for the checkpoint.

A `USABLE WITH MATERIAL LIMITATION` result is not a blocker. It narrows what
may be claimed, which is a documentation task already scheduled as T4.

---

## 1. Result

> # CONNECTION SHARE VALIDATED FOR FINAL SCOPE

> - stratum B: 482 rows across 87 markets, MAE 6.5 share points against an equal-share null of 9.4.
> - QSI-lite beats the null, so the layer contributes sizing and not only identification.

Hub SEA, year 2024, floor 4,000 annual O and D passengers. 1047 market-carrier rows across 176 markets, against 503 rows across 66 markets in the published check.

### By stratum

| stratum | markets | rows | passengers | median observed share | median modelled share | MAE | passenger-weighted MAE | equal-share null MAE | beats null | bias | Spearman | worst error |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **A nonstop competition** | 66 | 503 | 23,943,780 | 0.022 | 0.054 | **5.5** | 10.5 | 12.8 | yes | -0.05 | 0.887 | 48.6 |
| **B one-stop competition only** | 87 | 482 | 1,422,090 | 0.099 | 0.150 | **6.5** | 8.1 | 9.4 | yes | -0.03 | 0.874 | 46.5 |
| **C sole reconstructed carrier** | 23 | 62 | 977,700 | 0.037 | 0.000 | **5.9** | 16.9 | 5.9 | no | -0.00 | 0.837 | 34.2 |

All errors are in share points. Bias is modelled minus observed, so a negative value means the model understates.

### Reading the table

**Stratum B is the result T3 was commissioned for.** 482 market-carrier rows
across 87 markets, comfortably past the declared minimums of 30 and 10. MAE
6.5 share points against an equal-share null of 9.4, and Spearman 0.874
between modelled and observed share. The layer contributes sizing, not only
the identification of who competes, which is the bar protocol 0.7 set.

Stratum B is now the **largest** stratum by market count, 87 of 176. The old
50,000 passenger floor was the entire reason the regime looked unobservable:
it is not rare, it is small.

**Stratum B is only about one point worse than stratum A** on unweighted MAE,
6.5 against 5.5, and is **better** on passenger-weighted MAE, 8.1 against
10.5. Reconstructing competition from one-stops is not markedly harder than
scoring it where a nonstop exists. Both biases are near zero, so neither
regime is systematically over or under-stated.

**Stratum C cannot beat the null by construction**, and its row reads that
way: with one reconstructed carrier the equal-share null assigns that carrier
1.0, which is exactly what the model assigns. Its MAE is reported for
completeness and carries no verdict weight. The stratum is judged separately
below.

**Unresolved operating certificates contribute nothing at this hub.** The
mean unresolved share of competitor preference is 0.000 in every stratum,
consistent with the Stage 2R.5 measurement that unresolved regional flying is
0.09% of SEA departures. This is the second independent confirmation that
W2.2 was correctly classified NOT JUSTIFIED.

---

## 2. Stratum C: is the share-1.0 default defensible?

The candidate-side question. At 2022-01, 33 of 88 WestJet candidates receive
share 1.0 because the reconstruction finds no competitor at all. The
validation analogue is a market where the reconstruction finds exactly one
carrier and therefore gives it share 1.0.

| quantity | value |
|---|---|
| markets | 23 |
| median observed share of the sole reconstructed carrier | **0.987** |
| mean | 0.921 |
| interquartile range | 0.879 to 0.991 |
| fraction at or above the engine's own 0.70 limit | **95.7%** |
| mean number of carriers actually selling in those markets | 2.70 |

**Classification: defensible.**

The reconstruction does miss carriers: on average 2.70 carriers sell tickets
in these markets and the model finds one. But the carriers it misses are
small. The one it finds really does carry the market, at a median observed
share of 0.987, and 22 of 23 markets sit at or above the 0.70 limit the engine
already uses to distrust such a share.

So the share-1.0 default overstates by roughly one to twelve share points at
the median, which is inside the same error band as the other two strata. The
existing `share_uncertainty` guard in `build_screen`, which caps such a
verdict at MONITOR, is **correctly placed and precautionary rather than
load-bearing**. That is a stronger statement than the guard's own comment
makes, and it should be carried into the limitations document in T4.

**One protocol gap, disclosed.** Section 0.6 fixed a minimum for stratum B in
market-carrier rows. It did not fix one for stratum C, which yields exactly
one relevant observation per market, so the row minimum does not transfer. The
declared **market** minimum of 10 was applied instead, and stratum C's 23
markets clear it either way. The full distribution is reported above so a
reader who would set the bar elsewhere can do so without recomputing.

---

## 3. Representation in the Stage 2R candidate universe

A stratum can be well validated and still be rare. It is not, here.

| regime | share of the validation panel | share of the WestJet candidate universe |
|---|---|---|
| nonstop competition present | 66 of 176 markets | 3 of 88 candidates at 2022-01 |
| one-stop competition only | **87 of 176 markets** | the great majority |
| no competitor reconstructed | 23 of 176 markets | 33 of 88 at 2022-01, 1 of 80 and 1 of 76 after |

The validation panel now over-represents nonstop markets relative to the
flagship study rather than the reverse, which is the correct direction for a
check: the regime the study depends on is the one with 87 markets behind it.

The 2022-01 concentration of zero-competitor candidates is a COVID-window
artifact and not a heuristic failure. The trailing T-100 window at that cutoff
covers 2021, when connecting service was suspended at scale; at the two later
cutoffs the same reconstruction finds a competitor for all but one candidate.

---

## 4. Answers to the three questions T3 was asked

**1. Does the one-stop reconstruction produce directionally credible
competitive shares in the zero-nonstop regime?** Yes. MAE 6.5 share points on
87 markets, better than an equal-share null at 9.4, Spearman 0.874, and near
zero bias. It is about one point worse than the nonstop regime unweighted and
better passenger-weighted.

**2. Is the share-1.0 default empirically defensible?** Yes, and mildly
conservative in its consequence. The sole reconstructed carrier carries a
median 0.987 of its market. The default overstates the proposed service's
share by a few points, and the existing 0.70 guard already catches the cases
where it would matter.

**3. Can the competition and share layer remain a claimed component of the
final fixed-gauge screening product without further calibration?** **Yes**,
with the error band stated. The claim it supports is "modelled competitive
shares agree with observed DB1B ticketing shares to about 6 to 7 share points
in the regime the flagship study occupies, and beat an equal-share null".
It does not support a claim of calibrated share prediction, and T4 should
publish the figure with the stratum it came from.

---

## 5. Regression risk

**Guarded by** `tests/test_share_validation_strata.py`, ten tests: the
published check is unmodified, the sampling floor is the one the demand layer
already uses, the strata partition the sample, modelled and null values are
shares that sum to at most one per market, stratum B clears the declared
minimums, the null really is an equal split, the verdict rule maps to the
frozen protocol on synthetic frames, and no QSI or reconstruction parameter
moved.

**Would still slip through:**

- A regime difference between SEA and Calgary. The check is a US domestic
  proxy for a transborder competitive set, because DB1B is the only ticketing
  truth available and it does not cover Canadian origins. Nothing here closes
  that, and T4 must say so.
- Correlated error. Market is the cluster and the metrics are unclustered
  means, so the intervals a reader might infer from n are optimistic. No
  interval is reported for that reason.
- A reconstruction that is right on average and wrong on the markets that
  matter. The worst errors are 46.5 share points in stratum B.
- Year-specific structure. One DB1B year is scored.

---

## 6. Statistical meaningfulness

- **Sample size:** stratum B, 482 market-carrier rows across 87 markets.
- **Comparison:** an equal-share null on identical markets and carriers,
  which isolates sizing from identification.
- **Verdict: improvement over the null**, on a sample large enough to say so,
  and reported without a confidence interval because the clustering is not
  modelled.

---

## 7. Assumptions touched

**None.** No entry in `config/assumptions.yaml` or
`config/replay_protocol.yaml` was added, removed, fitted or moved. `MIN_PAX`
in the new module is the 4,000 threshold `replay/snapshot.py:build_demand` and
`models/economics.py:fare_curve` already use, asserted by a test rather than
restated.

The two reporting conventions, the 30-row and 10-market minimums, are declared
in protocol 0.6 and live in the module rather than in a config file because
they govern reporting rather than the model.

---

## 8. Adoption decision

> **ADOPTED. The competition and share layer stays in the final product**, with
> its error band published and its two limitations, the US domestic proxy and
> the unclustered metrics, carried into T4.

W2.3 is closed. No calibration was performed and none is justified: the layer
already beats its null in the regime that matters.
