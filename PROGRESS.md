# Progress log

## Stage 2R.1 to 2R.4 complete (2026-08-16): the mechanism diagnostics

Generated into `docs/STAGE_2R_DIAGNOSTICS.md` by `replay/stage2r_report.py`,
guarded by `tests/test_stage2r_diagnostics.py`. Nothing was fitted, calibrated
or repaired, no assumption or threshold moved, and the rebuilt chain reproduces
`decision_rows.parquet` market by market before any diagnostic runs.

**The binding constraint is not D1, D2 or D3.** Median modelled load factor at
3x weekly on the study gauge is 0.075 against a feasibility floor of 0.50. Only
18 of 463 decision rows reach the floor at any frequency and only 9 have a
positive annual contribution. The candidate sets are thinner than the smallest
schedule the model is allowed to fly, so every downstream layer is evaluated in
a regime where nothing is feasible.

**2R.1.** Two layers materially reorder and two do not. Share is MEANINGFUL
DIFFERENTIATION and rests almost entirely on the one-stop reconstruction: 85 of
88 WestJet candidates have no nonstop incumbent and 33 have no reconstructed
competitor at all. Economics is MEANINGFUL DIFFERENTIATION and applies a
distance tilt to captured demand. Right-sizing is MOSTLY REDUNDANT: ranking by
margin at the minimum option and at the chosen option are the same ordering,
Spearman exactly 1.000 at every date. The verdict is NOT SEPARABLY
IDENTIFIABLE, constant at two of three dates. This gives Stage 2R.0's null a
mechanical explanation: away from capacity, margin is a monotone function of
captured demand times a distance-driven fare-over-cost factor.

**2R.2.** D3A is a DOWNSTREAM ASYMMETRY, not a ranking bottleneck. The tied
block is 51, 50 and 49 rows at one value, sits entirely below demand rank 50,
reaches no demand top 20 and contains no WestJet launch, yet the margin score
pulls it into its own top 10 and top 20. D3B is a separate CORRECTNESS ISSUE:
the tie group is the same size at every floor from 280 to 4,000 and gets larger
as the floor falls, so a floor correction cannot be sold as removing the
compression. Porter has one capped launch, correcting the roadmap's
preliminary note.

**2R.3.** D2 is MULTIPLE INTERACTING CAUSES, and the QSI frequency exponent is
not among the primary ones. 445 of 463 decisions never reach a comparison: they
take the branch that fires when no option clears the load-factor floor, which
returns the highest load factor and is therefore identical to returning 3x.
7x wins in 2 of 463 rows, both where the 3x schedule is already 98% full. The
median market would need 78 times its captured demand for 7x to win.
Recommendation, not implemented: **RETIRE / DE-SCOPE RIGHT-SIZING**.

**2R.4.** D1's blast radius is DEMAND-LEVEL and ECONOMICS only. Growth is a
common positive scalar on every demand branch, verified on the rows: the demand
ratio is constant to six decimals, both rankings are identical, **zero WestJet
verdicts change**, and every Family 1 and Family 4 figure is unchanged. Porter
does move, 6 verdicts, because its candidate set reaches capacity where the
margin transform stops being monotone. The repair stays scheduled and
unconditional; 2023-01 is not rescued by it.

**Provisional W2 necessity, not authorised.** W2.1, W2.4 and W2.5 LIKELY NOT
JUSTIFIED. W2.2 and W2.3 DEPENDENT ON STRUCTURAL REPAIR.

**Next: 2R.5 and the Stage 2R decision gate.** Not started.

## Stage 2R.0 complete (2026-08-16): the resolution limit, measured

**Verdict: LIMITED TO LARGE EFFECTS.** The first stage of the redesigned
roadmap is done. It changed no model behaviour, no assumption and no frozen
number; it measured what the frozen V2 predictive comparison was ever capable
of distinguishing. Generated into `docs/STAGE_2R0_RESOLUTION.md` by
`replay/resolution.py`, guarded by `tests/test_stage2r0_resolution.py`.

