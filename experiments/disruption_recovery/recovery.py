"""Educational airline recovery MILP. Separate from frozen route-screen model.

Exact only within enumerated delay options and the finite flight/tail universe.
Enumerate rotations in ACTUAL departure order; scheduled order is not valid
under disruptions because delayed early flights can be overtaken.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix


@dataclass(frozen=True)
class Flight:
    id: str
    origin: str
    destination: str
    departure: int
    duration: int
    passengers: int
    cancel_cost: float


@dataclass(frozen=True)
class Tail:
    id: str
    location: str
    available: int


def parse_scenario(data):
    flights = [Flight(**f) for f in data["flights"]]
    tails = [Tail(**t) for t in data["tails"]]
    turn = int(data.get("turn_minutes", 30))
    delays = sorted(set(data.get("delay_options_minutes", [0, 15, 30, 60])))
    price = float(data.get("delay_cost_per_passenger_minute", 0.15))
    if not flights or not tails or len(flights) > 14:
        raise ValueError("Expected 1-14 flights and at least one tail")
    if len({f.id for f in flights}) != len(flights) or len({t.id for t in tails}) != len(tails):
        raise ValueError("Flight and tail IDs must be unique")
    if turn < 0 or not isfinite(price) or price < 0 or not delays or any(
        not isfinite(float(d)) or d < 0 for d in delays
    ):
        raise ValueError("Nonnegative finite turnaround, delays and costs required")
    for f in flights:
        if (not f.id or not f.origin or not f.destination or f.origin == f.destination
            or not all(isfinite(float(x)) for x in
                       (f.departure, f.duration, f.passengers, f.cancel_cost))
            or f.duration <= 0 or f.passengers < 0 or f.cancel_cost < 0):
            raise ValueError("Invalid flight bounds")
    for t in tails:
        if not t.id or not t.location or not isfinite(float(t.available)):
            raise ValueError("Invalid tail fields")
    return sorted(flights, key=lambda f: (f.departure, f.id)), tails, turn, delays, price


def enumerate_paths(flights, tail, turn, delays, price, max_paths=100000):
    """List every feasible aircraft rotation in ACTUAL flight order.

    Paths may stop at any point. Reusing a flight is impossible via bitmask.
    Raises rather than silently clipping a too-large instance.
    """
    paths = []
    chosen = []

    def visit(used, airport, ready, cost):
        paths.append((tuple(chosen), cost))
        if len(paths) > max_paths:
            raise ValueError("Too many paths; exact enumeration aborted")
        for ix, f in enumerate(flights):
            if used & (1 << ix) or f.origin != airport:
                continue
            for delay in delays:
                departure = f.departure + delay
                if departure < ready:
                    continue
                chosen.append((f.id, delay))
                visit(used | (1 << ix), f.destination,
                      departure + f.duration + turn,
                      cost + price * f.passengers * delay)
                chosen.pop()

    visit(0, tail.location, tail.available, 0.0)
    return paths


def validate_solution(flights, tails, assignments, canceled, turn, delays):
    by_flight = {f.id: f for f in flights}
    by_tail = {t.id: t for t in tails}
    if set(assignments) != set(by_tail) or len(canceled) != len(set(canceled)):
        return False
    if not set(canceled).issubset(by_flight):
        return False
    used = set()
    for tid, path in assignments.items():
        airport, ready = by_tail[tid].location, by_tail[tid].available
        for fid, delay in path:
            if fid not in by_flight:
                return False
            f = by_flight[fid]
            if (fid in used or delay not in delays or airport != f.origin
                or f.departure + delay < ready):
                return False
            used.add(fid)
            airport = f.destination
            ready = f.departure + delay + f.duration + turn
    return not used.intersection(canceled) and used | set(canceled) == set(by_flight)


def greedy_baseline(data):
    flights, tails, turn, delays, price = parse_scenario(data)
    current = {t.id: [t.location, t.available] for t in tails}
    assignments = {t.id: [] for t in tails}
    canceled = []
    for f in flights:
        feasible = [(d, t.id) for t in tails for d in delays
                    if current[t.id][0] == f.origin
                    and current[t.id][1] <= f.departure + d]
        if not feasible:
            canceled.append(f.id)
            continue
        delay, tid = min(feasible)
        assignments[tid].append((f.id, delay))
        current[tid] = [f.destination, f.departure + delay + f.duration + turn]
    assert validate_solution(flights, tails, assignments, canceled, turn, delays)
    by_id = {f.id: f for f in flights}
    objective_raw = (sum(by_id[fid].cancel_cost for fid in canceled)
        + sum(price * by_id[fid].passengers * delay
              for path in assignments.values() for fid, delay in path))
    return {"objective": round(objective_raw, 2),
            "objective_raw": float(objective_raw),
            "assignments": assignments, "canceled": canceled}


def optimize(data, *, time_limit=20.0):
    flights, tails, turn, delays, price = parse_scenario(data)
    if not isfinite(time_limit) or time_limit <= 0:
        raise ValueError("Invalid solver time limit")
    plans = [(t.id, path, cost) for t in tails
             for path, cost in enumerate_paths(flights, t, turn, delays, price)]
    nplan, nf = len(plans), len(flights)
    A = lil_matrix((len(tails) + nf, nplan + nf), dtype=float)
    tail_ix = {t.id: i for i, t in enumerate(tails)}
    flight_ix = {f.id: i for i, f in enumerate(flights)}
    for j, (tid, path, _) in enumerate(plans):
        A[tail_ix[tid], j] = 1
        for fid, _ in path:
            A[len(tails) + flight_ix[fid], j] = 1
    for i in range(nf):
        A[len(tails) + i, nplan + i] = 1
    c = np.array([p[2] for p in plans] + [f.cancel_cost for f in flights])
    constraint = LinearConstraint(A.tocsr(), np.ones(len(tails) + nf),
                                  np.ones(len(tails) + nf))
    result = milp(c, integrality=np.ones(nplan + nf),
                  bounds=Bounds(0, 1), constraints=constraint,
                  options={"time_limit": time_limit, "mip_rel_gap": 0.0})
    if result.x is None or result.status != 0:
        raise RuntimeError(f"Uncertified MILP: {result.status}: {result.message}")
    assignments = {t.id: [] for t in tails}
    for j, (tid, path, _) in enumerate(plans):
        if result.x[j] > 0.5:
            assignments[tid] = list(path)
    canceled = [f.id for i, f in enumerate(flights) if result.x[nplan + i] > 0.5]
    if not validate_solution(flights, tails, assignments, canceled, turn, delays):
        raise RuntimeError("Invalid solver assignment")
    baseline = greedy_baseline(data)
    if result.fun > baseline["objective_raw"] + 1e-6:
        raise AssertionError("Optimal solution worse than feasible baseline")
    return {"status": "optimal", "objective": round(float(result.fun), 2),
            "baseline_objective": baseline["objective"],
            "savings_vs_greedy": round(baseline["objective_raw"] - float(result.fun), 2),
            "assignments": assignments, "canceled": canceled,
            "paths_considered": nplan, "synthetic_data": True}
