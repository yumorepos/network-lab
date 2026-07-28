"""Mechanical route-spell register: every route start and stop filed to T-100.

PHASE_5_6_PLAN.md W1.2. The backtest through Round 4 scored 48 launches from a
74-row hand-compiled register built from news sources. That register is small,
selection-biased toward newsworthy carriers (Flair and Lynx supply most of the
ceased rows), and cannot be extended without more hand work. T-100 contains
every route start and stop ever filed, so the register can be derived instead.

A spell is a maximal run of active months for one carrier on one airport pair.
Three definitional decisions, each settled against the data rather than assumed:

**The 2020 bridge.** 2020 is excluded from the warehouse because COVID
operations are not usable for calibration. That exclusion silently manufactures
a 13-month hole between December 2019 and January 2021, and 5,010 of the 5,420
observed 13-month gaps start in exactly that month. Without a bridge the
register would record about five thousand route exits in December 2019 and five
thousand launches in January 2021, none of which happened. Gaps spanning an
excluded year therefore have that year's 12 months subtracted before the spell
test is applied.

**The merge threshold is 12 months, which is definitional rather than tuned.**
Annual seasonality has a period of 12 months, so a route flown one month a year
produces a 12-month gap and must not read as an annual launch and exit. Gaps
above 12 effective months open a new spell. Empirically 73.3% of all gaps fall
at or below 12.

**The activity floor** separates operating a route from a handful of diversions
or one-off charters. 24.3% of route-months carry a single departure while the
median is 26, so the low tail is not thin service, it is noise. The floor lives
in `config/assumptions.yaml` with its sensitivity measured, not hardcoded here.

The hand-compiled register is retained as the cross-check, not replaced by this
table: `tests/` asserts the derived spells reproduce it.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from models.common import assumptions, connect

# Definitional, not assumptions. Annual seasonality has a 12-month period, and
# the excluded COVID year is 12 months wide.
SEASON_PERIOD_MONTHS = 12
EXCLUDED_YEARS = (2020,)
# T-100 filings trail the current month; a spell still active within this many
# months of the data end is operating rather than ceased.
REPORTING_LAG_MONTHS = 2
MONTHS_TO_WEEKS = 365.25 / 12 / 7   # 4.348 weeks per average month


def _excluded_months_between(prev_ym: int, ym: int) -> int:
    """Months of deliberately excluded data lying strictly between two months."""
    n = 0
    for y in EXCLUDED_YEARS:
        lo, hi = y * 12 + 1, y * 12 + 12
        if prev_ym < lo and ym > hi:
            n += SEASON_PERIOD_MONTHS
    return n


def build(con=None, min_deps_month: float | None = None) -> pd.DataFrame:
    own = con is None
    con = con or connect(read_only=True)
    if min_deps_month is None:
        min_deps_month = float(
            assumptions()["route_spell_min_deps_month"]["value"])

    # Directional departures collapse to an unordered airport pair: a carrier
    # launching a route files both directions, and counting them separately
    # would double every launch. The per-direction maximum is retained because
    # frequency is quoted one way (see the units contract in models/economics).
    # A small number of legacy rows carry no carrier code (12,653 departures of
    # 155.2 M, 0.008%, concentrated in the early 1990s and almost all single
    # departures). They cannot be assigned to a route spell. Dropped explicitly
    # and reported rather than silently lost to a groupby, per LIMITATIONS
    # item 10.
    dropped = con.execute("""
        SELECT count(*), coalesce(sum(departures), 0) FROM fact_segment
        WHERE carrier IS NULL AND service_class IN ('F','L') AND departures > 0
    """).fetchone()
    if dropped[0]:
        print(f"[route_spells] dropped {dropped[0]:,} rows with no carrier code "
              f"({dropped[1]:,.0f} departures)")

    panel = con.execute(f"""
        WITH dir AS (
          SELECT year*12 + month AS ym, carrier,
                 least(origin, dest) AS a, greatest(origin, dest) AS b,
                 origin, dest, sum(departures) AS deps
          FROM fact_segment
          WHERE service_class IN ('F','L') AND departures > 0
            AND carrier IS NOT NULL
          GROUP BY 1,2,3,4,5,6
        )
        SELECT ym, carrier, a, b,
               sum(deps) AS deps_both,
               max(deps) AS deps_one_way
        FROM dir
        GROUP BY 1,2,3,4
        HAVING sum(deps) >= {min_deps_month}
        ORDER BY carrier, a, b, ym
    """).df()
    if own:
        con.close()
    if not len(panel):
        return panel

    panel["prev_ym"] = panel.groupby(["carrier", "a", "b"])["ym"].shift()
    gap = panel["ym"] - panel["prev_ym"]
    bridge = [
        _excluded_months_between(int(p), int(y)) if pd.notna(p) else 0
        for p, y in zip(panel["prev_ym"], panel["ym"])
    ]
    panel["effective_gap"] = gap - bridge
    panel["new_spell"] = (panel["prev_ym"].isna()
                          | (panel["effective_gap"] > SEASON_PERIOD_MONTHS))
    panel["spell_seq"] = (panel.groupby(["carrier", "a", "b"])["new_spell"]
                          .cumsum().astype(int))

    max_ym = int(panel["ym"].max())
    keys = ["carrier", "a", "b", "spell_seq"]
    g = panel.groupby(keys, sort=False)

    out = g.agg(first_ym=("ym", "min"), last_ym=("ym", "max"),
                n_active_months=("ym", "size"),
                peak_deps_one_way=("deps_one_way", "max")).reset_index()

    # Launch frequency from the first three ACTIVE months, taking the maximum:
    # a route that starts mid-month files a partial first month, and the hand
    # register quotes the intended schedule rather than the stub.
    first3 = (panel.sort_values("ym").groupby(keys, sort=False).head(3)
              .groupby(keys, sort=False)["deps_one_way"].max()
              .rename("initial_deps_one_way").reset_index())
    out = out.merge(first3, on=keys)

    out["span_months"] = out["last_ym"] - out["first_ym"] + 1
    # A spell with internal holes is seasonal or suspended, not continuous.
    out["seasonal_flag"] = out["n_active_months"] < out["span_months"]
    out["initial_freq_wk"] = out["initial_deps_one_way"] / MONTHS_TO_WEEKS
    out["peak_freq_wk"] = out["peak_deps_one_way"] / MONTHS_TO_WEEKS
    out["status"] = (out["last_ym"] >= max_ym - REPORTING_LAG_MONTHS).map(
        {True: "operating", False: "ceased"})
    for col, src in (("first", "first_ym"), ("last", "last_ym")):
        out[f"{col}_year"] = (out[src] - 1) // 12
        out[f"{col}_month"] = out[src] - out[f"{col}_year"] * 12
    return out.rename(columns={"a": "airport_a", "b": "airport_b"})


def validate_against_register(spells: pd.DataFrame | None = None,
                              con=None) -> dict:
    """Reproduce the hand-compiled launch register from the derived spells.

    PHASE_5_6_PLAN.md W1.2 gate: at least 90% of register rows that T-100 can
    contain, matched within one month on launch date, with every disagreement
    explained rather than tuned away.

    Two translations are required before the comparison means anything:

    - **Carrier codes.** The register uses IATA codes; T-100 uses BTS unique
      carrier codes. Flair is 07Q in T-100, and its IATA code F8 belongs to a
      different, defunct airline (Freedom Airlines) that filed 277,230
      departures between 2002 and 2010. Matching on F8 silently returns the
      wrong carrier. Mapping lives in data/reference/carrier_codes.csv.
    - **Date precision.** Some register rows carry a year only. Those are
      credited for a match anywhere in that calendar year rather than being
      failed for not landing in January.

    Rows T-100 structurally cannot contain are excluded from the denominator,
    not counted as failures: T-100 records segments touching the United States,
    so Canadian domestic (hard rule 5) and Canada to Mexico routes are invisible
    to it no matter how good the extractor is.
    """
    own = con is None
    con = con or connect(read_only=True)
    spells = build(con) if spells is None else spells
    us_airports = set(con.execute(
        "SELECT iata_code FROM dim_airport WHERE iso_country = 'US'"
    ).df()["iata_code"])
    if own:
        con.close()
    codes = pd.read_csv("data/reference/carrier_codes.csv")
    alias = {r.register_code: r.bts_carriers.split("|")
             for r in codes.itertuples()}

    reg = pd.read_csv("data/reference/launches.csv", dtype=str)
    reg["ld"] = pd.to_datetime(reg["launch_date"], format="mixed",
                               errors="coerce")
    reg["year_only"] = reg["launch_date"].str.len().le(4)
    reg = reg[reg["ld"].notna()].copy()
    reg["lym"] = reg["ld"].dt.year * 12 + reg["ld"].dt.month
    reg["a"] = np.minimum(reg["origin"], reg["destination"])
    reg["b"] = np.maximum(reg["origin"], reg["destination"])
    # T-100 records segments touching the United States and nothing else, so a
    # route with no US endpoint is invisible to it however good the extractor
    # is. Canadian domestic (hard rule 5) and Canada to Mexico both fall here.
    reg["reproducible"] = (reg["origin"].isin(us_airports)
                           | reg["destination"].isin(us_airports))
    reg["bts"] = reg["carrier"].map(alias)
    reg = reg.explode("bts")

    sp = spells.rename(columns={"airport_a": "a", "airport_b": "b",
                                "carrier": "bts"})
    m = reg.merge(sp, on=["bts", "a", "b"], how="left", suffixes=("", "_sp"))
    m["delta"] = m["first_ym"] - m["lym"]
    m["ok"] = m["delta"].abs() <= np.where(m["year_only"], 12, 1)
    m["_r"] = m["delta"].abs()
    best = (m.sort_values(["ok", "_r"], ascending=[False, True])
            .drop_duplicates(subset=["carrier", "origin", "destination",
                                     "launch_date"]))
    repro = best[best["reproducible"]]
    return {"register_rows": int(len(best)),
            "reproducible_rows": int(len(repro)),
            "excluded_no_us_touch": int((~best["reproducible"]).sum()),
            "matched": int(repro["first_ym"].notna().sum()),
            "reproduced": int(repro["ok"].sum()),
            "rate": float(repro["ok"].mean()) if len(repro) else 0.0,
            "disagreements": repro[~repro["ok"]][
                ["carrier", "bts", "origin", "destination", "launch_date",
                 "first_year", "first_month", "delta"]]}


if __name__ == "__main__":
    df = build()
    print(f"route spells: {len(df):,}")
    print(f"  carriers {df.carrier.nunique():,}  "
          f"pairs {df.groupby(['airport_a','airport_b']).ngroups:,}")
    print(f"  status {df.status.value_counts().to_dict()}")
    print(f"  seasonal {int(df.seasonal_flag.sum()):,}")
    print(f"  launches by decade:\n"
          f"{(df.first_year // 10 * 10).value_counts().sort_index().to_string()}")
