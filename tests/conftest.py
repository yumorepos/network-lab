"""Shared test preconditions.

The repository deliberately does not commit the DuckDB warehouse or the raw
downloads (hard rule 3), so a fresh checkout has the small precomputed outputs
under `data/parquet/outputs/` and nothing else. Tests that reconstruct the
model chain need the warehouse and cannot run there.

Before T6 those tests raised `IOException: database does not exist` instead of
skipping, which turned a fresh-checkout run into roughly a hundred errors. That
is worse than useless: it hides real failures in noise, and it made the CI
badge in README a statement about a run from before the replay machinery
existed rather than about the current tree.

Skipping on a missing precondition is not the same as relaxing an assertion.
Where the warehouse exists, which is every local `make test`, every one of
these tests runs exactly as before and nothing is waived.
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WAREHOUSE = ROOT / "data" / "warehouse.duckdb"
OUTPUTS = ROOT / "data" / "parquet" / "outputs"

WAREHOUSE_REASON = (
    "needs data/warehouse.duckdb, which is not committed (hard rule 3); "
    "run `make data` to build it"
)

# Modules whose tests reconstruct the model chain from the warehouse.
requires_warehouse = pytest.mark.skipif(
    not WAREHOUSE.exists(), reason=WAREHOUSE_REASON)


def need_warehouse():
    """Call at the top of a test that reads the warehouse mid-body."""
    if not WAREHOUSE.exists():
        pytest.skip(WAREHOUSE_REASON)


def pytest_report_header(config):
    return (f"network-lab: warehouse "
            f"{'present' if WAREHOUSE.exists() else 'ABSENT (chain tests skip)'}"
            f", outputs "
            f"{'present' if OUTPUTS.exists() else 'ABSENT'}")
