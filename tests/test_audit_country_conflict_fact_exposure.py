"""Actual warehouse country-conflict endpoint audit: fail-closed synthetic controls."""
from __future__ import annotations

import duckdb

from scripts.audit_country_conflict_fact_exposure import (
    audit, observed_conflicts, query_fact_exposure,
)


def fixture(tmp_path):
    con = duckdb.connect()
    con.execute("""
        CREATE TABLE dim_airport(
          iata_code VARCHAR, city_market_id INTEGER, city_market_name VARCHAR,
          iso_country VARCHAR)
    """)
    con.execute("""
        INSERT INTO dim_airport VALUES
          ('SAW',33459,'Istanbul','TR'),
          ('SJU',32768,'San Juan','PR'),
          ('SEA',30559,'Seattle','US')
    """)
    con.execute("""
        CREATE TABLE map_citymarket_cbsa(city_market_id INTEGER, cbsa VARCHAR)
    """)
    con.execute("INSERT INTO map_citymarket_cbsa VALUES (33459,'32100')")
    con.execute("""
        CREATE TABLE fact_segment(
          year INTEGER, month INTEGER, origin VARCHAR, dest VARCHAR,
          origin_country VARCHAR, dest_country VARCHAR,
          service_class VARCHAR, departures DOUBLE, passengers DOUBLE)
    """)
    con.execute("""
        INSERT INTO fact_segment VALUES
         (2026,4,'SEA','SAW','US','TR','F',1,100),
         (2026,4,'SEA','SJU','US','PR','F',1,50),
         (2026,4,'SEA','SAW','US','US','F',1,12),
         (2026,4,'SEA','SAW','US','TR','G',1,999),
         (2025,1,'SAW','SEA','TR','US','F',1,10),
         (2026,4,'SEA','SAW','US','TR','F',0,999)
    """)
    con.execute("""
        CREATE TABLE bts(
          AIRPORT VARCHAR, AIRPORT_ID INTEGER,
          CITY_MARKET_ID INTEGER, DISPLAY_CITY_MARKET_NAME_FULL VARCHAR,
          AIRPORT_COUNTRY_CODE_ISO VARCHAR, AIRPORT_IS_LATEST VARCHAR)
    """)
    con.execute("""
        INSERT INTO bts VALUES
        ('SAW',1,33459,'Marquette','US','true'),
        ('SJU',2,32768,'San Juan','US','true'),
        ('SEA',3,30559,'Seattle','US','true')
    """)
    src = tmp_path / "master.parquet"
    con.execute(f"COPY bts TO '{src}' (FORMAT PARQUET)")
    return con, src


def test_actual_source_country_mismatch_and_territory_conventions_separated(tmp_path):
    con, src = fixture(tmp_path)
    result = audit(con, src)
    assert result["country_conflicts_total"] == 2
    assert result["country_conflicts_by_category"] == {
        "unresolved_country_conflict": 1,
        "administrative_convention_to_verify": 1,
    }
    assert result["numeric_city_market_id_correctness_certified"] is False
    assert result["original_warehouse_modified"] is False
    summary = {x["category"]: x for x in result["summary_by_category"]}
    un = summary["unresolved_country_conflict"]
    assert un["endpoint_rows"] == 3
    assert un["passenger_segment_legs"] == 122
    assert un["latest12_endpoint_rows"] == 2  # Last source ym = 202604, excludes 202501.
    assert un["reported_country_matches_stored_rows"] == 2
    assert un["reported_country_matches_selected_market_rows"] == 1
    assert summary["administrative_convention_to_verify"]["passenger_segment_legs"] == 50
    hubs = result["hub_origin_us_destination_exposure"]
    assert len(hubs) == 1
    assert hubs[0]["code"] == "SAW"
    assert hubs[0]["segment_rows"] == 1
    assert hubs[0]["mapped_cbsa"] == "32100"
    assert hubs[0]["passenger_segment_legs"] == 12
    assert result["historical_463_replay_decisions_recomputed"] is False
    con.close()


def test_no_stored_country_difference_produces_no_exposure(tmp_path):
    con, src = fixture(tmp_path)
    con.execute("UPDATE dim_airport SET iso_country='US' WHERE iata_code IN ('SAW','SJU')")
    result = audit(con, src)
    assert result["country_conflicts_total"] == 0
    assert result["segment_endpoint_by_code_year_country"] == []
    assert result["hub_origin_us_destination_exposure"] == []
    con.close()


def test_missing_warehouse_tables_fails_closed():
    con = duckdb.connect()
    try:
        import pytest
        with pytest.raises(ValueError, match="Missing actual warehouse"):
            audit(con, __import__("pathlib").Path("/not-used"))
    finally:
        con.close()


def test_classification_ignores_missing_country_but_does_not_invent_one():
    rows = [
        {"iata_code": "ZZZ", "stored_country": None, "candidate_country": "US",
         "stored_market_id": "123", "candidate_market_name": "A"},
        {"iata_code": "AAA", "stored_country": "CA", "candidate_country": None,
         "stored_market_id": "123", "candidate_market_name": "B"},
    ]
    assert observed_conflicts(rows) == []
