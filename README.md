# Network Lab

Route evaluation for airline network planning, on open data only. Flagship:
WestJet transborder opportunities from Calgary. Validated end-to-end on Alaska
at Seattle, where demand, share, and fare are all observable. Portability shown
on Porter at Toronto Pearson.

Status: under construction. See PLAN.md for architecture and PROGRESS.md for
current state. Full README with validation headline numbers lands in Phase 6.

```
make setup   # venv + dependencies
make data    # download sources, build Parquet + DuckDB warehouse, reconcile
make models  # demand -> share -> economics -> screen for all three studies
make app     # Streamlit dashboard (reads precomputed outputs)
```
