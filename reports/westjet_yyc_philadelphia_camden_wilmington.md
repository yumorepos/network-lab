# Route evaluation: YYC - Philadelphia-Camden-Wilmington, PA-NJ-DE-MD (WestJet 737-8)

**Verdict: PASS** - margin stays negative at every tested frequency (confidence: medium).
The market was evaluated across 3x, 7x, and 14x weekly on the single configured
gauge. No tested option cleared the 50% load-factor floor (best achieved 20%), so the schedule reported below is the fallback the screen emits when nothing is feasible, not a selected schedule. It did not clear at any tested service level.

## The two numbers that drive this
1. base margin -266.7% vs hurdle 8.0%
2. modeled share 52% of 21k pax/yr (anchor_x_growth)

## Market
- Distance 2003 mi. Evaluated schedule
  3x weekly x 174 seats, reported
  from the fixed 3x/7x/14x weekly menu on the study gauge.
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
| AA        | onestop     |   8.25    |     6.52853 |

Modeled share for the proposed service at the chosen frequency:
52%.

## Economics at the chosen service level (fully-allocated proxy)
| fuel \ fare | -15% | base | +10% |
|---|---|---|---|
| -30% fuel | -285.3% | -227.5% | -197.7% |
| +0% fuel | -331.4% | -266.7% | -233.4% |
| +30% fuel | -377.5% | -305.9% | -269.0% |

Break-even load factor 0.75 vs achieved 0.20.
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
