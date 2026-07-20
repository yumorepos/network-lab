# Route evaluation: YYC - Salt Lake City-Murray, UT (WestJet 737-8)

**Verdict: PASS** - margin stays negative even at its best-fit frequency (confidence: medium).
The market was evaluated across 3x, 7x, and 14x weekly; its best-fit schedule
was 3x weekly x 174 seats, and it
did not clear at any service level.

## The two numbers that drive this
1. base margin -102.9% vs hurdle 8.0%
2. modeled share 27% of 26k pax/yr (anchor_x_growth)

## Market
- Distance 720 mi. Best-fit schedule
  3x weekly x 174 seats, chosen to
  maximize annual contribution at a feasible load factor.
- Demand 25,916 pax/yr, method **anchor_x_growth**:
  the market's own 2018 StatCan actual (22,250 pax,
  frozen table 23-10-0256) times T-100 corridor growth 1.16.
- Gravity cross-check: the gravity x transfer path would have said
  44,611 pax/yr, i.e.
  1.72x the anchor-based estimate - printed so a
  divergence from the last observed actual is never invisible. (Transfer
  factor: hub median 1.28, national median
  0.82, IQR [0.55, 2.04].)

## Competition (reconstructed from T-100; no MIDT)
| carrier   | itin_type   |   freq_wk |   elapsed_h |
|:----------|:------------|----------:|------------:|
| OO        | nonstop     |  13.9231  |     1.90598 |
| UA        | onestop     |  15.2692  |     5.01905 |
| OO        | onestop     |   4.76923 |     3.90598 |

Modeled share for the proposed service at the chosen frequency:
27%.

## Economics at the chosen service level (fully-allocated proxy)
| fuel \ fare | -15% | base | +10% |
|---|---|---|---|
| -30% fuel | -115.8% | -83.4% | -66.7% |
| +0% fuel | -138.7% | -102.9% | -84.4% |
| +30% fuel | -161.6% | -122.3% | -102.1% |

Break-even load factor 0.52 vs achieved 0.26.
Fare from distance-matched US markets x 1.10
premium (assumption, sensitivity in grid). Costs from Southwest P-5.2 filings
with fuel rebuilt at EIA scenario prices, carrying the comparator's own
indirect burden (fully-allocated).

## Why this is a PASS, plainly
gravity x transfer demand estimate; no current O&D truth for this market. This conclusion holds at WestJet's actual transborder
service levels: the market was tested at 3x, 7x, and 14x weekly and did not
clear. The broader finding is that WestJet already serves its viable YYC
transborder markets (New York, the California and Nevada leisure markets,
Houston, the Florida and Arizona sun routes); what remains unserved is either
too small (below the 2018 survey's own 4,000-passenger floor) or too
thoroughly held by a US network carrier's connecting hub, and this evaluation
is consistent with WestJet directing its recent transborder growth to Edmonton
and Vancouver rather than adding YYC breadth.
