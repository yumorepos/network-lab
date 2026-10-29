"""Independent tiny-schedule oracle for the separate recovery experiment."""
import itertools

import pytest

from experiments.disruption_recovery.recovery import (
    optimize, parse_scenario, validate_solution,
)


def overtaking_case(delays=(0, 120)):
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
        "turn_minutes": 0, "delay_options_minutes": list(delays),
        "delay_cost_per_passenger_minute": 0.1,
    }


def permutation_oracle(data):
    """Enumerate flight permutations independently of the MILP path code."""
    flights, tails, turn, delays, price = parse_scenario(data)
    assert len(tails) == 1
    best = float("inf")
    for size in range(len(flights) + 1):
        for picked in itertools.permutations(flights, size):
            canceled = set(f.id for f in flights) - set(f.id for f in picked)
            for shifts in itertools.product(delays, repeat=size):
                assigned = {tails[0].id: [
                    (f.id, shift) for f, shift in zip(picked, shifts)
                ]}
                if not validate_solution(flights, tails, assigned, canceled, turn, delays):
                    continue
                cost = (sum(f.cancel_cost for f in flights if f.id in canceled)
                    + sum(price * f.passengers * shift
                          for f, shift in zip(picked, shifts)))
                best = min(best, cost)
    return best


def test_delayed_early_flight_operates_after_later_departures():
    data = overtaking_case()
    result = optimize(data)
    assert result["objective"] == 12.0
    assert result["canceled"] == []
    assert result["assignments"]["A"] == [
        ("F2", 0), ("F3", 0), ("F1", 120)
    ]
    assert result["objective"] == permutation_oracle(data)


def test_with_no_long_delay_cancelation_is_correct():
    data = overtaking_case((0, 30))
    result = optimize(data)
    assert result["objective"] == permutation_oracle(data)
    assert len(result["canceled"]) == 1


def test_reject_nonfinite_cost():
    data = overtaking_case()
    data["flights"][0]["cancel_cost"] = float("nan")
    with pytest.raises(ValueError, match="flight"):
        optimize(data)


def test_validator_rejects_ghost_tail_and_duplicate_cancellations():
    flights, tails, turn, delays, _ = parse_scenario(overtaking_case())
    assert not validate_solution(flights, tails,
                                 {"A": [], "GHOST": []},
                                 ["F1", "F2", "F3"], turn, delays)
    assert not validate_solution(flights, tails,
                                 {"A": []}, ["F1", "F1", "F2", "F3"],
                                 turn, delays)


def test_small_two_tail_schedule_has_zero_cancellations():
    data = {"tails": [
        {"id": "T1", "location": "AAA", "available": 0},
        {"id": "T2", "location": "BBB", "available": 0}],
        "flights": [
            {"id": "X", "origin": "AAA", "destination": "BBB",
             "departure": 0, "duration": 20, "passengers": 10, "cancel_cost": 100},
            {"id": "Y", "origin": "BBB", "destination": "AAA",
             "departure": 0, "duration": 20, "passengers": 10, "cancel_cost": 100}],
        "turn_minutes": 15, "delay_options_minutes": [0, 30]}
    result = optimize(data)
    assert result["objective"] == 0
    assert result["canceled"] == []
