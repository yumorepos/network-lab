"""Phase 6A: Poisson QMLE gravity estimator.

Guards four things: the new estimator is deterministic, its calibration metric
is computed correctly, the frozen Version 1 baseline is untouched, and the new
artifacts are covered by the reproducibility gate.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

WAREHOUSE = Path("data/warehouse.duckdb")
OUTPUTS = Path("data/parquet/outputs")


def _need_warehouse():
    if not WAREHOUSE.exists():
        pytest.skip("warehouse not built")


def test_estimator_registry_and_default():
    """The default must remain the frozen baseline. Phase 6A ships Poisson as
    selectable; flipping the default is a separate, evidence-gated decision
    with its own change report."""
    from models import gravity, gravity_log_ols, gravity_poisson
    assert set(gravity.ESTIMATORS) == {gravity_log_ols.NAME, gravity_poisson.NAME}
    assert gravity.DEFAULT_ESTIMATOR == gravity_log_ols.NAME, (
        "the default gravity estimator moved off the frozen baseline; if that "
        "is intended it needs a change report and a new baseline freeze")


def test_poisson_predictions_are_deterministic():
    """Same inputs, same coefficients, same output. Poisson is fitted by IRLS,
    which is deterministic, but predict() must not introduce any state."""
    _need_warehouse()
    from models import gravity, gravity_poisson
    if not (OUTPUTS / "gravity_current_poisson.yaml").exists():
        pytest.skip("poisson artifact not built")
    pairs = pd.DataFrame({
        "pop_a": [2_000_000.0, 500_000.0, 8_000_000.0],
        "pop_b": [1_000_000.0, 900_000.0, 3_000_000.0],
        "inc_a": [55_000.0, 48_000.0, 70_000.0],
        "inc_b": [52_000.0, 51_000.0, 61_000.0],
        "dist_mi": [500.0, 1200.0, 2400.0]})
    a = gravity.predict(pairs, "current", estimator=gravity_poisson.NAME)
    b = gravity.predict(pairs, "current", estimator=gravity_poisson.NAME)
    assert np.array_equal(a, b)
    assert np.all(np.isfinite(a)) and np.all(a > 0)


def test_poisson_targets_the_mean_not_the_median():
    """The defect Phase 6A exists to fix. On the fitted frame the Poisson score
    equations force sum(fitted) == sum(observed) with a constant in the design,
    so aggregate calibration must be far closer to 1.0 than log-OLS."""
    _need_warehouse()
    from models import gravity, gravity_log_ols, gravity_poisson
    from models.common import connect
    for p in ("gravity_current.yaml", "gravity_current_poisson.yaml"):
        if not (OUTPUTS / p).exists():
            pytest.skip("gravity artifacts not built")
    con = connect(read_only=True)
    df = gravity.build_market_frame(con, gravity.VINTAGE_YEARS["current"])
    con.close()
    obs = df["pax_yr"].to_numpy(dtype=float)
    agg = {}
    for est in (gravity_log_ols.NAME, gravity_poisson.NAME):
        agg[est] = gravity.predict(df, "current", estimator=est).sum() / obs.sum()
    assert agg[gravity_log_ols.NAME] < 0.6, (
        "the log-OLS baseline is expected to under-recover total passengers "
        f"(measured {agg[gravity_log_ols.NAME]:.3f}); if this improved, the "
        "Phase 6A motivation needs rechecking")
    assert 0.85 < agg[gravity_poisson.NAME] < 1.15, (
        f"Poisson aggregate pred/obs is {agg[gravity_poisson.NAME]:.3f}, "
        "outside the calibrated band; the mean-targeting property is broken")
    assert agg[gravity_poisson.NAME] > agg[gravity_log_ols.NAME]


def test_poisson_reports_robust_covariance_and_dispersion():
    """At Pearson chi2/df in the hundreds of thousands the naive Poisson
    standard errors are invalid. The artifact must record that robust
    covariance was used and must expose the dispersion that makes it
    necessary."""
    _need_warehouse()
    import yaml
    p = OUTPUTS / "gravity_current_poisson.yaml"
    if not p.exists():
        pytest.skip("poisson artifact not built")
    g = yaml.safe_load(p.read_text())
    pred = g["predict"]
    assert pred["cov_type"] == "HC1", "robust covariance is mandatory here"
    assert "robust_se" in pred and pred["robust_se"]
    assert "r2" not in pred, "a GLM must not report an OLS R2"
    disp = pred["dispersion_pearson_chi2_over_df"]
    assert disp > 100, (
        f"dispersion {disp:.1f} is near 1, which would mean the data really is "
        "Poisson and the robust-covariance rationale no longer holds")
    assert pred["converged"] is True


def test_aggregate_calibration_metric_is_computed_correctly():
    """Guard the metric itself, on data with a known answer, so a bug in the
    comparison framework cannot masquerade as a modelling result."""
    from scripts.phase6a_compare import metrics
    obs = np.array([100.0, 200.0, 300.0, 400.0])
    pred = np.array([50.0, 100.0, 150.0, 200.0])       # exactly half
    m = metrics(obs, pred)
    assert m["aggregate_pred_over_obs"] == pytest.approx(0.5)
    assert m["mape"] == pytest.approx(0.5)
    assert m["median_ape"] == pytest.approx(0.5)
    assert m["rmse"] == pytest.approx(np.sqrt(np.mean((pred - obs) ** 2)))
    assert m["log_resid_mean"] == pytest.approx(np.log(2.0))
    perfect = metrics(obs, obs.copy())
    assert perfect["aggregate_pred_over_obs"] == pytest.approx(1.0)
    assert perfect["rmse"] == pytest.approx(0.0)
    assert perfect["log_resid_sd"] == pytest.approx(0.0)


def test_frozen_baseline_artifacts_are_unchanged():
    """The W1.4 baseline must survive Phase 6A untouched. The log_ols artifact
    keeps its original unsuffixed filename and its original contents."""
    _need_warehouse()
    import yaml
    for vintage, expect_r2 in (("current", 0.4924), ("pre2022", 0.5093)):
        p = OUTPUTS / f"gravity_{vintage}.yaml"
        if not p.exists():
            pytest.skip("gravity artifacts not built")
        g = yaml.safe_load(p.read_text())
        assert "estimator" not in g, (
            f"gravity_{vintage}.yaml gained an estimator key; the baseline "
            "artifact format changed")
        assert g["predict"]["r2"] == pytest.approx(expect_r2, abs=5e-4), (
            f"frozen baseline R2 for {vintage} moved to "
            f"{g['predict']['r2']:.4f}; the log-OLS path is not supposed to "
            "change in Phase 6A")
        assert set(g["predict"]["params"]) == {
            "const", "ln_pop_product", "ln_income_product", "ln_dist",
            "ln_dist_sq"}


def test_poisson_artifacts_are_covered_by_the_reproducibility_gate():
    """New artifacts must be inside the gate, otherwise a non-deterministic
    estimator could ship unnoticed. The gate globs the outputs directory, so
    this asserts the files land there and are readable by it."""
    _need_warehouse()
    from scripts.check_reproducible import _compare_frame  # noqa: F401
    import yaml
    found = sorted(p.name for p in OUTPUTS.glob("gravity_*_poisson.yaml"))
    if not found:
        pytest.skip("poisson artifacts not built")
    assert found == ["gravity_current_poisson.yaml",
                     "gravity_pre2022_poisson.yaml"]
    for name in found:
        g = yaml.safe_load((OUTPUTS / name).read_text())
        assert g["estimator"] == "poisson_qmle"
        assert "aggregate_pred_over_obs" in g["holdout"]
