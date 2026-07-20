# Progress log

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
- Transfer factor: 87 anchored pairs, median 0.82, IQR [0.55, 2.04],
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
  Bridgeport...). Final: WS YYC 2 LAUNCH / 3 MONITOR / 72 PASS;
  AS SEA all 49 PASS at daily mainline gauge (saturated-hub agreement);
  PD YYZ 10 / 5 / 65.

## Phase 6 - validation and packaging (2026-07-20)
- Backtest: 61 transborder launches, operating 0.90 vs ceased 0.86 median
  percentile; weak separation published with the pre-committed reading (the
  era's failures were cost-structure, not market selection; lookahead
  disclosed).
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
- Deterministic fits (ORDER BY) + consistency test; canonical numbers:
  transfer 0.82, MAE 7.0, N=48, medians 0.89/0.86. See INTEGRITY_REPORT.md.
