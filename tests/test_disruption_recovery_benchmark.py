"""Synthetic optimizer baselines, oracle scope and reproducibility guardrails."""
import pytest
from experiments.disruption_recovery.recovery import optimize, parse_scenario, validate_solution, greedy_baseline
from experiments.disruption_recovery.benchmark import (
    all_cancel_baseline, cost_aware_greedy_baseline,
    scenario, hash_scenario, run_benchmark,
)

def high_delay_cheaper_to_cancel():
    return {
        "tails":[{"id":"A","location":"AAA","available":50}],
        "flights":[{"id":"F1","origin":"AAA","destination":"BBB",
                    "departure":0,"duration":20,"passengers":10,"cancel_cost":15}],
        "turn_minutes":15,"delay_options_minutes":[0,60],
        "delay_cost_per_passenger_minute":.5
    }

def test_cost_aware_cancels_when_operating_penalty_exceeds_cancel_cost():
    data=high_delay_cheaper_to_cancel()
    greedy=greedy_baseline(data)
    aware=cost_aware_greedy_baseline(data)
    assert greedy["objective"]==300
    assert aware["objective"]==15
    assert aware["canceled"]==["F1"]
    assert optimize(data)["objective"]==15

def test_all_cancel_is_feasible_and_has_exact_cost():
    data=scenario(2)
    out=all_cancel_baseline(data)
    flights,tails,turn,delays,_=parse_scenario(data)
    assert validate_solution(flights,tails,out["assignments"],out["canceled"],turn,delays)
    assert out["objective"]==sum(f.cancel_cost for f in flights)

def test_bounded_synthetic_generator_is_deterministic():
    a=scenario(7)
    assert a==scenario(7)
    assert hash_scenario(a)==hash_scenario(scenario(7))
    assert scenario(7)!=scenario(8)
    assert len(a["flights"])==5 and len(a["tails"])==2

def test_cost_aware_greedy_is_feasible_on_multiple_deterministic_cases():
    for ix in range(5):
        data=scenario(ix)
        aware=cost_aware_greedy_baseline(data)
        flights,tails,turn,delays,_=parse_scenario(data)
        assert validate_solution(flights,tails,aware["assignments"],aware["canceled"],turn,delays)

def test_held_benchmark_is_repeatable_and_explicitly_synthetic():
    a=run_benchmark(3)
    b=run_benchmark(3)
    assert a==b
    assert a["synthetic_data"] is True
    assert a["units"].startswith("arbitrary illustrative")
    assert a["sample_count"]==3
    for comparator in ("greedy_fly_first","greedy_cost_aware","all_cancel"):
        assert a["comparisons"][comparator]["milp_worse"]==0
        assert a["comparisons"][comparator]["milp_better"]+a["comparisons"][comparator]["tied"]==3

def test_benchmark_count_is_bounded():
    with pytest.raises(ValueError,match="1-30"):
        run_benchmark(0)
    with pytest.raises(ValueError,match="1-30"):
        run_benchmark(31)
