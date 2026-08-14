"""Offline point-in-time metro covariates. NO NETWORK, EVER.

W1.3 audit fix 1 and fix 2. The BEA county files already in the frozen cache
carry every annual column (CAINC1 1969 to 2024, CAGDP2 2001 to 2024);
`ingest/census_bea_eia.py` computes `sorted(years)[-1]` and discards the rest.
StatCan 17-10-0135 likewise holds 2001 to 2022 while `dim_metro_ca` keeps only
`max(REF_DATE)`. Recovering the history needs no download and no new source.

**Fail closed.** `ingest.common.download_file` skips the network when a file
exists and otherwise DOWNLOADS. Reusing it here would silently fetch from the
internet the moment a cached file were missing or renamed, which is exactly
what the standing rule forbids. Nothing in this module imports a downloader.
Every path is checked and a missing input raises `CacheMissing`.

Outputs are Parquet under data/parquet/pit/ (gitignored like the rest of
data/), one row per (cbsa, year) or (cma, year). The warehouse is not modified:
Milestone A adds no mart and changes no existing table.
"""
from __future__ import annotations

import duckdb
import pandas as pd

from ingest.common import DATA_PARQUET, DATA_RAW

PIT_DIR = DATA_PARQUET / "pit"

CAINC1 = DATA_RAW / "bea" / "CAINC1_x" / "CAINC1__ALL_AREAS_1969_2024.csv"
CAGDP2 = DATA_RAW / "bea" / "CAGDP2_x" / "CAGDP2__ALL_AREAS_2001_2024.csv"
DELINEATION = DATA_PARQUET / "census" / "cbsa_delineation.parquet"
STATCAN_CMA = DATA_PARQUET / "statcan" / "sc_17100135.parquet"

# BEA CAINC1 line codes, from the file's own Description column.
LINE_PERSONAL_INCOME = "1"      # personal income, thousands of dollars
LINE_POPULATION = "2"           # population, persons
LINE_GDP_ALL_INDUSTRY = "1"     # CAGDP2 all-industry total, thousands


class CacheMissing(RuntimeError):
    """A required frozen input is absent. The replay stops rather than
    downloading it."""


def _require(path, what: str):
    if not path.exists():
        raise CacheMissing(
            f"{what} not found at {path}. This module is offline-only and will "
            "not download. Restore the frozen cache, or run the ingest "
            "deliberately and outside the baseline work.")
    return path


def _read_bea(path, label: str) -> tuple[pd.DataFrame, list[str]]:
    """BEA ALL_AREAS csv. Latin-1: the files contain non-UTF8 bytes in place
    names, which pandas' default codec rejects outright."""
    _require(path, label)
    df = pd.read_csv(path, dtype=str, encoding="latin-1",
                     on_bad_lines="skip", low_memory=False)
    df["fips"] = df["GeoFIPS"].str.replace('"', "", regex=False).str.strip()
    years = sorted(c for c in df.columns if c[:2] == "20" and c.isdigit())
    years += sorted(c for c in df.columns if c[:2] == "19" and c.isdigit())
    years = sorted(set(years))
    if not years:
        raise CacheMissing(f"{label} at {path} has no annual columns")
    return df, years


def _melt(df: pd.DataFrame, years: list[str], line: str,
          value_name: str) -> pd.DataFrame:
    sub = df[df["LineCode"] == line][["fips"] + years].copy()
    out = sub.melt(id_vars="fips", var_name="year", value_name=value_name)
    out["year"] = out["year"].astype(int)
    out[value_name] = pd.to_numeric(out[value_name], errors="coerce")
    return out.dropna(subset=[value_name])


