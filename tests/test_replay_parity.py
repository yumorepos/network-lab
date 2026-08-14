"""Parity: the replay chain must reproduce the shipped model exactly.

`replay/snapshot.py` re-implements the vintage-sensitive queries of the model
chain. That is the same shape of risk that let `models/share_validation.py`
silently measure a different model from the one shipping verdicts (integrity
round 4). The defence is this file: run the replay pinned to the production
vintages and require it to reproduce every committed verdict, market by market,
not merely the counts.

Counts alone hide compensating moves, which is the repository's own standing
rule for change reports and applies with equal force here.
"""
from __future__ import annotations

import pandas as pd
import pytest

from models.common import OUTPUTS, connect
from replay import snapshot as S

STUDIES = ["westjet_yyc", "alaska_sea", "porter_yyz"]


@pytest.fixture(scope="module")
def con():
    c = connect(read_only=True)
    yield c
    c.close()


@pytest.fixture(scope="module")
def replayed(con):
    return {s: S.snapshot(s, None, con) for s in STUDIES}


@pytest.mark.parametrize("study_id", STUDIES)
def test_candidate_set_matches_production(study_id, replayed):
    got = set(replayed[study_id]["candidates"]["cbsa"])
    want = set(pd.read_parquet(OUTPUTS / f"demand_{study_id}.parquet")["cbsa"])
    assert got == want, (
        f"{study_id}: candidate sets differ. "
        f"missing {sorted(want - got)[:5]}, extra {sorted(got - want)[:5]}")


@pytest.mark.parametrize("study_id", STUDIES)
def test_every_verdict_matches_production_market_by_market(study_id, replayed):
    got = replayed[study_id]["screen"][["cbsa", "verdict"]].copy()
    want = pd.read_parquet(OUTPUTS / f"screen_{study_id}.parquet")
    want = want.merge(
        pd.read_parquet(OUTPUTS / f"demand_{study_id}.parquet")[
            ["cbsa", "metro_name"]], on="metro_name", how="left")
    m = got.merge(want[["cbsa", "verdict", "metro_name"]], on="cbsa",
                  suffixes=("_replay", "_prod"))
    assert len(m) == len(want), f"{study_id}: join lost rows"
    bad = m[m["verdict_replay"] != m["verdict_prod"]]
    assert bad.empty, (
        f"{study_id}: {len(bad)} verdicts differ:\n"
        + bad[["metro_name", "verdict_prod", "verdict_replay"]].to_string())


@pytest.mark.parametrize("study_id", STUDIES)
def test_chosen_frequency_matches_production(study_id, replayed):
    """Right-sizing is a primary W1.4 metric, so the replay must reproduce the
    production choice exactly before its historical values mean anything."""
    got = replayed[study_id]["screen"][["cbsa", "chosen_freq_wk"]]
    want = pd.read_parquet(OUTPUTS / f"screen_{study_id}.parquet")
    dem = pd.read_parquet(OUTPUTS / f"demand_{study_id}.parquet")[
        ["cbsa", "metro_name"]]
    want = want.merge(dem, on="metro_name", how="left")
    m = got.merge(want[["cbsa", "chosen_freq_wk"]], on="cbsa",
                  suffixes=("_replay", "_prod"))
    bad = m[m["chosen_freq_wk_replay"] != m["chosen_freq_wk_prod"]]
    assert bad.empty, f"{study_id}: {len(bad)} chosen frequencies differ"


@pytest.mark.parametrize("study_id", STUDIES)
def test_demand_matches_production_within_tolerance(study_id, replayed):
    got = replayed[study_id]["demand"][["cbsa", "demand_pax_yr"]]
    want = pd.read_parquet(OUTPUTS / f"demand_{study_id}.parquet")[
        ["cbsa", "demand_pax_yr"]]
    m = got.merge(want, on="cbsa", suffixes=("_replay", "_prod"))
    rel = ((m["demand_pax_yr_replay"] - m["demand_pax_yr_prod"]).abs()
           / m["demand_pax_yr_prod"].abs().replace(0, pd.NA)).dropna()
    assert (rel < 1e-9).all(), (
        f"{study_id}: max relative demand difference {rel.max():.3e}")


def test_headline_totals_match_the_generated_source_of_truth(replayed):
    """Belt and braces against headline_metrics.yaml itself."""
    import yaml
    hm = yaml.safe_load((OUTPUTS / "headline_metrics.yaml").read_text())
    for study_id in STUDIES:
        counts = replayed[study_id]["screen"]["verdict"].value_counts().to_dict()
        rec = hm["studies"][study_id]
        for verdict in ("LAUNCH", "MONITOR", "PASS"):
            assert counts.get(verdict, 0) == rec[verdict], (
                f"{study_id} {verdict}: replay {counts.get(verdict, 0)} vs "
                f"headline_metrics {rec[verdict]}")
        assert len(replayed[study_id]["screen"]) == rec["n_candidates"]
