# Network Lab: verified audit

Date: 2026-07-27. Supersedes `AUDIT_2026-07-27.md`, which was written as a
first-pass hypothesis and is wrong in two places (marked below). Every finding
here was reproduced against the code, the warehouse, and the three prior Claude
Code session transcripts. Where a claim could not be verified it is labelled as
unverified rather than asserted.

No repository code was changed to produce this document. All counterfactuals
were run out of tree in `/tmp` against the committed artifacts.

---

## 1. Verdict

The engineering is real and the data work is genuinely good. The analytical
core has two independent defects that both push the same way, and together they
erase the project's headline result. A third defect means the test that is
advertised as the safety net for the candidate filter cannot fail.

Corrected, all three studies say launch nothing:

| study | as published | directionality fixed | one-stop rule fixed | both fixed |
|---|---|---|---|---|
| Porter YYZ | 5 LAUNCH / 3 MONITOR / 71 PASS | 1 / 1 / 77 | 5 / 2 / 72 | **0 / 1 / 78** |
| WestJet YYC | 0 / 0 / 76 | 0 / 0 / 76 | 0 / 0 / 76 | 0 / 0 / 76 |
| Alaska SEA | 0 / 1 / 48 | 0 / 0 / 49 | 0 / 0 / 49 | 0 / 0 / 49 |

The README's central framing ("the model says yes, no, and watch it") does not
survive. That is recoverable, and the recovery is more interesting than the
original claim, but it has to happen before this repo is shown to anyone else.

Hiring read at the bottom (section 9).

---

## 2. How this was verified

- Read every module in `models/`, `warehouse/`, `backtest/`, plus the configs,
  tests, generated reports and docs.
- Queried the live DuckDB warehouse directly for T-100 and DB1B ground truth.
- Re-ran the full share, economics and screen chain out of tree under four
  variants (as shipped, each fix alone, both fixes) for all three studies.
- Grepped the three prior session transcripts
  (`e7ac5739`, `dd222588`, `4be0a99e`) for whether any of these issues were
  raised and dismissed. They were not: `deps_yr` appears 51 times across the
  build sessions and was never questioned; "operating carrier" and "marketing
  carrier" appear zero times.

---

## 3. What the first-pass audit got right, wrong, and missed

**Confirmed.** The directionality defect; the reproducibility of `make all`
(verdicts identical, max margin drift 0.0); the linear fare curve being
empirically justified (R2 0.496 beats a log-log taper at 0.385); no committed
junk; the no-dash rule actually followed; 13 tests pass in 4 seconds; the
unanchored cap binding on 52 of 76 WestJet markets; `sensitivity:` keys never
executed; the backtest threshold drift; `spill.py:6` naming a test file that
does not exist; `PROGRESS.md:65` saying "6 tests green".

**Retracted.**

1. *"Empty `archive/` directory should be cleaned up."* Wrong. `archive/` is in
   `.gitignore` and is not in the public repo. Non-issue.
2. *"Lead with the share validation MAE of 7.0 as a credential."* Wrong, and
   the opposite of correct. See 5.4.
3. *"CI may be skipping the consistency tests."* Wrong. The 24 output artifacts
   are force-added to git, so the tests do run in CI. The real weakness is
   different and narrower: CI validates docs against **committed** artifacts and
   never regenerates them, so a code change that alters results passes CI as
   long as the stale parquet is not refreshed.

**Missed entirely by the first pass.** The same-carrier one-stop restriction
(P0-2), the circular incumbent-network cross-check (P0-3), the competition
reconstruction failing against observable DB1B truth (P1-1), the transfer
factor discarding a strong leisure/business signal (P1-3), and the fact that
the gravity model contributes nothing to either transborder study (P1-2).

---

## 4. P0 defects

### P0-1. Bidirectional demand divided by one-directional departures

`models/economics.py:182`

