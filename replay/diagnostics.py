"""Defects the replay exposed in the frozen model. Measured, not fixed.

Milestone A records defects; Phase 6 fixes them under a change report. This
module quantifies what the W1.4 replay surfaced so the completion report and
the V2 baseline can cite numbers rather than impressions.
"""
from __future__ import annotations

import pandas as pd

from ingest.common import DATA_PARQUET
from models.common import connect
from replay import snapshot as S

OUT = DATA_PARQUET / "replay"
CUTOFFS = [202201, 202301, 202401]


def transfer_and_growth() -> pd.DataFrame:
    """Per-cutoff transfer factor and corridor growth for the two study hubs.

    The corridor growth term is `T-100 transborder pax(latest complete year) /
    pax(anchor year)`, a raw ratio of two single years with no COVID handling.
    Anchored transborder demand is `anchor x growth`, so the growth year drives
    the level of every anchored market directly.
    """
    con = connect(read_only=True)
    rows = []
    for c in CUTOFFS:
        v = S.resolve_vintages(c, con)
        tf = S.build_transfer(con, v)
        for hub in ("YYC", "YYZ"):
            rows.append({
                "cutoff": c,
                "anchor_year": tf["anchor_year"],
                "growth_year": tf["growth_year"],
                "hub": hub,
                "transfer_per_hub_median": tf["per_hub_median"].get(hub),
                "corridor_growth": tf["growth_t100"].get(hub),
            })
    con.close()
    df = pd.DataFrame(rows)
    df.to_parquet(OUT / "vintage_transfer_growth.parquet", index=False)
    return df


def demand_dispersion() -> pd.DataFrame:
    """Anchored transborder demand by cutoff: what the growth term does to it."""
    rows = pd.read_parquet(OUT / "decision_rows.parquet")
    tb = rows[rows["study_id"].isin(["westjet_yyc", "porter_yyz"])]
    g = (tb.groupby(["study_id", "cutoff", "demand_method"])
         .agg(n=("demand_pax_yr", "size"),
              median_demand=("demand_pax_yr", "median"),
              median_margin=("margin_pct", "median"))
         .reset_index())
    g.to_parquet(OUT / "vintage_demand_dispersion.parquet", index=False)
    return g


if __name__ == "__main__":
    t = transfer_and_growth()
    print(t.to_string(index=False))
    print()
    print(demand_dispersion().to_string(index=False))
