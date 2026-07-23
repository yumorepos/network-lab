PY := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: setup data marts reconcile models screen backtest reports app test clean-data all deploy-prep

setup:
	python3 -m venv .venv
	$(PIP) install --upgrade pip -q
	$(PIP) install -r requirements.txt -q
	@echo "setup complete"

# Full pipeline: download everything, build Parquet, build DuckDB marts, reconcile.
data:
	$(PY) -m ingest.run_all
	$(PY) -m warehouse.build_marts
	$(PY) -m warehouse.reconcile

marts:
	$(PY) -m warehouse.build_marts

reconcile:
	$(PY) -m warehouse.reconcile

# Phase 2-5: demand -> share -> economics -> screen, all three study configs.
models:
	$(PY) -m models.run_all

screen:
	$(PY) -m models.screen

# Launch backtest against the register (single pre-2022 model, disclosed lookahead).
backtest:
	$(PY) -m backtest.run_backtest

# WestJet route evaluations, Alaska/Porter reports, two YYC-LAS post-mortems.
reports:
	$(PY) -m reports.generate

# Everything after `make data`: models, backtest, reports.
all: models backtest reports

app:
	.venv/bin/streamlit run app/streamlit_app.py

test:
	$(PY) -m pytest tests/ -q

clean-data:
	rm -rf data/raw data/parquet data/warehouse.duckdb

# Force-add the small precomputed outputs the Streamlit Community Cloud app
# needs (normally gitignored); the large raw data and warehouse stay out.
deploy-prep:
	git add -f data/parquet/outputs/*.parquet data/parquet/outputs/*.yaml data/parquet/outputs/*.csv
	@echo "outputs staged. commit, push, then deploy per docs/deploy.md"
