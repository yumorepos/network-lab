"""T3 guards: the connection-only share validation.

Protocol: `docs/change_reports/T3_connection_share_validation.md`.

The tests split into three jobs. First, the published check must not have
moved, because T3's whole design depends on adding a second check rather than
loosening the existing one. Second, the strata must partition the sample and
the shares must be shares. Third, the decision rule must map results to
verdicts the way the frozen protocol says, tested on synthetic frames so the
mapping is checked independently of today's data.

Sample sizes are asserted against the declared minimums rather than against
today's counts: the point is that stratum B is evaluable, not that it has
exactly 482 rows.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from models import share_validation as SV
from models import share_validation_strata as T3

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "parquet" / "outputs"


def _need(p: Path):
    if not p.exists():
        pytest.skip(f"{p.name} not built yet; run "
                    "models.share_validation_strata")


@pytest.fixture(scope="module")
def rows():
    p = OUT / "share_validation_strata.parquet"
    _need(p)
    return pd.read_parquet(p)


@pytest.fixture(scope="module")
def strata():
    p = OUT / "share_validation_by_stratum.parquet"
    _need(p)
    return pd.read_parquet(p)


def test_the_published_check_was_not_modified():
    """T3 adds a check. It does not loosen the one whose number is published
    in docs/validation.md and guarded by the consistency tests."""
    assert SV.MIN_PAX == 50_000
    assert SV.HUB == "SEA"
    assert T3.HUB == SV.HUB and T3.YEAR == SV.YEAR
    assert T3.MIN_PAX < SV.MIN_PAX, "the stratified floor must be the lower one"


def test_the_sampling_floor_is_not_a_new_constant():
    """Protocol 0.3: 4,000 is the threshold build_demand already uses for a
    thin us_domestic DB1B market, and fare_curve to admit a market to the fare
    fit. If either moves away from it, this bar was quietly invented."""
    assert T3.MIN_PAX == 4_000
    assert "thin" in (ROOT / "replay" / "snapshot.py").read_text()
    assert "< 4000" in (ROOT / "replay" / "snapshot.py").read_text()
    assert "> 4000" in (ROOT / "models" / "economics.py").read_text()


def test_strata_partition_the_sample(rows):
    assert set(rows["stratum"]) <= set(T3.STRATA)
    assert rows["stratum"].nunique() == len(T3.STRATA)
    # the definitions must be mutually exclusive by construction
    c = rows[rows["stratum"] == T3.STRATA[2]]
    assert (c["n_modeled_carriers"] == 1).all()
    a = rows[rows["stratum"] == T3.STRATA[0]]
    assert (a["n_nonstop_carriers"] > 0).all()
    assert (a["n_modeled_carriers"] > 1).all()
    b = rows[rows["stratum"] == T3.STRATA[1]]
    assert (b["n_nonstop_carriers"] == 0).all()
    assert (b["n_modeled_carriers"] > 1).all()


def test_modelled_and_null_shares_are_shares(rows):
    """A share model whose shares do not sum to one is attributing traffic to
    carriers the truth source does not report. This is the invariant that
    exposed the operating-versus-marketing carrier defect in Round 3."""
    for col in ("model_share", "null_share"):
        assert (rows[col] >= 0).all() and (rows[col] <= 1 + 1e-9).all()
    per_market = rows.groupby("other_cm")[["model_share", "null_share"]].sum()
    # DB1B may not report every carrier the model finds, so the sums are at
    # most one and should be close to it.
    assert (per_market <= 1 + 1e-9).all().all()
    assert per_market["model_share"].mean() > 0.9, (
        f"modelled shares sum to {per_market['model_share'].mean():.3f} per "
        "market on average; the brand resolution has regressed")


def test_stratum_b_is_evaluable(strata):
    """The gap T3 exists to close. Asserted against the declared minimums, not
    against today's counts."""
    b = strata[strata["stratum"] == T3.STRATA[1]].iloc[0]
    assert b["rows"] >= T3.MIN_ROWS, (
        f"stratum B has {b['rows']} rows, below the declared {T3.MIN_ROWS}")
    assert b["markets"] >= T3.MIN_MARKETS, (
        f"stratum B has {b['markets']} markets, below the declared "
        f"{T3.MIN_MARKETS}")


def test_stratum_b_is_the_regime_the_flagship_study_occupies(strata):
    """If stratum B ever stops being a large share of the panel, the sampling
    floor has drifted back towards the regime the old check already covered."""
    b = strata[strata["stratum"] == T3.STRATA[1]].iloc[0]
    assert b["markets"] > strata["markets"].sum() * 0.25


def test_the_null_is_an_equal_split_among_modelled_carriers(rows):
    live = rows[rows["null_share"] > 0]
    assert np.allclose(live["null_share"], 1.0 / live["n_modeled_carriers"])


def test_verdict_rule_matches_the_frozen_protocol():
    """Protocol 0.7, on synthetic frames, so the mapping is tested apart from
    today's numbers."""
    def frame(rows_, markets, mae, null_mae, rho):
        return pd.DataFrame([{"stratum": T3.STRATA[1], "rows": rows_,
                              "markets": markets, "mae": mae,
                              "null_mae": null_mae,
                              "beats_null": mae < null_mae,
                              "spearman": rho, "spearman_p": 0.01}])

    v, _ = T3.verdict(frame(T3.MIN_ROWS - 1, 50, 5.0, 9.0, 0.8))
    assert v == T3.VERDICTS[3], "too few rows must be INSUFFICIENT"
    v, _ = T3.verdict(frame(500, T3.MIN_MARKETS - 1, 5.0, 9.0, 0.8))
    assert v == T3.VERDICTS[3], "too few markets must be INSUFFICIENT"
    v, _ = T3.verdict(frame(500, 50, 5.0, 9.0, 0.8))
    assert v == T3.VERDICTS[0], "beating the null must be VALIDATED"
    v, _ = T3.verdict(frame(500, 50, 9.5, 9.0, 0.8))
    assert v == T3.VERDICTS[1], "losing to the null but rank-correlated is USABLE"
    v, _ = T3.verdict(frame(500, 50, 9.5, 9.0, -0.1))
    assert v == T3.VERDICTS[2], "neither must be NOT VALIDATED"


def test_published_verdict_matches_the_stored_strata(strata):
    v, reasons = T3.verdict(strata)
    assert v in T3.VERDICTS and reasons
    report = (ROOT / "docs" / "change_reports"
              / "T3_connection_share_validation.md")
    _need(report)
    text = report.read_text()
    assert v in text, f"the change report does not carry the verdict {v!r}"


def test_no_model_parameter_was_touched():
    """Validation only. The protocol names exactly what may not move."""
    from models.common import assumptions
    a = assumptions()
    assert float(a["qsi_weights"]["frequency_exponent"]) == 0.6
    assert float(a["qsi_elapsed_time_exponent"]["value"]) == -1.5
    assert float(a["qsi_weights"]["single_connect"]) == 0.20
    comp = (ROOT / "models" / "competition.py").read_text()
    assert "DETOUR_MAX = 2.0" in comp
    assert "DETOUR_ABS_MI = 700" in comp
    assert "MIN_SEGMENT_DEPS_YR = 26" in comp
    assert T3.SHARE_UNCERTAINTY_LIMIT == 0.70
    assert "proposed_share\"] > 0.70" in (ROOT / "models" / "screen.py").read_text()
