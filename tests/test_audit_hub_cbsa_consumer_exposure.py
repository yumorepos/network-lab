"""Synthetic consumer-path diagnostics, no network or production data needed."""
from __future__ import annotations

import pytest

duckdb = pytest.importorskip("duckdb")
from scripts.audit_hub_cbsa_consumer_exposure import audit


def fixture_con():
    con = duckdb.connect(":memory:")
    con.execute("""CREATE TABLE dim_airport (
        iata_code VARCHAR, city_market_id INTEGER,
        iso_country VARCHAR, city_market_name VARCHAR)""")
    con.execute("""CREATE TABLE map_citymarket_cbsa (
        city_market_id INTEGER, cbsa VARCHAR, cm_name VARCHAR, method VARCHAR)""")
    con.execute("""CREATE TABLE dim_metro_us (
        cbsa VARCHAR, name VARCHAR, population INTEGER)""")
    con.execute("""CREATE TABLE fact_segment (
        year INTEGER, month INTEGER, origin VARCHAR, dest VARCHAR,
        origin_country VARCHAR, dest_country VARCHAR,
        service_class VARCHAR, departures INTEGER, seats INTEGER, passengers INTEGER)""")
    con.execute("""INSERT INTO dim_airport VALUES
      ('ASE',30372,'US','Aspen, CO'),
      ('JFK',31703,'US','New York City, NY'),
      ('SJU',34819,'PR','San Juan, PR')""")
    con.execute("""INSERT INTO map_citymarket_cbsa VALUES
      (31703,'35620','New York City, NY','override'),
      (34819,'41980','San Juan, PR','override')""")
    con.execute("""INSERT INTO dim_metro_us VALUES
      ('35620','New York-Newark, NY',19000000),
      ('41980','San Juan, PR',2000000)""")
    con.execute("""INSERT INTO fact_segment VALUES
      (2026,4,'YYC','ASE','CA','US','F',2,200,100),
      (2026,4,'SEA','JFK','US','US','L',3,300,120),
      (2026,4,'YYZ','SJU','CA','US','F',5,500,250),
      (2026,4,'YYC','ZZZ','CA','US','F',1,100,10),
      (2025,4,'YYC','ASE','CA','US','F',4,400,200),
      (2025,5,'YYC','ASE','CA','US','F',1,100,50),
      (2026,4,'YYC','ASE','CA','US','G',7,700,600),
      (2026,4,'YYC','ASE','CA','US','F',0,100,100),
      (2026,4,'SEA','ASE','US','CA','F',1,100,30)""")
    return con


def test_latest_hub_path_classifies_missing_and_territory_without_claiming_deltas():
    con = fixture_con()
    try:
        a = audit(con)
        assert a['latest_reported_month'] == 202604
        assert a['latest12_cutoff_exclusive'] == 202504
        r = {(v['hub'], v['code']): v for v in a['hub_destination_mapping_rows']}
        assert set(r) == {('YYC','ASE'), ('SEA','JFK'), ('YYZ','SJU'), ('YYC','ZZZ')}
        assert r['YYC','ASE']['mapping_status'] == 'no_cbsa_mapping'
        assert r['YYC','ASE']['passenger_segment_legs'] == 150
        assert r['SEA','JFK']['mapping_status'] == 'mapped'
        assert r['YYC','ZZZ']['mapping_status'] == 'airport_not_in_dim'
        assert r['YYZ','SJU']['stored_airport_country'] == 'PR'
        assert r['YYZ','SJU']['source_reported_country'] == 'US'
        assert a['screen_or_replay_recomputed'] is False
        assert a['eligibility_or_brand_filter_applied'] is False
        assert con.execute('SELECT COUNT(*) FROM fact_segment').fetchone()[0] == 9
    finally:
        con.close()


def test_duplicate_mapping_key_fails_closed():
    con = fixture_con()
    try:
        con.execute("INSERT INTO map_citymarket_cbsa VALUES (31703,'99999','Bad','token')")
        with pytest.raises(ValueError, match='Non-unique map_citymarket_cbsa.city_market_id'):
            audit(con)
    finally:
        con.close()


def test_missing_table_fails_closed():
    con = fixture_con()
    try:
        con.execute('DROP TABLE dim_metro_us')
        with pytest.raises(ValueError, match='Missing required warehouse tables'):
            audit(con)
    finally:
        con.close()