```python
deps_yr = freq_wk * 52
pax_per_dep = spill.expected_boardings(carried / deps_yr, seats)
```

All three demand paths produce annual passengers in **both directions**:

- StatCan anchor filters on `Estimates = 'Number of outbound and inbound
  passengers'` (`models/demand.py:86`).
- DB1B sums `origin_cm = hub OR dest_cm = hub` (`models/demand.py:34`).
- Gravity is fit on markets grouped by `least/greatest` city market
  (`models/gravity.py`), so its target variable is bidirectional too.

`freq_wk` is unambiguously **one-way departures from the hub per week**. Three
independent confirmations: the QSI model compares it directly against T-100
`sum(departures)/52` for a single directed segment
(`models/competition.py:55`); `data/reference/launches_NOTES.md` defines
`initial_weekly_freq` as "one-way departures per week at launch"; and T-100
shows Alaska operating 62.96 one-way departures per week SEA to LAX. So an
aircraft flying `freq_wk` departures out of the hub also flies `freq_wk` back,
carrying the return half of the demand. The divisor is short by a factor of two.

**Ground truth that settles it.** SEA to Wichita, a market currently in the
Alaska candidate set:

| quantity | value | source |
|---|---|---|
| DB1B 2024 O&D, both directions | 45,680 | `fact_od_market` |
| Horizon departures SEA to ICT, trailing 12mo | 341 | `fact_segment` |
| Horizon departures ICT to SEA, trailing 12mo | 338 | `fact_segment` |
| onboard passengers, both directions | 43,529 | `fact_segment` |
| observed load factor | 0.833 / 0.854 | `fact_segment` |

Shipped formula at 7x weekly: 45,680 / 364 = **125.5 passengers per departure**.
Corrected formula: 45,680 / 728 = **62.7**, against an observed 64.1 onboard per
departure. The corrected arithmetic reproduces reality to within 2 percent. The
shipped arithmetic predicts double.

**Fix.** `deps_yr = freq_wk * 52 * 2`, with a comment stating the units
contract, and a unit test that pins SEA to ICT against the T-100 actual.

**Mitigating context, stated fairly.** The author reasons correctly about
direction elsewhere. `warehouse/reconcile.py:9-16` derives that a transborder
passenger touches exactly one Canadian airport per one-way journey while a
domestic passenger touches two, and uses that to set the expected ratio. This
is a localized units slip in one line, not a conceptual gap.

### P0-2. The one-stop reconstruction requires the same operating carrier

`models/competition.py:90`

```sql
JOIN seg12 l2 ON l2.carrier = l1.carrier AND l2.origin = l1.dest
```

T-100 reports the **operating** carrier. American's Toronto to Chicago flight
is `AA`; the Chicago to Dayton continuation is `MQ` (Envoy) or `OH` (PSA). To a
passenger that is one American itinerary. To this query it is nothing at all.

Measured, by rebuilding the one-stop set under a marketing-family rule
(AA/MQ/OH/PT/YX/OO/ZW, DL/9E/OO/YX/G7/EV, UA/OO/YX/ZW/C5/G7, AS/QX/OO) and
recomputing `comp_pref_sum` and `share_at_freq` at the reference frequency:

| study | one-stop paths, strict | family | median modeled share, strict -> family | mean abs. share error | markets above 0.70 share |
|---|---|---|---|---|---|
| Porter YYZ | 555 | 1,801 | 0.586 -> 0.345 | 19.7 pts | 20 -> 2 |
| WestJet YYC | 215 | 683 | 0.799 -> 0.546 | 22.2 pts | 55 -> 15 |
| Alaska SEA | 269 | 979 | 0.613 -> 0.268 | 31.6 pts | 17 -> 0 |

