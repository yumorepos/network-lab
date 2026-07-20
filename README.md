# Network Lab

**Route evaluation for airline network planning, built entirely on open
data.** Flagship study: WestJet transborder opportunities from Calgary (YYC).
Validation study: Alaska at Seattle (SEA), where demand, share, and fare are
all observable and the whole chain is checked against truth. Portability
proof: Porter at Toronto Pearson (YYZ).

## The planning workflow it implements

| Stage | What it does | Where |
|---|---|---|
| Market Intelligence | warehouse of T-100, DB1B, Form 41, StatCan, BEA, EIA; reconciled to published totals | `ingest/`, `warehouse/` |
| Opportunity Scan | candidate metros per hub: population, range, unserved by the study carrier | `models/candidates.py` |
| Route Evaluation | demand (observed or gravity x transfer) -> QSI-lite share vs reconstructed competition -> spill -> 3x3 fare-fuel economics | `models/` |
| Business Case | LAUNCH/MONITOR/PASS with drivers, risks, assumptions; written cases for the flagship | `models/screen.py`, `reports/` |
| Validation | reconciliation, gravity holdout, share MAE vs DB1B, launch backtest | `docs/validation.md`, `docs/reconciliation.md`, `docs/backtest.md` |

## Headline validation numbers

- Computed T-100 transborder totals match StatCan published figures **within
  1%** nationally and at YYZ/YVR/YYC/YUL (relationship derived from
  definitions before comparing; see `docs/reconciliation.md`).
- Transfer factor anchored to the discontinued 2018 StatCan city-pair
  survey: **median 0.83, IQR [0.56, 2.10]** across 87 pairs - dispersion
  reported everywhere the factor is used.
- 48 launched-and-resolved transborder routes (2021-2025) backtested with
  a pre-2022 model: survivors and ceased routes both sit in the top decile
  of modeled demand (**0.90 vs 0.86** median percentile), and the gap barely
  moves when Lynx's shutdown casualties are excluded (0.90 vs 0.86). Genuine
  route-level cuts by continuing carriers were also top-decile markets:
  demand rank alone does not predict survival, and the report says so
  rather than overclaiming signal.
- QSI-lite carrier shares vs observed DB1B shares at SEA: **MAE 6.7 share
  points** across 503 market-carrier rows, reported by market structure.
- Screens that behave like screens: WestJet YYC resolves 77 candidates to
  **2 LAUNCH / 3 MONITOR / 72 PASS**; Alaska SEA resolves all 49 remaining
  unserved candidates to PASS at daily mainline gauge, agreeing with the
  revealed saturation of a mature hub; Porter YYZ finds 10 LAUNCH among 80.

## Design in one paragraph

There is no public Canadian domestic O&D, no transborder fare data, and the
transborder O&D survey froze in 2018. So the gravity demand model is
calibrated where truth exists (~6,000 US city-market pairs from DB1B),
transferred to Canada-US markets with an anchored correction factor, and
validated end to end on a US hub. Every demand number carries an
`observed`/`modeled` flag; every non-derived value lives in
`config/assumptions.yaml` with source, confidence, and sensitivity; and a
proposed nonstop is never scored against an empty market - competitor
one-stops are reconstructed from T-100 segment frequencies first.

## Run it

```
make setup   # venv + dependencies
make data    # download all sources, build DuckDB warehouse, reconcile (~30-60 min)
make models  # demand -> share -> economics -> screens for all three studies
make test    # sanity tests
make app     # Streamlit dashboard (reads precomputed outputs)
python -m backtest.run_backtest   # launch backtest
python -m reports.generate        # business cases + validation reports
```

No API keys required. If you have a Census key, `CENSUS_API_KEY=... make
data` upgrades US income to ACS median household income (documented fallback
otherwise). Raw downloads stay out of git; `data/reference/launches.csv` is
the hand-compiled launch register with per-row confidence and sources.

## Honest limitations

See `docs/LIMITATIONS.md` - the ten limitations are stated with the design
decision each one forced, including the single-vintage backtest lookahead and
the airport-fee proxy. Planned extensions (route post-mortems, full Porter
study, connectivity view, per-vintage refits) are listed there rather than
implied to exist.

## Data sources and licenses

BTS TranStats (public domain), StatCan (Open Government Licence - Canada;
tables 23-10-0253/0256/0249/0255/0257/0259/0312, 17-10-0135), BEA (public
domain), EIA (public domain), Census delineation files (public domain),
OurAirports (public domain).
