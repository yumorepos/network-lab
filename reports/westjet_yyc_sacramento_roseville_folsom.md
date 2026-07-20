# Business case: YYC - Sacramento-Roseville-Folsom, CA (WestJet 737-8)

**Verdict: PASS** (confidence: low)

**Share-uncertainty flag:** modeled share exceeds 70% with no nonstop incumbent; competition reconstruction is likely incomplete. Verdict capped at MONITOR.

## The two numbers that drive this
1. base margin -161.8% vs hurdle 8.0%
2. modeled share 95% of 15k pax/yr (anchor_x_growth)

## Market
- Distance 934 mi, proposed 7x weekly, 174 seats.
- Demand 14,501 pax/yr, method **anchor_x_growth**:
  the market's own 2018 StatCan actual (12,450 pax,
  frozen table 23-10-0256) times T-100 corridor growth
  1.16. Market-specific evidence beats the hub-median
  gravity transfer wherever it exists.
- Gravity cross-check: the gravity x transfer path would have said
  66,295 pax/yr, i.e.
  4.57x the anchor-based estimate. That ratio
  is printed so a divergence from the last observed actual is never
  invisible. (Transfer factor context: hub median
  1.28, national median 0.82, IQR
  [0.55, 2.04].)

## Competition (reconstructed from T-100; no MIDT)
| carrier   | itin_type   |   freq_wk |   elapsed_h |
|:----------|:------------|----------:|------------:|
| QX        | onestop     |   3.84615 |     4.56601 |

Modeled share for the proposed service: 95%.

## Economics (fully-allocated proxy: direct cost x comparator indirect burden + fee proxy)
| fuel \ fare | -15% | base | +10% |
|---|---|---|---|
| -30% fuel | -177.4% | -135.8% | -114.4% |
| +0% fuel | -208.0% | -161.8% | -138.0% |
| +30% fuel | -238.5% | -187.7% | -161.6% |

Break-even load factor 0.57 vs planned 0.22.
Fare from distance-matched US markets x 1.10
premium (assumption, sensitivity in grid). Costs from Southwest P-5.2 filings
with fuel rebuilt at EIA scenario prices.

## Top risk
modeled share exceeds 70% with no nonstop incumbent: incomplete competition likely; capped at MONITOR

## Assumptions this rests on
transfer factor; fare premium; airport fee proxy - all in config/assumptions.yaml with sources,
confidence, and sensitivity ranges. Margins carry the comparator's own
indirect burden (derived from Form 41), so the hurdle is fully-allocated.
