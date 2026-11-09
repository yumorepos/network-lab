"""Read-only bounded current-hub source exposure to airport -> CBSA joins.

This is *not* a counterfactual model/replay test or an airport correction.

From an up-to-date network-lab checkout:
    python -m scripts.audit_hub_cbsa_consumer_exposure \\
      --root "$PWD" --output-dir "$HOME/Desktop/NetworkLab-Hub-CBSA-NEW"

Reads preserved data/warehouse.duckdb read-only, produces only small reports
in a *new*, external output directory. No model, input, warehouse or Git writes.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path

HUBS = ("YYC", "SEA", "YYZ")
FOCUS_CODES = ("ASE", "PFN", "PBI", "DJT", "SJU", "GUM", "STT", "SPN", "STX")


def _select(con, sql: str, params: list | None = None) -> list[dict]:
    cur = con.execute(sql, params or [])
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _validate(con) -> None:
    required = {"dim_airport", "map_citymarket_cbsa", "dim_metro_us", "fact_segment"}
    present = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    if missing := sorted(required - present):
        raise ValueError("Missing required warehouse tables: " + ", ".join(missing))
    for table, key in (("dim_airport", "iata_code"),
                       ("map_citymarket_cbsa", "city_market_id"),
                       ("dim_metro_us", "cbsa")):
        bad = con.execute(f"""
            SELECT {key}, count(*) AS n FROM {table}
            WHERE {key} IS NOT NULL GROUP BY 1 HAVING count(*) > 1 LIMIT 1
        """).fetchall()
        if bad:
            raise ValueError(f"Non-unique {table}.{key}: {bad[0]}")


def audit(con) -> dict:
    """Read-only F/L + positive-departure T-100 source traffic, not ticket O&D."""
    _validate(con)
    latest = con.execute("""
        SELECT max(year::INTEGER*100 + month::INTEGER)
        FROM fact_segment WHERE service_class IN ('F','L')
    """).fetchone()[0]
    if latest is None:
        raise ValueError("No F/L reported months")
    cutoff = int(latest) - 100

    hub_rows = _select(con, """
        SELECT s.origin AS hub, s.dest AS code,
               s.dest_country AS source_reported_country,
               a.iso_country AS stored_airport_country,
               CAST(a.city_market_id AS VARCHAR) AS stored_market_id,
               CAST(m.cbsa AS VARCHAR) AS mapped_cbsa,
               m.cm_name AS mapped_source_citymarket_name,
               m.method AS mapping_method,
               u.name AS census_metro_name,
               CASE
                 WHEN a.iata_code IS NULL THEN 'airport_not_in_dim'
                 WHEN a.city_market_id IS NULL THEN 'no_city_market_id'
                 WHEN m.city_market_id IS NULL THEN 'no_cbsa_mapping'
                 WHEN u.cbsa IS NULL THEN 'cbsa_not_in_metro'
                 ELSE 'mapped'
               END AS mapping_status,
               count(*)::BIGINT AS segment_rows,
               sum(coalesce(s.departures,0))::DOUBLE AS departures,
               sum(coalesce(s.seats,0))::DOUBLE AS seats,
               sum(coalesce(s.passengers,0))::DOUBLE AS passenger_segment_legs
        FROM fact_segment s
        LEFT JOIN dim_airport a ON a.iata_code = s.dest
        LEFT JOIN map_citymarket_cbsa m ON m.city_market_id = a.city_market_id
        LEFT JOIN dim_metro_us u ON u.cbsa = m.cbsa
        WHERE s.origin IN ('YYC','SEA','YYZ')
          AND s.dest_country = 'US'
          AND s.service_class IN ('F','L')
          AND s.departures > 0
          AND s.year::INTEGER*100 + s.month::INTEGER > ?
        GROUP BY 1,2,3,4,5,6,7,8,9,10
        ORDER BY 1, 10, 14 DESC, 2
    """, [cutoff])
    # Note the hub-path query deliberately does NOT resolve marketing brands,
    # population/seat candidate eligibility, historical identity or replays.
    summary = defaultdict(lambda: {"destination_codes": set(), "segment_rows": 0,
                                   "departures": 0., "seats": 0.,
                                   "passenger_segment_legs": 0.})
    for row in hub_rows:
        r = summary[(row["hub"], row["mapping_status"])]
        r["destination_codes"].add(row["code"])
        for k in ("segment_rows", "departures", "seats", "passenger_segment_legs"):
            r[k] += row[k]
    summary_rows = [{"hub": hub, "mapping_status": stat,
                     **{k: (len(v) if k == "destination_codes" else v)
                        for k,v in vals.items()}}
                    for (hub,stat), vals in sorted(summary.items())]

    focus_rows = _select(con, """
        WITH codes AS (SELECT unnest(?::VARCHAR[]) AS code),
        endpoints AS (
          SELECT s.origin AS code, 'origin' AS side,
                 s.origin_country AS source_reported_country,
                 s.year::INTEGER AS year, s.passengers, s.departures
          FROM fact_segment s JOIN codes c ON s.origin = c.code
          WHERE s.service_class IN ('F','L') AND s.departures > 0
          UNION ALL
          SELECT s.dest AS code, 'destination' AS side,
                 s.dest_country AS source_reported_country,
                 s.year::INTEGER AS year, s.passengers, s.departures
          FROM fact_segment s JOIN codes c ON s.dest = c.code
          WHERE s.service_class IN ('F','L') AND s.departures > 0
        )
        SELECT code, side, source_reported_country, year,
               count(*)::BIGINT AS endpoint_rows,
               sum(coalesce(departures,0))::DOUBLE AS departures,
               sum(coalesce(passengers,0))::DOUBLE AS passenger_segment_legs
        FROM endpoints GROUP BY 1,2,3,4
        ORDER BY code, year, side, source_reported_country
    """, [list(FOCUS_CODES)])

    focus_mappings = _select(con, """
        SELECT a.iata_code AS code,
               a.iso_country AS stored_airport_country,
               CAST(a.city_market_id AS VARCHAR) AS stored_market_id,
               a.city_market_name AS stored_market_name,
               CAST(m.cbsa AS VARCHAR) AS mapped_cbsa,
               m.cm_name AS mapped_source_citymarket_name,
               m.method AS mapping_method, u.name AS census_metro_name,
               u.population AS census_metro_population
        FROM dim_airport a
        LEFT JOIN map_citymarket_cbsa m ON m.city_market_id = a.city_market_id
        LEFT JOIN dim_metro_us u ON u.cbsa = m.cbsa
        WHERE a.iata_code IN (SELECT unnest(?::VARCHAR[]))
        ORDER BY code
    """, [list(FOCUS_CODES)])
    return {
        "scope": "READ-ONLY latest-12 hub-to-US source endpoint CBSA exposure",
        "latest_reported_month": int(latest),
        "latest12_cutoff_exclusive": cutoff,
        "hub_destination_mapping_rows": hub_rows,
        "hub_mapping_status_summary": summary_rows,
        "focus_airport_history_by_code_year_side_country": focus_rows,
        "focus_airport_stored_mapping": focus_mappings,
        "warehouse_modified": False,
        "official_historical_airport_ids_verified": False,
        "eligibility_or_brand_filter_applied": False,
        "screen_or_replay_recomputed": False,
        "warning": "T-100 passenger-segment legs are not unique travelers or ticket O&D; missing CBSA alone is not proven model error. No counterfactual verdict delta computed.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    out = args.output_dir.expanduser().resolve()
    if out.exists() or out == root or root in out.parents:
        parser.error("Output directory must be new and outside original project")
    db = root / "data" / "warehouse.duckdb"
    if not db.is_file():
        parser.error(f"Original warehouse not found: {db}")
    import duckdb
    con = duckdb.connect(str(db), read_only=True)
    try:
        con.execute("SET threads = 2")
        results = audit(con)
    finally:
        con.close()
    out.mkdir(parents=True, exist_ok=False)
    (out / "hub_cbsa_exposure.json").write_text(
        json.dumps(results, indent=2, sort_keys=True, default=str)+"\n",
        encoding="utf-8")
    cols = ["hub", "code", "source_reported_country", "stored_airport_country",
            "stored_market_id", "mapped_cbsa", "mapped_source_citymarket_name",
            "mapping_method", "census_metro_name", "mapping_status",
            "segment_rows", "departures", "seats", "passenger_segment_legs"]
    with (out / "hub_destinations.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore")
        w.writeheader()
        w.writerows(results["hub_destination_mapping_rows"])
    (out / "README.md").write_text(
        "# Narrow read-only hub→US CBSA mapping evidence\n\n"
        f"Latest month {results['latest_reported_month']}; cutoff exclusive "
        f"{results['latest12_cutoff_exclusive']}.\n"
        f"Hub/destination mapping groups: {len(results['hub_destination_mapping_rows'])}.\n\n"
        "No warehouse, source, screening model, or replay change.\n"
        "No ticket O&D, unique passengers, candidate eligibility, brand or verdict delta claimed.\n",
        encoding="utf-8")
    print("Report folder:",out)
    print("Hub/destination groups:",len(results["hub_destination_mapping_rows"]))
    print("No warehouse or model outputs modified.")


if __name__ == "__main__":
    main()