**The instrument is five times coarser than its own readings.** Agreement@k
and recall@k are lattice-valued: pooled over the three decision dates, one
launch moving in or out of a top-k is worth 0.0667 of agreement@5, 0.0333 of
agreement@10, and between 0.0476 and 0.1111 of recall depending on the date.
Every non-zero difference in the V2 Family 4 headline is exactly one such
event. The k=5 result is one launch, Denver, dropping out of the top five at
2022-01. The k=10 result is one launch, Anchorage, entering the top ten at
2024-01. Two label changes carry all six headline numbers.

**Against that, the minimum detectable difference is five events.** Estimated
by construction rather than by formula, because three temporal blocks do not
support an asymptotic cluster-robust calculation: rankings that beat the demand
comparator by exactly N net launch events were built and scored with the frozen
bootstrap. Four events or fewer never excludes zero. An improvement confined to
a single decision vintage never excludes zero at any size this sample permits,
which is precisely the shape of the observed k=10 result. Five events is half
the ten distinct launch events in the study.

**k=20 measures nothing.** Both scores already place every positive inside the
top twenty at all three dates, so headroom is zero, recall is pinned at 1.000
and agreement is pinned at P_d/20. Its 0.000 difference is a property of the
candidate set, not a comparison that happened to tie.

**The V2 intervals do not cover decision-date uncertainty.** The metro-cluster
bootstrap captures market-to-market variation and the repeated-market panel
structure; all three dates appear in all 2,000 resamples by construction. The
15 positive rows also rest on only 10 distinct launches, five of which are
scored at two dates.

**The consequence.** The null stands and is now bounded: no incremental value
larger than the study's detectable resolution was observed, and smaller effects
remain unresolved. The null is underpowered, not empty. Stage 2R.1 through
2R.5 proceed as mechanism attribution, which is arithmetic and unaffected by
this limit; no W2 calibration may be justified by an expected gain in a Family
4 metric.

**Not started: 2R.1 through 2R.5.** They await authorization under the
evidence standard this stage establishes.

## Phase 5 Milestone A complete (2026-08-14): W1.3 snapshots and the W1.4 replay

The point-in-time machinery and the decision replay, the two pieces Milestone A
was missing, are built. **The canonical numbers below are unchanged**: this work
measured the frozen model and changed no default, assumption or threshold.

`snapshot(t)` reconstructs the full verdict chain at a decision date from
offline point-in-time data, guarded by 36 leakage tests (all 10 injected leaks
demonstrated to fire), 13 parity tests requiring the replay to reproduce every
committed verdict market by market, and 49 historical-chain tests that execute
all six build layers at the approved cutoffs, assert the vintage each one read,
and assert that every vintage carries a provenance record naming the value
actually used. Those last two groups were added to close finding P1-1 of the
Milestone A independent review, in two parts: the historical chain was reached
by no test at all, and the corridor-growth year and EIA fuel `as_of` were
recorded nowhere. **143 tests total.**

**Milestone A is frozen.** Independent review verdict
**APPROVE WITH NONBLOCKING FINDINGS**; **P1-1 and P1-2 both closed**, no P0,
four nonblocking P2 items open. Roadmap verdict
**REDESIGN THE REMAINING ROADMAP**. See `docs/MILESTONE_A_COMPLETION.md`
section 10.

The per-date breakdown is now generated into `docs/W1.4_replay_results.md`
section 3. It is the reason the roadmap was redesigned rather than continued:
the pooled agreement@10 advantage rests entirely on 2024-01 and disappears when
that date is dropped, k=20 is saturated at recall 1.000 under both rankings,
and no date is positive at k=5.

**Next: Stage 2R**, a diagnostic stage defined in
`docs/REMAINING_ROADMAP_REDESIGN.md`, which replaces the automatic W2.1 to W2.5
sequence in `PHASE_5_6_PLAN.md` (preserved, superseded). Stage 2R establishes
the resolution limit of the predictive comparison first, then attributes the
score layers, then diagnoses the survey ceiling and the frequency degeneracy,
then measures D1's blast radius. It ends at a three-way decision gate and
changes no model behaviour.

The replay ran 7 study-by-date snapshots, 463 decision rows, 22 positives, over
decision dates 2022-01, 2023-01 and 2024-01 with 2020 and 2021 excluded.

