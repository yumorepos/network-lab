# Business case: YYC - Philadelphia-Camden-Wilmington, PA-NJ-DE-MD (WestJet 737-8)

**Verdict: LAUNCH** (confidence: low)

## The two numbers that drive this
1. base margin 18.3% vs hurdle 8.0%
2. modeled share 62% of 112k pax/yr (modeled)

## Market
- Distance 2003 mi, proposed 7x weekly, 174 seats.
- Modeled O&D demand: 112,105 pax/yr - **modeled, not
  observed**: gravity (US-calibrated) x transfer factor
  1.26 (hub median; national median 0.80,
  IQR [0.53, 1.99]) x T-100 corridor growth
  1.16.
- 2018 anchor cross-check: 18,180 pax in the 2018 StatCan survey (frozen table 23-10-0256).

## Competition (reconstructed from T-100; no MIDT)
| carrier   | itin_type   |   freq_wk |   elapsed_h |
|:----------|:------------|----------:|------------:|
| UA        | onestop     |  15.2692  |     7.29792 |
| DL        | onestop     |  10.9231  |     6.468   |
| UA        | onestop     |   9.26923 |     6.52853 |
| AA        | onestop     |   5.09615 |     6.52853 |
| DL        | onestop     |   4.44231 |     6.46604 |

Modeled share for the proposed service: 62%.

## Economics (fully-allocated proxy: direct cost x comparator indirect burden + fee proxy)
| fuel \ fare | -15% | base | +10% |
|---|---|---|---|
| -30% fuel | 14.1% | 27.0% | 33.6% |
| +0% fuel | 3.8% | 18.3% | 25.7% |
| +30% fuel | -6.5% | 9.5% | 17.7% |

Break-even load factor 0.75 vs planned 0.91.
Fare from distance-matched US markets x 1.10
premium (assumption, sensitivity in grid). Costs from Southwest P-5.2 filings
with fuel rebuilt at EIA scenario prices.

## Top risk
gravity x transfer demand estimate; no current O&D truth for this market

## Assumptions this rests on
transfer factor; fare premium; airport fee proxy - all in config/assumptions.yaml with sources,
confidence, and sensitivity ranges. Margins carry the comparator's own
indirect burden (derived from Form 41), so the hurdle is fully-allocated.
