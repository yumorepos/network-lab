"""Synthetic GSP/JAN audit controls; no original warehouse or source downloads."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

duckdb = pytest.importorskip("duckdb")
from scripts.audit_gsp_jan_geography import inspect


def fixture(tmp_path: Path):
    con = duckdb.connect(":memory:")
    con.execute("""CREATE TABLE dim_airport (
      iata_code VARCHAR, iso_country VARCHAR, city_market_id INTEGER,
      city_market_name VARCHAR)""")
    con.execute("""INSERT INTO dim_airport VALUES
      ('GSP','US',31871,'Greenville/Spartanburg, SC'),
      ('JAN','US',32448,'Jackson/Vicksburg, MS')""")
    con.execute("""CREATE TABLE map_citymarket_cbsa (
      city_market_id INTEGER, cbsa VARCHAR, cm_name VARCHAR, method VARCHAR)""")
    con.execute("""INSERT INTO map_citymarket_cbsa VALUES
      (31871,'24860','Greenville/Spartanburg, SC','token'),
      (32448,'27140','Jackson/Vicksburg, MS','token')""")
    con.execute("""CREATE TABLE dim_metro_us (
      cbsa VARCHAR, name VARCHAR, population INTEGER)""")
    con.execute("""INSERT INTO dim_metro_us VALUES
      ('24860','Greenville',996680),('43900','Spartanburg',395934),
      ('27140','Jackson',606178),('46980','Vicksburg',42105)""")
    con.execute("""CREATE TABLE fact_segment (
      year INTEGER, month INTEGER, origin VARCHAR, dest VARCHAR,
      dest_country VARCHAR, service_class VARCHAR, departures INTEGER,
      passengers INTEGER, seats INTEGER)""")
    con.execute("""INSERT INTO fact_segment VALUES
      (2026,4,'SEA','GSP','US','F',2,123,150),
      (2026,4,'YYC','JAN','US','L',1,22,44),
      (2025,4,'YYZ','JAN','US','F',1,300,400),
      (2026,4,'YYC','GSP','US','G',1,600,900),
      (2026,4,'YYZ','GSP','US','F',0,500,600),
      (2026,4,'SEA','GSP','CA','F',1,123,150)""")
    lookup = tmp_path / "data" / "parquet" / "lookups"
    lookup.mkdir(parents=True)
    con.execute("""COPY (
      SELECT 'GSP' AS AIRPORT, 111 AS AIRPORT_ID, 31871 AS CITY_MARKET_ID,
        'Greenville/Spartanburg, SC' AS DISPLAY_CITY_MARKET_NAME_FULL,
        'true' AS AIRPORT_IS_LATEST, 'US' AS AIRPORT_COUNTRY_CODE_ISO
      UNION ALL
      SELECT 'JAN', 222, 32448, 'Jackson/Vicksburg, MS', 'true', 'US'
    ) TO ? (FORMAT PARQUET)""", [str(lookup / "master_coord.parquet")])
    outputs = tmp_path / "data" / "parquet" / "outputs"
    outputs.mkdir(parents=True)
    fieldnames = [
       "study_id","dest_airport","metro_name","verdict","margin_pct",
       "load_factor","demand_pax_yr","demand_source","demand_method","confidence"
    ]
    for study in ("westjet_yyc","alaska_sea","porter_yyz"):
        with (outputs / f"screen_{study}.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for code in ("GSP","JAN"):
                w.writerow({
                  "study_id": study, "dest_airport":code, "metro_name":code,
                  "verdict":"PASS", "margin_pct":-20,
                  "load_factor":0.12,"demand_pax_yr":3000,
                  "demand_source":"modeled","demand_method":"test",
                  "confidence":"low"
                })
    return con


def test_readonly_source_window_six_candidates(tmp_path):
    con = fixture(tmp_path)
    try:
        result = inspect(con, tmp_path)
        rows = result["recent_direct_hub_operated_segments"]
        assert {(r["hub"],r["airport_code"]):r["passenger_segment_legs"]
                for r in rows} == {("SEA","GSP"):123,("YYC","JAN"):22}
        assert result["latest_reported_month"] == 202604
        assert len(result["published_six_screen_rows"]) == 6
        assert len(result["reference_census_cbsa_components"]) == 4
        assert result["warnings"] == []
        assert result["six_screen_verdicts_recomputed"] is False
        assert con.execute("SELECT count(*) FROM fact_segment").fetchone()[0] == 6
    finally:
        con.close()


def test_duplicate_join_fails_before_summing(tmp_path):
    con = fixture(tmp_path)
    try:
        con.execute("""INSERT INTO map_citymarket_cbsa
          VALUES (31871,'43900','Greenville/Spartanburg, SC','manual')""")
        with pytest.raises(ValueError, match="Non-unique map_citymarket_cbsa.city_market_id"):
            inspect(con, tmp_path)
    finally:
        con.close()


def test_missing_table_fails_closed(tmp_path):
    con = fixture(tmp_path)
    try:
        con.execute("DROP TABLE dim_metro_us")
        with pytest.raises(ValueError, match="Missing required warehouse tables"):
            inspect(con, tmp_path)
    finally:
        con.close()
