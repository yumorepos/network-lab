"""OurAirports reference: coordinates, IATA codes, countries. Public domain."""
from __future__ import annotations

import duckdb

from .common import DATA_PARQUET, DATA_RAW, download_file, log

URL = "https://davidmegginson.github.io/ourairports-data/airports.csv"


def run() -> None:
    raw = DATA_RAW / "ourairports" / "airports.csv"
    download_file(URL, raw)
    pq = DATA_PARQUET / "ourairports" / "airports.parquet"
    pq.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(f"""
        COPY (
          SELECT ident, type, name, latitude_deg, longitude_deg,
                 iso_country, iso_region, municipality, iata_code
          FROM read_csv_auto('{raw}', header=true)
          WHERE type IN ('large_airport','medium_airport','small_airport')
            AND iata_code IS NOT NULL AND iata_code != ''
        ) TO '{pq}' (FORMAT PARQUET)
    """)
    n = con.execute(f"SELECT count(*) FROM '{pq}'").fetchone()[0]
    yyc = con.execute(
        f"SELECT count(*) FROM '{pq}' WHERE iata_code='YYC'").fetchone()[0]
    assert n > 4000 and yyc == 1, "ourairports sanity failed"
    log(f"ourairports: {n} airports with IATA codes")


if __name__ == "__main__":
    run()
