"""Scaling audit: no production-savings or uncapped-runtime claims."""
from __future__ import annotations

from copy import deepcopy
import math

import pytest

from experiments.disruption_recovery.benchmark import (
    cost_aware_greedy_baseline, hash_scenario, scenario,
)
from experiments.disruption_recovery.recovery import (
    PathLimitExceeded, optimize, parse_scenario, validate_solution,
)
from experiments.disruption_recovery.scalability import (
    benchmark, calculate_objective, run_isolated, scaled_scenario,
)


def tiny_overtaking():
    return {
        "tails": [{"id": "A", "location": "AAA", "available": 0}],
        "flights": [
            {"id": "F1", "origin": "AAA", "destination": "BBB", "departure": 0,
             "duration": 30, "passengers": 1, "cancel_cost": 1000},
            {"id": "F2", "origin": "AAA", "destination": "CCC", "departure": 20,
             "duration": 30, "passengers": 1, "cancel_cost": 1000},
            {"id": "F3", "origin": "CCC", "destination": "AAA", "departure": 60,
             "duration": 30, "passengers": 1, "cancel_cost": 1000},
        ],
        "turn_minutes": 0, "delay_options_minutes": [0, 120],
        "delay_cost_per_passenger_minute": 0.1,
    }


def test_existing_three_flight_optimum_and_default_contract_unchanged():
    data = tiny_overtaking()
    before = deepcopy(data)
    old = optimize(data)
    new = optimize(data, profile=True, total_time_limit=10)
    assert data == before
    assert old["objective"] == new["objective"] == 12.0
    assert old["assignments"] == new["assignments"]
    assert old["canceled"] == new["canceled"] == []
    assert "timing_seconds" not in old
    assert new["paths_considered"] == sum(new["paths_by_tail"].values())
    phases = new["timing_seconds"]
    assert all(math.isfinite(v) and v >= 0 for v in phases.values())
    assert phases["total"] == pytest.approx(sum(v for k, v in phases.items() if k != "total"))
    assert calculate_objective(data, new) == pytest.approx(new["objective_raw"])
    assert new["savings_vs_fly_first_greedy"] == new["savings_vs_greedy"]


def test_existing_five_flight_scenarios_are_identical_under_scale_generator():
    for index in (0, 1, 2):
        assert scaled_scenario(index, 5) == scenario(index)
        assert hash_scenario(scaled_scenario(index, 5)) == hash_scenario(scenario(index))


def test_extended_scenarios_are_deterministic_and_valid():
    for n in (8, 11, 14):
        for topology in ("connected", "distributed"):
            a = scaled_scenario(1, n, topology=topology)
            b = scaled_scenario(1, n, topology=topology)
            assert hash_scenario(a) == hash_scenario(b)
            assert a["flights"][:5] == scenario(1)["flights"]
            assert len(a["flights"]) == n
            assert len({f["id"] for f in a["flights"]}) == n
            assert len(parse_scenario(a)[0]) == n
            baseline = cost_aware_greedy_baseline(a)
            assert calculate_objective(a, baseline) == pytest.approx(baseline["objective_raw"])


def test_optional_topology_tail_and_delay_axes():
    data = scaled_scenario(0, 8, topology="distributed", tails=3, delay_choices=3)
    assert len(data["tails"]) == 3
    assert data["delay_options_minutes"] == [0, 30, 90]
    assert len(data["flights"]) == 8
    parse_scenario(data)


def test_path_cap_fails_closed_without_truncated_optimum():
    with pytest.raises(PathLimitExceeded) as err:
        optimize(tiny_overtaking(), max_paths_per_tail=1)
    assert err.value.paths_generated == 2
    assert err.value.tail_id == "A"


def test_total_budget_and_resource_limit_validation():
    for kwargs in ({"total_time_limit": 0}, {"total_time_limit": -1},
                   {"total_time_limit": float("nan")}, {"max_paths_per_tail": 0},
                   {"max_paths_per_tail": 1.5}, {"time_limit": 0}):
        with pytest.raises(ValueError):
            optimize(tiny_overtaking(), **kwargs)
    with pytest.raises(ValueError):
        run_isolated(tiny_overtaking(), wall_seconds=31)
    with pytest.raises(ValueError):
        run_isolated(tiny_overtaking(), path_cap=0)


def test_hard_deadline_terminates_worker_without_optimality_claim():
    output = run_isolated(tiny_overtaking(), wall_seconds=0.001)
    assert output["status"] == "HARD_TIMEOUT"
    assert "milp_objective" not in output


def test_path_cap_worker_status_is_censored():
    result = run_isolated(tiny_overtaking(), path_cap=1, wall_seconds=10)
    assert result["status"] == "PATH_CAP"
    assert result["partial_paths"] == 2
    assert "milp_objective" not in result


def test_exact_worker_matches_cost_aware_on_same_synthetic_scenario():
    data = scaled_scenario(0, 5)
    result = run_isolated(data, wall_seconds=10)
    assert result["status"] == "OPTIMAL"
    assert result["path_count"] > 0
    assert result["milp_objective"] <= result["baseline_objective"] + 1e-6
    assert result["peak_process_rss_mib"] > 0
    assert result["timing_seconds"]["solve"] >= 0


def test_benchmark_aggregation_never_counts_censored_as_solved():
    report = benchmark(cases=1, sizes=(5,), wall_seconds=10, path_cap=1)
    assert report["generator"] == "recovery-scaling-v1"
    assert len(report["cases"]) == 1
    assert report["cases"][0]["status"] == "PATH_CAP"
    assert report["summary"][0]["optimal_count"] == 0
    assert report["summary"][0]["median_total_solver_pipeline_seconds_on_optimal_only"] is None


def test_invalid_generator_inputs_rejected():
    for kwargs in ({"n_flights": 4}, {"n_flights": 15}, {"n_flights": 8, "tails": 4},
                   {"n_flights": 8, "delay_choices": 1},
                   {"n_flights": 8, "topology": "wrong"}):
        with pytest.raises(ValueError):
            scaled_scenario(0, **kwargs)
    with pytest.raises(ValueError):
        benchmark(cases=0)
    with pytest.raises(ValueError):
        benchmark(sizes=(5, 5))
