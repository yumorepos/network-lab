# Network Lab: conventions for AI pair programming

> **Current status (2026-11-09):** This project is stable, evidence-bounded **fixed-gauge route screening**. Before any edit, read `docs/FINAL_SCOPE_CONTRACT.md`, `docs/REPOSITORY_MAINTENANCE_POLICY.md`, and `docs/NETWORK_LAB_AUDIT_HANDOFF_2026_11_09.md`. Prior Phase 5/6 and agent handoff documents remain historical, not an instruction to resume development. Do not rerun models or overwrite the original local DuckDB as part of documentation, design, or branch cleanup.

Route-evaluation engine for airline network planning, built on open government
data. One config-driven pipeline, three studies (WestJet YYC flagship, Alaska
SEA validation, Porter YYZ portability). The published results are frozen. Read the final scope contract and
computed `data/parquet/outputs/headline_metrics.yaml` for current claims;
`PROGRESS.md` and `INTEGRITY_REPORT.md` preserve historical corrections.

## Stack

Python 3.11, DuckDB over Parquet, Pandas, statsmodels, Streamlit, Plotly,
pytest. No new dependency without a one-line justification and approval.

## Hard rules

1. Never invent a numeric constant. Every non-derived value lives in
   `config/assumptions.yaml` with source, confidence, and sensitivity. Missing
   value: stop and ask. No plausible industry defaults.
2. Never invent a column name. Read the record layout in `data/reference/` or
   the mart definitions in `warehouse/` first.
3. Never commit raw downloads, warehouses or intermediate Parquet under `data/`.
   Public exceptions: vetted `data/reference/` and the existing small,
   explicitly force-tracked `data/parquet/outputs/` artifacts required by
   Streamlit. Keep output parity and source claims guarded (see docs/deploy.md).
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
- `models/screen.py` - the verdict logic and the fixed-menu schedule evaluation.
- `reports/generate.py`, `backtest/postmortem.py` - report generators.
- `tests/test_sanity.py` - correctness-critical logic and the served-market
  cross-check against `data/reference/incumbent_network_202604.csv`.
- `tests/test_consistency.py` - reader-facing docs and verdict counts must match
  the computed artifacts.
