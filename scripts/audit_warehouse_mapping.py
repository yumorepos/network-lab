"""Read-only warehouse-level mapping diagnostics. Does not modify data.

Execute against a fully built DuckDB warehouse. No CI result can substitute
for historical AirportID and published report parity.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
from ingest.common import WAREHOUSE_DB, DATA_PARQUET


def _query(con, sql):
    cur = con.execute(sql)
    cols = [x[0] for x in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def examine(con: duckdb.DuckDBPyConnection, lookup: Path | None = None) -> dict:
    """Diagnostic SQL only, no CREATE/UPDATE/DELETE statements."""
    present = {x[0] for x in con.execute("SHOW TABLES").fetchall()}
    required = {"fact_segment", "dim_airport", "map_citymarket_cbsa"}
    if missing := sorted(required - present):
        raise ValueError("Missing warehouse tables: " + ", ".join(missing))
    result = {}
    result["duplicate_airport_codes"] = _query(con, """
        SELECT iata_code, count(*) AS n
        FROM dim_airport
        GROUP BY 1 HAVING count(*) > 1
        ORDER BY n DESC, iata_code
    """)
    result["city_market_fanout_to_cbsa"] = _query(con, """
        SELECT city_market_id, count(*) AS n,
               count(DISTINCT cbsa) AS n_cbsa
        FROM map_citymarket_cbsa GROUP BY 1 HAVING count(*) > 1
        ORDER BY n DESC, city_market_id
    """)
    result["unmapped_us_airport_codes"] = _query(con, """
        SELECT count(*) AS n
        FROM dim_airport a
        LEFT JOIN map_citymarket_cbsa m USING (city_market_id)
        WHERE a.iso_country = 'US' AND m.city_market_id IS NULL
    """)[0]["n"]
    result["unmatched_us_segment_airport_by_year"] = _query(con, """
        WITH endpoints AS (
          SELECT s.year, s.origin AS code, 'origin' AS side,
                 s.passengers AS pax, s.seats, s.departures
          FROM fact_segment s
          WHERE s.origin_country = 'US' AND s.service_class IN ('F','L')
          UNION ALL
          SELECT s.year, s.dest AS code, 'dest' AS side,
                 s.passengers AS pax, s.seats, s.departures
          FROM fact_segment s
          WHERE s.dest_country = 'US' AND s.service_class IN ('F','L')
        )
        SELECT e.year, e.side, e.code, count(*) AS n_rows,
               sum(e.pax) AS segment_passenger_legs, sum(e.seats) AS seats,
               sum(e.departures) AS departures
        FROM endpoints e
        LEFT JOIN dim_airport a ON a.iata_code = e.code
        WHERE a.iata_code IS NULL
        GROUP BY 1,2,3 ORDER BY segment_passenger_legs DESC NULLS LAST
        LIMIT 100
    """)
    result["unmapped_us_metro_traffic"] = _query(con, """
        SELECT s.dest AS airport_code, count(*) AS n_rows,
               sum(s.passengers) AS segment_passenger_legs
        FROM fact_segment s
        LEFT JOIN dim_airport a ON a.iata_code = s.dest
        LEFT JOIN map_citymarket_cbsa m ON m.city_market_id = a.city_market_id
        WHERE s.dest_country = 'US' AND s.service_class IN ('F','L')
          AND m.cbsa IS NULL
        GROUP BY 1 ORDER BY segment_passenger_legs DESC NULLS LAST LIMIT 100
    """)
    result["pbi_djt_traffic_by_year"] = _query(con, """
        SELECT year, count(*) AS n_rows,
               sum(passengers) AS segment_passenger_legs
        FROM fact_segment
        WHERE origin IN ('PBI','DJT') OR dest IN ('PBI','DJT')
        GROUP BY 1 ORDER BY year
    """)
    result["t100_month_coverage"] = _query(con, """
        SELECT year, month, count(*) AS n_rows,
               count(DISTINCT carrier) AS operators
        FROM fact_segment GROUP BY 1,2 ORDER BY 1,2
    """)
    # The warehouse builder aggregates latest-code market IDs and display
    # names independently (max(CITY_MARKET_ID), any_value(name)). With reused
    # airport codes, those two attributes may refer to different places.
    # Detect actual mismatched stored labels without changing the warehouse.
    result["airport_dim_market_label_mismatches"] = None
    label_cols = {
        row[0] for row in con.execute("DESCRIBE dim_airport").fetchall()
    }
    if lookup and lookup.exists() and "city_market_name" in label_cols:
        quoted = str(lookup).replace("'", "''")
        result["airport_dim_market_label_mismatches"] = _query(con, f"""
            WITH latest AS (
              SELECT DISTINCT AIRPORT AS code,
                     CITY_MARKET_ID AS market_id,
                     DISPLAY_CITY_MARKET_NAME_FULL AS market_name
              FROM read_parquet('{quoted}')
              WHERE lower(cast(AIRPORT_IS_LATEST AS varchar)) IN ('true','1')
                AND AIRPORT IS NOT NULL AND CITY_MARKET_ID IS NOT NULL
            )
            SELECT a.iata_code, a.city_market_id, a.city_market_name,
                   string_agg(DISTINCT l.market_name, ' | '
                              ORDER BY l.market_name) AS source_market_names
            FROM dim_airport a
            JOIN latest l ON l.code = a.iata_code
                          AND l.market_id = a.city_market_id
            GROUP BY 1,2,3
            HAVING sum(CASE WHEN
                        a.city_market_name IS NOT DISTINCT FROM l.market_name
                       THEN 1 ELSE 0 END) = 0
            ORDER BY a.iata_code
        """)
    result["ambiguous_latest_airport_lookup"] = None
    if lookup and lookup.exists():
        quoted = str(lookup).replace("'", "''")
        result["ambiguous_latest_airport_lookup"] = _query(con, f"""
            SELECT AIRPORT AS airport_code,
                   count(DISTINCT AIRPORT_ID) AS airport_ids,
                   count(DISTINCT CITY_MARKET_ID) AS city_markets
            FROM read_parquet('{quoted}')
            WHERE lower(cast(AIRPORT_IS_LATEST AS varchar)) IN ('true','1')
              AND AIRPORT IS NOT NULL
            GROUP BY 1
            HAVING count(DISTINCT AIRPORT_ID) > 1
                OR count(DISTINCT CITY_MARKET_ID) > 1
            ORDER BY city_markets DESC, airport_code
        """)
    result["historical_stable_id_completeness_verified"] = False
    result["published_verdict_delta_measured"] = False
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--warehouse", type=Path, default=WAREHOUSE_DB)
    p.add_argument("--lookup", type=Path,
                   default=DATA_PARQUET / "lookups/master_coord.parquet")
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    if not a.warehouse.is_file():
        raise SystemExit(f"Warehouse not found: {a.warehouse}; run make data first")
    db = duckdb.connect(str(a.warehouse), read_only=True)
    try:
        result = examine(db, a.lookup)
    finally:
        db.close()
    payload = json.dumps(result, indent=2, sort_keys=True, default=str) + "\n"
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(payload)
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
