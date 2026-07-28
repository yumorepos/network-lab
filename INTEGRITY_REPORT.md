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

---

# Round 4: three P0 defects from the independent audit (2026-07-28)

An independent re-audit (`AUDIT_2026-07-27_VERIFIED.md`) found three defects
that had survived every prior round and the full test suite. All three were
real. All three changed the headline result. This round fixes them, adds
regression tests that fail when each defect is reintroduced, and records the
before and after honestly, including the places where the audit's own predicted
magnitudes turned out to be wrong.

The three share one root cause: a modeling assumption that was never checked
against a number the project already had in hand.

## 1. Bidirectional demand divided by one-directional departures

`models/economics.py` computed `deps_yr = freq_wk * 52`. But `demand_pax_yr` is
BIDIRECTIONAL (DB1B O&D and the StatCan anchor both count A to B plus B to A)
while `freq_wk` is ONE-WAY departures from the hub. A route is flown in both
directions, so annual departures are `freq_wk * 52 * 2`. Every route in every
study was scored at roughly twice its true load.

Ground truth, from a market that was in the Alaska candidate set at the time:

| quantity | value |
|---|---|
| DB1B 2024 O&D Seattle to Wichita, both directions | 45,680 |
| Horizon departures SEA to ICT, trailing 12 months | 341 |
| Horizon departures ICT to SEA, trailing 12 months | 338 |
| onboard passengers, both directions | 43,529 |
| observed passengers per departure | 64.1 |

The shipped formula gave 134.6 passengers per departure. The corrected formula
gives 67.3, within 5% of observed.

Checked at network scale rather than on one route. On the 46 Seattle routes
where the Alaska brand flies more than 90% of departures, modeled local O&D per
departure exceeded the total passengers the route actually carried on **25 of 46
routes (54%)** under the old convention, by up to **3.03x**. Local traffic
cannot exceed total onboard traffic, since onboard is local plus connecting
flow, so those rows were not a calibration disagreement but an arithmetic
impossibility. Under the corrected convention that falls to 4 of 46, and the
residual cases are markets where a real share of the O&D routes one-stop on
another carrier rather than on the nonstop. On the long-haul spokes where local
traffic dominates, the corrected numbers land on top of observed:

| route | observed onboard/dep | old formula | corrected |
|---|---|---|---|
| SEA-MSY | 147.4 | 304.5 | 152.2 |
| SEA-CMH | 148.2 | 295.2 | 147.6 |
| SEA-OKC | 144.5 | 279.7 | 139.9 |
| SEA-IND | 152.2 | 291.7 | 145.8 |
| SEA-CLE | 146.6 | 276.1 | 138.0 |

This was findable from day one. The Alaska SEA study exists to be the
ground-truth check, and it was used to validate demand levels and share but
never pointed at the economics arithmetic.

## 2. One-stop competitors joined on operating certificate, not marketing brand

`models/competition.py` joined connecting itineraries with
`l2.carrier = l1.carrier`, the OPERATING carrier. T-100 reports who flew the
metal; a passenger buys a brand. The two disagree for every regional affiliate,
and not marginally: over the current T-100 window SkyWest operates 884,171
departures, Republic 369,160 and Envoy 334,585, while **none of those codes
appears even once as a DB1B ticketing carrier**. Every one of those departures
is sold as American, Delta, United or Alaska.

Two consequences, both now fixed. A mainline leg connecting to a regional leg
was structurally invisible, so competition was understated. And Air Canada, the
incumbent the Porter study is entirely about, was split across three codes at
YYZ: AC mainline (11,970 departures), Jazz as Air Canada Express (11,693) and
Rouge (4,929).

`models/carriers.py` now resolves certificate to brand in two tiers, recorded
per row in `data/reference/carrier_families.csv`:

- **static**, where the operator flies for exactly one brand (wholly owned or a
  single capacity purchase agreement). Corroborated in data rather than trusted:
  the permitted brand sells nonstop on 95.9% to 100% of each single-brand
  operator's DB1B-covered segments.
- **db1b_per_segment**, where the operator flies for several brands (SkyWest,
  Republic, GoJet, Air Wisconsin). The brand is resolved for each segment by
  asking which permitted brand actually sells nonstop tickets on that airport
  pair. 85% to 94% of segments resolve, and the winning brand takes a median
  1.00 of within-set nonstop passengers, so the resolution is close to
  unambiguous where it fires. Unresolved segments keep their operating code,
  which never invents a competitor.

After the fix, 74% to 80% of reconstructed one-stops connect legs flown by
different certificates under one brand. Those itineraries could not previously
be seen at all.

