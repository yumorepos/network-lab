# Integrity report: correctness review fixes (2026-07-20)

A review of the built outputs found two factual errors in headline claims and
a systematic modeling bias producing false LAUNCH verdicts. All three were
real. This report records what changed, in which direction, and why. Where a
fix demoted a recommendation, it was demoted.

## 1. Backtest narrative was factually wrong

The claim "this era's route failures were Lynx cost-structure deaths" was
false. Ceased routes by carrier:

| carrier | n | cause | informative about route selection? |
|---|---|---|---|
| F8 (Flair) | 12 | route-level cuts by a carrier that kept operating | yes |
| Y9 (Lynx) | 9 | corporate shutdown 2024-02-26, all routes at once | no |

Most ceased routes were genuine route-level failures (the Flair leisure
cuts: Mesa, Sanford, Burbank, Las Vegas, Denver, Nashville), and they also
scored in the top demand decile. Separation, computed three ways
(operating median 0.89):

| comparison | ceased median | gap |
|---|---|---|
| vs all ceased (n=21) | 0.86 | +0.03 |
| vs ceased excluding Lynx (n=12) | 0.86 | +0.03 |
| vs Lynx-only (n=9) | 0.86 | +0.03 |

Corrected finding: demand ranking does not flag genuine route failures
either; discriminating survival needs economics and competitive-response
layers at launch vintage. The headline N is now **48** (launched with known
terminal status); never-launched (2) and unknown-status (11) rows are
separate labeled groups, not folded into a launch count. Fixed in
backtest.md, README.md, interview_story.md, resume_material.md.

## 2. Transfer factor was overriding market-specific evidence

