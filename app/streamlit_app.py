"""Network Lab dashboard. Reads precomputed outputs only; no live recompute."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "parquet" / "outputs"
DOCS = ROOT / "docs"

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
        st.caption("Margins are contribution over direct operating cost plus "
                   "the airport-fee proxy; demand rows are flagged observed "
                   "or modeled. See Validation for what that means.")
        show = df[["metro_name", "verdict", "confidence", "margin_pct",
                   "fare_down_margin", "fuel_down_margin", "belf",
                   "load_factor", "proposed_share", "demand_pax_yr",
                   "demand_source", "n_nonstop_incumbents", "top_competitor",
                   "top_risk"]]
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
        mkt = st.selectbox("Market", sorted(eco["metro_name"].unique()))
        e = eco[eco["metro_name"] == mkt]
        base = e[(e.fare_scenario_pct == 0) & (e.fuel_scenario_pct == 0)].iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Demand (pax/yr)", f"{base['demand_pax_yr']:,.0f}",
                  help=f"source: {base['demand_source']}")
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
    st.title("Backtest")
    p = DOCS / "backtest.md"
    if p.exists():
        st.markdown(p.read_text())
    else:
        st.warning("Run `python -m backtest.run_backtest`.")

else:
    st.title("Network Lab")
    st.markdown((ROOT / "README.md").read_text())