**Where the audit overstated the effect.** The audit predicted this fix would
move Porter's median modeled share from 0.586 to 0.345. It moved to 0.573. The
audit's simulation was wrong in two ways, and the corrected implementation is
the more conservative one. It mapped each regional to every mainline it has ever
flown for, which manufactures phantom competitors on segments SkyWest actually
flies for only one brand; per-segment DB1B resolution does not. And it did not
sum frequencies within a brand, so American mainline and Envoy on the same
segment stayed two competitors rather than becoming one larger one. Under a
concave frequency exponent, splitting a brand in two inflates its total QSI
preference, so the audit's version overstated competition in the opposite
direction. Correct QSI treats a brand as one choice with one frequency.

Measured at the 7x reference frequency:

| study | median share before | after | markets above 0.70 before | after |
|---|---|---|---|---|
| WestJet YYC | 0.800 | 0.712 | 55 | 43 |
| Alaska SEA | 0.613 | 0.429 | 17 | 0 |
| Porter YYZ | 0.586 | 0.573 | 20 | 14 |

Alaska is the study where truth is observable, and it is the one that moves
most: no market now models above a 70% share, against 17 before.

### The same defect lived in a second place

`models/share_validation.py` reimplements the competition reconstruction
independently, with its own operating-carrier one-stop join. The exhibit built
to validate the share model was therefore measuring a different model from the
one that ships verdicts, and it was comparing a certificate-denominated model
against DB1B truth denominated in ticketing carriers. Resolving both sides to
the brand is not a refinement; it is the only way the comparison means anything.

The invariant that makes this undeniable, and that required no prior knowledge
of the answer: **modeled carrier shares summed to 0.790 per market.** A fifth of
Seattle's traffic was credited to codes DB1B never reports as a ticketing
carrier. After the fix they sum to 0.996.

| measure | before | after |
|---|---|---|
| MAE | 6.95 pts | 5.73 pts |
| passenger-weighted MAE | 16.30 pts | 10.85 pts |
| MAE on markets with observed share >= 5% | 15.07 pts | 11.44 pts |
| modeled shares summed per market | 0.790 | 0.996 |

The audit separately noted that the headline MAE of 7.0 was flattered by
composition: 62% of the 503 rows are carriers holding under 5% of a market, and
predicting near zero for those is easy. The passenger-weighted figure and the
share sum are now computed, written into `docs/validation.md`, and pinned by a
test. The passenger-weighted 10.9 is the number a planner should read.

This is the one place where a reader-facing document was updated in this round,
because leaving it would have meant shipping a validation number computed from
code that no longer exists. Only the MAE figure changed, in README,
`docs/validation.md`, `docs/interview_story.md` and `docs/resume_material.md`.
Every other claim in those documents is still stale and listed below.

`docs/LIMITATIONS.md` item 3 stated the direction of this error backwards,
claiming the reconstruction was optimistic about competition. It was
pessimistic. That entry is corrected, and a new item 14 records that Air Canada
connecting itineraries out of Canadian hubs remain invisible because T-100
carries no Canadian domestic segments, so leg one of a YYZ over YUL connection
does not exist in any open source.

## 3. The incumbent cross-check was a dump of the code it was checking

`data/reference/incumbent_network_202604.csv` was described as an independently
auditable record. It was the output of the same T-100 query that
`models/candidates.py` runs to decide which metros are already served: all 99
rows matched on CBSA with a maximum departure delta of 0.0. Both sides shared
one query, one table and one carrier concept, so both shared the
operating-carrier bug above, and `test_no_screened_market_is_already_served`
could not fail. A cross-check that cannot disagree is not a cross-check.

Four Seattle metros that Horizon flies as Alaska leaked into the Alaska
candidate set and were screened as unserved markets:

| metro | operator | departures, trailing 12 months | Alaska nonstop tickets sold, DB1B 2024 |
|---|---|---|---|
| El Paso, TX | QX | 351 | 17,600 |
| Wichita, KS | QX | 341 | 13,400 |
| Salinas, CA (MRY) | QX and OO | 331 | 10,980 |
| Tulsa, OK | QX | 44 | none: launched March 2026 |

`warehouse/incumbent_reference.py` now rebuilds the file from sources
independent of the candidate filter, and every row records which source produced
it and how independent that source actually is:

- **alaska_sea, fully independent.** DB1B nonstop ticket sales. A different
  survey from T-100 (a 10% ticket sample, not the segment census), a different
  grain (origin and destination, not segment) and a different carrier concept
  (who sold the ticket, not who flew the metal). It found 81 served metros
  against the old file's 62, including 19 the operating-carrier view could not
  see, among them El Paso, Wichita and Salinas.
- **westjet_yyc and porter_yyz, partially independent.** DB1B does not cover
  Canadian origins and no open source gives carrier-level Canadian transborder
  service. Those rows read the inbound T-100 record set, which the candidate
  filter never touches, resolved to the marketing brand. That catches query,
  brand and rollup errors; it cannot catch T-100 itself being wrong, and the
  `independent_of_candidate_filter` column says `partial` rather than
  pretending otherwise.

DB1B's blind spot is time: it cannot see Tulsa, launched after the 2024 sample.
The brand-aware T-100 filter catches that one. The two sources have
complementary blind spots, which is the argument for having two.

