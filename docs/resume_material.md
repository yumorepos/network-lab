# Resume material

Fill-ins marked [N] are read directly from the repo's outputs so every number
on the resume is reproducible from `make data && make models`.

## Resume bullets (pick per posting)

- Built an airline route-evaluation platform (Python, DuckDB, statsmodels,
  Streamlit) on fully open data: gravity demand model calibrated on [N=6,002]
  US markets, transferred to Canada-US markets via a factor anchored to the
  discontinued StatCan city-pair survey, with computed totals reconciling to
  published StatCan/BTS figures within 1%.
- Reconstructed competitive one-stop itineraries from T-100 segment
  frequencies and validated a QSI-lite share model against observed DB1B
  carrier shares (MAE [N] share points), then screened [N] candidate markets
  across three hub studies into LAUNCH/MONITOR/PASS with 3x3 fare-fuel
  scenario grids.
- Backtested 50 real 2021-2025 transborder route launches against a
  fixed pre-2022 model and published the honest result: demand percentile
  does not separate survivors from failures in this period because the era's
  failures (Lynx) were cost-structure, not market-selection — with the
  lookahead limitation disclosed.

## LinkedIn project description

Network Lab is an airline network planning workbench built entirely on open
data. It sizes markets with a US-calibrated gravity model, carries demand
across the border with a factor anchored to Canada's last published
transborder O&D survey, reconstructs competing itineraries from T-100
frequencies, and turns Form 41 cost filings into route-level scenario grids.
Every demand number is flagged observed or modeled; every assumption lives in
one YAML file with source, confidence, and sensitivity; and the whole
warehouse reconciles against published government totals within 1%. Flagship
study: WestJet transborder opportunities from Calgary. Validation study:
Alaska at Seattle, where the full chain is checkable against observed truth.

## Talking points on honest tradeoffs

1. Single-vintage backtest (lookahead disclosed; production refits per
   decision date).
2. Airport-fee proxy (flat, sensitivity-tested; per-airport tariffs do not
   flip decisions at this margin scale).
3. No audit trail (explainability, not cryptographic reproducibility, is the
   requirement for decision support; versioned runs exist in my trading
   project and would come here the day money moved on these outputs).
4. Canadian domestic is out of evidentiary reach for anyone without IATA
   data — and being able to prove exactly why is worth more than a study
   that cannot be checked.