**`docs/LIMITATIONS.md` item 3 states the direction of this error backwards.**
It says the reconstruction "overstates connectivity where banks don't align and
misses interline/codeshare paths", and the earlier draft (found in the session
transcript) said explicitly: "Direction of error: usually optimistic about
competition, i.e. conservative about the proposed service's share." The
measurement says the opposite: the net effect is to overstate the proposed
service's share by 20 to 32 points. The stated sign is what justified leaving
it unfixed, so the disclosure is doing active harm.

Two effects run in opposite directions and the doc only reasoned about one.
Splitting one marketing carrier across five operating certificates does inflate
`comp_pref_sum` (with a concave frequency exponent, `10^0.6 + 20^0.6` exceeds
`30^0.6`). But dropping every mixed-metal itinerary deflates it far more. Only
one of these was considered.

**Caveat on my own number.** `OO`, `YX`, `ZW` and `G7` fly for several
mainlines, so a family rule that admits any shared parent is an upper bound on
connectivity. The truthful statement is: the strict rule is definitely wrong,
the family rule is probably slightly too permissive, and **the project as built
cannot tell you where between them the answer lies.** That is the finding.

**Fix.** Add `dim_carrier_family` to the warehouse (source: DOT operating
certificate to marketing brand), join one-stops on family, and collapse
`top_competitor` and `n_nonstop_incumbents` to the marketing brand. Ship the
strict and family variants side by side as a bound if a single answer cannot be
defended.

### P0-3. The incumbent-network cross-check is generated by the code it checks

`data/reference/incumbent_network_202604.csv` is presented as an independent,
hand-compiled control. `docs/LIMITATIONS.md:77` calls it "spot-verified against
published schedules". `tests/test_sanity.py:39` is built on it.

It is bit-identical to the output of the exact query in
`models/candidates.py:33-51`. All 99 rows match on CBSA, and every
`deps_trailing_12mo` value matches to 0.0. Its own `source` column reads "BTS
T-100 International trailing 12mo to 202604; PD spot-checked vs Porter newsroom"
on all 99 rows, including the 62 Alaska rows that have nothing to do with Porter.

So `test_no_screened_market_is_already_served` cannot fail. It compares the
screen against a dump of the filter that produced the screen.

**Proof that this is not academic.** The candidate filter matches on operating
carrier (`served["carrier"] == carrier`, `models/candidates.py:48`), so
Alaska service operated by Horizon is invisible to it. Four metros Alaska
demonstrably serves nonstop from Seattle are in the Alaska candidate set:

| metro | operator | departures, trailing 12mo | Alaska share of the O&D market, DB1B 2024 |
|---|---|---|---|
| El Paso, TX | QX | 351 | 0.529 |
| Wichita, KS | QX | 341 | 0.595 |
| Salinas, CA (MRY) | QX + OO | 331 | 0.908 |
| Tulsa, OK | QX | 44 (launched March 2026) | 0.071 |

El Paso, Wichita and Monterey are daily year-round Horizon routes. All four
screened as PASS, so no false LAUNCH resulted, but the validation study's
candidate universe is 4 of 49 contaminated and the advertised safety net did not
notice.

Worse, the study that is supposed to be the ground-truth check now contains its
own natural experiment and the model fails it. On SEA to Wichita, Alaska
observably holds 59.5 percent of the market with a daily nonstop; the QSI model
predicts a new Alaska daily nonstop would take 38.9 percent. On SEA to Monterey,
Alaska holds 90.8 percent; the model predicts 43.0 percent.

**Fix.** Build the incumbent file from an independent source (published route
maps, or Cirium/OAG schedules if available), not from `fact_segment`. Then make
the candidate exclusion carrier-family aware. Both changes are prerequisites for
the test to mean anything.

---

## 5. P1: analytically material

### 5.1. The competition reconstruction fails against observable truth

The Alaska SEA study exists precisely because demand, share and fare are all
observable there. That check was never run on the competition layer. Running it:

For each of the 49 Alaska candidate markets, take every DB1B ticketing carrier
holding at least 10 percent of observed 2024 passengers and ask whether the
reconstruction gave that carrier any itinerary at all.