## Verdicts that moved

| study | before | after |
|---|---|---|
| WestJet YYC | 0 LAUNCH / 0 MONITOR / 76 PASS | 0 LAUNCH / 0 MONITOR / 76 PASS |
| Alaska SEA | 0 LAUNCH / 1 MONITOR / 48 PASS | 0 LAUNCH / 0 MONITOR / 45 PASS |
| Porter YYZ | 5 LAUNCH / 3 MONITOR / 71 PASS | 1 LAUNCH / 1 MONITOR / 77 PASS |

Alaska's candidate count falls 49 to 45 as the four Horizon metros are excluded,
and its lone MONITOR (Fayetteville-Springdale-Rogers, best-fit margin +0.2%
before) goes negative once loads are halved. The validation study now returns a
clean all-PASS, which is the correct answer for a mature hub.

Four of the five Porter LAUNCHes demote to PASS. They were not marginal calls;
they were carrying twice their real load:

| market | verdict | base margin | modeled share | nonstop incumbents |
|---|---|---|---|---|
| Washington | PASS | -27.5% | 0.077 | 4 |
| Chicago | PASS | -11.1% | 0.057 | 5 |
| Philadelphia | PASS | -30.2% | 0.129 | 3 |
| Atlanta | PASS | -22.8% | 0.112 | 2 |
| Boston | LAUNCH | +32.6% | 0.159 | 1 |

Boston survives, and there is an out-of-sample postscript. The model
right-sizes it to 3x weekly at a 0.92 load factor. Porter began flying Toronto
Pearson to Boston on 2026-05-14, after the close of this data window, at 14x
weekly. The model picked the right market and sized it far too small, which is
a real and separate finding: at a modeled 15.9% share the market supports about
4x weekly, so Porter is either expecting a much larger share than the QSI model
gives it or is buying position. Right-sizing scope is a known limitation
(item 11) and this is the first external evidence about its calibration.

WestJet is unchanged at all-PASS, but for better reasons than before: median
modeled share falls from 0.800 to 0.712 and the share-uncertainty guard fires on
19 markets rather than 38, so fewer of the PASS verdicts now rest on a share
estimate the model itself flags as untrustworthy.

## Regression tests

`tests/test_p0_regressions.py`, 19 tests. Suite goes from 13 to 32.

These were verified to fail when the defects are present, not merely to pass
now. Run against the pre-fix artifacts, 13 of the 18 fail, covering all three
defects; the golden units test fails when `DIRECTIONS_PER_ROUTE` is reverted to
1 (134.6 against an expected 64.1); and the circularity guard fails with an
empty set when pointed at the old reference file.

A test that has never been shown to fail is a test of nothing. That is the
lesson of P0-3 and it is why this step was done explicitly.

## Notes and residual issues

- **`top_competitor` ranks by raw frequency and ignores itinerary type.** Air
  Canada is a nonstop competitor in 23 of 79 Porter markets at a median 10.4
  weekly frequencies, but reports as top competitor in only one, because
  high-frequency US hub one-stops outrank it on the raw number. The share model
  itself weights nonstop against connecting correctly, so no verdict is
  affected; the reporting field is misleading and should be ranked on QSI
  preference instead. Not fixed here to keep this round scoped to the P0s.
- **Run-to-run float noise of about 1e-15 relative** exists in the pipeline,
  from parallel float summation in DuckDB. Verdicts, chosen frequencies,
  demand and share are bit-identical across runs; only late-decimal digits of
  margin and contribution move. This predates this round (measured at 6.8e-13
  absolute on margin before the changes, 9.1e-13 after) and is immaterial, but
  it means artifact byte-equality is not a valid reproducibility check.
- **README verdict counts are not covered by the consistency tests.** Those
  tests pin the generated reports, the transfer median, share MAE, backtest N
  and gravity counts, but nothing asserts README's verdict counts against the
  screen. That is why README could carry 5 LAUNCH while the artifacts said
  otherwise. Extending the consistency test to README is the natural next fix,
  and it will then force the rewrite.

## Documents now stale and deliberately not updated

The corrected outputs are verified: `make all` is green, `make test` is 32 for
32, and each fix has a test proven to fail without it. Apart from the single
share-MAE figure discussed above, reader-facing documents were left alone
pending review, and the following now contradict the artifacts:

- `README.md`: the Porter 5 LAUNCH / 3 MONITOR / 71 PASS headline and its named
  LAUNCH list, the Alaska "48 PASS / 1 MONITOR" line, the "204 candidate
  markets" total (now 200), and the claim that BELF 0.85 lives in
  assumptions.yaml.
- `PROGRESS.md`: headline verdict counts.
- `docs/interview_story.md`, `docs/resume_material.md`, `docs/demo_script.md`:
  any verdict counts and the share-model framing.

The generated reports under `reports/` regenerate from artifacts and are already
correct.
