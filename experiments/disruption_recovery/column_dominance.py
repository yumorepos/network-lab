"""Paired exact-column dominance experiment on unchanged synthetic scenarios.

Two independently isolated runs per scenario: original full per-tail rotations
and exact same-tail flight-set minimum-cost columns. No partial-state pruning.
Results are censored when either method hits a path, raw visit or wall cap.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import statistics

from experiments.disruption_recovery.benchmark import DEFAULT_SEED, hash_scenario
from experiments.disruption_recovery.scalability import run_isolated, scaled_scenario

METHOD = "same-tail-flight-set-min-delay-cost-v1"
GRID = (
    (5, "connected", 0), (5, "connected", 1),
    (8, "connected", 0), (8, "connected", 1),
    (8, "distributed", 0), (8, "distributed", 1),
    (11, "connected", 0), (11, "connected", 1),
    (11, "distributed", 0), (11, "distributed", 1),
    (14, "connected", 0), (14, "distributed", 0),
)


def run_study(*, path_cap: int = 15000, raw_visit_cap: int = 250000,
              wall_seconds: float = 6.0, seed: int = DEFAULT_SEED,
              grid=GRID) -> dict:
    if not grid or len(grid) > 20:
        raise ValueError("Expected one to twenty predetermined comparisons")
    rows = []
    for size, topology, index in grid:
        data = scaled_scenario(index, size, topology=topology, seed=seed)
        original = run_isolated(data, path_cap=path_cap,
                                wall_seconds=wall_seconds, prune_columns=False,
                                raw_visit_cap=raw_visit_cap)
        pruned = run_isolated(data, path_cap=path_cap,
                              wall_seconds=wall_seconds, prune_columns=True,
                              raw_visit_cap=raw_visit_cap)
        if original["status"] == "ERROR" or pruned["status"] == "ERROR":
            raise RuntimeError(f"Unexpected execution error: {size}/{topology}/{index}")
        both = original["status"] == pruned["status"] == "OPTIMAL"
        if both:
            if abs(original["milp_objective"] - pruned["milp_objective"]) > 1e-6:
                raise AssertionError(f"Unsafe dominance changed the objective: {size}/{topology}/{index}")
            if abs(original["baseline_objective"] - pruned["baseline_objective"]) > 1e-6:
                raise AssertionError("Cost-aware greedy comparator disagreed across methods")
            if pruned["path_count"] > original["path_count"]:
                raise AssertionError("Dominance cannot increase retained exact columns")
        if pruned["status"] == "OPTIMAL":
            if pruned["raw_paths_explored"] < pruned["path_count"]:
                raise AssertionError("Pruning reported impossible counts")
            if pruned["pruning_method"] != METHOD[:-3]: # remove -v1 design tag
                raise AssertionError("Wrong pruning implementation")
        rows.append({
            "flights": size, "topology": topology, "case_index": index,
            "scenario_sha256": hash_scenario(data),
            "objective_parity_checked": both,
            "original": original, "pruned": pruned,
        })
    both = [r for r in rows if r["objective_parity_checked"]]
    status_count = lambda key: {x: sum(r[key]["status"] == x for r in rows)
                                for x in sorted({r[key]["status"] for r in rows})}
    return {
        "method": METHOD,
        "seed": seed,
        "synthetic_only": True,
        "comparison": "same input, per-tail flight-set terminal column dominance",
        "limits": {
            "retained_columns_per_tail": path_cap,
            "raw_search_states_per_tail_on_pruned_method": raw_visit_cap,
            "hard_wall_seconds_per_worker": wall_seconds,
        },
        "control": "original enumeration with original per-tail path cap",
        "equivalence_scope": (
            "After complete enumeration, removing higher-cost same-tail flight-set "
            "columns preserves the finite MILP optimum because the master incidence "
            "columns are identical. This model has no tail terminal-state constraint."
        ),
        "nonclaims": (
            "No real airline data or money; no causal claim, scalability guarantee, "
            "or inferred exact objective when either run was capped/time-limited."
        ),
        "environment": {"python": platform.python_version(),
                        "platform": platform.platform()},
        "summary": {
            "attempted_pairs": len(rows),
            "both_certified_objective_equal": len(both),
            "original_statuses": status_count("original"),
            "pruned_statuses": status_count("pruned"),
            "median_retained_column_reduction_percent_on_both_optimal": (
                round(statistics.median(
                    100 * (1 - r["pruned"]["path_count"] / r["original"]["path_count"])
                    for r in both), 3) if both else None),
            "median_full_optimizer_time_original_on_both_optimal": (
                round(statistics.median(r["original"]["timing_seconds"]["total"]
                                        for r in both), 6) if both else None),
            "median_full_optimizer_time_pruned_on_both_optimal": (
                round(statistics.median(r["pruned"]["timing_seconds"]["total"]
                                        for r in both), 6) if both else None),
        },
        "rows": rows,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--path-cap", type=int, default=15000)
    p.add_argument("--raw-visit-cap", type=int, default=250000)
    p.add_argument("--wall-seconds", type=float, default=6.0)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(argv)
    report = run_study(path_cap=args.path_cap, raw_visit_cap=args.raw_visit_cap,
                       wall_seconds=args.wall_seconds)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
