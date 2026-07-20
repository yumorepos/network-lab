"""US metro demographics and fuel.

Population and income: Census ACS is the preferred source but its API now
requires a key. When CENSUS_API_KEY is unset we build metro figures from BEA
county files (CAINC1: personal income, population, per-capita income),
aggregated to CBSAs with the official Census delineation file. BEA retired its
metro-level zips (the /regional/zip/MA*.zip URLs now serve an HTML page), so
county aggregation is the reproducible no-key path. Per-capita personal income
is a different measure than ACS median household income; recorded in
assumptions.yaml (us_metro_income_source) and docs/LIMITATIONS.md.

Metro GDP: BEA CAGDP2 county file aggregated the same way.
Fuel: EIA Gulf Coast jet spot, weekly, no key.
"""
from __future__ import annotations

import json
import os

import duckdb
import pandas as pd
import requests

from .common import DATA_PARQUET, DATA_RAW, UA, download_file, log, unzip_all

ACS_URL = ("https://api.census.gov/data/{yr}/acs/acs1"
           "?get=NAME,B01003_001E,B19013_001E"
           "&for=metropolitan%20statistical%20area/"
           "micropolitan%20statistical%20area:*&key={key}")
BEA_GDP_URL = "https://apps.bea.gov/regional/zip/CAGDP2.zip"
BEA_INC_URL = "https://apps.bea.gov/regional/zip/CAINC1.zip"
DELINEATION_URL = ("https://www2.census.gov/programs-surveys/metro-micro/"
                   "geographies/reference-files/2023/delineation-files/"
                   "list1_2023.xlsx")
EIA_URL = "https://www.eia.gov/dnav/pet/hist_xls/EER_EPJK_PF4_RGC_DPGw.xls"


def _county_bea(url: str, zname: str) -> tuple[pd.DataFrame, str]:
    """Load a BEA county ALL_AREAS file -> (df, latest_year)."""
    z = DATA_RAW / "bea" / zname
    download_file(url, z)
    extracted = unzip_all(z, DATA_RAW / "bea" / (zname.split(".")[0] + "_x"))
    all_areas = [p for p in extracted if "ALL_AREAS" in p.name.upper()
                 and p.suffix.lower() == ".csv"]
    assert all_areas, f"no ALL_AREAS csv in {zname}"
    con = duckdb.connect()
    df = con.execute(f"""
        SELECT * FROM read_csv('{all_areas[0]}', header=true,
                               all_varchar=true, ignore_errors=true)
    """).df()
    df["fips"] = df["GeoFIPS"].str.replace('"', "").str.strip()
    years = [c for c in df.columns if c[:2] == "20" and c.isdigit()]
    return df, sorted(years)[-1]


def delineation() -> pd.DataFrame:
    """County FIPS -> CBSA code/title (metropolitan areas only)."""
    x = DATA_RAW / "census" / "list1_2023.xlsx"
    download_file(DELINEATION_URL, x)
    d = pd.read_excel(x, skiprows=2, dtype=str)
    d.columns = [c.strip() for c in d.columns]
    d = d.dropna(subset=["CBSA Code"])
    d["fips"] = d["FIPS State Code"].str.zfill(2) + d["FIPS County Code"].str.zfill(3)
    d = d.rename(columns={
        "CBSA Code": "cbsa", "CBSA Title": "cbsa_title",
        "Metropolitan/Micropolitan Statistical Area": "kind"})
    pq = DATA_PARQUET / "census" / "cbsa_delineation.parquet"
    pq.parent.mkdir(parents=True, exist_ok=True)
    d[["cbsa", "cbsa_title", "kind", "fips"]].to_parquet(pq, index=False)
    return d


