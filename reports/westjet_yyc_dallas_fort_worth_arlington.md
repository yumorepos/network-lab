# Route evaluation: YYC - Dallas-Fort Worth-Arlington, TX (WestJet 737-8)

**Verdict: PASS** - margin stays negative at every tested frequency (confidence: medium).
The market was evaluated across 3x, 7x, and 14x weekly on the single configured
gauge. No tested option cleared the 50% load-factor floor (best achieved 28%), so the schedule reported below is the fallback the screen emits when nothing is feasible, not a selected schedule. It did not clear at any tested service level.

## The two numbers that drive this
1. base margin -145.8% vs hurdle 8.0%
2. modeled share 22% of 67k pax/yr (anchor_x_growth)

## Market
- Distance 1523 mi. Evaluated schedule
  3x weekly x 174 seats, reported
  from the fixed 3x/7x/14x weekly menu on the study gauge.
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
| AS        | onestop     |  11.3654  |     6.62617 |
| DL        | onestop     |  10.9231  |     6.21609 |
| UA        | onestop     |   9.26923 |     6.77067 |
| UA        | onestop     |   8.96154 |     6.35083 |
| AA        | onestop     |   8.25    |     6.77067 |

Modeled share for the proposed service at the chosen frequency:
22%.

## Economics at the chosen service level (fully-allocated proxy)
| fuel \ fare | -15% | base | +10% |
|---|---|---|---|
| -30% fuel | -158.9% | -120.1% | -100.1% |
| +0% fuel | -189.1% | -145.8% | -123.4% |
| +30% fuel | -219.3% | -171.4% | -146.7% |

Break-even load factor 0.68 vs achieved 0.28.
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
