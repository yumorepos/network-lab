"""T-100 Segment (All Carriers), Table 293: domestic and international segments
for every carrier reporting to BTS. One download per year -> slim Parquet.

2020 is deliberately excluded everywhere: COVID operations are not usable for
calibration, current-state capacity, or the backtest.

History runs from 1990, the earliest year TranStats offers for this table. The
window was 2018 onward through Round 4, which made every route launch and exit
before 2018 invisible and forced the backtest onto a 74-row hand-compiled
register. The full panel is small (about 5 MB per year) and contains every
route start and stop ever filed, which is what PHASE_5_6_PLAN.md W1.2 turns
into a mechanical route-spell register. Probed at the far end before
backfilling: 1990 returns the same 14 columns, 219 carriers and a system load
factor of 0.570, with foreign origins present, so the schema and the existing
assertions hold across the span.
"""
from __future__ import annotations

import duckdb

from .common import DATA_PARQUET, DATA_RAW, log
from .transtats import T100_SEGMENT_ALL, download_table_year, data_csv

EARLIEST_YEAR = 1990        # earliest year TranStats offers for table 293
COVID_EXCLUDED = {2020}
YEARS = [y for y in range(EARLIEST_YEAR, 2027) if y not in COVID_EXCLUDED]

FIELDS = ["YEAR", "QUARTER", "MONTH", "UNIQUE_CARRIER", "ORIGIN",
          "ORIGIN_COUNTRY", "DEST", "DEST_COUNTRY", "SEATS", "PASSENGERS",
          "DEPARTURES_PERFORMED", "DISTANCE", "AIRCRAFT_TYPE", "CLASS"]


def run() -> None:
    out_dir = DATA_PARQUET / "t100"
    out_dir.mkdir(parents=True, exist_ok=True)
    for year in YEARS:
        pq = out_dir / f"t100_{year}.parquet"
        if pq.exists():
            log(f"cached: {pq.name}")
            continue
        try:
            z = download_table_year(T100_SEGMENT_ALL, year, FIELDS,
                                    DATA_RAW / "t100" / f"t100_{year}.zip")
        except Exception as e:  # noqa: BLE001
            if year >= 2026:
                log(f"t100 {year} unavailable ({e}); skipping partial year")
                continue
            raise
        csv = data_csv(z, DATA_RAW / "t100" / "extract")
        con = duckdb.connect()
        con.execute(f"""
            COPY (
              SELECT YEAR::SMALLINT AS year, QUARTER::TINYINT AS quarter,
                     MONTH::TINYINT AS month, UNIQUE_CARRIER AS carrier,
                     ORIGIN AS origin, ORIGIN_COUNTRY AS origin_country,
                     DEST AS dest, DEST_COUNTRY AS dest_country,
                     SEATS::BIGINT AS seats, PASSENGERS::BIGINT AS passengers,
                     DEPARTURES_PERFORMED::INT AS departures,
                     DISTANCE::INT AS distance_mi,
                     AIRCRAFT_TYPE AS aircraft_type, CLASS AS service_class
              FROM read_csv_auto('{csv}', header=true)
              WHERE DEPARTURES_PERFORMED > 0
            ) TO '{pq}' (FORMAT PARQUET)
        """)
        n, mn_s, mn_p = con.execute(
            f"SELECT count(*), min(seats), min(passengers) FROM '{pq}'"
        ).fetchone()
        assert n > 10000, f"t100 {year}: suspiciously few rows ({n})"
        assert mn_s >= 0 and mn_p >= 0, f"t100 {year}: negative counts"
        # scheduled passenger service should have sane load factors overall
        lf = con.execute(f"""
            SELECT sum(passengers)::DOUBLE / nullif(sum(seats),0) FROM '{pq}'
            WHERE service_class IN ('F','L') AND seats > 0
        """).fetchone()[0]
        assert lf is None or 0.3 < lf < 1.0, f"t100 {year}: odd system LF {lf}"
        csv.unlink(missing_ok=True)
        log(f"t100 {year}: {n} rows, system LF {lf:.3f}" if lf else
            f"t100 {year}: {n} rows")


if __name__ == "__main__":
    run()
