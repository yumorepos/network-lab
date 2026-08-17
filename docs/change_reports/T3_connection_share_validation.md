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