- **30 of 49 markets** have at least one such carrier entirely absent.
- On average **30.4 share points** of observed traffic is held by carriers the
  model treats as not present.
- Lafayette LA: the reconstruction found **zero** competitors; DB1B shows AA, UA
  and DL each above 10 percent.

Across studies, markets where the reconstruction returns nothing and the
proposed service is therefore handed 100 percent share: Alaska 3, WestJet 12,
Porter 0. The README states that "a proposed nonstop is never scored against an
empty market". For 15 markets that is literally false.

The `>0.70 share and 0 nonstop incumbents` guard fires on **55 of 76** WestJet
markets (72 percent), 20 of 79 Porter, 17 of 49 Alaska. A guard that fires on
nearly three quarters of a study is not an exception handler, it is the modal
code path, and it is telling you the share model is not usable as built.

Separately, for a Canadian hub the reconstruction can never see Air Canada as a
connecting competitor: AC's Calgary to Toronto leg is Canadian domestic and
T-100 has no Canadian domestic segments (CLAUDE.md rule 5). `competition_westjet_yyc.parquet`
contains zero AC and zero WS one-stops. For a transborder study out of Calgary
that is the single most important competitor missing. This deserves an explicit
LIMITATIONS entry; it currently has none.

### 5.2. The gravity model does not run in either transborder study

`demand_method` counts:

| study | anchor_x_growth | unanchored_capped_at_ceiling | gravity_x_transfer |
|---|---|---|---|
| WestJet YYC | 24 | 52 | **0** |
| Porter YYZ | 58 | 21 | **0** |

The gravity path either loses to a StatCan anchor or is clipped to the survey
ceiling. It never survives to produce a number.

And the cap is a constant. All 52 capped WestJet markets carry
`demand_pax_yr = 4659.0` exactly, for metros ranging from 412,339 to 1,760,548
people, against gravity estimates spanning 4,698 to 36,132. A 7.7x range is
compressed to a single point, and the screen then emits 52 separate PASS
verdicts with per-market drivers as though each had been analyzed.

The cap itself is defensible and well argued (LIMITATIONS item 13). What is not
defensible is the presentation: the README bills a gravity model "calibrated on
6,002 US city-market pairs" as a core method, and in the flagship study its
contribution is zero. The model's own diagnostic says why:
`implied_vs_anchor_ratio` has a **median of 5.07** across the 24 anchored
WestJet markets, range 1.37 to 8.41. The gravity plus transfer path overshoots
the market's own observed 2018 actual by five times on the median market, and
that number is printed on every screen row.

**Fix.** Either recalibrate so the gravity path is usable transborder, or say
plainly in the README that transborder demand is anchor-driven and the gravity
model's live role is the US thin-market fallback and the backtest ranking. The
second is honest and costs nothing. The current framing oversells.

### 5.3. The transfer factor throws away a strong, learnable signal

The 11 YYC anchor pairs, sorted:

| pair | transfer | | pair | transfer |
|---|---|---|---|---|
| Boston | 0.44 | | Los Angeles | 1.60 |
| Dallas Fort Worth | 0.63 | | Houston | 2.43 |
| Chicago | 0.73 | | Orlando | 3.26 |
| New York | 0.77 | | Phoenix | 3.68 |
| San Diego | 1.08 | | Las Vegas | 8.78 |
| Denver | 1.28 | | | |

That is not dispersion, it is a leisure/VFR axis. The US-calibrated gravity
model systematically under-predicts Canadian sun and casino demand and
over-predicts business demand, by up to 20x end to end. Collapsing it to a
single hub median of 1.28 guarantees being wrong by three to eight times on
exactly the markets a Canadian carrier cares most about.

