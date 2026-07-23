"""Sanity tests: the handful that guard correctness-critical logic."""
import numpy as np
import pytest

from models import spill
from models.common import haversine_mi


def test_spill_unconstrained_recovers_mean():
    assert spill.expected_boardings(100, 10_000, cov=0.3) == pytest.approx(100, rel=1e-6)


def test_spill_never_exceeds_capacity_or_demand():
    for mu in (50, 150, 200):
        e = spill.expected_boardings(mu, 174, cov=0.3)
        assert e <= 174 + 1e-9
        assert e <= mu + 1e-9
        assert e > 0


def test_spill_monotone_in_capacity():
    vals = [spill.expected_boardings(150, c, cov=0.3) for c in (100, 140, 180)]
    assert vals == sorted(vals)


def test_haversine_known_distance():
    # YYC to LAX, great-circle roughly 1200 statute miles
    d = haversine_mi(51.1139, -114.0203, 33.9425, -118.4081)
    assert 1150 < d < 1260


def test_gravity_predict_refuses_missing_columns():
    import pandas as pd
    from models import gravity
    with pytest.raises((KeyError, FileNotFoundError)):
        gravity.predict(pd.DataFrame({"pop_a": [1]}), "pre2022")


def test_no_screened_market_is_already_served():
    """A LAUNCH/MONITOR/PASS row must never name a metro the study carrier
    already serves nonstop from the hub. Cross-checks the screen against the
    hand-auditable incumbent-network reference file. This would have caught the
    original candidate-filter leak (New York appeared as a Porter LAUNCH before
    the metro-level fix)."""
    from pathlib import Path
    import pandas as pd
    inc_path = Path("data/reference/incumbent_network_202604.csv")
    inc = pd.read_csv(inc_path)
    for sid in ("westjet_yyc", "alaska_sea", "porter_yyz"):
        p = Path(f"data/parquet/outputs/screen_{sid}.parquet")
        if not p.exists():
            pytest.skip(f"screen_{sid} not built yet")
        scr = pd.read_parquet(p)
        served = set(inc[inc["study_id"] == sid]["dest_metro_name"])
        overlap = set(scr["metro_name"]) & served
        assert not overlap, (
            f"{sid}: screened markets already served by the carrier: {overlap}")
        launched = set(scr[scr["verdict"] == "LAUNCH"]["metro_name"]) & served
        assert not launched, f"{sid}: LAUNCH on already-served market: {launched}"


def test_no_transborder_fare_from_db1b():
    """DB1B is US domestic only; the demand module must never mark a
    transborder market as having an observed fare."""
    from pathlib import Path
    import pandas as pd
    p = Path("data/parquet/outputs/demand_westjet_yyc.parquet")
    if not p.exists():
        pytest.skip("demand outputs not built yet")
    df = pd.read_parquet(p)
    assert df["fare_observed"].isna().all()
    assert (df["demand_source"] == "modeled").all()
