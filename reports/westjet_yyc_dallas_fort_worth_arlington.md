# Business case: YYC - Dallas-Fort Worth-Arlington, TX (WestJet 737-8)

**Verdict: MONITOR** (confidence: medium)

## The two numbers that drive this
1. base margin 11.4% vs hurdle 8.0%
2. modeled share 36% of 141k pax/yr (modeled)

## Market
- Distance 1523 mi, proposed 7x weekly, 174 seats.
- Modeled O&D demand: 140,809 pax/yr - **modeled, not
  observed**: gravity (US-calibrated) x transfer factor
  1.26 (hub median; national median 0.80,
  IQR [0.53, 1.99]) x T-100 corridor growth
  1.16.
- 2018 anchor cross-check: 57,711 pax in the 2018 StatCan survey (frozen table 23-10-0256).

## Competition (reconstructed from T-100; no MIDT)
| carrier   | itin_type   |   freq_wk |   elapsed_h |
|:----------|:------------|----------:|------------:|
| AA        | nonstop     |  13.1154  |     3.47405 |
| UA        | onestop     |  15.2692  |     5.50724 |
| DL        | onestop     |  10.9231  |     6.21609 |
| UA        | onestop     |   6.69231 |     6.34888 |

Modeled share for the proposed service: 36%.

## Economics (fully-allocated proxy: direct cost x comparator indirect burden + fee proxy)
| fuel \ fare | -15% | base | +10% |
|---|---|---|---|
| -30% fuel | 6.6% | 20.6% | 27.9% |
| +0% fuel | -4.2% | 11.4% | 19.4% |
| +30% fuel | -15.1% | 2.1% | 11.0% |

Break-even load factor 0.68 vs planned 0.77.
Fare from distance-matched US markets x 1.10
premium (assumption, sensitivity in grid). Costs from Southwest P-5.2 filings
with fuel rebuilt at EIA scenario prices.

## Top risk
gravity x transfer demand estimate; no current O&D truth for this market

## Assumptions this rests on
transfer factor; fare premium; airport fee proxy - all in config/assumptions.yaml with sources,
confidence, and sensitivity ranges. Margins carry the comparator's own
indirect burden (derived from Form 41), so the hurdle is fully-allocated.
