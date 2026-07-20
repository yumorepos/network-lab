# Interview story

## The problem airlines solve
A network planning team decides where to fly next: which unserved markets
clear an economic hurdle with a specific fleet, at a specific hub, against
specific competitors. The inputs they buy — MIDT bookings, OAG schedules —
are priced for airlines, not portfolios. The craft is the chain: market size,
achievable share, spill, cost, and a decision someone can defend.

## Why this project exists
Two reasons. First, to demonstrate that chain end to end on open data.
Second, and more interesting: Canada is a natural experiment in missing data.
There is no public Canadian domestic O&D, no public transborder fare data,
and the StatCan transborder city-pair survey froze around 2018. The design
answer — calibrate on US markets where truth exists, transfer across the
border with an anchored correction factor, and validate on a US hub where
every stage is checkable — is the project's core idea, and the
observed-vs-modeled flag on every demand number is its discipline.

## Architecture (60 seconds)
Python + DuckDB over Parquet. One command downloads BTS T-100/DB1B/Form 41,
StatCan, BEA, EIA, OurAirports; builds a warehouse; and reconciles it against
published totals. The model chain is catchment -> demand (observed DB1B or
gravity x transfer) -> QSI-lite share against competition reconstructed from
T-100 -> truncated-normal spill -> decomposed economics on a 3 fare x 3 fuel
grid -> LAUNCH/MONITOR/PASS with drivers, risks, and confidence. Streamlit
reads precomputed outputs. No orchestration framework, no audit layer:
explainability is the requirement here, and every number traces to a source
or a labeled assumption in one YAML file.

## Numbers I lead with
- Reconciliation: computed T-100 transborder totals match StatCan published
  enplaned+deplaned within 1% nationally and at YYZ/YVR/YYC/YUL — with the
  expected relationship derived from definitions before comparing.
- Transfer factor: median 0.86, IQR [0.55, 2.00] across 87 anchored pairs.
  I report the dispersion because it is the honest cost of transferring a
  US-calibrated model across a border.
- Gravity holdout: median APE ~0.6 on unseen markets. A three-covariate
  demand model is a screen, not an oracle, and the screen's job is ranking.
- Backtest: 50 real transborder launches 2021-2025 scored with a pre-2022
  model. Survivors and ceased routes both sit in the top decile of modeled
  demand (0.90 vs 0.86 median percentile) — the finding is that route
  failures in this period were cost-structure failures, not market-selection
  failures, and I say so instead of overclaiming signal.

## The tradeoffs I made on purpose
- Single fixed-vintage backtest with disclosed lookahead; production refits
  per decision date.
- One flat airport-fee proxy, sensitivity-tested, because the fee delta does
  not flip launch-vs-pass at this margin scale.
- Reconstructed connections from T-100 instead of MIDT; direction of error
  documented (conservative for the proposed service).
- No audit/versioning layer: for a decision-support tool the requirement is
  explainability; I built versioned-run infrastructure in a separate project
  and would add it here the day the tool fed real capital decisions.

## What a real team with MIDT and OAG would change
Swap reconstructed one-stops for observed itineraries; replace the fare curve
with filed fares; add schedule-quality timing (banks, local departure times)
to QSI; refit the backtest per vintage; and push demand below the 4,000
pax/yr survey floor where MIDT sees what public data cannot.