This is the most valuable unclaimed finding in the repo. A one-line regression
of `ln(transfer)` on a leisure indicator or on destination warm-weather/tourism
covariates would turn the project's biggest reported uncertainty into a modeled
effect, and would be a genuinely impressive thing to show an interviewer.

Two smaller points on the same object:

- The reported robustness statistic is for the wrong number.
  `leave_one_out_median_range: [0.799, 0.824]` is computed on the **national**
  median, but every study applies a **per-hub** median. Recomputed properly,
  YYC's leave-one-out range is [1.178, 1.439], four times wider. `PROGRESS.md:36`
  lists the per-hub medians and then says "leave-one-out stable", which
  attributes the national statistic to the per-hub numbers.
- `tests/test_consistency.py::test_transfer_median_consistent` pins the docs to
  `median 0.80`, the national figure that no study uses. The consistency suite is
  guarding the wrong value.

### 5.4. The share validation headline is flattered by sample composition

`share_validation.parquet`, 503 rows, headline MAE 7.0 share points, quoted in
the README, `docs/validation.md`, `docs/resume_material.md`,
`docs/interview_story.md` and `reports/alaska_sea_validation.md`.

- Observed share is below 5 percent on **310 of 503 rows** (62 percent). Their
  mean error is 1.9 points; 176 of them are predicted at exactly 0.000.
- MAE restricted to observed share at or above 5 percent: **15.1** (n=193).
  Above 10 percent: **18.0**. Above 20 percent: **21.6**.
- **Passenger-weighted MAE: 23.6 points.**
- `model_share` sums to 0.790 per market on average (std 0.293, min 0.000) while
  `obs_share` sums to 1.000 by construction. The carrier sets do not match, which
  is P0-2 and the operating-versus-marketing carrier problem showing through.
- Worst rows are all Alaska at its own hub: observed 0.950 against model 0.000;
  observed 0.997 against model 0.409.

The `by market structure` table in `docs/validation.md` reports its lowest MAE
(3.4) on the "0 nonstop" bucket, which is the bucket where predicting near zero
is nearly free. That table reads as a robustness check and is actually a
composition artifact.

MAE 7.0 is not a defensible credential. Passenger-weighted MAE, or MAE on
carriers above a materiality floor, is the number to publish, and it currently
looks bad. That is fine. It looks bad for reasons that P0-2 explains, and
publishing the honest number alongside the diagnosis is a stronger story than
the flattering one.

### 5.5. The uncertainty story is inverted

The 3 fare x 3 fuel grid varies fare by plus or minus 15 percent and fuel by
plus or minus 30 percent. The gravity model's own holdout median absolute
percentage error is **0.62** (0.80 in the 500,000-plus passenger band), and the
transfer factor's IQR spans [0.55, 2.02]. The scenario grid stress-tests the two
best-known inputs and holds the worst-known one fixed.

`config/assumptions.yaml` contains **19 `sensitivity:` blocks. Zero are read by
any code.** `models/economics.py:19` asserts that a possible cost double-count
"is inside the fee's +/-30% sensitivity band"; that band is never computed.

`stimulation_elasticity: -0.8` is defined with a source, a rationale and a
sensitivity range, and is **never referenced anywhere in the codebase**. Entry
stimulation by a low-cost carrier is a first-order effect for both Porter and
WestJet. Declaring the constant and not using it is worse than omitting it,
because the YAML implies it is modeled.

**Fix.** Make one assumption's sensitivity actually propagate end to end
(transfer factor is the highest-value choice) and report the verdict-flip count.
Delete `stimulation_elasticity` or implement it.

---

## 6. P2: correctness-adjacent and rule violations

### 6.1. CLAUDE.md rule 1 is violated in at least 14 places

"Never invent a numeric constant. Every non-derived value lives in
`config/assumptions.yaml` with source, confidence, and sensitivity."

