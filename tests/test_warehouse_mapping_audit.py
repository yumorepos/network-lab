"""Synthetic tests showing the read-only mapping audit finds real join defects."""
from __future__ import annotations

import duckdb
import pytest

from scripts.audit_warehouse_mapping import examine


def fixture():
    con = duckdb.connect()
    con.execute("""
        CREATE TABLE dim_airport (
          iata_code VARCHAR, iso_country VARCHAR, city_market_id INTEGER
        )
    """)
    con.execute("""
        INSERT INTO dim_airport VALUES
          ('YYC','CA',20), ('JFK','US',100), ('DJT','US',101)
    """)
    con.execute("""
        CREATE TABLE map_citymarket_cbsa (
          city_market_id INTEGER, cbsa VARCHAR
        )
    """)
    con.execute("""
        INSERT INTO map_citymarket_cbsa VALUES
          (100,'35620'), (100,'11111'), (101,'33100')
    """)
    con.execute("""
        CREATE TABLE fact_segment (
          year INTEGER, month INTEGER, origin VARCHAR, dest VARCHAR,
          origin_country VARCHAR, dest_country VARCHAR,
          carrier VARCHAR, service_class VARCHAR,
          passengers INTEGER, seats INTEGER, departures INTEGER
        )
    """)
    con.execute("""
        INSERT INTO fact_segment VALUES
          (2026,7,'YYC','PBI','CA','US','WS','F',80,100,1),
          (2026,7,'JFK','YYC','US','CA','AA','F',60,100,1)
    """)
    return con


def test_read_only_audit_detects_ambiguous_metro_and_lost_code():
    con = fixture()
    report = examine(con, None)
    assert report["city_market_fanout_to_cbsa"] == [
        {"city_market_id": 100, "n": 2, "n_cbsa": 2}
    ]
    missing = report["unmatched_us_segment_airport_by_year"]
    assert len(missing) == 1
    assert missing[0]["code"] == "PBI"
    assert missing[0]["segment_passenger_legs"] == 80
    assert report["historical_stable_id_completeness_verified"] is False
    con.close()


def test_negative_control_reused_code_appears_in_lookup_audit(tmp_path):
    con = fixture()
    con.execute("""
        CREATE TABLE master (
           AIRPORT VARCHAR, AIRPORT_ID INTEGER,
           CITY_MARKET_ID INTEGER, AIRPORT_IS_LATEST VARCHAR
        )
    """)
    con.execute("""
        INSERT INTO master VALUES
        ('SAW',1,101,'true'),('SAW',2,202,'true'),
        ('JFK',3,100,'true')
    """)
    out = tmp_path / "master.parquet"
    con.execute(f"COPY master TO '{out}' (FORMAT PARQUET)")
    result = examine(con, out)
    assert result["ambiguous_latest_airport_lookup"] == [
        {"airport_code": "SAW", "airport_ids": 2, "city_markets": 2}
    ]
    con.close()


def test_negative_control_missing_warehouse_tables_fails_loudly():
    con = duckdb.connect()
    with pytest.raises(ValueError, match="Missing warehouse tables"):
        examine(con)
    con.close()
