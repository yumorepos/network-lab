"""Independent tests for exact completed-column pruning (no partial-state pruning)."""
from __future__ import annotations

from itertools import permutations, product
import math

import pytest

from experiments.disruption_recovery.benchmark import (
    run_benchmark, scenario,
)
from experiments.disruption_recovery.column_dominance import run_study
from experiments.disruption_recovery.recovery import (
    PathExplorationLimitExceeded, PathLimitExceeded, enumerate_paths,
    optimize, parse_scenario, validate_solution,
)
from experiments.disruption_recovery.scalability import run_isolated, scaled_scenario


def overtaking_case():
    return {
        "tails": [{"id": "T", "location": "AAA", "available": 0}],
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


def independent_single_tail_oracle(data):
    """Explicit permutation + delay product, not path enumeration or MILP."""
    flights, tails, turn, delays, price = parse_scenario(data)
    assert len(tails) == 1 and len(flights) <= 4
    best = math.inf
    for n in range(len(flights) + 1):
        for order in permutations(flights, n):
            canceled = list({f.id for f in flights} - {f.id for f in order})
            for shifts in product(delays, repeat=n):
                paths = {tails[0].id: [(f.id, d) for f, d in zip(order, shifts)]}
                if not validate_solution(flights, tails, paths, canceled, turn, delays):
                    continue
                cost = sum(f.cancel_cost for f in flights if f.id in canceled)
                cost += sum(price * f.passengers * d for f, d in zip(order, shifts))
                best = min(best, cost)
    return best


def test_complete_columns_keep_cheapest_per_flight_set():
    data = scaled_scenario(0, 5)
    flights, tails, turn, delays, price = parse_scenario(data)
    raw = enumerate_paths(flights, tails[0], turn, delays, price, max_paths=100000)
    stats = {}
    kept = enumerate_paths(flights, tails[0], turn, delays, price,
                           max_paths=100000, prune_dominated_columns=True,
                           stats=stats)
    def key(path):
        return frozenset(fid for fid, _ in path)
    best = {}
    for path, cost in raw:
        best[key(path)] = min(best.get(key(path), math.inf), cost)
    actual = {key(path): cost for path, cost in kept}
    assert actual == best
    assert stats["explored"] == len(raw)
    assert stats["retained"] == len(kept)
    assert stats["discarded"] == len(raw) - len(kept) > 0
    assert len(actual) == len(kept)
    assert stats["cheaper_replacements"] >= 0


def test_overtaking_counterexample_retains_independently_verified_optimum():
    data = overtaking_case()
    original = optimize(data)
    reduced = optimize(data, prune_dominated_columns=True, profile=True)
    assert original["objective"] == reduced["objective"] == 12
    assert reduced["objective_raw"] == independent_single_tail_oracle(data)
    assert set(reduced["assignments"]["T"]) == {
        ("F1", 120), ("F2", 0), ("F3", 0)}
    assert reduced["paths_considered"] <= original["paths_considered"]


def test_independent_four_flight_permutation_oracle():
    data = {
        "tails": [{"id": "T", "location": "AAA", "available": 0}],
        "flights": [
            {"id": "A", "origin": "AAA", "destination": "BBB", "departure": 0,
             "duration": 10, "passengers": 2, "cancel_cost": 100},
            {"id": "B", "origin": "BBB", "destination": "AAA", "departure": 20,
             "duration": 10, "passengers": 3, "cancel_cost": 70},
            {"id": "C", "origin": "AAA", "destination": "BBB", "departure": 30,
             "duration": 15, "passengers": 5, "cancel_cost": 110},
            {"id": "D", "origin": "BBB", "destination": "AAA", "departure": 40,
             "duration": 10, "passengers": 2, "cancel_cost": 90},
        ],
        "turn_minutes": 5, "delay_options_minutes": [0, 15, 30],
        "delay_cost_per_passenger_minute": 0.3,
    }
    reference = independent_single_tail_oracle(data)
    for prune in (False, True):
        answer = optimize(data, prune_dominated_columns=prune, profile=True)
        assert answer["objective_raw"] == pytest.approx(reference)
        assert answer["raw_paths_explored"] >= answer["paths_considered"]


@pytest.mark.parametrize("n,topology", [
    (5, "connected"), (8, "connected"), (8, "distributed"),
    (11, "distributed"),
])
def test_seeded_scaling_objective_parity(n, topology):
    data = scaled_scenario(0, n, topology=topology)
    baseline = optimize(data, profile=True, total_time_limit=10,
                        max_paths_per_tail=20000)
    pruned = optimize(data, profile=True, total_time_limit=10,
                      max_paths_per_tail=20000,
                      prune_dominated_columns=True)
    assert baseline["objective_raw"] == pytest.approx(pruned["objective_raw"])
    assert pruned["paths_considered"] <= baseline["paths_considered"]
    assert pruned["raw_paths_explored"] == baseline["raw_paths_explored"]
    assert pruned["timing_seconds"]["total"] >= 0


def test_reference_generator_keeps_original_thirty_case_results():
    # Primary baseline is intentionally untouched by opt-in pruning.
    report = run_benchmark()
    assert report["summary"]["milp"]["mean_objective"] == 413.62
    assert report["summary"]["greedy_cost_aware"]["mean_objective"] == 503.67
    assert report["comparisons"]["greedy_cost_aware"]["milp_better"] == 12
    assert report["comparisons"]["greedy_cost_aware"]["tied"] == 18


def test_raw_search_cap_and_retained_column_cap_are_distinct():
    data = scaled_scenario(0, 5)
    with pytest.raises(PathExplorationLimitExceeded) as caught:
        optimize(data, prune_dominated_columns=True,
                 max_explored_states_per_tail=1)
    assert caught.value.explored == 2
    with pytest.raises(PathLimitExceeded):
        optimize(data, prune_dominated_columns=True, max_paths_per_tail=1)
    output = run_isolated(data, wall_seconds=10,
                          prune_columns=True, raw_visit_cap=1)
    assert output["status"] == "RAW_VISIT_CAP"
    assert "milp_objective" not in output


def test_pruning_argument_and_budget_validation():
    data = overtaking_case()
    with pytest.raises(ValueError):
        optimize(data, prune_dominated_columns="yes")
    with pytest.raises(ValueError):
        optimize(data, prune_dominated_columns=True,
                 max_explored_states_per_tail=0)
    with pytest.raises(ValueError):
        run_isolated(data, prune_columns=True, raw_visit_cap=0)


def test_paired_study_reports_objective_parity_and_censored_cases():
    grid = ((5, "connected", 0),)
    result = run_study(grid=grid, wall_seconds=10)
    assert result["summary"]["both_certified_objective_equal"] == 1
    assert result["rows"][0]["objective_parity_checked"]
    assert result["rows"][0]["original"]["status"] == "OPTIMAL"
    assert result["rows"][0]["pruned"]["status"] == "OPTIMAL"


def test_paired_study_does_not_claim_parity_when_both_are_capped():
    result = run_study(grid=((5, "connected", 0),),
                       path_cap=1, wall_seconds=10)
    assert result["summary"]["both_certified_objective_equal"] == 0
    assert not result["rows"][0]["objective_parity_checked"]
    assert "milp_objective" not in result["rows"][0]["pruned"]


def test_later_cheaper_order_replaces_earlier_expensive_column():
    # Same three-flight coverage via two *different actual departure orders*.
    # DFS first finds F1→F3→F2 (F2 incurs large delay), then F2→F3→F1
    # (only F1 incurs a small passenger-weighted delay). The latter must win.
    data = {
        "tails": [{"id": "T", "location": "AAA", "available": 0}],
        "flights": [
            {"id": "F1", "origin": "AAA", "destination": "BBB",
             "departure": 0, "duration": 10, "passengers": 1,
             "cancel_cost": 10000},
            {"id": "F2", "origin": "AAA", "destination": "BBB",
             "departure": 20, "duration": 10, "passengers": 100,
             "cancel_cost": 10000},
            {"id": "F3", "origin": "BBB", "destination": "AAA",
             "departure": 40, "duration": 10, "passengers": 1,
             "cancel_cost": 10000},
        ],
        "turn_minutes": 0, "delay_options_minutes": [0, 30, 60],
        "delay_cost_per_passenger_minute": 1.0,
    }
    flights, tails, turn, delays, price = parse_scenario(data)
    control = enumerate_paths(flights, tails[0], turn, delays, price)
    stats = {}
    reduced = enumerate_paths(flights, tails[0], turn, delays, price,
                              prune_dominated_columns=True, stats=stats)
    covered_all = frozenset({"F1", "F2", "F3"})
    costs = [cost for path, cost in control
             if frozenset(fid for fid, _ in path) == covered_all]
    kept = [cost for path, cost in reduced
            if frozenset(fid for fid, _ in path) == covered_all]
    assert len(costs) > 1 and kept == [min(costs)] == [60.0]
    assert stats["cheaper_replacements"] > 0
    assert optimize(data)["objective"] == optimize(
        data, prune_dominated_columns=True)["objective"] == 60.0


@pytest.mark.parametrize("index", range(30))
def test_all_frozen_five_flight_baseline_objectives_preserved_by_pruning(index):
    data = scenario(index)
    full = optimize(data)
    pruned = optimize(data, prune_dominated_columns=True, profile=True)
    assert pruned["objective"] == full["objective"]
    assert pruned["paths_considered"] <= full["paths_considered"]
