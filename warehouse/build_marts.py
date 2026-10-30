"""Build the DuckDB warehouse from Parquet.

Marts:
  dim_airport            OurAirports + Master Coordinate (CityMarketID)
  dim_carrier            Carrier Decode
  dim_metro              US CBSA (ACS pop/income + BEA GDP) and Canadian CMA
                         (StatCan population); airport -> metro via BTS city
                         market IDs for US and a small documented mapping for
                         Canadian airports
  fact_segment           T-100 all-carrier segments, all vintages
  fact_od_market         DB1B market, 10% sample expanded once (pax x 10)
  fact_costs             Form 41 P-5.2 (+ P-1.2 kept raw alongside)
  fact_fuel              EIA weekly jet fuel spot
  fact_ca_airport        StatCan 23-10-0253 airport traffic by sector
  fact_od_transborder_2018  StatCan 23-10-0256 city-pair table (name carries
                         the vintage on purpose; the table is frozen ~2018)
"""
from __future__ import annotations

import duckdb
import yaml

from ingest.common import DATA_PARQUET, ROOT, WAREHOUSE_DB, log

# Canadian airports relevant to the studies: airport -> (CMA name used by
# StatCan 17-10-0135, ICAO-region sanity). Small, documented, human-checked.
# This is the "about a dozen mappings" human-judgment item from the plan.
CA_AIRPORT_CMA = {
    "YYC": "Calgary",
    "YYZ": "Toronto",
    "YTZ": "Toronto",
    "YHM": "Hamilton",
    "YKF": "Kitchener - Cambridge - Waterloo",
    "YUL": "Montréal",
    "YVR": "Vancouver",
    "YXX": "Abbotsford - Mission",
    "YEG": "Edmonton",
    "YOW": "Ottawa - Gatineau",
    "YWG": "Winnipeg",
    "YHZ": "Halifax",
    "YQB": "Québec",
    "YYJ": "Victoria",
    "YXE": "Saskatoon",
    "YQR": "Regina",
    "YLW": "Kelowna",
    "YYT": "St. John's",
}


def _build_dim_airport(con, p) -> None:
    """Build airport market labels from the SAME source row as their market ID.

    Preserves the legacy max(CITY_MARKET_ID) numeric selection for each code,
    while ensuring city_market_name belongs to that same market. This does
    NOT resolve historical airport-code reuse or correct market geography.
    The production warehouse must only be rebuilt in an isolated copy after
    fixed-source screen/replay comparison.
    """
    con.execute(f"""
        CREATE OR REPLACE TABLE dim_airport AS
        WITH oa AS (
          SELECT iata_code, any_value(name) AS name,
                 any_value(latitude_deg) AS lat, any_value(longitude_deg) AS lon,
                 any_value(iso_country) AS iso_country,
                 any_value(iso_region) AS iso_region,
                 any_value(municipality) AS municipality
          FROM read_parquet('{p}/ourairports/airports.parquet')
          GROUP BY iata_code
        ),
        mc_ranked AS (
          SELECT AIRPORT AS iata_code, CITY_MARKET_ID AS city_market_id,
                 DISPLAY_CITY_MARKET_NAME_FULL AS city_market_name,
                 row_number() OVER (
                   PARTITION BY AIRPORT
                   ORDER BY CITY_MARKET_ID DESC NULLS LAST,
                            DISPLAY_CITY_MARKET_NAME_FULL ASC NULLS LAST,
                            AIRPORT_ID DESC NULLS LAST
                 ) AS rn
          FROM read_parquet('{p}/lookups/master_coord.parquet')
          WHERE AIRPORT_IS_LATEST = 'true' OR AIRPORT_IS_LATEST = '1'
        ),
        mc AS (
          SELECT iata_code, city_market_id, city_market_name
          FROM mc_ranked WHERE rn = 1
        )
        SELECT oa.*, mc.city_market_id, mc.city_market_name
        FROM oa LEFT JOIN mc USING (iata_code)
    """)