| location | constant | why it matters |
|---|---|---|
| `models/screen.py:19` | `BELF_MAX = 0.85` | verdict-determining, and the README table presents it as an assumptions.yaml threshold |
| `models/transfer.py:65` | `MIN_ANCHOR_PAX = 40_000` | defines the 87-pair sample behind the headline median and IQR |
| `models/transfer.py:172` | `len(g) >= 3` | decides per-hub versus national median; YYC gets 1.28 instead of 0.80, a 59 percent demand difference for the flagship study |
| `models/demand.py:141` | `SURVEY_THRESHOLD = 4000.0` | sets the demand of 52 of 76 WestJet markets |
| `models/economics.py:33` | `E2_FUEL_IMPROVEMENT = 0.12` | drives the entire Porter cost base off "Embraer public claims" with no YAML entry |
| `models/competition.py:26,27` | `DETOUR_MAX = 2.0`, `DETOUR_ABS_MI = 700` | defines the competitive set |
| `models/competition.py:62,100` | `>= 26`, `>= 3` | 26 silently duplicates `served_market_min_deps_yr`; the `>= 3` leg filter is undocumented |
| `models/economics.py:111` | `> 4000` | fare-curve sample floor |
| `models/share_validation.py:19,17,18` | `MIN_PAX = 50_000`, `HUB`, `YEAR` | defines the headline MAE sample |
| `backtest/run_backtest.py:66,67` | `250_000`, `(250, 3000)` | the backtest's candidate universe differs from the live screen's 400k floor, so percentiles are computed against a different denominator than the screen uses |

`BELF_MAX` is the one to fix first: the README explicitly promises every
threshold in the table lives in the YAML with a source and a sensitivity range,
and this one does not.

### 6.2. The hub's income is never used

`models/demand.py:80-81` and `backtest/run_backtest.py:69-70` both set
`inc_a = inc_b = destination metro income`. The gravity model was fit on
`ln(income_a * income_b)` with a coefficient of 1.026, so substituting the
destination income for both terms **doubles the destination-income elasticity**
rather than combining a hub constant with a destination variable.

The docstring at `models/demand.py:9-11` discloses the substitution and argues
the level error cancels through the transfer ratio. That argument is correct for
the level and `models/transfer.py:134` uses the same convention, so the
convention is at least consistent. But a scalar factor cannot correct a slope.
The cross-sectional distortion across destinations is roughly
`(income_dest / income_hub)^1.026`, which is a plus or minus 35 percent swing
correlated with destination income, and it is part of why the transfer IQR is
so wide.

Mitigating: `dim_metro_ca` carries population only. There is **no Canadian
income variable in the warehouse**, so this is a genuine data constraint, not
laziness. The criticism is narrow and fair: the level-cancellation argument is
disclosed, the slope distortion is not.

### 6.3. Smaller confirmed items

- `backtest/run_backtest.py:72-74`: the per-hub transfer factor is applied and
  then a percentile rank is taken. A scalar cancels out of a rank, so the line is
  inert. Harmless, but it reads as if the transfer factor affects the backtest.
- CI (`.github/workflows/ci.yml`) runs only `pytest tests/ -q`. It never
  executes `models.run_all`, so nothing checks that the pipeline still runs, and
  the consistency tests validate docs against **committed** artifacts rather than
  freshly computed ones.
- `make all` rewrites 14 tracked Parquet files with float64 last-bit noise, so a
  reviewer who clones and runs the documented commands gets a dirty tree.
- `models/spill.py:6` cites `tests/test_spill.py`, which does not exist.
- `PROGRESS.md:65` says "6 tests green"; there are 13.
- `README.md:151`: "No single open-source project combines DB1B, T-100, Form 41,
  gravity, QSI, and route economics end to end." Unfalsifiable and unnecessary.
  Cut it; the work stands without it.
- `docs/linkedin_posts.md`, `docs/resume_material.md`, `docs/interview_story.md`
  and `docs/demo_script.md` are in the public repo. A hiring reviewer reading the
  resume bullets next to the code is being shown the sales pitch and the product
  at the same time. Move them out of the published tree.
