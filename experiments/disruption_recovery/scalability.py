"""Bounded, reproducible scalability study for the *existing* synthetic MILP.

Comparison uses the exact same scenarios and objective for cost-aware greedy.
A child process enforces a hard per-instance wall deadline: a slow path
enumeration or native solver must never hang the benchmark indefinitely.
No real-flight, crew, maintenance or financial inference is supported.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
from pathlib import Path
import platform
import random
import resource
import statistics
import sys
from time import perf_counter
import numpy
import scipy

from experiments.disruption_recovery.benchmark import (
    DEFAULT_SEED, cost_aware_greedy_baseline, hash_scenario, scenario,
)
from experiments.disruption_recovery.recovery import (
    PathLimitExceeded, PathExplorationLimitExceeded, optimize,
    parse_scenario, validate_solution,
)

GENERATOR_VERSION = "recovery-scaling-v1"
MAX_HARD_BUDGET = 30.0
MAX_PATH_CAP = 100_000


def scaled_scenario(index: int, n_flights: int, *, topology: str = "connected",
                    tails: int = 2, delay_choices: int = 6,
                    seed: int = DEFAULT_SEED) -> dict:
    """Extend the original 5-flight baseline without changing its first 5 rows.

    New routes remain fictional and are not sampled from an actual airline.
    Connected repeats AAA↔BBB; distributed cycles across three airports.
    """
    if not 5 <= n_flights <= 14 or topology not in ("connected", "distributed"):
        raise ValueError("Expected 5–14 flights and a known network topology")
    if tails not in (2, 3) or delay_choices not in (3, 6):
        raise ValueError("Bounded study supports 2–3 tails and 3 or 6 delays")
    if not 0 <= index < 1000:
        raise ValueError("Scenario index out of bounded range")
    data = scenario(index, seed=seed)
    rng = random.Random(seed + 104729 * index + 8191 * n_flights
                        + (11 if topology == "connected" else 17))
    connected = (("AAA", "BBB"), ("BBB", "AAA"))
    distributed = (("AAA", "BBB"), ("BBB", "CCC"),
                   ("CCC", "AAA"), ("AAA", "CCC"),
                   ("CCC", "BBB"), ("BBB", "AAA"))
    routes = connected if topology == "connected" else distributed
    for j in range(5, n_flights):
        origin, dest = routes[(j - 5) % len(routes)]
        data["flights"].append({
            "id": f"F{j + 1}", "origin": origin, "destination": dest,
            "departure": 160 + 30 * (j - 5) + rng.randint(-12, 12),
            "duration": rng.choice((20, 30, 40, 50)),
            "passengers": rng.randint(20, 140),
            "cancel_cost": rng.choice((25, 80, 180, 400, 650)),
        })
    if tails == 3:
        data["tails"].append({"id": "C", "location": "CCC", "available": 0})
    if delay_choices == 3:
        data["delay_options_minutes"] = [0, 30, 90]
    return data


def calculate_objective(data: dict, result: dict) -> float:
    """Independently reconstruct cost from selected assignments/cancellations."""
    flights, tails, turn, delays, price = parse_scenario(data)
    if not validate_solution(flights, tails, result["assignments"],
                             result["canceled"], turn, delays):
        raise ValueError("Baseline or solver assignment failed feasibility audit")
    by_id = {f.id: f for f in flights}
    return (sum(by_id[fid].cancel_cost for fid in result["canceled"])
            + sum(price * by_id[fid].passengers * delay
                  for path in result["assignments"].values()
                  for fid, delay in path))


def _peak_process_rss_mib() -> float:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Linux reports KiB; macOS reports bytes. This is an OS-specific
    # process high-water mark, including native libraries and interpreter.
    return round(peak / (1024 * 1024 if sys.platform == "darwin" else 1024), 3)


def _evaluate(data: dict, path_cap: int, deadline: float,
              prune_columns: bool = False,
              raw_visit_cap: int = 250000) -> dict:
    t0 = perf_counter()
    baseline = cost_aware_greedy_baseline(data)
    greedy_cost = calculate_objective(data, baseline)
    if abs(greedy_cost - baseline["objective_raw"]) > 1e-6:
        raise AssertionError("Cost-aware baseline cost arithmetic disagrees")
    greedy_seconds = perf_counter() - t0
    remaining = deadline - greedy_seconds
    if remaining <= 0:
        raise TimeoutError("Entire budget consumed by baseline calculation")
    try:
        exact = optimize(data, time_limit=remaining,
                         total_time_limit=remaining,
                         max_paths_per_tail=path_cap, profile=True,
                         prune_dominated_columns=prune_columns,
                         max_explored_states_per_tail=raw_visit_cap)
    except PathLimitExceeded as exc:
        return {"status": "PATH_CAP", "detail": str(exc),
                "partial_paths": exc.paths_generated,
                "baseline_objective": greedy_cost,
                "baseline_seconds": greedy_seconds,
                "peak_process_rss_mib": _peak_process_rss_mib()}
    except PathExplorationLimitExceeded as exc:
        return {"status": "RAW_VISIT_CAP", "detail": str(exc),
                "raw_visits_before_cap": exc.explored,
                "baseline_objective": greedy_cost,
                "baseline_seconds": greedy_seconds,
                "peak_process_rss_mib": _peak_process_rss_mib()}
    except TimeoutError as exc:
        return {"status": "COOPERATIVE_TIMEOUT", "detail": str(exc),
                "baseline_objective": greedy_cost,
                "baseline_seconds": greedy_seconds,
                "peak_process_rss_mib": _peak_process_rss_mib()}
    except RuntimeError as exc:
        return {"status": "UNCERTIFIED", "detail": str(exc),
                "baseline_objective": greedy_cost,
                "baseline_seconds": greedy_seconds,
                "peak_process_rss_mib": _peak_process_rss_mib()}
    exact_cost = calculate_objective(data, exact)
    if abs(exact_cost - exact["objective_raw"]) > 1e-6:
        raise AssertionError("Solver objective disagrees with independently priced assignments")
    if exact_cost > greedy_cost + 1e-6:
        raise AssertionError("Exact finite solution worse than feasible greedy baseline")
    return {
        "status": "OPTIMAL", "baseline_objective": greedy_cost,
        "milp_objective": exact_cost,
        "milp_improvement_vs_cost_aware_greedy": round(greedy_cost - exact_cost, 6),
        "milp_cancellations": len(exact["canceled"]),
        "baseline_cancellations": len(baseline["canceled"]),
        "path_count": exact["paths_considered"],
        "paths_by_tail": exact["paths_by_tail"],
        "raw_paths_explored": exact["raw_paths_explored"],
        "pruning_method": exact["pruning_method"],
        "enumeration_stats_by_tail": exact["enumeration_stats_by_tail"],
        "timing_seconds": exact["timing_seconds"],
        "baseline_seconds": greedy_seconds,
        "peak_process_rss_mib": _peak_process_rss_mib(),
    }


def _worker(pipe, data: dict, cap: int, seconds: float,
            prune_columns: bool = False, raw_visit_cap: int = 250000):
    try:
        result = _evaluate(data, cap, seconds,
                           prune_columns=prune_columns, raw_visit_cap=raw_visit_cap)
    except Exception as exc:
        result = {"status": "ERROR", "detail": f"{type(exc).__name__}: {exc}"}
    try:
        pipe.send(result)
    finally:
        pipe.close()


def run_isolated(data: dict, *, path_cap: int = 15000,
                 wall_seconds: float = 6.0,
                 prune_columns: bool = False,
                 raw_visit_cap: int = 250000) -> dict:
    """Terminate hung work after its hard wall deadline; never claim optimality."""
    if (not 0 < wall_seconds <= MAX_HARD_BUDGET
            or type(path_cap) is not int or not 0 < path_cap <= MAX_PATH_CAP
            or type(raw_visit_cap) is not int or not 0 < raw_visit_cap <= 1000000
            or type(prune_columns) is not bool):
        raise ValueError("Invalid bounded benchmark resource limits")
    ctx = mp.get_context("spawn")
    parent, child = ctx.Pipe(duplex=False)
    process = ctx.Process(
        target=_worker,
        args=(child, data, path_cap, wall_seconds, prune_columns, raw_visit_cap))
    start = perf_counter()
    process.start()
    child.close()
    try:
        # Count process startup in the hard deadline, not just join time.
        remaining = max(0.0, wall_seconds - (perf_counter() - start))
        process.join(remaining)
        if process.is_alive():
            process.terminate()
            process.join(timeout=1)
            if process.is_alive():
                process.kill()
                process.join(timeout=1)
            return {"status": "HARD_TIMEOUT", "detail": "Per-case process deadline exceeded",
                    "wall_seconds": round(perf_counter() - start, 6)}
        if not parent.poll():
            return {"status": "ERROR", "detail": f"Worker exited {process.exitcode} without results",
                    "wall_seconds": round(perf_counter() - start, 6)}
        result = parent.recv()
        result["wall_seconds"] = round(perf_counter() - start, 6)
        return result
    finally:
        parent.close()
        if process.is_alive():
            process.kill()
            process.join(timeout=1)
        process.close()


def benchmark(*, cases: int = 2, sizes: tuple[int, ...] = (5, 8, 11),
              path_cap: int = 15000, wall_seconds: float = 6.0,
              seed: int = DEFAULT_SEED, tails: int = 2,
              delay_choices: int = 6) -> dict:
    if type(cases) is not int or not 1 <= cases <= 4:
        raise ValueError("Benchmark supports 1–4 seeded cases per design cell")
    if (not sizes or len(sizes) > 3 or len(set(sizes)) != len(sizes)
            or any(n not in (5, 8, 11, 14) for n in sizes)):
        raise ValueError("Sizes must be distinct within (5, 8, 11, 14)")
    if tails not in (2, 3) or delay_choices not in (3, 6):
        raise ValueError("Invalid bounded aircraft or delay-choice factor")
    rows = []
    for n in sizes:
        topologies = ("connected",) if n == 5 else ("connected", "distributed")
        for topology in topologies:
            for index in range(cases):
                data = scaled_scenario(index, n, topology=topology, seed=seed,
                                       tails=tails, delay_choices=delay_choices)
                observed = run_isolated(data, path_cap=path_cap, wall_seconds=wall_seconds)
                rows.append({"flights": n, "tails": len(data["tails"]),
                             "delay_choices": len(data["delay_options_minutes"]),
                             "topology": topology, "case_index": index,
                             "scenario_sha256": hash_scenario(data), **observed})
    aggregate = []
    for n in sizes:
        sample = [x for x in rows if x["flights"] == n]
        successes = [x for x in sample if x["status"] == "OPTIMAL"]
        statuses = {s: sum(x["status"] == s for x in sample)
                    for s in sorted({x["status"] for x in sample})}
        aggregate.append({
            "flights": n, "attempted": len(sample), "statuses": statuses,
            "optimal_count": len(successes),
            "median_total_solver_pipeline_seconds_on_optimal_only": (
                round(statistics.median(x["timing_seconds"]["total"] for x in successes), 6)
                if successes else None),
            "median_enumerated_paths_on_optimal_only": (
                statistics.median(x["path_count"] for x in successes)
                if successes else None),
            "median_peak_process_rss_mib_on_optimal_only": (
                round(statistics.median(x["peak_process_rss_mib"] for x in successes), 3)
                if successes else None),
        })
    return {
        "generator": GENERATOR_VERSION, "baseline_generator": "bounded-recovery-scenarios-v1",
        "seed": seed, "synthetic_data": True,
        "study_type": "bounded benchmark, not an estimate of production scalability",
        "scenarios_per_cell": cases,
        "factor_settings": {"tails": tails, "delay_choices": delay_choices},
        "limits": {"path_cap_per_tail": path_cap,
                   "hard_wall_seconds_per_case": wall_seconds,
                   "max_flights_supported_by_unchanged_model": 14},
        "environment": {"python": platform.python_version(),
                        "scipy": scipy.__version__, "numpy": numpy.__version__,
                        "platform": platform.platform(),
                        "machine": platform.machine(), "cpu_count": os.cpu_count()},
        "memory_measurement": "OS process high-water RSS in MiB, includes Python and native solver libraries; not exact solver allocation",
        "interpretation": "Only OPTIMAL entries have certified finite-universe objectives; capped/timeout entries are censored and cannot be compared as if optimized",
        "summary": aggregate, "cases": rows,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cases", type=int, default=2)
    p.add_argument("--sizes", type=int, nargs="+", default=[5, 8, 11])
    p.add_argument("--path-cap", type=int, default=15000)
    p.add_argument("--wall-seconds", type=float, default=6.0)
    p.add_argument("--seed", type=int, default=DEFAULT_SEED)
    p.add_argument("--tails", type=int, default=2)
    p.add_argument("--delay-choices", type=int, default=6)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args(argv)
    result = benchmark(cases=a.cases, sizes=tuple(a.sizes),
                       path_cap=a.path_cap, wall_seconds=a.wall_seconds,
                       seed=a.seed, tails=a.tails, delay_choices=a.delay_choices)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open("x", encoding="utf8") as out:
        json.dump(result, out, indent=2, sort_keys=True, allow_nan=False)
        out.write("\n")
    print(json.dumps({"summary": result["summary"], "output": str(a.output)}, indent=2))
    if any(row["status"] == "ERROR" for row in result["cases"]):
        raise RuntimeError("Unexpected benchmark errors; inspect result artifact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
