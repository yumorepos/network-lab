"""Headline numbers must be identical everywhere they appear. This test reads
the canonical values from the computed artifacts and fails if any
reader-facing doc drifts."""
from pathlib import Path

import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "parquet" / "outputs"


def _need(p):
    if not p.exists():
        pytest.skip(f"{p.name} not built yet")


def test_transfer_median_consistent():
    _need(OUT / "transfer_factor.yaml")
    tf = yaml.safe_load((OUT / "transfer_factor.yaml").read_text())
    canon = f"median {tf['median']:.2f}"
    for f in ("README.md", "docs/validation.md", "docs/interview_story.md"):
        assert canon in (ROOT / f).read_text(), f"{f} lacks '{canon}'"


def test_share_mae_consistent():
    _need(OUT / "share_validation.parquet")
    sv = pd.read_parquet(OUT / "share_validation.parquet")
    canon = f"{100 * sv['abs_err'].mean():.1f} share"
    for f in ("README.md", "docs/validation.md", "docs/interview_story.md",
              "docs/resume_material.md", "reports/alaska_sea_validation.md"):
        assert canon in (ROOT / f).read_text(), f"{f} lacks '{canon}'"


def test_backtest_n_consistent():
    _need(OUT / "backtest_scores.parquet")
    df = pd.read_parquet(OUT / "backtest_scores.parquet").dropna(
        subset=["pctile"])
    n = int(df["outcome"].isin(["operating", "ceased"]).sum())
    assert f"N = {n}" in (ROOT / "docs" / "backtest.md").read_text()
    for f in ("README.md", "docs/interview_story.md",
              "docs/resume_material.md"):
        assert f"{n} " in (ROOT / f).read_text(), f"{f} lacks N={n}"


def test_gravity_counts_labeled_by_vintage():
    _need(OUT / "gravity_pre2022.yaml")
    pre = yaml.safe_load((OUT / "gravity_pre2022.yaml").read_text())
    cur = yaml.safe_load((OUT / "gravity_current.yaml").read_text())
    v = (ROOT / "docs" / "validation.md").read_text()
    assert f"markets: {pre['n_markets']}" in v
    assert f"markets: {cur['n_markets']}" in v
    # docs must never blend the two counts into one unlabeled number
    readme = (ROOT / "README.md").read_text()
    assert f"{pre['n_markets']:,}" in readme
