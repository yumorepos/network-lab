"""Test the preserved local warehouse audit using a tiny fake DuckDB.

No real user warehouse, airport mapping or passenger record is copied here.
"""
from __future__ import annotations

import hashlib

import duckdb
import pytest

from scripts.audit_preserved_warehouse import (
    _year_month_gaps, audit_preserved, summarize,
)


def _warehouse(tmp_path):
    path = tmp_path / "data"
    path.mkdir()
    file = path / "warehouse.duckdb"
    con = duckdb.connect(str(file))
    con.execute("CREATE TABLE dim_airport(iata_code VARCHAR, iso_country VARCHAR, city_market_id INT)")
    con.execute("INSERT INTO dim_airport VALUES ('YYC','CA',10), ('DJT','US',100), ('JFK','US',101)")
    con.execute("CREATE TABLE map_citymarket_cbsa(city_market_id INT,cbsa VARCHAR)")
    con.execute("INSERT INTO map_citymarket_cbsa VALUES (100,'33100'),(101,'35620'),(101,'99999')")
    con.execute("""CREATE TABLE fact_segment(
      year INT, month INT, origin VARCHAR, dest VARCHAR,
      origin_country VARCHAR, dest_country VARCHAR,
      carrier VARCHAR, service_class VARCHAR,
      passengers INT, seats INT, departures INT)""")
    con.execute("""INSERT INTO fact_segment VALUES
      (2025,7,'YYC','PBI','CA','US','WS','F',80,100,1),
      (2025,8,'YYC','JFK','CA','US','WS','F',60,100,1),
      (2025,10,'JFK','YYC','US','CA','AA','F',55,90,1)""")
    con.close()
    # Mimic directory footprint without creating real data.
    (path / "raw").mkdir()
    (path / "raw" / "sample.zip").write_bytes(b"dummy")
    (path / "parquet").mkdir()
    (path / "parquet" / "sample.parquet").write_bytes(b"dummy")
    return file


def test_readonly_warehouse_diagnostics_and_source_inventory(tmp_path):
    db = _warehouse(tmp_path)
    before = hashlib.sha256(db.read_bytes()).hexdigest()
    report = audit_preserved(tmp_path)
    after = hashlib.sha256(db.read_bytes()).hexdigest()
    assert before == after, "audit must not alter the stored DuckDB database"
    assert report["warehouse_exists"] is True
    assert report["source_inventory"]["raw"]["file_count"] == 1
    assert report["source_inventory"]["parquet"]["file_count"] == 1
    assert report["warehouse_table_rows"]["fact_segment"] == 3
    assert report["warehouse_table_rows"]["fact_od_market"] is None
    assert report["t100_internal_missing_months_for_review"] == ["2025-09"]
    assert report["mapping_diagnostics"]["unmatched_us_segment_airport_by_year"][0]["code"] == "PBI"
    assert not report["full_external_source_completeness_verified"]
    assert not report["production_verdict_delta_measured"]
    markdown = summarize(report)
    assert "No official sources were redownloaded" in markdown
    assert "NOT certified" in markdown


def test_bad_month_gap_has_no_deceptive_completeness_claim():
    assert _year_month_gaps([]) == []
    assert _year_month_gaps([{"year": 2025, "month": 10}]) == []
    assert _year_month_gaps([
        {"year": 2025, "month": 11},
        {"year": 2026, "month": 2},
    ]) == ["2025-12", "2026-01"]


def test_missing_preserved_warehouse_fails_without_creating_outputs(tmp_path):
    with pytest.raises(FileNotFoundError, match="Preserved warehouse missing"):
        audit_preserved(tmp_path)
    assert not (tmp_path / "data").exists()
