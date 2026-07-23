# Network Lab: conventions for AI pair programming

Route-evaluation engine for airline network planning, built on open government
data. One config-driven pipeline, three studies (WestJet YYC flagship, Alaska
SEA validation, Porter YYZ portability). The build is complete; work now is
correctness, documentation, and packaging. Read PROGRESS.md for the canonical
current numbers and NEXT_SESSION.md for the active work plan.

## Stack

Python 3.11, DuckDB over Parquet, Pandas, statsmodels, Streamlit, Plotly,
pytest. No new dependency without a one-line justification and approval.

## Hard rules

1. Never invent a numeric constant. Every non-derived value lives in
   `config/assumptions.yaml` with source, confidence, and sensitivity. Missing
   value: stop and ask. No plausible industry defaults.
2. Never invent a column name. Read the record layout in `data/reference/` or
   the mart definitions in `warehouse/` first.
3. Never commit anything under `data/` except `data/reference/`. The Streamlit
   deploy force-adds `data/parquet/outputs/` explicitly (see docs/deploy.md).
4. Demand is observed (DB1B) where it exists, anchor-scaled or gravity+transfer
   only where it does not. Every demand row records which path produced it via
   the `demand_source` and `demand_method` fields.
5. T-100 is SEGMENT data; DB1B is O&D data. Never join as if the same grain.
   T-100 has no Canadian domestic segments (they never touch the US).
6. Reader-facing numbers and verdict counts are read from computed artifacts,
   never hardcoded. Regenerate reports with `make reports`; never hand-edit the
   generated markdown in `reports/` (fix the generator in `reports/generate.py`
   or `backtest/postmortem.py`).
7. If a test fails, report the failing values. Never relax an assertion, widen a
   tolerance, or edit an expected value to make a test pass.
8. The backtest scores launches with a single pre-2022 model and discloses the
   lookahead. Do not quietly refit per vintage without saying so.
9. No em dashes, en dashes, or double hyphens in any generated text, comment, or
   doc. Spaced hyphens only.
10. Money is USD internally; distance is converted once on ingest.

## Definition of done

`make all && make test` is green from a clean state; new constants are in
`assumptions.yaml` with a source; reports are regenerated from outputs, not
hand-edited; the consistency tests pass (they fail the build if any headline
number or verdict count drifts); PROGRESS.md reflects the current numbers.

## Where things are

- `config/assumptions.yaml` - every assumption, one file.
- `config/studies/*.yaml` - a study is a config, not a code change.
- `models/screen.py` - the verdict logic and right-sizing.
- `reports/generate.py`, `backtest/postmortem.py` - report generators.
- `tests/test_sanity.py` - correctness-critical logic and the served-market
  cross-check against `data/reference/incumbent_network_202604.csv`.
- `tests/test_consistency.py` - reader-facing docs and verdict counts must match
  the computed artifacts.