def build() -> None:
    con = duckdb.connect(str(WAREHOUSE_DB))
    p = DATA_PARQUET

    log("dim_airport")
    _build_dim_airport(con, p)

    log("dim_carrier")
    con.execute(f"""
        CREATE OR REPLACE TABLE dim_carrier AS
        SELECT UNIQUE_CARRIER AS carrier,
               any_value(UNIQUE_CARRIER_NAME) AS carrier_name
        FROM read_parquet('{p}/lookups/carrier_decode.parquet')
        GROUP BY UNIQUE_CARRIER
    """)

    log("fact_segment")
    con.execute(f"""
        CREATE OR REPLACE TABLE fact_segment AS
        SELECT * FROM read_parquet('{p}/t100/t100_*.parquet')
    """)

    if list((p / "db1b").glob("db1b_*.parquet")):
        log("fact_od_market (DB1B, sample expanded x10)")
        con.execute(f"""
            CREATE OR REPLACE TABLE fact_od_market AS
            SELECT year, quarter, origin, origin_cm, dest, dest_cm, tk_carrier,
                   passengers * 10.0 AS passengers_est,   -- 10% sample, expanded once here
                   mkt_fare, mkt_distance, nonstop_miles, coupons
            FROM read_parquet('{p}/db1b/db1b_*.parquet')
        """)
    else:
        log("fact_od_market skipped: no DB1B parquet yet")

    log("fact_costs (Form 41 P-5.2, P-1.2)")
    con.execute(f"""
        CREATE OR REPLACE TABLE fact_costs AS
        SELECT * FROM read_parquet('{p}/form41/p52_*.parquet',
                                   union_by_name=true)
    """)
    con.execute(f"""
        CREATE OR REPLACE TABLE fact_income_p12 AS
        SELECT * FROM read_parquet('{p}/form41/p12_*.parquet',
                                   union_by_name=true)
    """)

    log("fact_fuel")
    con.execute(f"""
        CREATE OR REPLACE TABLE fact_fuel AS
        SELECT * FROM read_parquet('{p}/eia/jet_fuel_weekly.parquet')
    """)

    log("fact_ca_airport (StatCan 23-10-0253, loaded as published)")
    _generic_statcan(con, p, "23100253", "fact_ca_airport")

    log("fact_od_transborder_2018 (StatCan 23-10-0256)")
    _generic_statcan(con, p, "23100256", "fact_od_transborder_2018")
    for tid in ("23100249", "23100255", "23100257", "23100259", "23100312"):
        _generic_statcan(con, p, tid, f"statcan_{tid}")

    log("dim_metro")
    # US: CBSA population/income + GDP, both county-aggregated upstream.
    con.execute(f"""
        CREATE OR REPLACE TABLE dim_metro_us AS
        SELECT a.cbsa, a.name, a.population, a.income, a.income_measure,
               g.gdp_kusd
        FROM read_parquet('{p}/census/metro_pop_income.parquet') a
        LEFT JOIN (SELECT cbsa, gdp_kusd
                   FROM read_parquet('{p}/bea/metro_gdp.parquet')) g
        USING (cbsa)
    """)
    if _exists(p, "statcan/sc_17100135.parquet"):
        sc_cols = [r[0] for r in con.execute(
            f"DESCRIBE SELECT * FROM read_parquet("
            f"'{p}/statcan/sc_17100135.parquet')").fetchall()]
        extra = ""
        if "Sex" in sc_cols:
            extra += " AND \"Sex\" = 'Both sexes'"
        if "Age group" in sc_cols:
            extra += " AND \"Age group\" = 'All ages'"
        con.execute(f"""
            CREATE OR REPLACE TABLE dim_metro_ca AS
            WITH latest AS (
              SELECT max(REF_DATE) AS y
              FROM read_parquet('{p}/statcan/sc_17100135.parquet')
            )
            SELECT GEO AS cma, max(try_cast(VALUE AS DOUBLE)) AS population
            FROM read_parquet('{p}/statcan/sc_17100135.parquet'), latest
            WHERE REF_DATE = latest.y AND GEO LIKE '%(CMA)%'{extra}
            GROUP BY GEO
        """)

    con.execute("CREATE OR REPLACE TABLE ca_airport_cma AS SELECT * FROM (VALUES "
                + ",".join("('{}','{}')".format(k, v.replace("'", "''"))
                           for k, v in CA_AIRPORT_CMA.items())
                + ") t(iata_code, cma_name)")

    # Resolved Canadian hub airport -> metro population, built once.
    #
    # Four call sites each ran `dim_metro_ca m ON m.cma LIKE c.cma_name||'%'`
    # independently and collapsed the result with dict() or iloc[0]. That prefix
    # join is not unique: StatCan splits the one interprovincial CMA into three
    # records, so YOW matched the Quebec part (355,203), the Ontario part
    # (1,143,407) and the full CMA (1,498,610), and which one won depended on
    # row order. It silently swapped Ottawa's population by a factor of 4.2
    # between rebuilds and moved backtest demand estimates by 2.8x.
    #
    # Provincial parts are excluded because a hub airport serves the whole CMA,
    # and the result is asserted unique so a future ambiguity fails loudly
    # instead of being picked.
    con.execute("""
        CREATE OR REPLACE TABLE map_ca_airport_metro AS
        SELECT c.iata_code, m.cma, m.population
        FROM ca_airport_cma c
        JOIN dim_metro_ca m ON m.cma LIKE c.cma_name || '%'
        WHERE m.cma NOT LIKE '% part,%'
    """)
    dupes = con.execute("""
        SELECT iata_code, count(*) n, string_agg(cma, ' | ' ORDER BY cma) hits
        FROM map_ca_airport_metro GROUP BY 1 HAVING count(*) > 1
    """).df()
    assert not len(dupes), (
        "Canadian airport to CMA mapping is ambiguous, the defect class that "
        f"mis-populated Ottawa:\n{dupes.to_string(index=False)}")
    log("map_ca_airport_metro: " + str(con.execute(
        "SELECT count(*) FROM map_ca_airport_metro").fetchone()[0]) + " airports")

    from warehouse.metro_map import build_map
    build_map(con)

    have = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
    counts = {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
              for t in ["dim_airport", "dim_carrier", "fact_segment",
                        "fact_od_market", "fact_costs", "fact_fuel"]
              if t in have}
    log(f"warehouse built: {counts}")
    con.close()


def _exists(p, rel) -> bool:
    return (p / rel).exists()


def _generic_statcan(con, p, tid, table) -> None:
    path = p / "statcan" / f"sc_{tid}.parquet"
    if not path.exists():
        log(f"skip {table}: {path.name} missing")
        return
    con.execute(f"""
        CREATE OR REPLACE TABLE {table} AS
        SELECT * FROM read_parquet('{path}')
    """)


if __name__ == "__main__":
    build()
