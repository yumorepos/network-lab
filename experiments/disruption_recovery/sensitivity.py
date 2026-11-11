"""Finite synthetic recovery sensitivity to assumed delay and turn costs.

Reuses the unchanged existing scenario generator and optimizer.
No airline observations, crew legality, financial savings or generalization.
"""
from __future__ import annotations
import argparse
import copy
from pathlib import Path
import json

from experiments.disruption_recovery.benchmark import (
    DEFAULT_SEED, GENERATOR_VERSION, hash_scenario, scenario,
    cost_aware_greedy_baseline,
)
from experiments.disruption_recovery.recovery import optimize, parse_scenario, validate_solution

VARIANTS=(
    ("reference",1.0,0,1.0),
    ("half_delay_penalty",0.5,0,1.0),
    ("double_delay_penalty",2.0,0,1.0),
    ("plus_20_turn_minutes",1.0,20,1.0),
    ("double_cancellation_penalty",1.0,0,2.0),
)

def changed(data, variant):
    name,delay_factor,turn_increase,cancel_factor=variant
    x=copy.deepcopy(data)
    # Exact reference identity matters: avoid int -> float coercion when
    # multiplying an integer cancellation penalty by the no-op factor 1.0.
    if delay_factor!=1.0:
        x["delay_cost_per_passenger_minute"]*=delay_factor
    if turn_increase:
        x["turn_minutes"]+=turn_increase
    if cancel_factor!=1.0:
        for flight in x["flights"]:
            flight["cancel_cost"]*=cancel_factor
    return x

def benchmark(count=30,seed=DEFAULT_SEED):
    if not 1<=count<=30:
        raise ValueError("Bounded sensitivity uses 1-30 cases")
    results=[]
    for name,d,turn,ca in VARIANTS:
        diffs=[]
        rows=[]
        for index in range(count):
            data=changed(scenario(index,seed=seed),(name,d,turn,ca))
            flights,tails,turn_min,delays,price=parse_scenario(data)
            greedy=cost_aware_greedy_baseline(data)
            if not validate_solution(flights,tails,greedy["assignments"],
                                     greedy["canceled"],turn_min,delays):
                raise AssertionError("Greedy sensitivity assignment infeasible")
            exact=optimize(data,time_limit=20.0)
            gap=greedy["objective_raw"]-exact["objective"]
            if gap < -.011:
                raise AssertionError(f"Certified MILP worse than feasible cost-aware greedy: {name}/{index}")
            diffs.append(gap)
            rows.append({
               "index":index,"sha256":hash_scenario(data),
               "milp_objective":exact["objective"],
               "cost_aware_greedy_objective":greedy["objective"],
               "gap_illustrative_units":round(gap,2),
               "milp_cancellations":len(exact["canceled"]),
               "greedy_cancellations":len(greedy["canceled"]),
            })
        results.append({
          "variant":name,"delay_cost_factor":d,
          "additional_turn_minutes":turn,"cancellation_cost_factor":ca,
          "count":count,
          "milp_better":sum(x>.011 for x in diffs),
          "tied":sum(abs(x)<=.011 for x in diffs),
          "milp_worse":sum(x<-.011 for x in diffs),
          "mean_milp_objective":round(sum(x["milp_objective"] for x in rows)/count,2),
          "mean_greedy_objective":round(sum(x["cost_aware_greedy_objective"] for x in rows)/count,2),
          "mean_gap_illustrative_units":round(sum(diffs)/count,2),
          "mean_milp_cancellations":round(sum(x["milp_cancellations"] for x in rows)/count,2),
          "rows":rows,
        })
    return {
      "synthetic_data":True,
      "purpose":"sensitivity of a finite synthetic aircraft recovery MILP to assumed objective and turn parameters",
      "units":"arbitrary illustrative cost units, not dollars or airline savings",
      "generator":GENERATOR_VERSION,
      "seed":seed,"count_per_variant":count,
      "scope":"five fictional flights, two fictional aircraft positions and a discrete finite delay menu",
      "not_proven":"operational realism, general optimizer advantage, real airline savings",
      "variants":results
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--count",type=int,default=30)
    p.add_argument("--seed",type=int,default=DEFAULT_SEED)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args(argv)
    result=benchmark(count=a.count,seed=a.seed)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"seed":result["seed"],"count_per_variant":a.count,
          "variants":[{k:v for k,v in entry.items() if k!="rows"}
                      for entry in result["variants"]]},indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
