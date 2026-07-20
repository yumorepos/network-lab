# Business case: YYC - Dallas-Fort Worth-Arlington, TX (WestJet 737-8)

**Verdict: PASS** (confidence: medium)

## The two numbers that drive this
1. base margin -89.2% vs hurdle 8.0%
2. modeled share 34% of 67k pax/yr (anchor_x_growth)

## Market
- Distance 1523 mi, proposed 7x weekly, 174 seats.
- Demand 67,219 pax/yr, method **anchor_x_growth**:
  the market's own 2018 StatCan actual (57,711 pax,
  frozen table 23-10-0256) times T-100 corridor growth
  1.16. Market-specific evidence beats the hub-median
  gravity transfer wherever it exists.
- Gravity cross-check: the gravity x transfer path would have said
  141,351 pax/yr, i.e.
  2.10x the anchor-based estimate. That ratio
  is printed so a divergence from the last observed actual is never
  invisible. (Transfer factor context: hub median
  1.28, national median 0.82, IQR
  [0.55, 2.04].)

## Competition (reconstructed from T-100; no MIDT)
| carrier   | itin_type   |   freq_wk |   elapsed_h |
|:----------|:------------|----------:|------------:|
| AA        | nonstop     |  13.1154  |     3.47405 |
| UA        | onestop     |  15.2692  |     5.50724 |
| DL        | onestop     |  10.9231  |     6.21609 |
| UA        | onestop     |   9.26923 |     6.77067 |
| UA        | onestop     |   6.69231 |     6.34888 |
| AA        | onestop     |   5.09615 |     6.77067 |

Modeled share for the proposed service: 34%.

## Economics (fully-allocated proxy: direct cost x comparator indirect burden + fee proxy)
| fuel \ fare | -15% | base | +10% |
|---|---|---|---|
| -30% fuel | -99.4% | -69.4% | -54.0% |
| +0% fuel | -122.6% | -89.2% | -72.0% |
| +30% fuel | -145.8% | -109.0% | -90.0% |

Break-even load factor 0.68 vs planned 0.36.
Fare from distance-matched US markets x 1.10
premium (assumption, sensitivity in grid). Costs from Southwest P-5.2 filings
with fuel rebuilt at EIA scenario prices.

## Top risk
gravity x transfer demand estimate; no current O&D truth for this market

## Assumptions this rests on
transfer factor; fare premium; airport fee proxy - all in config/assumptions.yaml with sources,
confidence, and sensitivity ranges. Margins carry the comparator's own
indirect burden (derived from Form 41), so the hurdle is fully-allocated.
