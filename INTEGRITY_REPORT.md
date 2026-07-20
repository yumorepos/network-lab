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
