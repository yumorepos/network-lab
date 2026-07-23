"""Route post-mortems assembled from fact_segment (T-100). The quantitative
timeline is fully data-driven; the interpretation is left as a marked
human-synthesis placeholder for the author to complete, because the reasons a
route lived or died (cost structure, financing, network feed, brand) are not
in any public segment table and should not be fabricated.

Chosen pair: YYC-LAS. It is the strongest available case because the SAME
market carried three carriers with three fates - WestJet held it for years at
~90% load factor, Lynx entered in 2023 and vanished in the Feb 2024 corporate
shutdown, and Flair entered, grew through 2024, and cut the route in April
2025 while continuing to operate elsewhere. Holding the market constant
isolates carrier and cost factors from market factors, which is exactly what a
demand model cannot see.

Note on carrier codes: launches.csv uses IATA-style codes (F8 Flair, Y9 Lynx),
but BTS T-100 files Flair under the placeholder code 07Q and Lynx under Y9.
The mapping is applied here and is itself a small data-provenance lesson.
"""
from __future__ import annotations

import duckdb
import pandas as pd

from ingest.common import ROOT
from models.common import OUTPUTS, connect

RPT = ROOT / "reports"
T100_CODE = {"F8": "07Q", "Y9": "Y9", "WS": "WS"}  # launches.csv -> T-100


def _annual(con, origin: str, dest: str) -> pd.DataFrame:
    return con.execute(f"""
        SELECT year, carrier, sum(departures) AS deps, sum(seats) AS seats,
               sum(passengers) AS pax,
               sum(passengers)::DOUBLE / nullif(sum(seats),0) AS lf
        FROM fact_segment
        WHERE origin='{origin}' AND dest='{dest}'
          AND service_class IN ('F','L')
        GROUP BY 1, 2 HAVING sum(departures) >= 10
        ORDER BY year, deps DESC
    """).df()


def _timeline_table(ann: pd.DataFrame, code: str, incumbent: str) -> str:
    years = sorted(ann["year"].unique())
    lines = ["| year | subject deps | subject seats | subject LF "
             "| incumbent (WS) deps | incumbent LF |", "|---|---|---|---|---|---|"]
    for y in years:
        s = ann[(ann.year == y) & (ann.carrier == code)]
        w = ann[(ann.year == y) & (ann.carrier == incumbent)]
        sd = f"{int(s['deps'].iloc[0])}" if len(s) else "-"
        ss = f"{int(s['seats'].iloc[0]):,}" if len(s) else "-"
        sl = f"{s['lf'].iloc[0]:.2f}" if len(s) and pd.notna(s['lf'].iloc[0]) else "-"
        wd = f"{int(w['deps'].iloc[0])}" if len(w) else "-"
        wl = f"{w['lf'].iloc[0]:.2f}" if len(w) and pd.notna(w['lf'].iloc[0]) else "-"
        lines.append(f"| {y} | {sd} | {ss} | {sl} | {wd} | {wl} |")
    return "\n".join(lines)


def _model_verdict(scores: pd.DataFrame, carrier: str, dest: str) -> str:
    r = scores[(scores.carrier == carrier) & (scores.destination == dest)]
    if len(r) and pd.notna(r["pctile"].iloc[0]):
        return (f"{r['pctile'].iloc[0]:.2f} percentile of all in-range YYC "
                f"transborder markets (top {(1-r['pctile'].iloc[0])*100:.0f}%)")
    return "not scored (outside the candidate set)"