**The headline, on the only statistically FULL cell in the project.** WestJet
launch agreement, 244 rows, 15 positives: the model puts two thirds of real
launches in its top ten of roughly eighty candidates (recall@10 0.679
[0.325, 0.953]). But against a demand-percentile ranking on identical rows,
**every one of six difference intervals spans zero**. The full engine shows no
measurable incremental value over ranking by modeled demand alone. Published as
the finding, per the protocol's pre-commitment.

**Right-sizing.** The model chose the minimum of its frequency list on 461 of
463 decision rows and 18 of 18 paired launches. Median chosen-to-observed ratio:
WestJet 1.003 [0.725, 1.449], Alaska 0.428 [0.421, 0.435], Porter 0.461
[0.285, 0.864]. This refines the earlier "3x on 200 of 200" diagnostic rather
than confirming it: the bias is study-specific, and a constant cannot correlate
with anything.

**Newly discovered defect, recorded not fixed.** Corridor growth is a raw ratio
of two single T-100 years with no COVID handling. At a 2023-01 cutoff it is
0.196 at YYC, collapsing median anchored WestJet demand from 13,156 to 2,023.

Protocol: `docs/W1.4_REPLAY_PROTOCOL.md` (frozen before results).
Results: `docs/W1.4_replay_results.md` (generated).
Scoreboard: `docs/W1.4_predictive_baseline_v2.md`.

## Phase 6A (2026-07-28): Poisson QMLE gravity implemented, adoption deferred

The log-linear gravity model recovers the conditional median, not the mean:
`sum(predicted)/sum(observed) = 0.439` on the US calibration frame. A Poisson
QMLE estimator with robust HC1 covariance now exists alongside it
(`models/gravity_poisson.py`) and fixes that: aggregate 0.44 to 0.95, RMSE down
28%, calibration flat across seven predicted deciles where log-OLS is off by up
to 3.4x on the largest markets.

**It is implemented and measured but is NOT the default**, and the canonical
numbers below are unchanged. A counterfactual through the real pipeline moved
**zero of 200 verdicts**, because the transfer factor is estimated as
`observed / gravity_pred` and therefore absorbs any uniform rescaling of gravity
by construction. Adoption is recommended together with Phase 6B, which is what
lets the gravity path actually drive transborder demand instead of being
bypassed by the survey cap.

Evidence: `docs/phase6a_poisson_comparison.md`.
Decision and reasoning: `docs/phase6a_implementation_report.md`.

## Canonical numbers (current, post round 4 and Phase 5 Milestone A)

The machine-readable source of truth is
`data/parquet/outputs/headline_metrics.yaml`, regenerated by `make models`.
`tests/test_consistency.py` fails the build if any hand-written doc disagrees
with it. This block restates it for readers; if the two ever differ, the
generated file wins and the test will say so.

The dated phase entries below record the state at each phase and several were
superseded, first by the round-3 right-sizing pass and then by the round-4
correctness fixes (see INTEGRITY_REPORT.md). Where a phase entry differs, this
block wins.

- Porter YYZ screen: 1 LAUNCH (Boston) / 1 MONITOR (Hartford) / 77 PASS.
- WestJet YYC screen: 0 LAUNCH / 0 MONITOR / 76 PASS (deliberate honest negative).
- Alaska SEA screen: 45 PASS, all-PASS. The four Horizon-operated metros that
  previously leaked into the candidate set are gone, and the former lone
  MONITOR (Fayetteville) now screens PASS.
- Transfer factor: median 0.80, IQR [0.55, 2.02], 87 anchored pairs.
- Share MAE 5.7 points unweighted, 10.9 passenger-weighted; backtest N = 48
  launched-and-resolved of 61 scored (operating 0.89 vs ceased 0.86);
  gravity 6,002 (2018-19) / 6,092 (2023-24), R2 0.50.
- T-100 history spans 1990-2026 excluding 2020; 89,502 derived route spells.

## Phase 0 - plan and assumption engine (2026-07-20)
- Repo, PLAN.md, assumptions.yaml, three study configs, Makefile.

