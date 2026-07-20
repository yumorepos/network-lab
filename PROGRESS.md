# Progress log

## Phase 0 — plan and assumption engine (2026-07-20)
- Repo initialized. PLAN.md (architecture, dataset manifest, milestones),
  config/assumptions.yaml (seeded assumption engine), three study configs
  (westjet_yyc flagship, alaska_sea validation, porter_yyz portability),
  Makefile, requirements.
- data/reference/launches.csv (74 rows) and companion notes were compiled
  earlier from carrier press releases; they are the backtest target.
- Environment: Python 3.12.6 (plan says 3.11; 3.12 works, noted), 101 GB free
  disk, macOS.

## Phase 1 — data pipeline (in progress)
- [ ] ingest scripts per source
- [ ] make data end-to-end
- [ ] DuckDB marts
- [ ] reconciliation report
