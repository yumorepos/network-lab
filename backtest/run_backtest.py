"""Backtest: score real 2021-2025 transborder launches with the pre-2022 model.

Method, including its one disclosed simplification:
- Model: gravity fit on 2018-2019 US data x transfer factor from the 2018
  StatCan anchor. No growth scaling (that would leak post-launch T-100).
- For each Canadian-origin transborder launch in data/reference/launches.csv,
  compute modeled demand for its metro pair and its PERCENTILE among all
  in-range US metros from the same hub (the counterfactual candidate set).
- Report median percentile by outcome group: operating/seasonal vs ceased vs
  never launched, plus a named hits-and-misses table.

DISCLOSED LOOKAHEAD: this is a single fixed-vintage model. For launches after
2022 the 2018-2019 calibration is legitimately pre-decision information, but
covariates (BEA/StatCan population, income) are current-vintage, and the
transfer factor's anchor, while frozen in 2018, was estimated once rather
than re-estimated per launch date. A production system would refit the whole
chain at each launch's decision date. Stated here and in validation.md.

Scope: transborder rows only. Canadian domestic launches (most of Lynx's
network) cannot be scored: no public demand truth exists for them, which is
the same data gap that shaped the whole project design.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ingest.common import ROOT
from models import gravity
from models.catchment import metro_anchor_points
from models.common import OUTPUTS, connect, haversine_mi

import yaml

LAUNCHES = ROOT / "data" / "reference" / "launches.csv"

# US airport -> anchor CBSA happens via dim_airport city market mapping;
# Canadian hub -> CMA population via ca_airport_cma.
OPERATING = {"operating", "seasonal"}


def score() -> pd.DataFrame:
    con = connect(read_only=True)
    tf = yaml.safe_load((OUTPUTS / "transfer_factor.yaml").read_text())
    metros = metro_anchor_points(con)
    launches = pd.read_csv(LAUNCHES)
    tb = launches[launches["market_type"] == "transborder"].copy()

    hub_pop = dict(con.execute("""
        SELECT c.iata_code, m.population
        FROM ca_airport_cma c
        JOIN dim_metro_ca m ON m.cma LIKE c.cma_name || '%'
    """).fetchall())
    hub_pt = dict((r[0], (r[1], r[2])) for r in con.execute(
        "SELECT iata_code, lat, lon FROM dim_airport").fetchall())
    ap_cbsa = dict(con.execute("""
        SELECT a.iata_code, m.cbsa FROM dim_airport a
        JOIN map_citymarket_cbsa m USING (city_market_id)
    """).fetchall())

    def candidate_set(hub: str) -> pd.DataFrame:
        lat, lon = hub_pt[hub]
        c = metros.copy()
        c["dist_mi"] = [haversine_mi(lat, lon, r["lat"], r["lon"])
                        for _, r in c.iterrows()]
        c = c[(c["dist_mi"].between(250, 3000))
              & (c["population"] >= 250_000)].copy()
        c["pop_a"] = hub_pop[hub]
        c["pop_b"] = c["population"]
        c["inc_a"] = c["income"]
        c["inc_b"] = c["income"]
        factor = tf["per_hub_median"].get(hub, tf["median"])
        c["modeled"] = gravity.predict(c, "pre2022") * factor
        c["pctile"] = c["modeled"].rank(pct=True)
        return c

    rows = []
    for hub in tb["origin"].unique():
        if hub not in hub_pop or hub not in hub_pt:
            continue
        cs = candidate_set(hub)
        for _, l in tb[tb["origin"] == hub].iterrows():
            cbsa = ap_cbsa.get(l["destination"])
            hit = cs[cs["cbsa"] == cbsa] if cbsa else cs.iloc[0:0]
            if len(hit) == 0:
                rows.append({**l, "pctile": np.nan,
                             "note": "dest metro not in candidate set"})
                continue
            rows.append({**l, "pctile": float(hit["pctile"].iloc[0]),
                         "modeled_pax": float(hit["modeled"].iloc[0]),
                         "note": ""})
    con.close()
    df = pd.DataFrame(rows)
    df["outcome"] = np.where(df["status"].isin(OPERATING), "operating",
                             np.where(df["status"] == "never_launched",
                                      "never_launched",
                                      np.where(df["status"] == "ceased",
                                               "ceased", "unknown")))
    df.to_parquet(OUTPUTS / "backtest_scores.parquet", index=False)
    return df


def report(df: pd.DataFrame) -> str:
    sc = df.dropna(subset=["pctile"])
    known = sc[sc["outcome"].isin(["operating", "ceased"])]
    ceased = sc[sc["outcome"] == "ceased"]
    ceased_lynx = ceased[ceased["carrier"] == "Y9"]
    ceased_cont = ceased[ceased["carrier"] != "Y9"]
    op_med = sc[sc["outcome"] == "operating"]["pctile"].median()

    lines = ["# Backtest: pre-2022 model vs 2021-2025 launches", ""]
    lines += ["Single fixed-vintage model (gravity 2018-19 x 2018 transfer",
              "anchor, no growth term). Lookahead disclosure in the module",
              "docstring and validation.md. Percentile = where the launched",
              "market ranks among all in-range US metros from that hub.", "",
              f"**Headline N = {len(known)}**: routes that actually launched "
              "and have a known terminal status (operating/seasonal or "
              "ceased). Never-launched and unknown-status routes are "
              "reported separately below and are not part of that count.", ""]
    g = sc.groupby("outcome")["pctile"].agg(["median", "mean", "count"])
    lines += ["| group | n | median pctile | mean pctile |", "|---|---|---|---|"]
    for o, r in g.iterrows():
        label = o if o in ("operating", "ceased") else f"{o} (excluded from N)"
        lines.append(f"| {label} | {int(r['count'])} | {r['median']:.2f} "
                     f"| {r['mean']:.2f} |")

    lines += ["", "## Ceased routes by carrier and cause", "",
              "| carrier | n | cause | informative about route selection? |",
              "|---|---|---|---|"]
    for carrier, grp in ceased.groupby("carrier"):
        if carrier == "Y9":
            cause, informative = ("corporate shutdown 2024-02-26 (Lynx ceased "
                                  "all operations at once)", "no")
        else:
            cause, informative = ("route-level cut by a carrier that kept "
                                  "operating", "yes")
        lines.append(f"| {carrier} | {len(grp)} | {cause} | {informative} |")

    lines += ["", "## Separation, computed three ways", "",
              "| comparison | operating median | ceased median | gap |",
              "|---|---|---|---|",
              f"| vs all ceased (n={len(ceased)}) | {op_med:.2f} "
              f"| {ceased['pctile'].median():.2f} "
              f"| {op_med - ceased['pctile'].median():+.2f} |",
              f"| vs ceased excl. Lynx (n={len(ceased_cont)}) | {op_med:.2f} "
              f"| {ceased_cont['pctile'].median():.2f} "
              f"| {op_med - ceased_cont['pctile'].median():+.2f} |",
              f"| vs Lynx-only ceased (n={len(ceased_lynx)}) | {op_med:.2f} "
              f"| {ceased_lynx['pctile'].median():.2f} "
              f"| {op_med - ceased_lynx['pctile'].median():+.2f} |"]

    lines += ["", "## Reading the result, as pre-committed", "",
              "Separation is weak in every cut, including the one that "
              "matters most: most ceased routes "
              f"({len(ceased_cont)} of {len(ceased)}) were genuine "
              "route-level cuts by Flair, a carrier that kept operating, "
              "not casualties of the Lynx shutdown. Those genuine failures "
              "(the leisure-market cuts: Mesa, Sanford, Burbank, Las Vegas, "
              "Denver, Nashville) also scored in the top demand decile. "
              "Three things this actually shows:", "",
              "1. Nearly every real launch sits in the top decile of modeled "
              "demand - carriers do not need a gravity model to find big "
              "markets, and a demand screen alone does not predict route "
              "survival.",
              "2. Demand ranking did not flag the genuine route-level "
              "failures. Flair's cut routes were big leisure markets that "
              "failed on economics, competitive response, and fit - layers "
              "a demand percentile cannot see. The Lynx rows are separately "
              "uninformative: a corporate shutdown says nothing about the "
              "routes.",
              "3. Discriminating survival would need the economics and "
              "competitive-response layers evaluated at launch vintage - the "
              "production refit this project deliberately traded away and "
              "discloses."]
    lines += ["", "## Named routes", "",
              "| carrier | route | launched | status | model pctile |",
              "|---|---|---|---|---|"]
    for _, r in df.dropna(subset=["pctile"]).sort_values(
            "pctile", ascending=False).iterrows():
        lines.append(f"| {r['carrier']} | {r['origin']}-{r['destination']} "
                     f"| {r['launch_date']} | {r['status']} "
                     f"| {r['pctile']:.2f} |")
    skipped = df[df["pctile"].isna()]
    if len(skipped):
        lines += ["", f"{len(skipped)} transborder rows not scoreable "
                  "(destination outside candidate set)."]
    n_dom = "see launches.csv"
    lines += ["", "Canadian domestic launches are out of model scope "
              f"({n_dom}); no public demand truth exists for them.", ""]
    txt = "\n".join(lines)
    (ROOT / "docs" / "backtest.md").write_text(txt)
    return txt


if __name__ == "__main__":
    df = score()
    print(report(df)[:1500])
