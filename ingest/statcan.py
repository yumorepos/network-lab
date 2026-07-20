"""StatCan stable-URL table CSVs (Open Government Licence — Canada; attributed
in README). Includes the discontinued transborder O&D tables frozen around
2018, which anchor the transfer factor, and current airport traffic tables
used as reconciliation controls.
"""
from __future__ import annotations

import duckdb

from .common import DATA_PARQUET, DATA_RAW, download_file, log, unzip_all

URL = "https://www150.statcan.gc.ca/n1/tbl/csv/{tid}-eng.zip"

TABLES = {
    "23100253": "airport traffic by sector (annual control totals)",
    "23100256": "transborder city-pair >4000 pax (frozen ~2018; transfer anchor)",
    "23100249": "transborder O&D detail (frozen)",
    "23100255": "transborder O&D detail (frozen)",
    "23100257": "transborder O&D detail (frozen)",
    "23100259": "quarterly passengers by sector (reconciliation control)",
    "23100312": "monthly screened passengers (seasonality)",
    "17100135": "population estimates, census metropolitan areas",
}


def run() -> None:
    out_dir = DATA_PARQUET / "statcan"
    out_dir.mkdir(parents=True, exist_ok=True)
    for tid, desc in TABLES.items():
        pq = out_dir / f"sc_{tid}.parquet"
        if pq.exists():
            log(f"cached: {pq.name}")
            continue
        z = DATA_RAW / "statcan" / f"{tid}.zip"
        ok = download_file(URL.format(tid=tid), z, ok_404=True)
        if not ok:
            log(f"statcan {tid} 404 — record in LIMITATIONS if load-bearing")
            continue
        extracted = unzip_all(z, DATA_RAW / "statcan" / tid)
        csv = [p for p in extracted
               if p.name == f"{tid}.csv"][0]
        con = duckdb.connect()
        con.execute(f"""
            COPY (SELECT * FROM read_csv('{csv}', header=true,
                  all_varchar=true))
            TO '{pq}' (FORMAT PARQUET)
        """)
        n = con.execute(f"SELECT count(*) FROM '{pq}'").fetchone()[0]
        assert n > 10, f"statcan {tid}: too few rows"
        log(f"statcan {tid}: {n} rows — {desc}")


if __name__ == "__main__":
    run()
