"""Recommendation screen: LAUNCH / MONITOR / PASS per candidate.

Rules (from the project brief, thresholds in assumptions.yaml):
  LAUNCH  - base margin clears the hurdle AND the downside fare scenario stays
            positive AND base break-even load factor is attainable (<= 0.85).
  MONITOR - base margin positive but a downside test fails.
  PASS    - base margin negative.

Every verdict ships with: the two numbers that drove it, the top assumptions
it rests on, the biggest risk, and a confidence grade derived from data
coverage (observed vs modeled demand, incumbent structure).
"""
from __future__ import annotations

import pandas as pd

from .common import OUTPUTS, assumptions, study

BELF_MAX = 0.85


def confidence(row) -> str:
    if row["demand_source"] == "observed":
        return "high" if row["n_nonstop_incumbents"] > 0 else "medium"
    return "medium" if row["n_nonstop_incumbents"] > 0 else "low"


def top_risk(row) -> str:
    if row["demand_source"] == "modeled":
        return ("gravity x transfer demand estimate; no current O&D truth "
                "for this market")
    if row["belf"] > 0.80:
        return "break-even load factor leaves little room below plan"
    if row["n_nonstop_incumbents"] >= 2:
        return "two or more nonstop incumbents; share model optimistic if they respond"
    if row["fuel_down_margin"] < 0:
        return "margin goes negative in the high-fuel scenario"
    return "thin absolute contribution; schedule utility matters"


def run(study_id: str) -> pd.DataFrame:
    a = assumptions()
    hurdle = float(a["hurdle_margin_pct"]["value"])
    eco = pd.read_parquet(OUTPUTS / f"economics_{study_id}.parquet")

    base = eco[(eco.fare_scenario_pct == 0) & (eco.fuel_scenario_pct == 0)]
    fare_dn = eco[(eco.fare_scenario_pct == eco.fare_scenario_pct.min())
                  & (eco.fuel_scenario_pct == 0)]
    fuel_up = eco[(eco.fare_scenario_pct == 0)
                  & (eco.fuel_scenario_pct == eco.fuel_scenario_pct.max())]

    m = (base
         .merge(fare_dn[["cbsa", "margin_pct"]].rename(
             columns={"margin_pct": "fare_down_margin"}), on="cbsa")
         .merge(fuel_up[["cbsa", "margin_pct"]].rename(
             columns={"margin_pct": "fuel_down_margin"}), on="cbsa"))

    def verdict(r):
        if pd.isna(r["margin_pct"]) or r["margin_pct"] < 0:
            return "PASS"
        if (r["margin_pct"] >= hurdle and r["fare_down_margin"] > 0
                and r["belf"] <= BELF_MAX):
            return "LAUNCH"
        return "MONITOR"

    m["verdict"] = m.apply(verdict, axis=1)
    m["confidence"] = m.apply(confidence, axis=1)
    m["driver_1"] = ("base margin " + m["margin_pct"].round(1).astype(str)
                     + "% vs hurdle " + str(hurdle) + "%")
    m["driver_2"] = ("modeled share "
                     + (100 * m["proposed_share"]).round(0).astype(int).astype(str)
                     + "% of " + (m["demand_pax_yr"] / 1000).round(0).astype(int)
                     .astype(str) + "k pax/yr (" + m["demand_source"] + ")")
    m["top_risk"] = m.apply(top_risk, axis=1)
    m["key_assumptions"] = (
        "transfer factor; fare premium; airport fee proxy"
        if study(study_id)["market_scope"] == "transborder"
        else "comparator cost rates; spill cov; fee proxy")

    cols = ["study_id", "metro_name", "dest_airport", "dist_mi", "verdict",
            "confidence", "margin_pct", "fare_down_margin", "fuel_down_margin",
            "belf", "load_factor", "proposed_share", "demand_pax_yr",
            "demand_source", "n_nonstop_incumbents", "top_competitor",
            "driver_1", "driver_2", "top_risk", "key_assumptions"]
    out = (m[cols].sort_values(["verdict", "margin_pct"],
                               ascending=[True, False])
           .reset_index(drop=True))
    out.to_parquet(OUTPUTS / f"screen_{study_id}.parquet", index=False)
    out.to_csv(OUTPUTS / f"screen_{study_id}.csv", index=False)
    return out


if __name__ == "__main__":
    for s in ("westjet_yyc", "alaska_sea", "porter_yyz"):
        try:
            df = run(s)
            print(f"{s}: {df['verdict'].value_counts().to_dict()}")
            print(df[df.verdict == 'LAUNCH'][["metro_name", "margin_pct",
                                              "load_factor"]].head(5).to_string())
        except Exception as e:  # noqa: BLE001
            print(f"{s}: {e}")
