PY := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: setup data marts reconcile models screen app test clean-data

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

app:
	.venv/bin/streamlit run app/streamlit_app.py

test:
	$(PY) -m pytest tests/ -q

clean-data:
	rm -rf data/raw data/parquet data/warehouse.duckdb