Demand used gravity x hub-median transfer even where the market had its own
2018 StatCan anchor, over-predicting small anchored markets (Sacramento:
12,450 anchor vs 66k modeled) and under-predicting huge ones (Toronto-New
York: 1.59M anchor vs 0.57M modeled). Now: anchor x T-100 corridor growth
wherever an anchor exists; gravity x transfer only for unanchored pairs; no
shrinkage (every anchor clears the survey's own >4,000 floor). Anchor
matching parses city tokens AND state, fixing three matching bugs found on
the way ("Columbia, SC" had matched District of Columbia; Portland ME had
matched Portland OR; compound names like "Dallas-Fort Worth, Texas" had
matched nothing). Every screen row and business case now carries
implied_vs_anchor_ratio so a divergence from the last observed actual is
visible on the page.

### Verdict changes (old -> new)

WestJet YYC (5 changes, all demotions):

| market | old | new | why |
|---|---|---|---|
| Sacramento | LAUNCH | PASS | anchor 12,450 pax vs 66k gravity; also share-uncertainty flag |
| Philadelphia | LAUNCH | PASS | anchor 18,180 vs 112k gravity |
| Dallas-Fort Worth | MONITOR | PASS | anchor 57,711 vs 141k gravity |
| St. Louis | MONITOR | PASS | anchor 10,730 vs 71k gravity |
| Kansas City | MONITOR | PASS | anchor 9,550 vs 50k gravity |

WestJet YYC final: **0 LAUNCH / 0 MONITOR / 77 PASS**. The unserved YYC
transborder map is thin because WestJet already serves everything large
(New York, Houston, SFO, Las Vegas, Phoenix...); this agrees with WestJet
pointing its recent transborder growth at Edmonton and Vancouver.

Porter YYZ (18 changes, both directions - the fix moves estimates toward
market evidence, not uniformly down):

- Demoted to PASS on anchor evidence: Hartford, Milwaukee, Grand Rapids,
  Indianapolis, Richmond, Louisville, Cincinnati, Philadelphia, St. Louis,
  Kansas City, Columbus, Dayton, Portland ME.
- Capped LAUNCH -> MONITOR by the share guard: Albany (91% share, zero
  nonstop incumbents).
- Promoted on anchor evidence (gravity had under-predicted): New York
  PASS -> LAUNCH (anchor-based 1.48M pax market, modeled share 4%),
  Washington PASS -> MONITOR, Atlanta PASS -> MONITOR, Chicago
  PASS -> MONITOR.

Porter YYZ final: **2 LAUNCH (New York, Boston) / 4 MONITOR / 74 PASS**.

## 3. Share guard and wider circuity

Any market with modeled share above 70% and zero nonstop incumbents is now
flagged "incomplete competition likely", capped at MONITOR, and printed in
the business case. The one-stop corridor widened from 1.30x nonstop to
min(nonstop + 700 mi, 2.0x): hub connects run far off great-circle
(YYC-Denver-Sacramento is 1.77x). Share MAE moved 6.7 -> 7.0 points with
the wider net; reported, not hidden.

## 4. Alaska reframe

The all-PASS screen is a fixed-gauge artifact (daily 178-seat mainline into
thin markets loses money by construction), not proof of hub saturation. The
validation report now leads with the share MAE as the ground-truth check and
says exactly that; saturation language softened in README and reports.

## 5. Headline numbers that moved

| number | before | after | why |
|---|---|---|---|
| backtest N | "61 launches" | 48 launched-and-resolved (+2 never-launched, +11 unknown, labeled) | precise counting |
| backtest medians | 0.90 vs 0.86 | 0.89 vs 0.86 (all three cuts reported) | deterministic refit + three-way computation |
| transfer median | 0.83 (and 0.86 in one doc) | 0.82, IQR [0.55, 2.04], identical everywhere | order-stable fits + consistency test |
| share MAE | 6.7 pts | 7.0 pts | wider circuity net |
| WS YYC screen | 2 LAUNCH / 3 MONITOR | 0 LAUNCH / 0 MONITOR / 77 PASS | anchor-first demand |
| PD YYZ screen | 10 LAUNCH / 5 MONITOR | 2 LAUNCH / 4 MONITOR | anchor-first demand + share guard |
| gravity counts | sometimes unlabeled | 6,002 (2018-19) / 6,092 (2023-24), always labeled by vintage | consistency pass |

A reproducibility bug surfaced during the consistency pass: the gravity
market frame had no stable row order, so the holdout split (and every
downstream headline number) drifted between reruns. Fixed with a stable
ORDER BY; two consecutive full-chain runs now produce identical numbers,
and tests/test_consistency.py fails if any reader-facing doc drifts from
the computed artifacts.

---

# Round 3: right-size service, then package (2026-07-20)

The prior rounds evaluated every candidate at a single hardcoded schedule (7x
weekly, mainline gauge). That forced daily mainline capacity onto markets far
too thin for it and produced meaningless verdicts (YYC-Sacramento: 22% load
factor, -161% margin). The fix and its consequences:

## 1. Frequency (and gauge) right-sizing

Economics now evaluates each candidate across the study's
`target_frequency_weekly` list (3x, 7x, 14x) and gauge list, and the screen
selects the option that **maximizes total annual contribution** subject to a
load-factor floor (`min_feasible_load_factor` = 0.50), then applies
LAUNCH/MONITOR/PASS to that best schedule. "Total annual contribution" (dollars),
not margin percentage, is the objective on purpose: maximizing margin percentage
would trivially pick the lowest frequency every time (fuller planes), whereas a
planner sizes the schedule to the demand a market can fill. The chosen frequency
is a column on every screen row and business case. Each study operates a single
transborder/domestic mainline gauge, so frequency is the active axis; the gauge
search runs for any study that lists more than one, and no regional-gauge option
was invented for WestJet (it flies 737s transborder).

Right-sizing's effect on Porter's non-PASS markets (margin at the chosen
frequency vs at the old hardcoded 7x):

| market | verdict | chosen | margin @ chosen | margin @ 7x |
|---|---|---|---|---|
| Philadelphia | LAUNCH | 3x | +23.2% | -13.2% |
| Washington | LAUNCH | 3x | +32.0% | +7.1% |
| Chicago | LAUNCH | 3x | +31.3% | +13.1% |
| Atlanta | LAUNCH | 3x | +20.0% | +3.1% |
| Boston | LAUNCH | 14x | +24.9% | +34.7% |
| Hartford | MONITOR | 3x | +37.5% | -4.5% |
| Milwaukee | MONITOR | 3x | +33.2% | -23.2% |
| Cincinnati | MONITOR | 3x | +6.0% | -56.1% |

Philadelphia lost money at a forced 7x and is viable at 3x - the exact
"evaluated at the wrong service level" case. Boston is the reverse tell: it
picks 14x at a *lower* margin percentage than 7x, because filling more total
seats yields higher total contribution - confirming the objective is
contribution, not margin percentage. Hartford/Milwaukee/Cincinnati clear on
margin at 3x but are held at MONITOR by the existing share-uncertainty guard or
the hurdle.

## 2. Candidate-filter leak fixed (metro-level)

Markets the study carrier already serves nonstop were leaking in because the
filter matched on the metro's busiest airport: WestJet flies YYC-IAD at ~1x
weekly, but the Washington metro's busiest airport is BWI, so an airport match
missed it. The exclusion is now metro-level (any airport in the metro, trailing
12 months, >= `served_market_min_deps_yr` = 26 departures ~ weekly). Dropped as
already-served: 23 WS, 48 AS, 11 PD metros. This also correctly removes New York
from Porter's candidate set (Porter flies YYZ-Newark), so NYC is no longer a
Porter LAUNCH - it is an existing route, not a new-market opportunity.

## 3. Negative-space demand cap (entailed by right-sizing)

Right-sizing thin markets to 3x weekly initially manufactured false LAUNCHes on
unanchored gravity markets (Boise, Spokane, Fresno at 18-34k modeled pax). But a
market ABSENT from the 2018 StatCan >4,000 city-pair table had at most ~4,000
transborder O&D that year by construction, and the US-calibrated gravity model
over-predicts these by 5-8x. Unanchored transborder demand is now capped at
4,000 x corridor growth (~4,660 for YYC) - a generous upper bound. With the cap,
every unanchored thin market screens PASS at every frequency, which is the honest
result.

## Verdicts that moved

WestJet YYC: **0 LAUNCH / 0 MONITOR / 77 PASS -> 0 LAUNCH / 0 MONITOR / 76 PASS**
(candidate count 77->76 from the leak fix). Right-sizing did NOT create any
WestJet LAUNCH: the unserved YYC markets are either capped-tiny (unanchored) or
uncompetitive (Dallas at 23% share against American's hub, PASS at every
frequency). WestJet's all-PASS is now robust across service levels, and the
WestJet documents are retitled "Route evaluation" with the verdict in the first
line.

Porter YYZ: **2 LAUNCH / 4 MONITOR / 74 PASS -> 5 LAUNCH / 3 MONITOR / 71 PASS**.
New York exits the candidate set (already served). Boston stays LAUNCH. Right-
sizing promotes Washington, Chicago, Philadelphia, and Atlanta to LAUNCH - all
large anchor-backed markets that lost money only because they were being
evaluated at a frequency too high for their share.

Alaska SEA: **all PASS -> all PASS**, now after right-sizing (lowering frequency
did not rescue thin mainline markets), so the earlier "fixed-gauge artifact"
caveat is partly resolved into a genuine gauge limitation.

## Headline numbers that changed

| number | before | after | why |
|---|---|---|---|
| Porter screen | 2 LAUNCH / 4 MONITOR | 5 LAUNCH / 3 MONITOR | right-sizing + NYC exclusion |
| WS candidates | 77 | 76 | metro-level leak fix |
| candidates screened (total) | 206 | 204 | leak fix (metro-level exclusion) |
| new columns | - | chosen_freq_wk, chosen_seats, chosen_gauge, annual_contribution, survey_ceiling_pax | right-sizing + demand cap |

Validation numbers are stable except one that shifted for a real reason: the
transfer-factor median moved from 0.82 to **0.80** (IQR [0.55, 2.02]) because
the metro anchor-point selection changed slightly during the right-sizing work
(the busiest-airport pick for one metro flipped a single anchor pair across the
median). The pipeline is deterministic - three consecutive runs give 0.8019
exactly - and the consistency test caught the docs still pinned to the old
0.82 and now enforces the new value across README, PROGRESS.md,
interview_story, and validation.md, with an explicit guard against the stale
0.82/0.83/0.86 reappearing. Share MAE 7.0, backtest N=48, and gravity
6,002 / 6,092 are unchanged. Two route post-mortems were added (YYC-LAS: Flair
route cut vs Lynx corporate shutdown, same market), and deploy/demo docs
complete the package.
