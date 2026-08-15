"""W1.4 decision replay: the four metric families, exactly as frozen.

Implements `docs/W1.4_REPLAY_PROTOCOL.md`. Every design choice that could have
been made after seeing results (ranking score, k values, frequency proxy,
bootstrap design, feasibility classification, no Cox model) was frozen in that
document at commit e6ea62e, before this file existed.

Writes to data/parquet/replay/ (gitignored) and prints a report. Touches no
model, no assumption and no tracked artifact.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from models.common import connect
from replay import snapshot as S
from replay.vintage import protocol
from warehouse import route_spells

OUT = None          # set in main()
RNG_SEED = 7
N_BOOT = 2000
K_VALUES = (5, 10, 20)
HORIZON_F1 = 24

# Frozen in the protocol, section 1.1.
DECISION_DATES = {
    "westjet_yyc": [202201, 202301, 202401],
    "alaska_sea": [202201, 202301, 202401],
    "porter_yyz": [202401],
}
BRAND_CERTS = {
    "westjet_yyc": ["WS", "WO", "WR"],
    "alaska_sea": ["AS", "QX"],
    "porter_yyz": ["PD"],
}
HUBS = {"westjet_yyc": "YYC", "alaska_sea": "SEA", "porter_yyz": "YYZ"}
PANEL_END = 202604
REPORTING_LAG = 2


# --------------------------------------------------------------- outcomes
def build_outcomes(con) -> pd.DataFrame:
    """Launch events per study, rolled up to metro, from the route-spell
    register. This is the register's Milestone A role: outcomes, not decisions.
    """
    spells = route_spells.build(con)
    ap = con.execute("""
        SELECT a.iata_code, a.iso_country, m.cbsa
        FROM dim_airport a
        LEFT JOIN map_citymarket_cbsa m USING (city_market_id)
    """).df()
    country = dict(zip(ap["iata_code"], ap["iso_country"]))
    cbsa = dict(zip(ap["iata_code"], ap["cbsa"]))

    out = []
    for sid, certs in BRAND_CERTS.items():
        hub = HUBS[sid]
        sp = spells[spells["carrier"].isin(certs)].copy()
        sp = sp[(sp["airport_a"] == hub) | (sp["airport_b"] == hub)].copy()
        sp["other"] = np.where(sp["airport_a"] == hub, sp["airport_b"],
                               sp["airport_a"])
        sp = sp[sp["other"].map(country) == "US"].copy()
        sp["cbsa"] = sp["other"].map(cbsa)
        sp["study_id"] = sid
        sp["first_ym"] = sp["first_year"] * 12 + sp["first_month"]
        sp["last_ym"] = sp["last_year"] * 12 + sp["last_month"]
        out.append(sp[["study_id", "carrier", "other", "cbsa", "first_ym",
                       "last_ym", "seasonal_flag", "status",
                       "initial_freq_wk", "peak_freq_wk"]])
    return pd.concat(out, ignore_index=True).dropna(subset=["cbsa"])


def _ym_from_yyyymm(v: int) -> int:
    return (v // 100) * 12 + (v % 100)


# --------------------------------------------------------------- bootstrap
def cluster_bootstrap(df: pd.DataFrame, stat_fn, cluster="cbsa",
                      n=N_BOOT, seed=RNG_SEED) -> tuple[float, float, float]:
    """Percentile interval, resampling CLUSTERS (metros), per protocol s3."""
    point = stat_fn(df)
    clusters = df[cluster].unique()
    if len(clusters) < 2:
        return point, np.nan, np.nan
    rng = np.random.default_rng(seed)
    groups = {c: g for c, g in df.groupby(cluster)}
    vals = []
    for _ in range(n):
        pick = rng.choice(clusters, size=len(clusters), replace=True)
        vals.append(stat_fn(pd.concat([groups[c] for c in pick],
                                      ignore_index=True)))
    vals = [v for v in vals if v == v]
    if not vals:
        return point, np.nan, np.nan
    return point, float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


# ----------------------------------------------------------------- family 1
def _agreement_at_k(rows: pd.DataFrame, score: str, k: int) -> float:
    """Fraction of the top k by `score` that launched, averaged over dates."""
    per = []
    for _, g in rows.groupby("cutoff"):
        top = g.nlargest(min(k, len(g)), score)
        if len(top):
            per.append(top["positive"].mean())
    return float(np.mean(per)) if per else np.nan


def _recall_at_k(rows: pd.DataFrame, score: str, k: int) -> float:
    per = []
    for _, g in rows.groupby("cutoff"):
        pos = g["positive"].sum()
        if pos == 0:
            continue
        top = g.nlargest(min(k, len(g)), score)
        per.append(top["positive"].sum() / pos)
    return float(np.mean(per)) if per else np.nan


def family_1_and_4(decision_rows: pd.DataFrame) -> dict:
    res = {}
    for sid, rows in decision_rows.groupby("study_id"):
        entry = {"n_decision_rows": int(len(rows)),
                 "n_unique_metros": int(rows["cbsa"].nunique()),
                 "n_positives": int(rows["positive"].sum()),
                 "n_decision_dates": int(rows["cutoff"].nunique()),
                 "positives_by_date": {
                     str(c): int(g["positive"].sum())
                     for c, g in rows.groupby("cutoff")},
                 "k": {}}
        for k in K_VALUES:
            a = cluster_bootstrap(rows, lambda d, k=k: _agreement_at_k(
                d, "score_model", k))
            r = cluster_bootstrap(rows, lambda d, k=k: _recall_at_k(
                d, "score_model", k))
            ad = cluster_bootstrap(rows, lambda d, k=k: _agreement_at_k(
                d, "score_demand", k))
            rd = cluster_bootstrap(rows, lambda d, k=k: _recall_at_k(
                d, "score_demand", k))
            diff_a = cluster_bootstrap(
                rows, lambda d, k=k: (_agreement_at_k(d, "score_model", k)
                                      - _agreement_at_k(d, "score_demand", k)))
            diff_r = cluster_bootstrap(
                rows, lambda d, k=k: (_recall_at_k(d, "score_model", k)
                                      - _recall_at_k(d, "score_demand", k)))
            entry["k"][k] = {
                "model_agreement": a, "model_recall": r,
                "demand_agreement": ad, "demand_recall": rd,
                "diff_agreement": diff_a, "diff_recall": diff_r,
            }
        res[sid] = entry
    return res


# ----------------------------------------------------------------- family 2
def family_2(outcomes: pd.DataFrame) -> dict:
    res = {}
    for sid, dates in DECISION_DATES.items():
        first = _ym_from_yyyymm(min(dates))
        sp = outcomes[(outcomes["study_id"] == sid)
                      & (outcomes["first_ym"] >= first)]
        sp = sp[~((sp["first_ym"] - 1) // 12).isin([2020, 2021])]
        entry = {}
        for h in (24, 36):
            el = sp[sp["first_ym"] + h <= _ym_from_yyyymm(PANEL_END)]
            ended = el["last_ym"] < el["first_ym"] + h
            event = ended & (el["last_ym"]
                             < _ym_from_yyyymm(PANEL_END) - REPORTING_LAG)
            entry[f"{h}m"] = {
                "eligible": int(len(el)),
                "events": int(event.sum()),
                "censored": int(len(el) - event.sum()),
                "seasonal_eligible": int(el["seasonal_flag"].sum()),
                "events_among_seasonal": int(
                    (event & el["seasonal_flag"]).sum()),
                "events_among_year_round": int(
                    (event & ~el["seasonal_flag"]).sum()),
                "corporate_shutdown_events": 0,
            }
        res[sid] = entry
    return res


# ----------------------------------------------------------------- family 3
def family_3(decision_rows: pd.DataFrame, outcomes: pd.DataFrame) -> dict:
    """Model chosen frequency at the last decision date preceding the launch,
    against the observed opening frequency. Primary proxy first3_max."""
    proxy = protocol()["frequency_proxy"]["primary"]["value"]
    assert proxy == "first3_max", f"protocol froze first3_max, got {proxy}"
    rows = []
    for sid, dates in DECISION_DATES.items():
        launches = outcomes[outcomes["study_id"] == sid]
        for _, L in launches.iterrows():
            prior = [d for d in dates if _ym_from_yyyymm(d) < L["first_ym"]]
            if not prior:
                continue
            cut = max(prior)
            m = decision_rows[(decision_rows["study_id"] == sid)
                              & (decision_rows["cutoff"] == cut)
                              & (decision_rows["cbsa"] == L["cbsa"])]
            if not len(m):
                continue
            rows.append({
                "study_id": sid, "cbsa": L["cbsa"],
                "metro_name": m["metro_name"].iloc[0],
                "cutoff": cut, "launch_ym": int(L["first_ym"]),
                "chosen_freq_wk": float(m["chosen_freq_wk"].iloc[0]),
                "observed_freq_wk": float(L["initial_freq_wk"]),
                "seasonal": bool(L["seasonal_flag"]),
            })
    df = pd.DataFrame(rows)
    if not len(df):
        return {"paired": 0, "note": "no launch had a preceding decision date"}
    df["bias"] = df["chosen_freq_wk"] - df["observed_freq_wk"]
    df["ratio"] = df["chosen_freq_wk"] / df["observed_freq_wk"]
    res = {"paired_total": int(len(df)), "by_study": {}}
    for sid, g in df.groupby("study_id"):
        b = cluster_bootstrap(g, lambda d: float(d["bias"].median()))
        r = cluster_bootstrap(g, lambda d: float(d["ratio"].median()))
        res["by_study"][sid] = {
            "n": int(len(g)),
            "median_chosen": float(g["chosen_freq_wk"].median()),
            "median_observed": float(g["observed_freq_wk"].median()),
            "median_bias": b, "median_ratio": r,
            "mae": float(g["bias"].abs().mean()),
            "share_chose_minimum_option": float(
                (g["chosen_freq_wk"] == g["chosen_freq_wk"].min()).mean()),
            "n_seasonal": int(g["seasonal"].sum()),
        }
    pooled_b = cluster_bootstrap(df, lambda d: float(d["bias"].median()))
    pooled_r = cluster_bootstrap(df, lambda d: float(d["ratio"].median()))
    res["pooled"] = {"n": int(len(df)), "median_bias": pooled_b,
                     "median_ratio": pooled_r,
                     "mae": float(df["bias"].abs().mean())}
    res["_frame"] = df
    return res


# -------------------------------------------------------------------- main
def main() -> dict:
    global OUT
    from ingest.common import DATA_PARQUET
    OUT = DATA_PARQUET / "replay"
    OUT.mkdir(parents=True, exist_ok=True)

    con = connect(read_only=True)
    outcomes = build_outcomes(con)
    outcomes.to_parquet(OUT / "outcomes.parquet", index=False)

    all_rows, prov = [], []
    for sid, dates in DECISION_DATES.items():
        for cut in dates:
            snap = S.snapshot(sid, cut, con)
            scr = snap["screen"]
            v = snap["vintages"]
            pf = v.provenance_frame()
            pf["study_id"], pf["cutoff"] = sid, cut
            prov.append(pf)

            launched = outcomes[(outcomes["study_id"] == sid)
                                & (outcomes["first_ym"] > _ym_from_yyyymm(cut))
                                & (outcomes["first_ym"]
                                   <= _ym_from_yyyymm(cut) + HORIZON_F1)]
            pos = set(launched["cbsa"])
            r = scr[["cbsa", "metro_name", "verdict", "chosen_freq_wk",
                     "margin_pct", "annual_contribution", "demand_pax_yr",
                     "proposed_share", "demand_method",
                     "n_nonstop_incumbents"]].copy()
            r["study_id"], r["cutoff"] = sid, cut
            r["positive"] = r["cbsa"].isin(pos).astype(int)
            # frozen ranking scores, protocol section 4
            r["score_model"] = r["margin_pct"]
            r["score_demand"] = r["demand_pax_yr"].rank(pct=True)
            all_rows.append(r)
            print(f"[replay] {sid} @ {cut}: {len(r)} candidates, "
                  f"{int(r['positive'].sum())} positives, verdicts "
                  f"{r['verdict'].value_counts().to_dict()}")
    con.close()

    decision_rows = pd.concat(all_rows, ignore_index=True)
    decision_rows.to_parquet(OUT / "decision_rows.parquet", index=False)
    pd.concat(prov, ignore_index=True).to_parquet(
        OUT / "provenance.parquet", index=False)

    results = {
        "family_1_and_4": family_1_and_4(decision_rows),
        "family_2": family_2(outcomes),
        "family_3": family_3(decision_rows, outcomes),
    }
    f3 = results["family_3"].pop("_frame", None)
    if f3 is not None:
        f3.to_parquet(OUT / "rightsizing_pairs.parquet", index=False)
    (OUT / "results.json").write_text(json.dumps(results, indent=2,
                                                 default=str))
    return results


if __name__ == "__main__":
    r = main()
    print()
    print(json.dumps(r, indent=2, default=str))
