# Route evaluation: YYC - Dallas-Fort Worth-Arlington, TX (WestJet 737-8)

**Verdict: PASS** - margin stays negative even at its best-fit frequency (confidence: medium).
The market was evaluated across 3x, 7x, and 14x weekly; its best-fit schedule
was 3x weekly x 174 seats, and it
did not clear at any service level.

## The two numbers that drive this
1. base margin -16.7% vs hurdle 8.0%
2. modeled share 24% of 67k pax/yr (anchor_x_growth)

## Market
- Distance 1523 mi. Best-fit schedule
  3x weekly x 174 seats, chosen to
  maximize annual contribution at a feasible load factor.
- Demand 67,219 pax/yr, method **anchor_x_growth**:
  the market's own 2018 StatCan actual (57,711 pax,
  frozen table 23-10-0256) times T-100 corridor growth 1.16.
- Gravity cross-check: the gravity x transfer path would have said
  141,351 pax/yr, i.e.
  2.10x the anchor-based estimate - printed so a
  divergence from the last observed actual is never invisible. (Transfer
  factor: hub median 1.28, national median
  0.80, IQR [0.55, 2.02].)

## Competition (reconstructed from T-100; no MIDT)
| carrier   | itin_type   |   freq_wk |   elapsed_h |
|:----------|:------------|----------:|------------:|
| AA        | nonstop     |  13.1154  |     3.47405 |
| UA        | onestop     |  15.2692  |     5.50724 |
| DL        | onestop     |  10.9231  |     6.21609 |
| UA        | onestop     |   9.26923 |     6.77067 |
| UA        | onestop     |   6.69231 |     6.34888 |
| AA        | onestop     |   5.09615 |     6.77067 |

Modeled share for the proposed service at the chosen frequency:
24%.

## Economics at the chosen service level (fully-allocated proxy)
| fuel \ fare | -15% | base | +10% |
|---|---|---|---|
| -30% fuel | -23.0% | -4.5% | 5.0% |
| +0% fuel | -37.3% | -16.7% | -6.1% |
| +30% fuel | -51.7% | -28.9% | -17.2% |

Break-even load factor 0.68 vs achieved 0.58.
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
