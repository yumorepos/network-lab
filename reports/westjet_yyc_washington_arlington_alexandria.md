# Business case: YYC - Washington-Arlington-Alexandria, DC-VA-MD-WV (WestJet 737-8)

**Verdict: PASS** (confidence: medium)

## The two numbers that drive this
1. base margin -174.0% vs hurdle 8.0%
2. modeled share 34% of 51k pax/yr (anchor_x_growth)

## Market
- Distance 1971 mi, proposed 7x weekly, 174 seats.
- Demand 50,562 pax/yr, method **anchor_x_growth**:
  the market's own 2018 StatCan actual (43,410 pax,
  frozen table 23-10-0256) times T-100 corridor growth
  1.16. Market-specific evidence beats the hub-median
  gravity transfer wherever it exists.
- Gravity cross-check: the gravity x transfer path would have said
  118,842 pax/yr, i.e.
  2.35x the anchor-based estimate. That ratio
  is printed so a divergence from the last observed actual is never
  invisible. (Transfer factor context: hub median
  1.26, national median 0.80, IQR
  [0.53, 1.99].)

## Competition (reconstructed from T-100; no MIDT)
| carrier   | itin_type   |   freq_wk |   elapsed_h |
|:----------|:------------|----------:|------------:|
| UA        | nonstop     |   1.28846 |     4.30982 |
| WS        | nonstop     |   1.05769 |     4.30982 |
| UA        | onestop     |  15.2692  |     7.16708 |
| UA        | onestop     |  15.2692  |     7.09093 |
| DL        | onestop     |  10.9231  |     6.37036 |
| DL        | onestop     |  10.9231  |     6.38012 |
| UA        | onestop     |   9.26923 |     6.35278 |
| UA        | onestop     |   9.26923 |     6.39965 |

Modeled share for the proposed service: 34%.

## Economics (fully-allocated proxy: direct cost x comparator indirect burden + fee proxy)
| fuel \ fare | -15% | base | +10% |
|---|---|---|---|
| -30% fuel | -187.9% | -144.7% | -122.5% |
| +0% fuel | -222.3% | -174.0% | -149.1% |
| +30% fuel | -256.7% | -203.2% | -175.7% |

Break-even load factor 0.74 vs planned 0.27.
Fare from distance-matched US markets x 1.10
premium (assumption, sensitivity in grid). Costs from Southwest P-5.2 filings
with fuel rebuilt at EIA scenario prices.

## Top risk
gravity x transfer demand estimate; no current O&D truth for this market

## Assumptions this rests on
transfer factor; fare premium; airport fee proxy - all in config/assumptions.yaml with sources,
confidence, and sensitivity ranges. Margins carry the comparator's own
indirect burden (derived from Form 41), so the hurdle is fully-allocated.
