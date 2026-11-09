"""Read-only verification of two BTS city markets with multiple Census components.

GSP / BTS 31871: Greenville/Spartanburg, SC; 2023 Census CBSAs 24860, 43900.
JAN / BTS 32448: Jackson/Vicksburg, MS; 2023 CBSAs 27140, 46980.

This script does not choose a replacement CBSA or calculate a counterfactual.
It inspects the ORIGINAL DuckDB read-only, saved BTS lookup rows, and the
three committed screening CSVs; it writes only a new external report.

python -m scripts.audit_gsp_jan_geography --root "$PWD" \
    --output-dir "$HOME/Desktop/NetworkLab-GSP-JAN-NEW"
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
from pathlib import Path

TARGETS = {"GSP": 31871, "JAN": 32448}
ALTERNATIVES = {"GSP": ("24860", "43900"), "JAN": ("27140", "46980")}
STUDIES = ("westjet_yyc", "alaska_sea", "porter_yyz")


def query(con, sql: str, args: list | None = None) -> list[dict]:
    cur = con.execute(sql, args or [])
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def inspect(con, root: Path) -> dict:
    required = {"dim_airport", "map_citymarket_cbsa", "dim_metro_us", "fact_segment"}
    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    if missing := sorted(required - tables):
        raise ValueError("Missing required warehouse tables: " + ", ".join(missing))

    # Fail rather than count a duplicated geography join as extra passengers.
    for table, key in (
        ("dim_airport", "iata_code"),
        ("map_citymarket_cbsa", "city_market_id"),
        ("dim_metro_us", "cbsa"),
    ):
        duplicate = query(con, f"""
            SELECT {key}, count(*) AS n FROM {table}
            WHERE {key} IS NOT NULL
            GROUP BY 1 HAVING count(*) > 1 LIMIT 1
        """)
        if duplicate:
            raise ValueError(f"Non-unique {table}.{key}: {duplicate}")

    airport_rows = query(con, """
        SELECT a.iata_code AS airport_code, a.iso_country AS airport_country,
               CAST(a.city_market_id AS VARCHAR) AS stored_city_market_id,
               a.city_market_name AS stored_city_market_name,
               CAST(m.cbsa AS VARCHAR) AS selected_cbsa,
               m.cm_name AS mapping_city_market_name,
               m.method AS mapping_method,
               u.name AS census_cbsa_name, u.population AS census_population
        FROM dim_airport a
        LEFT JOIN map_citymarket_cbsa m ON a.city_market_id=m.city_market_id
        LEFT JOIN dim_metro_us u ON m.cbsa=u.cbsa
        WHERE a.iata_code IN ('GSP','JAN')
        ORDER BY a.iata_code
    """)
    if {r["airport_code"] for r in airport_rows} != set(TARGETS):
        raise ValueError("Both GSP and JAN must be present in dim_airport")

    # Reference alternatives are separate CBSAs, NOT automatic substitutes.
    cbsa_rows = query(con, """
        SELECT CAST(cbsa AS VARCHAR) AS cbsa, name, population
        FROM dim_metro_us
        WHERE CAST(cbsa AS VARCHAR) IN ('24860','43900','27140','46980')
        ORDER BY cbsa
    """)
    latest = con.execute("""
        SELECT max(year::INTEGER*100 + month::INTEGER)
        FROM fact_segment WHERE service_class IN ('F','L')
    """).fetchone()[0]
    if latest is None:
        raise ValueError("No F/L operating segment months")
    cutoff = int(latest) - 100

    # Reproduce the candidate consumer's recent source window, but not its
    # operating-carrier -> marketing-brand resolution or market exclusions.
    recent = query(con, """
        SELECT origin AS hub, dest AS airport_code,
               year::INTEGER AS year, month::INTEGER AS month,
               dest_country AS source_country,
               count(*)::BIGINT AS source_segment_rows,
               sum(departures)::DOUBLE AS departures,
               sum(passengers)::DOUBLE AS passenger_segment_legs,
               sum(seats)::DOUBLE AS seats
        FROM fact_segment
        WHERE origin IN ('YYC','SEA','YYZ') AND dest IN ('GSP','JAN')
          AND dest_country='US' AND service_class IN ('F','L')
          AND departures > 0 AND year::INTEGER*100+month::INTEGER > ?
        GROUP BY 1,2,3,4,5 ORDER BY hub,airport_code,year,month
    """, [cutoff])

    # Archived Master Coordinate may retain historic AirportID and reuse.
    lookup = root / "data" / "parquet" / "lookups" / "master_coord.parquet"
    if not lookup.is_file():
        raise FileNotFoundError(f"Archived BTS lookup missing: {lookup}")
    source_ids = query(con, """
        SELECT CAST(AIRPORT AS VARCHAR) AS airport_code,
               CAST(AIRPORT_ID AS VARCHAR) AS source_airport_id,
               CAST(CITY_MARKET_ID AS VARCHAR) AS source_city_market_id,
               CAST(DISPLAY_CITY_MARKET_NAME_FULL AS VARCHAR) AS source_market_name,
               CAST(AIRPORT_IS_LATEST AS VARCHAR) AS source_latest_flag,
               CAST(AIRPORT_COUNTRY_CODE_ISO AS VARCHAR) AS source_country
        FROM read_parquet(?)
        WHERE AIRPORT IN ('GSP','JAN')
        GROUP BY ALL
        ORDER BY airport_code,source_airport_id,source_city_market_id
    """, [str(lookup)])

    screen_rows = []
    for study in STUDIES:
        screen = root / "data" / "parquet" / "outputs" / f"screen_{study}.csv"
        if not screen.is_file():
            raise FileNotFoundError(f"Frozen screening CSV missing: {screen}")
        with screen.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["dest_airport"] in TARGETS:
                    screen_rows.append({
                        k: row[k] for k in (
                            "study_id", "dest_airport", "metro_name", "verdict",
                            "margin_pct", "load_factor", "demand_pax_yr",
                            "demand_source", "demand_method", "confidence"
                        )
                    })
    if len(screen_rows) != 6:
        raise ValueError("Expected six published GSP/JAN rows; review source snapshot")

    warnings = []
    for a in airport_rows:
        code = a["airport_code"]
        if a["stored_city_market_id"] != str(TARGETS[code]):
            warnings.append(f"{code}: archived expected market ID differs from warehouse")
        if a["selected_cbsa"] not in ALTERNATIVES[code]:
            warnings.append(f"{code}: selected CBSA outside the two documented possibilities")
    return {
        "scope": "READ-ONLY GSP/JAN source-vintage and published-candidate geography diagnostic",
        "airport_dimension_and_selected_mapping": airport_rows,
        "reference_census_cbsa_components": cbsa_rows,
        "archived_bts_airport_id_records": source_ids,
        "recent_direct_hub_operated_segments": recent,
        "published_six_screen_rows": screen_rows,
        "latest_reported_month": int(latest),
        "latest12_cutoff_exclusive": cutoff,
        "warnings": warnings,
        "original_warehouse_modified": False,
        "source_stable_airport_id_snapshot_certified": False,
        "bts_citymarket_cbsa_semantics_certified": False,
        "brand_resolved_served_competition_recomputed": False,
        "six_screen_verdicts_recomputed": False,
        "historical_463_replay_decisions_recomputed": False,
        "note": (
            "CBSA components are reference alternatives, not a proposed swap. "
            "F/L segment passenger-legs are not unique travelers, ticket O&D "
            "or a demonstrated wrong verdict."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    a = p.parse_args()
    root = a.root.expanduser().resolve()
    output = a.output_dir.expanduser().resolve()
    if output.exists() or output == root or root in output.parents:
        p.error("Output directory must be new and outside the original repository")
    db = root / "data" / "warehouse.duckdb"
    if not db.is_file():
        p.error(f"Original warehouse not found: {db}")
    import duckdb
    con = duckdb.connect(str(db), read_only=True)
    try:
        con.execute("SET threads=2")
        result = inspect(con, root)
    finally:
        con.close()
    output.mkdir(parents=True, exist_ok=False)
    (output / "gsp_jan_geography.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8")
    (output / "README.md").write_text(
        "# GSP/JAN bounded source and candidate geography audit\n\n"
        "Original DuckDB opened READ-ONLY. No source or model outputs altered.\n"
        f"Published rows inspected: {len(result['published_six_screen_rows'])}.\n"
        "Multiple Census CBSAs do not establish a correct replacement for "
        "a BTS city market. No candidate or historical verdict was recomputed.\n",
        encoding="utf-8")
    print("Report folder:", output)
    print("Published GSP/JAN screen rows:", len(result["published_six_screen_rows"]))
    print("No warehouse, model or replay outputs modified.")


if __name__ == "__main__":
    main()
