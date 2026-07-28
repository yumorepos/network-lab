"""Assert that rebuilding the warehouse leaves every model output unchanged.

Milestone A integrity gate (PHASE_5_6_PLAN.md). The two defects found during the
T-100 backfill, a prefix match over StatCan CMA records and a dict() over a
multi-row-per-CBSA query, both produced correct-looking numbers that changed
when DuckDB happened to return rows in a different order. No existing test could
see them: `make test` runs the models against a fixed warehouse, so the
mart-to-model boundary was never exercised twice in one run.

Row order is not part of the contract, so comparison is order-insensitive. Where
a file has a unique key the diff is reported per column, which is what makes a
failure diagnosable; where it does not (competition has 3 duplicate itinerary
tuples and a null connect_ap) both sides are canonically sorted and compared
positionally instead.

YAML and CSV outputs are compared too. `transfer_factor.yaml` is precisely where
the Ottawa defect surfaced, so a gate that only read Parquet would have missed
the thing it was written for.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

# Only used when the tuple is actually unique on both sides; otherwise the file
# falls back to a canonical sort. Keeping the map small is deliberate.
KEYS = {
    "screen_": ["metro_name"],
    "demand_": ["cbsa"],
    "share_validation": ["other_cm", "carrier"],
    "share_": ["cbsa"],
    "economics_": ["cbsa", "freq_wk", "seats", "fare_scenario_pct",
                   "fuel_scenario_pct"],
    "transfer_pairs": ["geo", "hub"],
    "backtest_scores": ["carrier", "origin", "destination", "launch_date"],
}
TOL = 1e-6


def _keys_for(stem: str, b: pd.DataFrame, a: pd.DataFrame) -> list[str]:
    for prefix, keys in KEYS.items():
        if not stem.startswith(prefix):
            continue
        if not all(k in b.columns and k in a.columns for k in keys):
            return []
        # a key with nulls or duplicates cannot drive a merge
        if any(b[k].isna().any() or a[k].isna().any() for k in keys):
            return []
        if b.duplicated(subset=keys).any() or a.duplicated(subset=keys).any():
            return []
        return keys
    return []


def _cmp_series(name: str, col: str, x: pd.Series, y: pd.Series) -> list[str]:
    if x.dtype.kind == "f" or y.dtype.kind == "f":
        d = (pd.to_numeric(x, errors="coerce").fillna(-1)
             - pd.to_numeric(y, errors="coerce").fillna(-1)).abs()
        if d.max() > TOL:
            return [f"{name}: {col} moved, max delta {d.max():.6g} on "
                    f"{int((d > TOL).sum())} rows"]
        return []
    if not x.astype(str).equals(y.astype(str)):
        n = int((x.astype(str) != y.astype(str)).sum())
        return [f"{name}: {col} moved on {n} rows"]
    return []


def _compare_frame(name: str, b: pd.DataFrame, a: pd.DataFrame) -> list[str]:
    if len(b) != len(a):
        return [f"{name}: {len(b)} rows -> {len(a)}"]
    if set(b.columns) != set(a.columns):
        only_b = sorted(set(b.columns) - set(a.columns))
        only_a = sorted(set(a.columns) - set(b.columns))
        return [f"{name}: columns changed, removed {only_b}, added {only_a}"]

    keys = _keys_for(name.replace(".parquet", "").replace(".csv", ""), b, a)
    if keys:
        m = b.merge(a, on=keys, how="outer", suffixes=("_b", "_a"),
                    indicator=True)
        if (m["_merge"] != "both").any():
            return [f"{name}: key set changed on "
                    f"{int((m['_merge'] != 'both').sum())} rows"]
        out = []
        for c in b.columns:
            if c in keys:
                continue
            out += _cmp_series(name, c, m[f"{c}_b"], m[f"{c}_a"])
        return out

    # No usable key: sort both sides canonically and compare positionally.
    cols = list(b.columns)
    bs = b.sort_values(cols, na_position="last").reset_index(drop=True)
    as_ = a.sort_values(cols, na_position="last").reset_index(drop=True)
    out = []
    for c in cols:
        out += _cmp_series(f"{name} [unkeyed]", c, bs[c], as_[c])
    return out


def _flatten(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _flatten(v, f"{prefix}.{k}" if prefix else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _flatten(v, f"{prefix}[{i}]")
    else:
        yield prefix, obj


def _compare_yaml(name: str, b: Path, a: Path) -> list[str]:
    xb = dict(_flatten(yaml.safe_load(b.read_text())))
    xa = dict(_flatten(yaml.safe_load(a.read_text())))
    out = []
    for k in sorted(set(xb) | set(xa)):
        vb, va = xb.get(k, "<missing>"), xa.get(k, "<missing>")
        if isinstance(vb, float) and isinstance(va, float):
            if abs(vb - va) > TOL:
                out.append(f"{name}: {k} {vb} -> {va}")
        elif vb != va:
            out.append(f"{name}: {k} {vb!r} -> {va!r}")
    return out


def main(before: str, after: str) -> int:
    b_dir, a_dir = Path(before), Path(after)
    problems, checked = [], 0
    for f in sorted(b_dir.iterdir()):
        if f.suffix not in (".parquet", ".csv", ".yaml"):
            continue
        other = a_dir / f.name
        if not other.exists():
            problems.append(f"{f.name}: missing after rebuild")
            continue
        checked += 1
        if f.suffix == ".yaml":
            problems += _compare_yaml(f.name, f, other)
        elif f.suffix == ".parquet":
            problems += _compare_frame(f.name, pd.read_parquet(f),
                                       pd.read_parquet(other))
        else:
            problems += _compare_frame(f.name, pd.read_csv(f),
                                       pd.read_csv(other))
    for f in sorted(a_dir.iterdir()):
        if f.suffix in (".parquet", ".csv", ".yaml") and not (b_dir / f.name).exists():
            problems.append(f"{f.name}: appeared after rebuild")

    if problems:
        print(f"REPRODUCIBILITY FAILURE ({checked} artifacts compared): "
              "outputs changed across a warehouse rebuild")
        for p in problems:
            print(f"  {p}")
        return 1
    print(f"reproducible: {checked} artifacts identical across a warehouse "
          "rebuild")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
