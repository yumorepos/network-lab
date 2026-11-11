"""Scenario perturbations remain fixed-seed, bounded, and fully synthetic."""
from experiments.disruption_recovery.benchmark import scenario,hash_scenario
from experiments.disruption_recovery.sensitivity import VARIANTS,changed,benchmark
import pytest

def test_reference_is_identical_to_existing_scenario():
    data=scenario(0)
    original=changed(data,VARIANTS[0])
    assert data==original
    assert hash_scenario(data)==hash_scenario(original)

def test_variant_changes_are_isolated_and_do_not_mutate_source():
    base=scenario(1)
    previous=hash_scenario(base)
    half=changed(base,VARIANTS[1])
    twice=changed(base,VARIANTS[2])
    longer=changed(base,VARIANTS[3])
    high_cancel=changed(base,VARIANTS[4])
    assert half["delay_cost_per_passenger_minute"]==base["delay_cost_per_passenger_minute"]*.5
    assert twice["delay_cost_per_passenger_minute"]==base["delay_cost_per_passenger_minute"]*2
    assert longer["turn_minutes"]==base["turn_minutes"]+20
    assert high_cancel["flights"][0]["cancel_cost"]==2*base["flights"][0]["cancel_cost"]
    assert hash_scenario(base)==previous

def test_small_sensitivity_benchmark_is_reproducible_and_noncausal():
    first=benchmark(2)
    assert first==benchmark(2)
    assert first["synthetic_data"] is True
    assert len(first["variants"])==len(VARIANTS)
    for variant in first["variants"]:
        assert variant["milp_better"]+variant["tied"]==2
        assert variant["milp_worse"]==0
        assert len(variant["rows"])==2
    assert "not dollars or airline savings" in first["units"]

def test_bounded_case_count_and_finite_input_set():
    with pytest.raises(ValueError,match="1-30"):
        benchmark(0)
    with pytest.raises(ValueError,match="1-30"):
        benchmark(31)
