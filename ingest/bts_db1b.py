"""DB1B Market: 10% ticket sample, market-level O&D with fares.

PREZIP bulk endpoint, one zip per quarter. US domestic only by construction -
there are no transborder fares in DB1B and nothing here implies otherwise.
Raw zips are kept as the local cache; extracted CSVs are deleted after the
slim Parquet is written.
"""
from __future__ import annotations

import duckdb

from .common import DATA_PARQUET, DATA_RAW, download_file, log, unzip_all

PREZIP = ("https://transtats.bts.gov/PREZIP/"
          "Origin_and_Destination_Survey_DB1BMarket_{y}_{q}.zip")

# calibration (pre-COVID), backtest vintages, current
QUARTERS = ([(y, q) for y in (2018, 2019) for q in (1, 2, 3, 4)]
            + [(y, q) for y in (2021, 2022) for q in (1, 2, 3, 4)]
            + [(y, q) for y in (2023, 2024, 2025) for q in (1, 2, 3, 4)])


def run() -> None:
    out_dir = DATA_PARQUET / "db1b"
    out_dir.mkdir(parents=True, exist_ok=True)
    for y, q in QUARTERS:
        pq = out_dir / f"db1b_{y}_q{q}.parquet"
        if pq.exists():
            log(f"cached: {pq.name}")
            continue
        z = DATA_RAW / "db1b" / f"db1b_{y}_{q}.zip"
        ok = download_file(PREZIP.format(y=y, q=q), z, ok_404=True)
        if not ok:
            log(f"db1b {y} Q{q}: not published yet; skipping")
            continue
        extracted = unzip_all(z, DATA_RAW / "db1b" / "extract")
        csv = [p for p in extracted if p.suffix.lower() == ".csv"][0]
        con = duckdb.connect()
        con.execute(f"""
            COPY (
              SELECT Year::SMALLINT AS year, Quarter::TINYINT AS quarter,
                     Origin AS origin, OriginCityMarketID::INT AS origin_cm,
                     Dest AS dest, DestCityMarketID::INT AS dest_cm,
                     TkCarrier AS tk_carrier, OpCarrier AS op_carrier,
                     Passengers::DOUBLE AS passengers,
                     MktFare::DOUBLE AS mkt_fare,
                     MktDistance::DOUBLE AS mkt_distance,
                     NonStopMiles::DOUBLE AS nonstop_miles,
                     MktCoupons::TINYINT AS coupons
              FROM read_csv_auto('{csv}', header=true)
              WHERE Passengers > 0 AND MktFare BETWEEN 25 AND 5000
            ) TO '{pq}' (FORMAT PARQUET)
        """)
        n, f_lo, f_hi = con.execute(
            f"SELECT count(*), min(mkt_fare), max(mkt_fare) FROM '{pq}'"
        ).fetchone()
        assert n > 100_000, f"db1b {y}Q{q}: too few rows ({n})"
        assert f_lo >= 25 and f_hi <= 5000, "fare filter failed"
        for p in extracted:
            p.unlink(missing_ok=True)
        log(f"db1b {y} Q{q}: {n} rows")


if __name__ == "__main__":
    run()
