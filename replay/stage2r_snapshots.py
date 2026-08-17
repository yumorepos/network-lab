"""Rebuild and cache the frozen Stage 2R diagnostic universe.

Stage 2R needs the intermediate layers of the verdict chain, and
`data/parquet/replay/decision_rows.parquet` carries only the final screen. This
module re-runs `replay.snapshot` at the approved cutoffs and caches the demand,
share and full economics frames so the diagnostics can be re-run in seconds
without touching the warehouse again.

**Nothing here changes the model.** It calls the same frozen builders
`replay/run_replay.py` calls, at the same cutoffs, and asserts the screen it
gets back reproduces `decision_rows.parquet` market by market. If it does not,
the cache is refused rather than written.

    .venv/bin/python -m replay.stage2r_snapshots
"""
from __future__ import annotations

import pandas as pd

from ingest.common import DATA_PARQUET
from models.common import connect
from replay import snapshot as S
from replay.run_replay import DECISION_DATES

CACHE = DATA_PARQUET / "replay" / "stage2r"
LAYERS = ("demand", "share", "economics", "screen")


def build(force: bool = False) -> dict[str, pd.DataFrame]:
    CACHE.mkdir(parents=True, exist_ok=True)
    paths = {n: CACHE / f"{n}.parquet" for n in LAYERS}
    paths["transfer"] = CACHE / "transfer.parquet"
    if not force and all(p.exists() for p in paths.values()):
        return {n: pd.read_parquet(p) for n, p in paths.items()}

    con = connect(read_only=True)
    acc = {n: [] for n in LAYERS}
    tf_rows = []
    try:
        for sid, dates in DECISION_DATES.items():
            for cut in dates:
                snap = S.snapshot(sid, cut, con)
                for n in LAYERS:
                    d = snap[n].copy()
                    d["study_id"], d["cutoff"] = sid, cut
                    acc[n].append(d)
                tf = snap["transfer"]
                tf_rows.append({
                    "study_id": sid, "cutoff": cut,
                    "anchor_year": tf["anchor_year"],
                    "growth_year": tf["growth_year"],
                    "hub": S.study(sid)["hub"],
                    "growth": tf["growth_t100"].get(S.study(sid)["hub"]),
                    "transfer": tf["per_hub_median"].get(
                        S.study(sid)["hub"], tf["median"]),
                })
                print(f"[stage2r] cached {sid} @ {cut}: "
                      f"{len(snap['screen'])} screened, "
                      f"{len(snap['economics'])} economics rows")
    finally:
        con.close()

    out = {n: pd.concat(acc[n], ignore_index=True) for n in LAYERS}
    out["transfer"] = pd.DataFrame(tf_rows)
    _check_against_frozen(out["screen"])
    for n, d in out.items():
        d.to_parquet(paths[n], index=False)
    return out


def _check_against_frozen(screen: pd.DataFrame) -> None:
    """The rebuilt screen must reproduce the frozen decision rows exactly.

    `replay/run_replay.py` reads the same chain, so a mismatch means the
    diagnostics are describing a different universe than the one V2 measured.
    """
    frozen = pd.read_parquet(DATA_PARQUET / "replay" / "decision_rows.parquet")
    got = screen[["study_id", "cutoff", "cbsa", "verdict", "chosen_freq_wk",
                  "margin_pct", "demand_pax_yr"]]
    m = frozen.merge(got, on=["study_id", "cutoff", "cbsa"],
                     suffixes=("_frozen", "_rebuilt"), how="outer",
                     indicator=True)
    missing = m[m["_merge"] != "both"]
    assert missing.empty, f"row set differs from the frozen replay:\n{missing}"
    for col in ("verdict", "chosen_freq_wk"):
        bad = m[m[f"{col}_frozen"] != m[f"{col}_rebuilt"]]
        assert bad.empty, f"{col} differs from the frozen replay:\n{bad}"
    for col in ("margin_pct", "demand_pax_yr"):
        d = (m[f"{col}_frozen"] - m[f"{col}_rebuilt"]).abs()
        # Replay outputs differ run to run at float-noise scale; anything
        # larger is a real divergence.
        assert d.max() < 1e-6, (
            f"{col} differs from the frozen replay by up to {d.max():.3g}")


if __name__ == "__main__":
    import sys
    d = build(force="--force" in sys.argv)
    for n, f in d.items():
        print(f"{n}: {len(f)} rows")