def acs_or_bea() -> None:
    key = os.environ.get("CENSUS_API_KEY", "")
    pq = DATA_PARQUET / "census" / "metro_pop_income.parquet"
    pq.parent.mkdir(parents=True, exist_ok=True)
    if pq.exists():
        log(f"cached: {pq.name}")
        return
    if key:
        r = requests.get(ACS_URL.format(yr=2023, key=key), headers=UA,
                         timeout=120)
        r.raise_for_status()
        rows = json.loads(r.text)
        df = pd.DataFrame(rows[1:], columns=rows[0]).rename(columns={
            "NAME": "name", "B01003_001E": "population",
            "B19013_001E": "income",
            "metropolitan statistical area/micropolitan statistical area":
                "cbsa"})
        df["income_measure"] = "acs_median_hh_income"
        df = df[["cbsa", "name", "population", "income", "income_measure"]]
        for c in ("population", "income"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
        src = "ACS 2023 1-year"
    else:
        d = delineation()
        metro = d.dropna(subset=["kind"])   # metro + micro CBSAs
        inc, latest = _county_bea(BEA_INC_URL, "CAINC1.zip")
        inc["val"] = pd.to_numeric(inc[latest], errors="coerce")
        pi = inc[inc["LineCode"] == "1"].set_index("fips")["val"]     # $000s
        pop = inc[inc["LineCode"] == "2"].set_index("fips")["val"]    # persons
        m = metro[["cbsa", "cbsa_title", "fips"]].copy()
        m["pi_kusd"] = m["fips"].map(pi)
        m["pop"] = m["fips"].map(pop)
        g = m.groupby(["cbsa", "cbsa_title"], as_index=False)[
            ["pi_kusd", "pop"]].sum(min_count=1)
        g["income"] = g["pi_kusd"] * 1000.0 / g["pop"]
        df = g.rename(columns={"cbsa_title": "name", "pop": "population"})[
            ["cbsa", "name", "population", "income"]]
        df["income_measure"] = "bea_per_capita_personal_income"
        src = f"BEA CAINC1 {latest} counties x Census 2023 delineation"
    assert len(df) > 250 and df["population"].max() > 15_000_000, \
        f"metro pop/income sanity failed: {len(df)} rows"
    df.to_parquet(pq, index=False)
    log(f"metro pop/income: {len(df)} metros from {src}")


def bea_gdp() -> None:
    pq = DATA_PARQUET / "bea" / "metro_gdp.parquet"
    pq.parent.mkdir(parents=True, exist_ok=True)
    if pq.exists():
        log(f"cached: {pq.name}")
        return
    d = delineation()
    metro = d.dropna(subset=["kind"])   # metro + micro CBSAs
    gdp, latest = _county_bea(BEA_GDP_URL, "CAGDP2.zip")
    gdp = gdp[gdp["LineCode"] == "1"].copy()   # all-industry total, $000s
    gdp["val"] = pd.to_numeric(gdp[latest], errors="coerce")
    per_county = gdp.set_index("fips")["val"]
    m = metro[["cbsa", "cbsa_title", "fips"]].copy()
    m["gdp_kusd"] = m["fips"].map(per_county)
    g = m.groupby(["cbsa", "cbsa_title"], as_index=False)["gdp_kusd"].sum(
        min_count=1)
    g = g.rename(columns={"cbsa_title": "name"})
    assert len(g) > 250 and g["gdp_kusd"].max() > 1e9, "BEA metro GDP sanity"
    g.to_parquet(pq, index=False)
    log(f"BEA CAGDP2 {latest}: {len(g)} metros (county-aggregated GDP)")


def eia() -> None:
    pq = DATA_PARQUET / "eia" / "jet_fuel_weekly.parquet"
    pq.parent.mkdir(parents=True, exist_ok=True)
    if pq.exists():
        log(f"cached: {pq.name}")
        return
    x = DATA_RAW / "eia" / "jet_gulf_weekly.xls"
    download_file(EIA_URL, x)
    df = pd.read_excel(x, sheet_name="Data 1", skiprows=2)
    df.columns = ["date", "usd_per_gal"]
    df = df.dropna()
    df["date"] = pd.to_datetime(df["date"])
    assert len(df) > 1000 and 0.2 < df["usd_per_gal"].median() < 6, "EIA sanity"
    df.to_parquet(pq, index=False)
    log(f"EIA jet fuel: {len(df)} weekly obs, "
        f"latest {df['date'].max().date()} ${df['usd_per_gal'].iloc[-1]:.2f}/gal")


def run() -> None:
    acs_or_bea()
    bea_gdp()
    eia()


if __name__ == "__main__":
    run()
