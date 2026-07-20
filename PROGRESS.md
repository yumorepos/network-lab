# Progress log

## Phase 0 — plan and assumption engine (2026-07-20)
- Repo, PLAN.md, assumptions.yaml, three study configs, Makefile.
- Environment: Python 3.12.6 (plan says 3.11; works), 101 GB free disk.

## Phase 1 — data pipeline (2026-07-20)
- TranStats client drives the site's own DL_SelectFields form (URL params are
  rot13 over [A-Z0-9]; ASP.NET event validation requires posting only valid
  dropdown options). Old Download_Lookup.asp is dead; support tables 288/300/
  304 replace it.
- Census ACS API now requires a key -> BEA county files (CAINC1/CAGDP2)
  aggregated to CBSA via the official delineation file; documented in
  assumptions.yaml. BEA metro-level zips are retired (HTML at old URLs).
- T-100 2018-2026, Form 41 P-5.2/P-1.2 2018-2025, StatCan 8 tables, EIA,
  OurAirports all land. DB1B 28 quarters via PREZIP (long pole).
- Marts + city-market->CBSA mapping (810 mapped; unmatched-with-traffic
  logged; territories/rural AK legitimately outside CBSA system).
- Reconciliation: national transborder T-100 vs StatCan within 1% for
  2018/2019/2023/2024; airport-level YYZ/YVR/YYC/YUL within 1%. DB1B check
  reruns after full download.

## Phases 2-5 — model chain (2026-07-20, code complete)
- Gravity: pre2022 fit n=6002, R2 0.51, holdout median APE 0.59 (reported
  honestly; quadratic log-distance added for the ground-substitution hump).
- Transfer factor: 87 anchor pairs, median 0.86, IQR [0.55, 2.00]; per-hub
  medians (YYC 1.26, YYZ 0.77, YVR 0.80). Border effect visible and reported.
- Candidates: 105 (YYC) / 76 (SEA) / 104 (YYZ). Competition reconstruction,
  QSI-lite, spill, P-5.2 economics (fuel burn derived from AIR_FUELS_ISSUED),
  3x3 grids, screen. Share validation vs DB1B (SEA) written.
- Waiting on DB1B completion to fit the current-vintage gravity and run the
  full chain end to end.

## Phase 6 — in progress
- Backtest module, Streamlit app, report generator, LIMITATIONS.md, CI
  written; run + final docs after the chain completes.
