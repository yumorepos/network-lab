"""Reproducible, illustrative baselines for the separate synthetic recovery MILP.

No original Network Lab route-screening model, airline data, or money amounts.
30 small seeded scenarios and two additional feasible decision comparators.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random

from experiments.disruption_recovery.recovery import (
    greedy_baseline, optimize, parse_scenario, validate_solution
)

DEFAULT_SEED = 20261111
GENERATOR_VERSION = "bounded-recovery-scenarios-v1"
AIRPORTS = ("AAA", "BBB", "CCC")
MOTIFS = (
    (("AAA","CCC"),("CCC","AAA"),("AAA","BBB"),("BBB","CCC"),("CCC","BBB")),
    (("BBB","AAA"),("AAA","CCC"),("CCC","BBB"),("BBB","CCC"),("CCC","AAA")),
    (("AAA","BBB"),("BBB","AAA"),("AAA","CCC"),("CCC","BBB"),("BBB","AAA")),
)

def scenario(index: int, *, seed: int = DEFAULT_SEED) -> dict:
    if not 0 <= index < 1000:
        raise ValueError("Scenario index must be in range [0, 1000)")
    r = random.Random(seed + 7919 * index)
    motif = MOTIFS[index % len(MOTIFS)]
    departures = (0, 30, 65, 95, 140)
    flights = []
    for ix, (origin, dest) in enumerate(motif):
        # Fixed-seed variation in gates, flight duration, passengers and penalty.
        # All units and airport names are deliberately illustrative.
        flights.append({
            "id": f"F{ix + 1}",
            "origin": origin, "destination": dest,
            "departure": max(0, departures[ix] + r.randint(-15, 15)),
            "duration": r.choice((20, 30, 40, 50)),
            "passengers": r.randint(20, 140),
            "cancel_cost": r.choice((25, 80, 180, 400, 650)),
        })
    return {
        "tails": [
            {"id": "A", "location": "AAA", "available": r.choice((0, 10, 30))},
            {"id": "B", "location": "BBB", "available": r.choice((0, 10, 30))},
        ],
        "flights": flights,
        "turn_minutes": r.choice((10, 20, 30)),
        "delay_options_minutes": [0, 15, 30, 60, 90, 120],
        "delay_cost_per_passenger_minute": r.choice((0.05, 0.1, 0.2, 0.3)),
    }

def hash_scenario(data: dict) -> str:
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def all_cancel_baseline(data: dict) -> dict:
    flights, tails, turn, delays, price = parse_scenario(data)
    assignment = {tail.id: [] for tail in tails}
    canceled = [f.id for f in flights]
    assert validate_solution(flights, tails, assignment, canceled, turn, delays)
    raw = float(sum(f.cancel_cost for f in flights))
    return {
        "objective": round(raw, 2), "objective_raw": raw,
        "assignments": assignment, "canceled": canceled,
        "synthetic_data": True
    }

def cost_aware_greedy_baseline(data: dict) -> dict:
    """Schedule-order feasible greedy, but cancel if the immediate flight cost is higher.

    No future lookahead, no fleet repositioning and no implicit global optimality.
    It can be worse than the existing fly-first greedy on subsequent flights.
    """
    flights, tails, turn, delays, price = parse_scenario(data)
    current = {t.id: [t.location, t.available] for t in tails}
    assignments = {t.id: [] for t in tails}
    canceled = []
    for flight in flights:
        choices = [
            (price * flight.passengers * shift, shift, tail.id)
            for tail in tails for shift in delays
            if current[tail.id][0] == flight.origin
            and current[tail.id][1] <= flight.departure + shift
        ]
        if not choices or min(choices)[0] >= flight.cancel_cost:
            canceled.append(flight.id)
            continue
        extra_cost, delay, tailid = min(choices)
        assignments[tailid].append((flight.id, delay))
        current[tailid] = [
            flight.destination, flight.departure + delay + flight.duration + turn
        ]
    if not validate_solution(flights, tails, assignments, canceled, turn, delays):
        raise AssertionError("Cost-aware greedy produced an infeasible schedule")
    by_id = {f.id: f for f in flights}
    objective_raw = (
        sum(by_id[fid].cancel_cost for fid in canceled) +
        sum(price * by_id[fid].passengers * delay
            for path in assignments.values() for fid, delay in path)
    )
    return {
        "objective": round(objective_raw, 2),
        "objective_raw": float(objective_raw),
        "assignments": assignments,
        "canceled": canceled,
        "synthetic_data": True
    }

def run_benchmark(count: int = 30, *, seed: int = DEFAULT_SEED) -> dict:
    if not 1 <= count <= 30:
        raise ValueError("Bounded synthetic benchmark uses 1-30 instances")
    rows = []
    for index in range(count):
        data = scenario(index, seed=seed)
        standard = greedy_baseline(data)
        aware = cost_aware_greedy_baseline(data)
        cancel = all_cancel_baseline(data)
        exact = optimize(data, time_limit=20.0)
        objectives = {
            "milp": float(exact["objective"]),
            "greedy_fly_first": float(standard["objective_raw"]),
            "greedy_cost_aware": float(aware["objective_raw"]),
            "all_cancel": float(cancel["objective_raw"]),
        }
        for comparator in ("greedy_fly_first", "greedy_cost_aware", "all_cancel"):
            if objectives["milp"] > objectives[comparator] + .011:
                raise AssertionError(f"MILP unexpectedly more expensive than {comparator}")
        rows.append({
            "scenario": index,
            "scenario_sha256": hash_scenario(data),
            "objectives": {k: round(v, 2) for k,v in objectives.items()},
            "milp_cancelled": len(exact["canceled"]),
            "greedy_cost_aware_cancelled": len(aware["canceled"]),
            "milp_paths_enumerated": exact["paths_considered"],
        })
    summary = {}
    for name in ("milp", "greedy_fly_first", "greedy_cost_aware", "all_cancel"):
        summary[name] = {
            "mean_objective": round(
                sum(r["objectives"][name] for r in rows)/len(rows), 2
            )
        }
    comparisons = {}
    for name in ("greedy_fly_first", "greedy_cost_aware", "all_cancel"):
        differences = [
            r["objectives"][name] - r["objectives"]["milp"] for r in rows
        ]
        comparisons[name] = {
            "milp_better": sum(x > .011 for x in differences),
            "tied": sum(abs(x) <= .011 for x in differences),
            "milp_worse": sum(x < -.011 for x in differences),
            "mean_illustrative_unit_gap": round(sum(differences)/len(differences),2),
        }
    return {
        "scenario_generator": GENERATOR_VERSION,
        "seed": seed, "sample_count": count,
        "synthetic_data": True,
        "units": "arbitrary illustrative cost units (not currency)",
        "not_demonstrated": [
            "real airline savings", "crew legality", "airport slots",
            "fleet or maintenance realism", "network-wide optimal recovery"
        ],
        "summary": summary,
        "comparisons": comparisons,
        "cases": rows,
    }

def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--count", type=int, default=30)
    p.add_argument("--seed", type=int, default=DEFAULT_SEED)
    p.add_argument("--output", type=Path, required=True)
    a=p.parse_args(argv)
    report=run_benchmark(a.count,seed=a.seed)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "scenario_generator": report["scenario_generator"],
        "seed": report["seed"],
        "sample_count": report["sample_count"],
        "summary": report["summary"],
        "comparisons": report["comparisons"]
    },indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