def build_us(force: bool = False) -> pd.DataFrame:
    """One row per (cbsa, year): population, per-capita income, GDP.

    County values are aggregated to CBSAs with the cached 2023 delineation, the
    same crosswalk the production ingest uses, so the only difference from
    `dim_metro_us` is that every year is kept instead of the last one.
    """
    PIT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PIT_DIR / "dim_metro_us_pit.parquet"
    if out_path.exists() and not force:
        return pd.read_parquet(out_path)

    inc, inc_years = _read_bea(CAINC1, "BEA CAINC1 county file")
    gdp, gdp_years = _read_bea(CAGDP2, "BEA CAGDP2 county file")
    _require(DELINEATION, "Census CBSA delineation parquet")
    delin = pd.read_parquet(DELINEATION)
    metro = delin.dropna(subset=["kind"])[["cbsa", "cbsa_title", "fips"]]

    pi = _melt(inc, inc_years, LINE_PERSONAL_INCOME, "pi_kusd")
    pop = _melt(inc, inc_years, LINE_POPULATION, "population")
    gd = _melt(gdp, gdp_years, LINE_GDP_ALL_INDUSTRY, "gdp_kusd")

    con = duckdb.connect()
    con.register("metro", metro)
    con.register("pi", pi)
    con.register("pop", pop)
    con.register("gd", gd)
    # min_count semantics: a CBSA-year is emitted only when at least one county
    # reported, and income is personal income over population rather than a
    # mean of county per-capita figures.
    res = con.execute("""
        WITH agg AS (
          SELECT m.cbsa, m.cbsa_title AS cbsa_name, p.year,
                 sum(p.pi_kusd)      AS pi_kusd,
                 sum(q.population)   AS population,
                 sum(g.gdp_kusd)     AS gdp_kusd
          FROM metro m
          JOIN pi p  ON p.fips = m.fips
          LEFT JOIN pop q ON q.fips = m.fips AND q.year = p.year
          LEFT JOIN gd  g ON g.fips = m.fips AND g.year = p.year
          GROUP BY 1,2,3
        )
        SELECT cbsa, cbsa_name, year, population, gdp_kusd,
               CASE WHEN population > 0
                    THEN pi_kusd * 1000.0 / population END AS income
        FROM agg
        WHERE population IS NOT NULL AND population > 0
        ORDER BY cbsa, year
    """).df()
    con.close()

    if len(res) < 10_000:
        raise CacheMissing(
            f"PIT US metro build produced only {len(res)} rows; the cached BEA "
            "extract is incomplete")
    res.to_parquet(out_path, index=False)
    return res


def build_ca(force: bool = False) -> pd.DataFrame:
    """One row per (cma, year): population, from StatCan 17-10-0135.

    Mirrors `warehouse/build_marts.py`'s dim_metro_ca filter (both sexes, all
    ages) but keeps every REF_DATE instead of only the maximum.
    """
    PIT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PIT_DIR / "dim_metro_ca_pit.parquet"
    if out_path.exists() and not force:
        return pd.read_parquet(out_path)

    _require(STATCAN_CMA, "StatCan 17-10-0135 CMA population parquet")
    con = duckdb.connect()
    res = con.execute(f"""
        SELECT GEO AS cma,
               try_cast(REF_DATE AS INT) AS year,
               try_cast(VALUE AS DOUBLE) AS population
        FROM read_parquet('{STATCAN_CMA}')
        WHERE Sex IN ('Both sexes')
          AND "Age group" IN ('All ages')
          AND try_cast(VALUE AS DOUBLE) IS NOT NULL
          AND try_cast(REF_DATE AS INT) IS NOT NULL
        ORDER BY cma, year
    """).df()
    con.close()
    if not len(res):
        raise CacheMissing(
            "PIT Canadian metro build produced no rows; check the Sex and Age "
            "group filters against the cached StatCan extract")
    res.to_parquet(out_path, index=False)
    return res


def us_at(year: int) -> pd.DataFrame:
    """US metro covariates for one reference year. Raises if absent."""
    df = build_us()
    out = df[df["year"] == year]
    if not len(out):
        raise CacheMissing(
            f"no PIT US metro rows for reference year {year}; available "
            f"{int(df['year'].min())} to {int(df['year'].max())}")
    return out.reset_index(drop=True)


def ca_at(year: int) -> pd.DataFrame:
    df = build_ca()
    out = df[df["year"] == year]
    if not len(out):
        raise CacheMissing(
            f"no PIT Canadian metro rows for reference year {year}; available "
            f"{int(df['year'].min())} to {int(df['year'].max())}")
    return out.reset_index(drop=True)


def available_years() -> dict[str, list[int]]:
    return {
        "us": sorted(int(y) for y in build_us()["year"].unique()),
        "ca": sorted(int(y) for y in build_ca()["year"].unique()),
    }


if __name__ == "__main__":
    us, ca = build_us(force=True), build_ca(force=True)
    print(f"dim_metro_us_pit: {len(us):,} rows, "
          f"{us['cbsa'].nunique():,} metros, "
          f"{int(us['year'].min())} to {int(us['year'].max())}")
    print(f"dim_metro_ca_pit: {len(ca):,} rows, "
          f"{ca['cma'].nunique():,} CMAs, "
          f"{int(ca['year'].min())} to {int(ca['year'].max())}")
