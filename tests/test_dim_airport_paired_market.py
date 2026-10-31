"""Regression: a chosen airport CityMarketID and name must come from one row.

These tests exercise the actual builder helper against synthetic source Parquet.
They do not rebuild or modify a user's preserved production DuckDB.
"""
import duckdb

from warehouse.build_marts import _build_dim_airport


def sources(tmp_path):
    root = tmp_path
    (root / "ourairports").mkdir()
    (root / "lookups").mkdir()
    db = duckdb.connect()
    db.execute("""
        CREATE TABLE oa (
          iata_code VARCHAR, name VARCHAR, latitude_deg DOUBLE,
          longitude_deg DOUBLE, iso_country VARCHAR,
          iso_region VARCHAR, municipality VARCHAR
        )
    """)
    db.execute("""
        INSERT INTO oa VALUES
          ('SAW', 'Istanbul Sabiha Gokcen', 40.9, 29.3, 'TR','TR-34','Istanbul'),
          ('ISL', 'Other airport', 40.9, 28.8, 'TR','TR-34','Istanbul'),
          ('JFK', 'John F Kennedy', 40.6,-73.8,'US','US-NY','New York')
    """)
    db.execute("""
        CREATE TABLE mc (
          AIRPORT VARCHAR, AIRPORT_ID VARCHAR, CITY_MARKET_ID VARCHAR,
          DISPLAY_CITY_MARKET_NAME_FULL VARCHAR, AIRPORT_IS_LATEST VARCHAR
        )
    """)
    db.execute("""
        INSERT INTO mc VALUES
          ('SAW','12345','32395','Istanbul, Turkey','true'),
          ('SAW','12346','33459','Marquette, MI','true'),
          ('ISL','11111','32395','Istanbul, Turkey','1'),
          ('ISL','11112','23459','Isabel Pass, AK','1'),
          ('JFK','98765','31703','New York, NY','true'),
          ('JFK','98766','99999','obsolete historical market','false')
    """)
    db.execute(f"COPY oa TO '{root / 'ourairports' / 'airports.parquet'}' (FORMAT PARQUET)")
    db.execute(f"COPY mc TO '{root / 'lookups' / 'master_coord.parquet'}' (FORMAT PARQUET)")
    return db, root


def test_selected_id_and_name_always_belong_to_same_source_row(tmp_path):
    db, root = sources(tmp_path)
    _build_dim_airport(db, root)
    rows = db.execute("""
        SELECT iata_code, city_market_id, city_market_name
        FROM dim_airport ORDER BY iata_code
    """).fetchall()
    assert rows == [
        ('ISL', '32395', 'Istanbul, Turkey'),
        ('JFK', '31703', 'New York, NY'),
        ('SAW', '33459', 'Marquette, MI'),
    ]
    assert db.execute("""
        SELECT count(*) FROM dim_airport
    """).fetchone()[0] == 3
    assert db.execute("""
        SELECT count(*)
        FROM dim_airport a
        JOIN read_parquet(?) m
          ON a.iata_code = m.AIRPORT
         AND a.city_market_id = m.CITY_MARKET_ID
         AND a.city_market_name = m.DISPLAY_CITY_MARKET_NAME_FULL
        WHERE m.AIRPORT_IS_LATEST IN ('true','1')
    """, [str(root / "lookups/master_coord.parquet")]).fetchone()[0] == 3
    db.close()


def test_same_max_market_id_label_tie_break_is_stable(tmp_path):
    db, root = sources(tmp_path)
    db.execute("""
        INSERT INTO mc VALUES
          ('SAW','99999','33459','Z-label','true'),
          ('SAW','00001','33459','A-label','true')
    """)
    db.execute(f"COPY mc TO '{root / 'lookups' / 'master_coord.parquet'}' (FORMAT PARQUET)")
    _build_dim_airport(db, root)
    first = db.execute("""
        SELECT city_market_id, city_market_name FROM dim_airport WHERE iata_code='SAW'
    """).fetchone()
    _build_dim_airport(db, root)
    second = db.execute("""
        SELECT city_market_id, city_market_name FROM dim_airport WHERE iata_code='SAW'
    """).fetchone()
    assert first == second == ('33459','A-label')
    db.close()
