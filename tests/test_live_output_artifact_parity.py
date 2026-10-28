"""Verify EXACT reader-facing output datasets, not only CSV headlines.

The Streamlit app loads Parquet. A passing CSV-only test can miss an
independently stale Parquet deployment artifact. No warehouse is required.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/parquet/outputs"
STUDIES = ("westjet_yyc", "alaska_sea", "porter_yyz")
KEY = ["study_id", "metro_name", "dest_airport"]


def _compare(csv: pd.DataFrame, parquet: pd.DataFrame, study: str) -> None:
    assert set(csv.columns) == set(parquet.columns), (
        f"{study} schema differs: CSV-only {sorted(set(csv)-set(parquet))}; "
        f"Parquet-only {sorted(set(parquet)-set(csv))}"
    )
    assert len(csv) == len(parquet), (
        f"{study}: CSV has {len(csv)} rows, Parquet has {len(parquet)}"
    )
    for name, frame in (("CSV", csv), ("Parquet", parquet)):
        assert not frame[KEY].isna().any().any(), f"{study}: blank {name} keys"
        assert not frame.duplicated(KEY).any(), f"{study}: duplicate {name} keys"
    left = csv.set_index(KEY).sort_index()
    right = parquet.set_index(KEY).sort_index()
    assert left.index.equals(right.index), (
        f"{study}: different market keysets, "
        f"CSV-only={left.index.difference(right.index).tolist()[:5]}, "
        f"Parquet-only={right.index.difference(left.index).tolist()[:5]}"
    )
    for col in sorted(left.columns):
        a = left[col]
        b = right[col]
        blanks_equal = a.isna().to_numpy() == b.isna().to_numpy()
        assert blanks_equal.all(), (
            f"{study}: mismatching missing-value mask in {col}: "
            f"{left.index[~blanks_equal].tolist()[:5]}"
        )
        mask = ~a.isna()
        a, b = a[mask], b[mask]
        if (pd.api.types.is_numeric_dtype(a) and not pd.api.types.is_bool_dtype(a)
                and pd.api.types.is_numeric_dtype(b) and not pd.api.types.is_bool_dtype(b)):
            values_ok = np.isclose(a.to_numpy(dtype=float),
                                   b.to_numpy(dtype=float),
                                   atol=1e-6, rtol=0, equal_nan=False)
        else:
            values_ok = (
                a.astype(str).str.strip().str.casefold().to_numpy()
                == b.astype(str).str.strip().str.casefold().to_numpy()
            )
        assert values_ok.all(), (
            f"{study} {col}: CSV/Parquet disagreement at "
            f"{a.index[~values_ok].tolist()[:5]}, "
            f"CSV={a[~values_ok].astype(str).tolist()[:5]}, "
            f"Parquet={b[~values_ok].astype(str).tolist()[:5]}"
        )


@pytest.mark.parametrize("study", STUDIES)
def test_csv_and_deployed_parquet_match_every_market_field(study):
    csv_file = OUT / f"screen_{study}.csv"
    parquet_file = OUT / f"screen_{study}.parquet"
    assert csv_file.is_file(), f"Missing tracked CSV: {csv_file}"
    assert parquet_file.is_file(), f"Missing tracked Parquet: {parquet_file}"
    _compare(pd.read_csv(csv_file), pd.read_parquet(parquet_file), study)


def test_live_parquet_verdicts_match_generated_canonical_headline():
    headline = yaml.safe_load((OUT / "headline_metrics.yaml").read_text())
    total = 0
    for study in STUDIES:
        df = pd.read_parquet(OUT / f"screen_{study}.parquet")
        expected = headline["studies"][study]
        assert len(df) == expected["n_candidates"], (
            study, len(df), expected["n_candidates"])
        counts = df["verdict"].value_counts()
        for status in ("LAUNCH", "MONITOR", "PASS"):
            assert int(counts.get(status, 0)) == expected[status], (
                study, status, int(counts.get(status, 0)), expected[status])
        for status, key in (("LAUNCH", "launch_markets"),
                            ("MONITOR", "monitor_markets")):
            assert sorted(df.loc[df.verdict == status, "metro_name"]) == sorted(
                expected[key]), (study, status)
        total += len(df)
    assert total == headline["n_candidates_total"], (total, headline["n_candidates_total"])
