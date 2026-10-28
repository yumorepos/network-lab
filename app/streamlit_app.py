"""Network Lab dashboard. Reads precomputed outputs only; no live recompute."""
from __future__ import annotations

from pathlib import Path
import html
import re

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


st.set_page_config(page_title="Network Lab | Aviation Route Research",
                   page_icon="✦", layout="wide")
# Theme is presentation-only. It does not touch the model or committed outputs.
st.markdown("<style>" + (ROOT / "app" / "theme.css").read_text() + "</style>",
            unsafe_allow_html=True)


def page_heading(section: str, title: str, subtitle: str) -> None:
    st.markdown(
        '<div class="nl-brand"><span class="nl-star"></span> NETWORK / LAB'
        ' &nbsp;·&nbsp; OPEN DATA RESEARCH</div>'
        f'<section class="nl-hero"><div class="nl-eyebrow">{html.escape(section)}</div>'
        f'<h1>{html.escape(title)}</h1>'
        f'<div class="nl-subtitle">{html.escape(subtitle)}</div></section>',
        unsafe_allow_html=True,
    )


def metric_strip(items: list[tuple[str, str]]) -> None:
    cards = "".join(
        '<div class="nl-metric">'
        f'<span class="nl-metric-label">{html.escape(label)}</span>'
        f'<span class="nl-metric-value">{html.escape(str(value))}</span>'
        '</div>' for label, value in items
    )
    n = " four" if len(items) == 4 else ""
    st.markdown(f'<div class="nl-metrics{n}">{cards}</div>',
                unsafe_allow_html=True)


def notice(message: str, muted: bool = False) -> None:
    kind = " neutral" if muted else ""
    st.markdown(f'<div class="nl-notice{kind}">{html.escape(message)}</div>',
                unsafe_allow_html=True)


def market_cards(rows: pd.DataFrame) -> None:
    cards = []
    for _, row in rows.iterrows():
        verdict = str(row["verdict"])
        klass = verdict.lower() if verdict in ("LAUNCH", "MONITOR") else ""
        cards.append(
            '<article class="nl-market"><div class="nl-market-top">'
            f'<span class="nl-market-name">{html.escape(str(row["metro_name"]))}</span>'
            f'<span class="nl-pill {klass}">{html.escape(verdict)}</span>'
            '</div><div class="nl-market-detail">'
            f'<span>MODELED MARGIN {row["margin_pct"]:.1f}%</span>'
            f'<span>LOAD FACTOR {row["load_factor"]:.0%}</span>'
            '</div></article>'
        )
    st.markdown('<div class="nl-market-grid">' + "".join(cards) + '</div>',
                unsafe_allow_html=True)


def section_heading(title: str, detail: str = "") -> None:
    st.markdown(
        '<div class="nl-section-header">'
        f'<span>{html.escape(title)}</span>'
        f'<small>{html.escape(detail)}</small></div>',
        unsafe_allow_html=True,
    )



STUDIES = {
    "WestJet YYC transborder (flagship)": "westjet_yyc",
    "Alaska SEA domestic (validation)": "alaska_sea",
    "Porter YYZ transborder (portability)": "porter_yyz",
}


def load(name: str) -> pd.DataFrame | None:
    p = OUT / name
    return pd.read_parquet(p) if p.exists() else None


st.sidebar.caption("RESEARCH WORKSPACE · SCREENING, NOT A FORECAST")
page = st.sidebar.radio("View", ["Route screen", "Market detail",
                                 "Validation", "Backtest", "About"])
study_label = st.sidebar.selectbox("Study", list(STUDIES))
sid = STUDIES[study_label]

