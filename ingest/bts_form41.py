"""Form 41 financial schedules: P-5.2 (aircraft operating expenses by carrier
and aircraft type, Table 297) and P-1.2 (income statement, Table 295).
Small tables; download all columns per year.
"""
from __future__ import annotations

import duckdb

from .common import DATA_PARQUET, DATA_RAW, log
from .transtats import ALL_FIELDS, download_table_year, data_csv

P12_TABLE = 295
P52_TABLE = 297
YEARS = [2018, 2019, 2021, 2022, 2023, 2024, 2025]


def _fetch(table_id: int, name: str) -> None:
    out_dir = DATA_PARQUET / "form41"
    out_dir.mkdir(parents=True, exist_ok=True)
    for year in YEARS:
        pq = out_dir / f"{name}_{year}.parquet"
        if pq.exists():
            log(f"cached: {pq.name}")
            continue
        try:
            z = download_table_year(table_id, year, ALL_FIELDS,
                                    DATA_RAW / "form41" / f"{name}_{year}.zip")
        except Exception as e:  # noqa: BLE001
            if year >= 2025:
                log(f"{name} {year} unavailable ({e}); skipping")
                continue
            raise
        csv = data_csv(z, DATA_RAW / "form41" / "extract")
        con = duckdb.connect()
        con.execute(f"""
            COPY (SELECT * FROM read_csv_auto('{csv}', header=true))
            TO '{pq}' (FORMAT PARQUET)
        """)
        n = con.execute(f"SELECT count(*) FROM '{pq}'").fetchone()[0]
        assert n > 50, f"{name} {year}: suspiciously few rows ({n})"
        csv.unlink(missing_ok=True)
        log(f"{name} {year}: {n} rows")


def run() -> None:
    _fetch(P52_TABLE, "p52")
    _fetch(P12_TABLE, "p12")


if __name__ == "__main__":
    run()
