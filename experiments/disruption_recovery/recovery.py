"""Educational airline recovery MILP. Separate from frozen route-screen model.

Exact only within enumerated delay options and the finite flight/tail universe.
Enumerate rotations in ACTUAL departure order; scheduled order is not valid
under disruptions because delayed early flights can be overtaken.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite
from time import perf_counter
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


class PathLimitExceeded(ValueError):
    """Exact enumeration aborted; partial paths must never be optimized."""

    def __init__(self, tail_id: str, paths_generated: int, cap: int):
        self.tail_id = tail_id
        self.paths_generated = paths_generated
        self.cap = cap
        super().__init__(f"Too many paths for {tail_id}: {paths_generated} > {cap}")


def enumerate_paths(flights, tail, turn, delays, price, max_paths=100000, *, deadline=None):
    """List all feasible rotations or fail before any truncated solution is used.

    A shared wall deadline can interrupt exponential DFS growth. The optional
    deadline is cooperative: callers needing a hard deadline must also isolate
    the optimizer in a separately time-limited process.
    """
    if type(max_paths) is not int or max_paths <= 0:
        raise ValueError("max_paths must be a positive integer")
    paths = []
    chosen = []

    def visit(used, airport, ready, cost):
        if deadline is not None and perf_counter() >= deadline:
            raise TimeoutError("Total optimization budget exhausted during path enumeration")
        paths.append((tuple(chosen), cost))
        if len(paths) > max_paths:
            raise PathLimitExceeded(tail.id, len(paths), max_paths)
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


def optimize(data, *, time_limit=20.0, total_time_limit=None,
             max_paths_per_tail=100000, profile=False):
    """Certify exact finite MILP or fail; optionally expose phase timings.

    The solver time_limit only bounds HiGHS, not Python preprocessing.
    total_time_limit is cooperative during preprocessing, and the remaining
    budget is passed to HiGHS. For hard deadlines use process isolation.
    Defaults preserve the original optimization problem and API behavior.
    """
    started = perf_counter()
    flights, tails, turn, delays, price = parse_scenario(data)
    parsed = perf_counter()
    if not isfinite(time_limit) or time_limit <= 0:
        raise ValueError("Invalid solver time limit")
    if (total_time_limit is not None
            and (not isfinite(total_time_limit) or total_time_limit <= 0)):
        raise ValueError("Invalid total optimization time limit")
    if type(max_paths_per_tail) is not int or max_paths_per_tail <= 0:
        raise ValueError("max_paths_per_tail must be a positive integer")
    deadline = (started + total_time_limit
                if total_time_limit is not None else None)

    def remaining(stage):
        if deadline is None:
            return time_limit
        left = deadline - perf_counter()
        if left <= 0:
            raise TimeoutError(f"Total optimization budget exhausted during {stage}")
        return min(time_limit, left)

    plans = []
    paths_by_tail = {}
    for tail in tails:
        remaining("enumeration")
        options = enumerate_paths(flights, tail, turn, delays, price,
                                  max_paths=max_paths_per_tail, deadline=deadline)
        paths_by_tail[tail.id] = len(options)
        plans.extend((tail.id, path, cost) for path, cost in options)
    enumerated = perf_counter()

    remaining("construction")
    nplan, nf = len(plans), len(flights)
    A = lil_matrix((len(tails) + nf, nplan + nf), dtype=float)
    tail_ix = {t.id: i for i, t in enumerate(tails)}
    flight_ix = {f.id: i for i, f in enumerate(flights)}
    for j, (tid, path, _) in enumerate(plans):
        if j % 256 == 0:
            remaining("construction")
        A[tail_ix[tid], j] = 1
        for fid, _ in path:
            A[len(tails) + flight_ix[fid], j] = 1
    for i in range(nf):
        A[len(tails) + i, nplan + i] = 1
    c = np.array([p[2] for p in plans] + [f.cancel_cost for f in flights])
    constraint = LinearConstraint(A.tocsr(), np.ones(len(tails) + nf),
                                  np.ones(len(tails) + nf))
    constructed = perf_counter()

    solve_limit = remaining("solve")
    result = milp(c, integrality=np.ones(nplan + nf),
                  bounds=Bounds(0, 1), constraints=constraint,
                  options={"time_limit": solve_limit, "mip_rel_gap": 0.0})
    solved = perf_counter()
    remaining("post-solve validation")
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
    finished = perf_counter()
    if deadline is not None and finished >= deadline:
        raise TimeoutError("Total optimization budget exhausted during post-solve validation")

    output = {"status": "optimal", "objective": round(float(result.fun), 2),
              "baseline_objective": baseline["objective"],
              "savings_vs_greedy": round(baseline["objective_raw"] - float(result.fun), 2),
              "assignments": assignments, "canceled": canceled,
              "paths_considered": nplan, "synthetic_data": True}
    if profile:
        output["objective_raw"] = float(result.fun)
        output["savings_vs_fly_first_greedy"] = output["savings_vs_greedy"]
        output["paths_by_tail"] = paths_by_tail
        output["timing_seconds"] = {
            "parse": parsed - started,
            "enumeration": enumerated - parsed,
            "construction": constructed - enumerated,
            "solve": solved - constructed,
            "post_solve_validation": finished - solved,
            "total": finished - started,
        }
    return output
