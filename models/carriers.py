"""Marketing-carrier families: which operating certificate sells under which brand.

T-100 reports the OPERATING carrier. DB1B reports the TICKETING (marketing)
carrier. The two disagree for every regional affiliate, and the disagreement is
not marginal: over the current T-100 window SkyWest operates 884,171
departures, Republic 369,160 and Envoy 334,585, while none of those codes
appears even once as a DB1B ticketing carrier. Every one of those departures is
sold to a passenger as American, Delta, United or Alaska.

A route planner competes against brands, not certificates. Treating them as
separate carriers has two consequences, both corrected by this module:

  1. A mainline leg plus a regional leg is a real connecting itinerary that a
     passenger can buy, but a same-operating-carrier join cannot see it. The
     competitive set is understated and the proposed service's share is
     overstated.
  2. A metro served by a wholly owned regional looks unserved by the mainline,
     so it leaks into the candidate set.

Resolution has two tiers, recorded per row in data/reference/carrier_families.csv:

  static             the operator flies for exactly one brand (wholly owned or a
                     single capacity purchase agreement), so the brand is a
                     matter of public corporate record.
  db1b_per_segment   the operator flies for several brands, so the brand is
                     resolved for each segment by asking which permitted brand
                     actually sells nonstop tickets on that airport pair in
                     DB1B. Where DB1B does not cover the segment (any Canadian
                     origin, or a pair with no sampled nonstop traffic) the
                     segment stays unresolved and keeps its operating code,
                     which is the conservative choice: it never invents a
                     competitor.

The static tier is corroborated in data rather than asserted: the permitted
brand sells nonstop on 95.9% to 100% of each single-brand operator's
DB1B-covered segments. For the multi-brand tier the winning brand takes a
median 1.00 of within-set nonstop passengers, so the per-segment resolution is
close to unambiguous where it fires.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

FAMILIES_CSV = Path("data/reference/carrier_families.csv")


def partner_table() -> pd.DataFrame:
    """The hand-auditable operator to brand reference file."""
    df = pd.read_csv(FAMILIES_CSV)
    df["brand_partners"] = df["brand_partners"].str.split("|")
    return df


def _segment_window(con) -> int:
    return con.execute("""
        SELECT max(year::INT*100+month) FROM fact_segment
        WHERE service_class IN ('F','L')
    """).fetchone()[0]


def segment_brands(con, min_deps: float, db1b_year: int = 2024) -> pd.DataFrame:
    """One row per (op_carrier, origin, dest) that a regional operates, giving
    the marketing brand it is sold under and the basis for that resolution.

    Segments operated by a carrier that is its own brand are absent: callers
    coalesce a missing brand back to the operating code.
    """
    tbl = partner_table()
    win = _segment_window(con)

    seg = con.execute(f"""
        SELECT carrier AS op_carrier, origin, dest
        FROM fact_segment
        WHERE service_class IN ('F','L')
          AND (year::INT*100+month) > {win} - 100
          AND departures > 0 AND seats > 0
        GROUP BY 1,2,3
        HAVING sum(departures) >= {min_deps}
    """).df()
    seg = seg[seg["op_carrier"].isin(tbl["operating_carrier"])].copy()

    single = tbl[tbl["resolution"] == "static"]
    static_map = {r["operating_carrier"]: r["brand_partners"][0]
                  for _, r in single.iterrows()}
    seg["brand"] = seg["op_carrier"].map(static_map)
    seg["basis"] = seg["brand"].notna().map({True: "static", False: None})

    # Multi-brand operators: ask DB1B which permitted brand sells the pair.
    multi = {r["operating_carrier"]: set(r["brand_partners"])
             for _, r in tbl[tbl["resolution"] == "db1b_per_segment"].iterrows()}
    todo = seg[seg["brand"].isna()]
    if len(todo) and multi:
        db = con.execute(f"""
            SELECT origin, dest, tk_carrier AS brand,
                   sum(passengers_est) AS pax
            FROM fact_od_market
            WHERE year = {db1b_year} AND coupons = 1
            GROUP BY 1,2,3
        """).df()
        # DB1B nonstop sales are a property of the airport pair, not of a
        # direction, so collapse to an unordered pair before matching.
        db["a"] = db[["origin", "dest"]].min(axis=1)
        db["b"] = db[["origin", "dest"]].max(axis=1)
        db = db.groupby(["a", "b", "brand"], as_index=False)["pax"].sum()

        t = todo.copy()
        t["a"] = t[["origin", "dest"]].min(axis=1)
        t["b"] = t[["origin", "dest"]].max(axis=1)
        cand = t.merge(db, on=["a", "b"], how="inner", suffixes=("", "_db"))
        permitted = [b in multi.get(op, set())
                     for op, b in zip(cand["op_carrier"], cand["brand_db"])]
        cand = cand[permitted]
        best = (cand.sort_values("pax", ascending=False)
                .drop_duplicates(["op_carrier", "origin", "dest"])
                [["op_carrier", "origin", "dest", "brand_db"]])
        seg = seg.merge(best, on=["op_carrier", "origin", "dest"], how="left")
        fill = seg["brand"].isna() & seg["brand_db"].notna()
        seg.loc[fill, "brand"] = seg.loc[fill, "brand_db"]
        seg.loc[fill, "basis"] = "db1b_per_segment"
        seg = seg.drop(columns=["brand_db"])

    # Unresolved multi-brand segments keep their operating code. Inventing a
    # brand here would invent a competitor.
    unresolved = seg["brand"].isna()
    seg.loc[unresolved, "brand"] = seg.loc[unresolved, "op_carrier"]
    seg.loc[unresolved, "basis"] = "unresolved"
    return seg[["op_carrier", "origin", "dest", "brand", "basis"]]


def register_segment_brands(con, min_deps: float,
                            view: str = "map_segment_brand") -> pd.DataFrame:
    """Build the map and register it on the connection for SQL joins."""
    df = segment_brands(con, min_deps)
    con.register(view, df)
    return df


def operators_for_brand(con, brand: str, min_deps: float) -> set[str]:
    """Every operating code that sells under `brand` somewhere in the window.

    Used by the candidate filter, which asks whether the study carrier already
    serves a metro. It must count the mainline's own metal plus anything flown
    on its behalf.
    """
    df = segment_brands(con, min_deps)
    return {brand} | set(df[df["brand"] == brand]["op_carrier"])
