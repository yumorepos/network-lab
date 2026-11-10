# Network Lab - Coding agent instructions

**Current project status:** frozen, evidence-bounded airline route-screening research, **not** a validated route-success predictor. Read the [scope contract](docs/FINAL_SCOPE_CONTRACT.md), [limitations](docs/LIMITATIONS.md), [November warehouse audit handoff](docs/NETWORK_LAB_AUDIT_HANDOFF_2026_11_09.md) and [public repository policy](docs/REPOSITORY_MAINTENANCE_POLICY.md) before changes.

## Sources of truth

- Frozen research: 200 published market screens and 463 historical replay decisions. Preserve the published counts, assumptions, candidate ordering and conclusions unless an independently tested, separately approved correction is made.
- Machine-readable results: `data/parquet/outputs/` and `config/`. The live Streamlit app reads committed outputs. It does not access the original Mac DuckDB.
- Research methods: `models/`, `warehouse/`, `ingest/`, `backtest/`, `replay/`; tests and reproducibility are in `tests/` and `scripts/`.
- Full engineering safety rules: [CLAUDE.md](CLAUDE.md). If a dated historical document conflicts with the final scope contract or current outputs, the **current source files and verified contract** win.

## Non-negotiable constraints

1. **Never commit or publish raw source archives, original `data/warehouse.duckdb`, credentials, personal documents or employer/client records.** Only vetted `data/reference/` and already committed small `data/parquet/outputs/` artifacts are intentionally public.
2. Never invent source values, columns or airline business assumptions. Model constants and provenance live in `config/assumptions.yaml`.
3. Distinguish T-100 *flight segments* from DB1B *origin-destination passengers*. Disclose missing coverage, source vintage, proxy geography and model resolution.
4. Never present LAUNCH/MONITOR/PASS research classifications as operational route recommendations. Historical replay did **not** demonstrate ranking lift over a demand-only baseline at the detectable resolution.
5. Do not silently refit models, regenerate the 200 screens, overwrite the local warehouse, change the 463 replay decisions or promote unfinished geography patches.
6. Do not hand-edit generated research reports; repair the source and reproduce the outputs in an isolated environment only with approval.
7. Run `pytest tests/ -q` on the applicable environment and explain skipped warehouse-dependent tests. Do not weaken assertions to pass CI.
8. Use temporary feature branches and reviewable pull requests for new substantive work. Do not force-push or rewrite public Git history as a cleanup shortcut.

## Active vs historical documents

The current instructions are **this file and CLAUDE.md**. Historical notes and retired plans reside in [docs/history/](docs/history/README.md); they explain prior choices and **are not new work authorizations**. `PROGRESS.md` remains at root temporarily because canonical-value tests explicitly read it. See [documentation index](docs/README.md) for the latest public research narrative.

The synthetic `experiments/disruption_recovery/` is separate, unfinished experimental code and must not be presented as a validated capability of Network Lab.
