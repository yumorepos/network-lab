"""Aviation Support Tables via the same DL_SelectFields mechanism:
288 Master Coordinate (airport <-> CityMarketID + coordinates),
304 Carrier Decode, 300 AircraftTypes. The old Download_Lookup.asp endpoint
redirects to the homepage and is treated as retired.
"""
from __future__ import annotations

import duckdb

from .common import DATA_PARQUET, DATA_RAW, log
from .transtats import ALL_FIELDS, download_table_year, data_csv

TABLES = {288: "master_coord", 304: "carrier_decode", 300: "aircraft_types"}


def run() -> None:
    out_dir = DATA_PARQUET / "lookups"
    out_dir.mkdir(parents=True, exist_ok=True)
    for tid, name in TABLES.items():
        pq = out_dir / f"{name}.parquet"
        if pq.exists():
            log(f"cached: {pq.name}")
            continue
        z = download_table_year(tid, "All", ALL_FIELDS,
                                DATA_RAW / "lookups" / f"{name}.zip")
        csv = data_csv(z, DATA_RAW / "lookups" / "extract")
        con = duckdb.connect()
        con.execute(f"""
            COPY (SELECT * FROM read_csv('{csv}', header=true,
                  all_varchar=true, ignore_errors=true))
            TO '{pq}' (FORMAT PARQUET)
        """)
        n = con.execute(f"SELECT count(*) FROM '{pq}'").fetchone()[0]
        assert n > 50, f"{name}: too few rows"
        csv.unlink(missing_ok=True)
        log(f"{name}: {n} rows")


if __name__ == "__main__":
    run()
