# Interview story

## The problem airlines solve
A network planning team decides where to fly next: which unserved markets
clear an economic hurdle with a specific fleet, at a specific hub, against
specific competitors. The inputs they buy - MIDT bookings, OAG schedules -
are priced for airlines, not portfolios. The craft is the chain: market size,
achievable share, spill, cost, and a decision someone can defend.

## Why this project exists
Two reasons. First, to demonstrate that chain end to end on open data.
Second, and more interesting: Canada is a natural experiment in missing data.
There is no public Canadian domestic O&D, no public transborder fare data,
and the StatCan transborder city-pair survey froze around 2018. The design
answer - calibrate on US markets where truth exists, transfer across the
border with an anchored correction factor, and validate on a US hub where
every stage is checkable - is the project's core idea, and the
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
- The recommendations: Porter YYZ surfaces one LAUNCH market (Boston), a large
  anchor-backed market entered at 16% share against real incumbents - the
  low-cost entry logic of taking a slice of a big market, evaluated across the
  fixed 3x/7x/14x weekly menu. An earlier version reported five LAUNCHes and did not
  survive correctness review; the two defects and the before and after are in
  INTEGRITY_REPORT.md. WestJet YYC comes back all-PASS, and I
  lead with that too: it stays PASS at every service level, because WestJet
  already flies its viable YYC transborder markets and what is left is either
  below the 2018 survey's 4,000-passenger floor or held by a US hub carrier
  (Dallas at 23% share vs American). A tool that only ever says "launch" is a
  cheerleader; one that can say "you have already picked the fruit here, go
  build breadth at Edmonton" - which is what WestJet actually did - is a
  planner.
- Share model: MAE 5.7 share points against observed DB1B carrier shares at
  SEA, split by market structure, using the identical machinery that scores
  unserved Canadian candidates.
- Reconciliation: computed T-100 transborder totals match StatCan published
  enplaned+deplaned within 1% nationally and at YYZ/YVR/YYC/YUL - with the
  expected relationship derived from definitions before comparing.
- Transfer factor: median 0.80, IQR [0.55, 2.02] across 87 anchored pairs.
  I report the dispersion because it is the honest cost of transferring a
  US-calibrated model across a border.
- Gravity holdout: median APE ~0.6 on unseen markets. A three-covariate
  demand model is a screen, not an oracle, and the screen's job is ranking.
- Backtest: 48 launched-and-resolved transborder routes 2021-2025 scored
  with a pre-2022 model (never-launched and unknown-status rows reported
  separately). Survivors 0.89 vs ceased 0.86 median demand percentile, and
  excluding Lynx's shutdown casualties barely moves it: most ceased routes
  were genuine cuts by Flair, a continuing carrier, in top-decile leisure
  markets. Demand rank alone does not flag route failure; that needs the
  economics and competitive layers at launch vintage, and I say so instead
  of overclaiming signal.

## The part I would actually want to be asked about

I tested the engine against the simplest possible competitor and it did not
win.

I built a point-in-time replay: reconstruct the whole verdict chain at three
historical decision dates from offline data only, guarded by leakage tests
where all ten injected leaks were demonstrated to fire, then score it against
the launches that actually happened. Then I ranked the same rows by modeled
demand alone and compared.

Before reading the comparison I measured what it could resolve, which turned
out to be the important step. The 15 positive rows rest on only 10 distinct
launch events across 3 vintages, the smallest difference the design can detect
is roughly 5 net launch events spread over two vintages, and at k=20 the demand
ranking already contains every positive, so nothing can beat it there by any
amount. Every non-zero number in the headline was one launch label moving at
one date.

So the honest statement is bounded: no detectable incremental ranking value at
effects larger than the study's resolution, smaller effects unresolved. Not
"the model does not beat demand", which claims an equivalence this design
cannot establish, and not a quiet reframing into something that sounds
positive.

Two things followed, and I think the second is the more interesting one.

First, the replay showed one component was doing no work at all. The frequency
and gauge step was described as right-sizing, a claim I have retired. Each
study configures a single gauge, the menu starts at 3x weekly, and 445 of 463
decisions never reached a comparison because nothing was feasible. Ranking by margin
at the minimum option and at the chosen option is the same ordering, Spearman
exactly 1.000 at every date. I retired the claim instead of building a
fleet-assignment layer to justify it.

Second, I did not react to a null by deleting everything sophisticated. I asked
which layers had mechanistic evidence. Share and economics genuinely reorder
the candidate set; the schedule step does not. The share layer rested almost
entirely on the one-stop reconstruction and had been validated almost entirely
outside that regime, because the published check's passenger floor selected
against it. So I re-ran the validation at the floor the demand layer already
uses, with the protocol frozen first, and the one-stop-only regime is now the
largest stratum and beats an equal-share null there. I kept that layer, and I
can say why.

The summary I would give: I falsified my own headline component, published a
negative result against my own engine, and narrowed the claim to what survived.
Knowing when to stop defending a model is the part that took judgment.

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
