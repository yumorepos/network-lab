# Route evaluation: YYC - Philadelphia-Camden-Wilmington, PA-NJ-DE-MD (WestJet 737-8)

**Verdict: PASS** - margin stays negative even at its best-fit frequency (confidence: medium).
The market was evaluated across 3x, 7x, and 14x weekly; its best-fit schedule
was 3x weekly x 174 seats, and it
did not clear at any service level.

## The two numbers that drive this
1. base margin -92.1% vs hurdle 8.0%
2. modeled share 50% of 21k pax/yr (anchor_x_growth)

## Market
- Distance 2003 mi. Best-fit schedule
  3x weekly x 174 seats, chosen to
  maximize annual contribution at a feasible load factor.
- Demand 21,175 pax/yr, method **anchor_x_growth**:
  the market's own 2018 StatCan actual (18,180 pax,
  frozen table 23-10-0256) times T-100 corridor growth 1.16.
- Gravity cross-check: the gravity x transfer path would have said
  113,457 pax/yr, i.e.
  5.36x the anchor-based estimate - printed so a
  divergence from the last observed actual is never invisible. (Transfer
  factor: hub median 1.28, national median
  0.80, IQR [0.55, 2.02].)

## Competition (reconstructed from T-100; no MIDT)
| carrier   | itin_type   |   freq_wk |   elapsed_h |
|:----------|:------------|----------:|------------:|
| UA        | onestop     |  15.2692  |     7.29792 |
| DL        | onestop     |  10.9231  |     6.468   |
| UA        | onestop     |   9.26923 |     6.52853 |
| AA        | onestop     |   5.09615 |     6.52853 |
| DL        | onestop     |   4.44231 |     6.46604 |

Modeled share for the proposed service at the chosen frequency:
50%.

## Economics at the chosen service level (fully-allocated proxy)
| fuel \ fare | -15% | base | +10% |
|---|---|---|---|
| -30% fuel | -101.9% | -71.6% | -56.0% |
| +0% fuel | -126.0% | -92.1% | -74.6% |
| +30% fuel | -150.2% | -112.6% | -93.3% |

Break-even load factor 0.75 vs achieved 0.39.
Fare from distance-matched US markets x 1.10
premium (assumption, sensitivity in grid). Costs from Southwest P-5.2 filings
with fuel rebuilt at EIA scenario prices, carrying the comparator's own
indirect burden (fully-allocated).

## Why this is a PASS, plainly
demand anchored to the 2018 StatCan actual scaled by T-100 corridor growth; the 2018 survey is the last transborder O&D truth. This conclusion holds at WestJet's actual transborder
service levels: the market was tested at 3x, 7x, and 14x weekly and did not
clear. The broader finding is that WestJet already serves its viable YYC
transborder markets (New York, the California and Nevada leisure markets,
Houston, the Florida and Arizona sun routes); what remains unserved is either
too small (below the 2018 survey's own 4,000-passenger floor) or too
thoroughly held by a US network carrier's connecting hub, and this evaluation
is consistent with WestJet directing its recent transborder growth to Edmonton
and Vancouver rather than adding YYC breadth.