- Zero unit tests on `economics.py`, `demand.py`, `competition.py`, `screen.py`.
  Six of the thirteen tests are string matching between docs and artifacts. That
  is the direct cause of P0-1 surviving four self-review passes: consistency
  testing is not correctness testing.

---

## 7. What is genuinely strong, verified

Stated because a fair audit has to separate the defects from the substance, and
the substance is real.

1. **The reconciliation is excellent and holds up.** `warehouse/reconcile.py`
   derives the expected relationship from the source definitions before
   comparing (a transborder passenger touches exactly one Canadian airport per
   one-way journey, so the ratio should be about 1.0; a domestic passenger
   touches two, so that sector is 2x journeys and has no T-100 counterpart).
   Computed: 0.994 to 1.007 nationally across four years, 1.003 to 1.009 at YYZ,
   YVR, YYC and YUL. Bands are declared before the numbers are computed and
   failures are printed, not tuned. This is the single best artifact in the
   repository and it is what a data engineering interviewer should be shown
   first. One nitpick: the DB1B band (1.05, 1.60) is wide enough to be
   non-binding and all six years cluster at its top edge.
2. **The gravity model has the right specification for its job.** The `predict`
   variant deliberately excludes `has_nonstop` and `ln_seats` (R2 0.49) while a
   `diagnostic` variant includes them (R2 0.80). Excluding supply variables when
   forecasting demand for a route that does not exist yet is correct and most
   people get it wrong. It is disclosed in `docs/validation.md`.
3. **The negative results are real analysis, not filler.** The WestJet null and
   the Flair-versus-Lynx post-mortem contrast (route-level economic cut at 0.59
   to 0.70 load factor versus a corporate shutdown at 0.53) are the kind of
   distinction a network planner actually makes.
4. **The backtest refuses to overclaim.** It reports weak separation (0.89
   versus 0.86 median percentile), explains why, and pre-commits to the reading.
5. **Config-driven studies genuinely work.** Three carriers, three hubs, two
   countries, one code path.
6. **Rule 6 is honored.** Reports are generated from artifacts; the consistency
   tests do catch doc drift. The mechanism is sound even where it is pointed at
   the wrong number.
7. **The disclosure culture is real.** LIMITATIONS is 13 substantive items, not
   boilerplate. The problem found here is that two of them have the wrong sign or
   an overstated provenance, not that they are missing.

---

## 8. Prioritized plan

**P0, before this repo is shown to anyone.**

1. Fix `deps_yr = freq_wk * 52 * 2`. Add a units comment and a golden test
   pinning SEA to ICT against the T-100 actual (62.7 modeled versus 64.1
   observed passengers per departure).
2. Add carrier-family grouping to the warehouse; join one-stops on family;
   report `top_competitor` and `n_nonstop_incumbents` as marketing brands.
   Publish strict and family as a bound if a point estimate cannot be defended.
3. Correct `docs/LIMITATIONS.md` item 3: state the measured direction of the
   error (optimistic about the proposed share by 20 to 32 points), not the
   assumed one.
4. Rebuild `data/reference/incumbent_network_202604.csv` from an independent
   source, and make the candidate exclusion carrier-family aware. Verify the
   four Alaska metros drop out.
5. Regenerate everything (`make all && make test`), update PROGRESS.md, and add
   a "Round 4" section to INTEGRITY_REPORT.md that says plainly what was wrong
   and what the corrected numbers are.
6. Rewrite the README's decision section around the corrected result. **This is
   an opportunity, not damage control.** "Three studies, all say launch nothing,
   and here is the one market that survives to MONITOR and exactly why" is a
   more credible story than five LAUNCHes, and the write-up of how a two-times
   units error was caught by a validation study against T-100 is a better
   interview artifact than any of the current headline numbers.