## Phase 1 - data pipeline (2026-07-20)
- TranStats client drives the site's own DL_SelectFields form (URL params are
  rot13 over [A-Z0-9]; ASP.NET event validation requires posting only valid
  dropdown options). Retired endpoints (Download_Lookup.asp, BEA metro zips,
  keyless ACS) all found documented alternates.
- T-100 2018-2026, Form 41 P-5.2/P-1.2, StatCan 8 tables, BEA county files
  aggregated via the Census delineation crosswalk, EIA, OurAirports, DB1B 26
  quarters (2025 Q3/Q4 unpublished, tolerated). ~50 min wall clock.
- Reconciliation 14/14 in band: national transborder T-100 vs StatCan within
  1% (2018/2019/2023/2024); airport-level YYZ/YVR/YYC/YUL within 1%; DB1B
  journeys vs T-100 boardings 1.52-1.57 for all complete years.

## Phase 2 - demand (2026-07-20)
- Gravity: current n=6092 R2 0.50, pre2022 n=6002 R2 0.50, holdout median
  APE ~0.6 reported by size band. Quadratic log-distance.
- Transfer factor: 87 anchored pairs, median 0.80, IQR [0.55, 2.02],
  per-hub medians (YYC 1.28, YYZ 0.78, YVR 0.83), leave-one-out stable.
- Every demand row flagged observed/modeled; transborder rows carry the 2018
  anchor value alongside where it exists.

## Phase 3 - share (2026-07-20)
- One-stop reconstruction with ratio + absolute circuity allowance (the
  absolute floor matters on short markets: YYZ-BDL via PHL is a real path at
  1.4x circuity). QSI-lite validated vs DB1B at SEA: MAE 6.7 share points
  (503 rows, by market structure in validation.md).

## Phase 4 - economics (2026-07-20)
- P-5.2 rates with fuel burn derived from AIR_FUELS_ISSUED/TOTAL_AIR_HOURS;
  indirect burden derived from P-1.2/P-5.2 (fully-allocated proxy margins);
  3x3 fare-fuel grids; truncated-normal spill.

## Phase 5 - screens (2026-07-20)
- Candidate hygiene that changed the story: airport seat floor + satellite
  rule removed 25-28 phantom "virgin markets" per study (Provo, Naples,
  Bridgeport...). Initial screens at a single hardcoded schedule (superseded by
  round-3 right-sizing; see the canonical block above for final numbers).

## Phase 6 - validation and packaging (2026-07-20)
- Backtest: N = 48 launched-and-resolved transborder routes, operating 0.89 vs
  ceased 0.86 median percentile; weak separation published with the pre-committed
  reading (the era's failures were cost-structure, not market selection;
  lookahead disclosed). Earlier drafts said "61 launches / 0.90"; corrected in
  the integrity pass to the precise N=48 count and deterministic 0.89.
- Three WestJet business cases, Alaska validation report, Porter portability
  table, validation.md, reconciliation.md, LIMITATIONS.md, interview story,
  resume material, Streamlit app, CI, 6 tests green.

## Known future work
- Route post-mortems (two, highest ROI), per-vintage backtest refit, ACS
  income with a key, connectivity view, full Porter study.

## Integrity pass (2026-07-20, post-review)
- Backtest narrative corrected: 12 of 21 ceased routes were Flair route-level
  cuts, not Lynx shutdown casualties; N pinned at 48 launched-and-resolved.
- Anchor-first transborder demand (market's own 2018 actual beats hub-median
  transfer); three anchor-matching bugs fixed; verdicts moved both ways
  (WS YYC 2 LAUNCH -> 0; PD NYC PASS -> LAUNCH).
- Share guard (>70% share + 0 nonstops -> MONITOR cap) and 700mi circuity.
- Alaska all-PASS reframed as fixed-gauge artifact, not saturation.
- Deterministic fits (ORDER BY) + consistency test. Round-3 right-sizing then
  moved the transfer median from 0.82 to the current 0.80 and re-scored every
  screen; the canonical numbers are in the block at the top of this file and in
  INTEGRITY_REPORT.md.