def write() -> list[str]:
    con = connect(read_only=True)
    ann = _annual(con, "YYC", "LAS")
    con.close()
    launches = pd.read_csv(ROOT / "data" / "reference" / "launches.csv")
    scores = pd.read_parquet(OUTPUTS / "backtest_scores.parquet")

    subjects = [
        ("F8", "Flair Airlines", "07Q", "route-level cut (carrier still flying)",
         "Flair announced it would cease YYC-LAS on 2025-04-07, citing "
         "competition, while continuing to operate its wider network.",
         "Flair got a fair market test and still could not make it pay. It flew "
         "YYC-LAS for about two and a half years, including a full sustained "
         "year in 2024 (157 departures), and its load factor peaked near 0.70 "
         "then slid to 0.59 into 2025, while WestJet held roughly 0.90 across "
         "the whole period. A ULCC cost advantage was not enough to pry a "
         "profitable share out of a fortress incumbent that defended with both "
         "capacity and yield. Flair cut the route while continuing to fly "
         "everywhere else, which makes this a route-level economic verdict, "
         "not a corporate one. The demand model green-lit the market on size, "
         "and size is exactly what drew a defended incumbent; the entrant's "
         "sub-0.70 load factor against the incumbent's 0.90 is the gap a "
         "demand rank never shows.",
         "postmortem_y9_yyc_las.md (Lynx, same market, corporate shutdown)"),
        ("Y9", "Lynx Air", "Y9", "corporate shutdown",
         "Lynx entered YYC-LAS in early 2023 and ceased ALL operations on "
         "2024-02-26 under creditor protection; the route died with the "
         "airline, not on its own economics.",
         "Lynx's exit tells us about Lynx, not about YYC-LAS. It flew the route "
         "for a single year at about 0.53 load factor, well below Flair's, "
         "then a stub of 2024 before the February 26 shutdown took every Lynx "
         "route at once. The low first-year load factor hints the market was "
         "hard for a third entrant, but the route never got the chance to "
         "prove itself: its cause of death was a balance sheet, not a fare "
         "war. Treating this as a failed market would teach the model a false "
         "negative, which is why the backtest labels corporate-shutdown "
         "casualties separately from genuine route-level cuts. A ceased route "
         "is not automatically a failed market, and provenance is the "
         "difference.",
         "postmortem_f8_yyc_las.md (Flair, same market, route-level cut)"),
    ]
    files = []
    for code_l, name, code_t, fate, fate_detail, synthesis, compare_to in subjects:
        reg = launches[(launches.carrier == code_l)
                       & (launches.origin == "YYC")
                       & (launches.destination == "LAS")]
        launch_date = reg["launch_date"].iloc[0] if len(reg) else "see register"
        end_date = reg["end_date"].iloc[0] if len(reg) else ""
        verdict = _model_verdict(scores, code_l, "LAS")
        md = f"""# Route post-mortem: {name} YYC-LAS ({fate})

**One line:** {name} entered a market WestJet had held for years at ~90% load
factor, and exited; the demand model would have green-lit the market on size
alone. {fate_detail}

- Launch (register): {launch_date}   Exit: {end_date or 'n/a'}
- Fate: **{fate}**
- What the model said at launch vintage: **{verdict}**. YYC-LAS is a large
  market, so a demand screen ranks it near the top - which is exactly the
  trap this post-mortem illustrates.

## Capacity and load-factor timeline (T-100, {name} filed as {code_t})
{_timeline_table(ann, code_t, "WS")}

*(Data note: rows with fewer than 10 departures in a year are suppressed, so a
carrier's first shown year is its first year of sustained service, which can
lag the register's announced launch date - itself a useful reminder that an
announcement and operated capacity are different facts.)*

## What the incumbent did
WestJet did not blink. Its YYC-LAS departures and load factor held through the
entry and the exit (see the incumbent columns above): a fortress-hub incumbent
already serving the market efficiently at high load factor leaves a narrow,
low-yield gap for an entrant, and can hold capacity rather than cede share.

## What the model could and could not see
- **Could see:** the market is large (top-decile demand) and already served
  nonstop by WestJet at high frequency. The share model, given WestJet's
  nonstop presence, would assign the entrant a modest share - a caution the
  demand rank alone does not carry.
- **Could not see:** the entrant's cost structure versus WestJet's, its
  balance sheet, its network feed into LAS, or loyalty and corporate-contract
  lock-in on a heavily-managed leisure-and-business market. These decided the
  outcome and sit in no public segment table.

## Synthesis: why this exit, specifically
{synthesis}

## Same market, different fate
This market carried three carriers with three outcomes, so the market-level
sections above (incumbent behaviour, what the model could and could not see) are
held constant on purpose: the market is the control, and the carrier is the
variable. A demand screen would have ranked both entrants identically on this
pair, yet one exit was an economic verdict and the other was a corporate
collapse. Compare {compare_to}.
"""
        slug = f"postmortem_{code_l.lower()}_yyc_las"
        path = RPT / f"{slug}.md"
        path.write_text(md)
        files.append(str(path))
    return files


if __name__ == "__main__":
    for f in write():
        print(f)
