"""Shared model helpers: config loading, distances, warehouse access."""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import duckdb
import yaml

from ingest.common import ROOT, WAREHOUSE_DB

OUTPUTS = ROOT / "data" / "parquet" / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def assumptions() -> dict:
    return yaml.safe_load((ROOT / "config" / "assumptions.yaml").read_text())


@lru_cache(maxsize=8)
def study(study_id: str) -> dict:
    return yaml.safe_load(
        (ROOT / "config" / "studies" / f"{study_id}.yaml").read_text())


def connect(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(WAREHOUSE_DB), read_only=read_only)


def haversine_mi(lat1, lon1, lat2, lon2) -> float:
    r = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def register_haversine(con) -> None:
    con.create_function("haversine_mi", haversine_mi,
                        [float, float, float, float], float)