**P1, before any interview.**

7. Add unit tests to `economics.py`, `demand.py`, `competition.py`, `screen.py`.
   Start with dimensional identities: passengers per departure times departures
   equals carried demand; contribution equals departures times margin per
   departure; BELF times revenue at full load equals cost.
8. Run the competition reconstruction against DB1B observed carriers at SEA and
   publish the result. It currently fails on 30 of 49 markets; publishing that
   with the family-rule fix applied turns a hidden defect into a validation
   exhibit.
9. Replace the MAE 7.0 headline with passenger-weighted MAE and a materiality
   floor. Explain the composition effect.
10. Regress `ln(transfer)` on a leisure indicator. This is the highest
    value-per-hour item in the whole plan.
11. Report leave-one-out on the per-hub medians actually used, and repoint
    `test_transfer_median_consistent` at them.
12. Add a LIMITATIONS entry for Air Canada being structurally invisible as a
    connecting competitor out of Canadian hubs.
13. Reframe the gravity model's role honestly in the README given that
    `gravity_x_transfer` never fires transborder.

**P2, portfolio polish.**

14. Move `BELF_MAX`, `MIN_ANCHOR_PAX`, `SURVEY_THRESHOLD`, `E2_FUEL_IMPROVEMENT`,
    the detour bounds, and the backtest thresholds into `assumptions.yaml`.
    Align the backtest candidate universe with the screen's.
15. Make at least one `sensitivity:` block propagate end to end and report
    verdict flips. Delete or implement `stimulation_elasticity`.
16. Disclose the doubled destination-income elasticity in `demand.py`'s
    docstring and LIMITATIONS.
17. Have CI run `models.run_all` on a small fixture warehouse, or at minimum
    import-check every module, so the pipeline cannot silently break.
18. Move the marketing docs out of the public tree. Cut README:151. Fix
    `spill.py:6` and `PROGRESS.md:65`.

**P3, if time permits.** Map view in the app; per-vintage backtest refit;
WestJet add-frequency study; the three-minute demo video.

---

## 9. Hiring debrief

**Would I hire on this project alone?** For a mid-level analytics or data
engineering role, yes, after P0 lands. For a senior network planning role, not
in its current state.

**What it proves.** This person can find, ingest, reconcile and model real
government aviation data end to end, can build a config-driven pipeline that
actually generalizes across carriers and countries, understands the T-100 versus
DB1B grain distinction well enough to write a definitional reconciliation that
lands within 1 percent, knows to exclude supply variables from a demand model,
and has the discipline to publish a null result and a weak backtest rather than
dress them up. The `reconcile.py` docstring alone is better reasoning than most
candidates produce.

**What it does not prove, and what a domain interviewer will find.** The two P0
defects are both the same class of error: a modeling assumption that was never
checked against a number the project already had in hand. T-100 shows Alaska
flying 62.96 one-way departures per week to LAX; the model divides bidirectional
demand by half of that. DB1B shows which carriers actually carry passengers in
every one of the 49 Alaska markets; the competition module never looked. The
Alaska SEA study was built explicitly to be the ground-truth check and was used
to validate demand and share levels but never the competition layer or the
economics arithmetic. The instinct to build a validation study was right. The
follow-through of actually pointing it at the parts most likely to be wrong was
missing.

The operating-versus-marketing carrier distinction is the tell a network
planner will notice fastest. `top_competitor` reports `MQ`, `YX`, `OH` and `OO`
on 29 of 79 Porter markets. Those are not airlines a planner competes against;
they are operating certificates. It is a five-minute conversation and it is
better to have already fixed it.

**Strongest signal available after the fixes.** Not the LAUNCH list. It is:
"I built a validation study against observable ground truth, then used it to
find a two-times units error and a competitive-set error in my own model, and
here is the before and after." Very few portfolio projects contain a genuine
self-caught falsification. That is the thing to lead with.