if page == "Route screen":
    page_heading("01 / Route screening", "Route screen",
                 f"{study_label} · Fixed-gauge research screen")
    df = load(f"screen_{sid}.parquet")
    if df is None:
        st.warning("Run `make models` first.")
    else:
        counts = df["verdict"].value_counts()
        metric_strip([
            ("LAUNCH", str(int(counts.get("LAUNCH", 0)))),
            ("MONITOR", str(int(counts.get("MONITOR", 0)))),
            ("PASS", str(int(counts.get("PASS", 0)))),
        ])
        st.caption("Fixed-gauge research · 3x / 7x / 14x weekly · "
                   "not a route recommendation.")

        # Presentation only: sort order and verdicts come from the committed
        # artifact. No re-scoring, model adjustment, or new recommendations.
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
            notice(f"No tested schedule meets the {LF_FLOOR:.0%} "
                   "load-factor floor.")
        else:
            notice(f"{n_feas}/{len(show)} markets meet the "
                   f"{LF_FLOOR:.0%} load-factor floor.", muted=True)
        with st.expander("How to read these results"):
            st.caption("A single aircraft size and a fixed schedule menu are "
                       "evaluated for each candidate. Verdicts are research "
                       "screens, not operational advice. Demand may be observed "
                       "or estimated; modeled margins have uncertainty. "
                       "Row order is not a validated opportunity ranking.")

        section_heading("Explore candidate markets",
                        "Search by metro · original research order retained")
        search = st.text_input("Search markets", placeholder="e.g., Boston, Dallas...",
                               key=f"market_search_{sid}")
        filtered = (show[show["metro_name"].str.contains(re.escape(search),
                    case=False, na=False)] if search else show)
        st.caption(f"Showing {min(10, len(filtered))} of {len(filtered)} matching "
                   f"markets. {len(show)} total; expand for full data.")
        market_cards(filtered.head(10))
        with st.expander("Full research table · all candidates and fields"):
            st.dataframe(show, use_container_width=True,
                         hide_index=True, height=460)
        st.download_button("Download full CSV", df.to_csv(index=False),
                           f"screen_{sid}.csv")


elif page == "Market detail":
    page_heading("02 / Scenario explorer", "Market detail",
                 f"{study_label} · One evaluated schedule, scenario economics")
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
                notice(f"Below {LF_FLOOR:.0%} load-factor floor. "
                       "Displayed frequency is a fallback.")
                with st.expander("Why the fallback appears"):
                    st.caption("None of the tested frequencies clears the "
                               "load-factor threshold. The displayed option "
                               "is a research comparison, not a selected "
                               "flight schedule.")
        base = e[(e.fare_scenario_pct == 0) & (e.fuel_scenario_pct == 0)].iloc[0]
        metric_strip([
            ("Demand / year", f"{base['demand_pax_yr']:,.0f}"),
            ("Modeled share", f"{base['proposed_share']:.0%}"),
            ("Base margin", f"{base['margin_pct']:.1f}%"),
            ("Break-even LF", f"{base['belf']:.2f}"),
        ])
        st.caption(f"Demand source: {base['demand_source']} / "
                   f"{base.get('demand_method', '')}. All figures are modeled "
                   "or observed as marked in source artifacts.")
        grid = e.pivot_table(index="fuel_scenario_pct",
                             columns="fare_scenario_pct",
                             values="margin_pct")
        fig = px.imshow(grid, text_auto=".1f", aspect="auto",
                        labels=dict(x="fare scenario %", y="fuel scenario %",
                                    color="margin %"),
                        color_continuous_scale="RdYlGn",
                        color_continuous_midpoint=0)
        fig.update_layout(template="plotly_dark", paper_bgcolor="#0a0b0e",
                          plot_bgcolor="#12151a", font_color="#d8dee6")
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
    page_heading("03 / Evidence & checks", "Validation",
                 "Reconciliation, share error, and known limits")
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
    page_heading("04 / Historical evidence", "Backtest & replay",
                 "Two distinct evaluations with explicitly bounded claims")
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
    page_heading("05 / Project notes", "About Network Lab",
                 "Architecture, assumptions, data sources and project history")
    st.markdown((ROOT / "README.md").read_text())
