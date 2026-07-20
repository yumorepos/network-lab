# Business case: YYC - Sacramento-Roseville-Folsom, CA (WestJet 737-8)

**Verdict: LAUNCH** (confidence: low)

## The two numbers that drive this
1. base margin 34.8% vs hurdle 8.0%
2. modeled share 95% of 66k pax/yr (modeled)

## Market
- Distance 934 mi, proposed 7x weekly, 174 seats.
- Modeled O&D demand: 65,656 pax/yr - **modeled, not
  observed**: gravity (US-calibrated) x transfer factor
  1.26 (hub median; national median 0.80,
  IQR [0.53, 1.99]) x T-100 corridor growth
  1.16.
- 2018 anchor cross-check: 12,450 pax in the 2018 StatCan survey (frozen table 23-10-0256).

## Competition (reconstructed from T-100; no MIDT)
| carrier   | itin_type   |   freq_wk |   elapsed_h |
|:----------|:------------|----------:|------------:|
| QX        | onestop     |   3.84615 |     4.56601 |

Modeled share for the proposed service: 95%.

## Economics (fully-allocated proxy: direct cost x comparator indirect burden + fee proxy)
| fuel \ fare | -15% | base | +10% |
|---|---|---|---|
| -30% fuel | 30.9% | 41.3% | 46.6% |
| +0% fuel | 23.3% | 34.8% | 40.7% |
| +30% fuel | 15.7% | 28.4% | 34.9% |

Break-even load factor 0.57 vs planned 0.88.
Fare from distance-matched US markets x 1.10
premium (assumption, sensitivity in grid). Costs from Southwest P-5.2 filings
with fuel rebuilt at EIA scenario prices.

## Top risk
gravity x transfer demand estimate; no current O&D truth for this market

## Assumptions this rests on
transfer factor; fare premium; airport fee proxy - all in config/assumptions.yaml with sources,
confidence, and sensitivity ranges. Margins carry the comparator's own
indirect burden (derived from Form 41), so the hurdle is fully-allocated.
