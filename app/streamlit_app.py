"""Network Lab dashboard. Reads precomputed outputs only; no live recompute."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "parquet" / "outputs"
DOCS = ROOT / "docs"

# The feasibility floor is read from the one assumptions file, never restated.
LF_FLOOR = float(yaml.safe_load((ROOT / "config" / "assumptions.yaml")
                                .read_text())["min_feasible_load_factor"]["value"])

st.set_page_config(page_title="Network Lab", layout="wide")

STUDIES = {
    "WestJet YYC transborder (flagship)": "westjet_yyc",
    "Alaska SEA domestic (validation)": "alaska_sea",
    "Porter YYZ transborder (portability)": "porter_yyz",
}


def load(name: str) -> pd.DataFrame | None:
    p = OUT / name
    return pd.read_parquet(p) if p.exists() else None


page = st.sidebar.radio("View", ["Route screen", "Market detail",
                                 "Validation", "Backtest", "About"])
study_label = st.sidebar.selectbox("Study", list(STUDIES))
sid = STUDIES[study_label]

if page == "Route screen":
    st.title(f"Route screen: {study_label}")
    df = load(f"screen_{sid}.parquet")
    if df is None:
        st.warning("Run `make models` first.")
    else:
        counts = df["verdict"].value_counts()
        c1, c2, c3 = st.columns(3)
        c1.metric("LAUNCH", int(counts.get("LAUNCH", 0)))
        c2.metric("MONITOR", int(counts.get("MONITOR", 0)))
        c3.metric("PASS", int(counts.get("PASS", 0)))
        st.caption("Fixed-gauge route screening. Each market is evaluated "
                   "against this study's single configured gauge and a fixed "
                   "schedule menu (3x/7x/14x weekly); the screen reports the "
                   "best feasible option, or that none is feasible, and judges "
                   "that schedule. This is not fleet assignment or frequency "
                   "selection. Margins are a fully-allocated proxy; demand "
                   "rows are flagged observed or modeled. See Validation.")
        # Presentation only: the artifact is already ordered verdict first,
        # then margin within verdict (models/screen.py). Nothing is re-scored
        # or re-ranked here; `feasible` is a readout of the existing load
        # factor against the configured floor, not a new criterion.
        show = df.copy()
        show.insert(2, "feasible", show["load_factor"] >= LF_FLOOR)
        show = show[["metro_name", "verdict", "feasible", "confidence",
                     "chosen_freq_wk", "chosen_seats", "margin_pct",
                     "fare_down_margin", "fuel_down_margin", "belf",
                     "load_factor", "proposed_share", "demand_pax_yr",
                     "demand_method", "n_nonstop_incumbents",
                     "top_competitor", "top_risk"]]
        n_feas = int(show["feasible"].sum())
        if n_feas == 0:
            st.warning(
                f"No candidate in this study clears the {LF_FLOOR:.0%} "
                f"load-factor floor at any tested frequency. Rows are ordered "
                f"by verdict and then by margin, which is a research "
                f"comparator retained for the historical replay; it is not an "
                f"opportunity ranking, and the row at the top is not a "
                f"recommendation.")
        else:
            st.info(
                f"{n_feas} of {len(show)} candidates clear the "
                f"{LF_FLOOR:.0%} load-factor floor. Read the verdict first: "
                f"ordering within a verdict is by margin and is a research "
                f"comparator, not an opportunity ranking.")
        st.dataframe(show, use_container_width=True, height=560)
        st.download_button("Download CSV", df.to_csv(index=False),
                           f"screen_{sid}.csv")

elif page == "Market detail":
    st.title(f"Market detail: {study_label}")
    eco = load(f"economics_{sid}.parquet")
    comp = load(f"competition_{sid}.parquet")
    if eco is None:
        st.warning("Run `make models` first.")
    else:
        scr = load(f"screen_{sid}.parquet")
        mkt = st.selectbox("Market", sorted(eco["metro_name"].unique()))
        e = eco[eco["metro_name"] == mkt]
        # filter economics to the schedule the screen evaluated (the frequency
        # and gauge it reported), so the scenario grid is one schedule
        if scr is not None and (scr["metro_name"] == mkt).any():
            srow = scr[scr["metro_name"] == mkt].iloc[0]
            e = e[(e["freq_wk"] == srow["chosen_freq_wk"])
                  & (e["seats"] == srow["chosen_seats"])]
            feasible = float(srow["load_factor"]) >= LF_FLOOR
            st.caption(f"Evaluated schedule: {int(srow['chosen_freq_wk'])}x "
                       f"weekly x {int(srow['chosen_seats'])} seats "
                       f"({srow['chosen_gauge']}) - verdict {srow['verdict']}")
            if not feasible:
                st.warning(
                    f"No option on the tested menu clears the "
                    f"{LF_FLOOR:.0%} load-factor floor for this market "
                    f"(best achieved {srow['load_factor']:.0%}). The "
                    f"frequency shown is the fallback the screen reports when "
                    f"nothing is feasible, not a selected schedule.")
        base = e[(e.fare_scenario_pct == 0) & (e.fuel_scenario_pct == 0)].iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Demand (pax/yr)", f"{base['demand_pax_yr']:,.0f}",
                  help=f"source: {base['demand_source']} / "
                       f"{base.get('demand_method','')}")
        c2.metric("Modeled share", f"{base['proposed_share']:.0%}")
        c3.metric("Base margin", f"{base['margin_pct']:.1f}%")
        c4.metric("Break-even LF", f"{base['belf']:.2f}")
        grid = e.pivot_table(index="fuel_scenario_pct",
                             columns="fare_scenario_pct",
                             values="margin_pct")
        fig = px.imshow(grid, text_auto=".1f", aspect="auto",
                        labels=dict(x="fare scenario %", y="fuel scenario %",
                                    color="margin %"),
                        color_continuous_scale="RdYlGn",
                        color_continuous_midpoint=0)
        st.plotly_chart(fig, use_container_width=True)
        if comp is not None:
            cm = comp[comp["cbsa"] == e["cbsa"].iloc[0]]
            st.subheader("Reconstructed competition")
            if len(cm):
                st.dataframe(cm[["carrier", "itin_type", "freq_wk",
                                 "elapsed_h", "connect_ap"]]
                             .sort_values(["itin_type", "freq_wk"],
                                          ascending=[True, False]),
                             use_container_width=True)
            else:
                st.info("No incumbent itineraries reconstructed - check the "
                        "share number skeptically, not gratefully.")

elif page == "Validation":
    st.title("Validation")
    for f in ("validation.md", "reconciliation.md"):
        p = DOCS / f
        if p.exists():
            st.markdown(p.read_text())
            st.divider()
    tp = load("transfer_pairs.parquet")
    if tp is not None:
        st.subheader("Transfer factor distribution (2018 anchor pairs)")
        fig = px.histogram(tp, x="transfer", nbins=30,
                           hover_data=["geo"])
        st.plotly_chart(fig, use_container_width=True)

elif page == "Backtest":
    st.title("Backtest and predictive validation")
    st.info(
        "**Two different things live here, and only one of them is a test of "
        "this engine.**\n\n"
        "**The launch backtest** (below) scores real 2021-2025 launches on "
        "demand percentile using a single pre-2022 model. It asks whether "
        "demand rank alone separates survivors from failures. It does not.\n\n"
        "**The point-in-time replay** reconstructs the full verdict chain at "
        "three historical decision dates and compares the whole engine against "
        "a demand-only ranking on identical rows. Its result: no detectable "
        "incremental ranking value at effects larger than the study's "
        "resolution, with smaller effects unresolved. That is a bounded "
        "negative, not a demonstration that the two are equivalent.\n\n"
        "The screen on the other pages is a **screening** output. It has not "
        "been shown to rank better than demand, and it is not presented as a "
        "validated predictor.")
    with st.expander("What bounds the predictive result"):
        st.markdown(
            "- 15 positive rows rest on only **10 distinct launch events** "
            "across **3 decision vintages**\n"
            "- roughly **5 net launch events** spread across two vintages is "
            "the optimistic detectability floor, and it is a floor because it "
            "was built by an oracle construction\n"
            "- the largest observed difference was **one event**\n"
            "- an effect confined to a single vintage cannot be identified at "
            "any magnitude this sample permits\n"
            "- **k=20 is arithmetically saturated**: the demand comparator "
            "already contains every positive, so nothing can beat it there\n\n"
            "Full measurement in `docs/STAGE_2R0_RESOLUTION.md`; scope and "
            "evidence boundary in `docs/LIMITATIONS.md`.")
    st.divider()
    p = DOCS / "backtest.md"
    if p.exists():
        st.markdown(p.read_text())
    else:
        st.warning("Run `python -m backtest.run_backtest`.")

else:
    st.title("Network Lab")
    st.markdown((ROOT / "README.md").read_text())
