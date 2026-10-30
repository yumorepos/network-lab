"""Read-only actual Mac warehouse country-conflict segment exposure audit.

Uses ORIGINAL dim_airport + fact_segment and SAME archived Master Coordinate
source Parquet. This diagnoses source-country join exposure but does not repair
AirportIDs, alter data, or certify screen/replay verdict changes.

Run from an isolated *current* repository checkout:
python -m scripts.audit_country_conflict_fact_exposure \
  --root "$HOME/Projects/network-lab" --output-dir "$HOME/Desktop/NEW_FOLDER"
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path

from scripts.audit_airport_label_candidate import project_labels
from scripts.audit_cross_source_country_exposure import CONVENTIONS_TO_VERIFY


def observed_conflicts(dim_rows: list[dict]) -> list[dict]:
    """Classify the warehouse's actual stored ISO country versus selected market."""
    conflicts = []
    for row in dim_rows:
        a, b = row.get("stored_country"), row.get("candidate_country")
        if not a or not b or a == b:
            continue
        category = ("administrative_convention_to_verify"
                    if (a, b) in CONVENTIONS_TO_VERIFY
                    else "unresolved_country_conflict")
        conflicts.append({
            "code": row["iata_code"], "stored_country": a,
            "market_source_country": b, "category": category,
            "stored_market_id": row.get("stored_market_id"),
            "market_source_name": row.get("candidate_market_name"),
        })
    return sorted(conflicts, key=lambda x: x["code"])


def query_fact_exposure(con, conflicts: list[dict]) -> dict:
    """Group source segment endpoints; no mutations, no ticket O&D claims."""
    if not conflicts:
        return {"latest_reported_month": None, "latest12_cutoff_exclusive": None,
                "segment_endpoint_by_code_year_country": [],
                "hub_origin_us_destination_exposure": [],
                "summary_by_category": []}
    codes = sorted({x["code"] for x in conflicts})
    latest = con.execute("""
        SELECT max(year::INTEGER * 100 + month::INTEGER)
        FROM fact_segment WHERE service_class IN ('F','L')
    """).fetchone()[0]
    if latest is None:
        raise ValueError("No F/L source months in actual fact_segment")
    cutoff = int(latest) - 100
    # Country is the *actual* T-100 operated-segment source country field,
    # which is independent of both the OurAirports country and BTS master
    # coordinate lookup's code-only country.
    query = """
        WITH conflict_codes AS (
          SELECT unnest(?::VARCHAR[]) AS code
        ), endpoint AS (
          SELECT s.origin AS code, 'origin' AS side,
                 s.origin_country AS reported_country,
                 s.year::INTEGER AS year, s.month::INTEGER AS month,
                 s.passengers, s.departures
          FROM fact_segment s
          JOIN conflict_codes c ON s.origin = c.code
          WHERE s.service_class IN ('F','L')
            AND s.departures > 0
          UNION ALL
          SELECT s.dest AS code, 'destination' AS side,
                 s.dest_country AS reported_country,
                 s.year::INTEGER AS year, s.month::INTEGER AS month,
                 s.passengers, s.departures
          FROM fact_segment s
          JOIN conflict_codes c ON s.dest = c.code
          WHERE s.service_class IN ('F','L')
            AND s.departures > 0
        )
        SELECT code, side, year, reported_country,
               count(*)::BIGINT AS endpoint_rows,
               sum(coalesce(passengers,0))::DOUBLE AS passenger_segment_legs,
               sum(coalesce(departures,0))::DOUBLE AS departures,
               sum(CASE WHEN year * 100 + month > ?
                   THEN 1 ELSE 0 END)::BIGINT AS latest12_endpoint_rows,
               sum(CASE WHEN year * 100 + month > ?
                   THEN coalesce(passengers,0) ELSE 0 END)::DOUBLE
                   AS latest12_passenger_segment_legs
        FROM endpoint
        GROUP BY 1,2,3,4
        ORDER BY year DESC, code, side, reported_country
    """
    cur = con.execute(query, [codes, cutoff, cutoff])
    names = [x[0] for x in cur.description]
    endpoints = [dict(zip(names, row)) for row in cur.fetchall()]

    # Narrowest current candidate-served path: hub-origin flights bound for
    # US destinations. This does NOT apply marketing-brand rules or simulate
    # the actual candidate/replay results; it only bounds direct source rows.
    query_hubs = """
        WITH conflict_codes AS (SELECT unnest(?::VARCHAR[]) AS code)
        SELECT s.origin AS hub, s.dest AS code, s.dest_country AS reported_country,
               a.iso_country AS stored_airport_country,
               cast(a.city_market_id AS VARCHAR) AS stored_market_id,
               cast(m.cbsa AS VARCHAR) AS mapped_cbsa,
               count(*)::BIGINT AS segment_rows,
               sum(coalesce(s.passengers,0))::DOUBLE AS passenger_segment_legs,
               sum(coalesce(s.departures,0))::DOUBLE AS departures
        FROM fact_segment s
        JOIN conflict_codes c ON s.dest = c.code
        LEFT JOIN dim_airport a ON a.iata_code = s.dest
        LEFT JOIN map_citymarket_cbsa m ON m.city_market_id = a.city_market_id
        WHERE s.origin IN ('YYC','SEA','YYZ')
          AND s.dest_country = 'US'
          AND s.service_class IN ('F','L')
          AND s.departures > 0 AND
              s.year::INTEGER*100 + s.month::INTEGER > ?
        GROUP BY 1,2,3,4,5,6
        ORDER BY segment_rows DESC, code
    """
    cur = con.execute(query_hubs, [codes, cutoff])
    hub_names = [x[0] for x in cur.description]
    hub_rows = [dict(zip(hub_names, row)) for row in cur.fetchall()]

    lookup = {x["code"]: x for x in conflicts}
    aggregate = {}
    for e in endpoints:
        c = lookup[e["code"]]
        e["country_conflict_category"] = c["category"]
        e["stored_country"] = c["stored_country"]
        e["selected_market_country"] = c["market_source_country"]
        category = aggregate.setdefault(c["category"], {
            "codes_with_operated_segments": set(), "endpoint_rows": 0,
            "passenger_segment_legs": 0.0, "latest12_endpoint_rows": 0,
            "latest12_passenger_segment_legs": 0.0,
            "reported_country_matches_stored_rows": 0,
            "reported_country_matches_selected_market_rows": 0,
            "reported_country_matches_neither_rows": 0,
        })
        category["codes_with_operated_segments"].add(e["code"])
        n = int(e["endpoint_rows"])
        category["endpoint_rows"] += n
        category["passenger_segment_legs"] += float(e["passenger_segment_legs"])
        category["latest12_endpoint_rows"] += int(e["latest12_endpoint_rows"])
        category["latest12_passenger_segment_legs"] += float(
            e["latest12_passenger_segment_legs"])
        if e["reported_country"] == c["stored_country"]:
            category["reported_country_matches_stored_rows"] += n
        elif e["reported_country"] == c["market_source_country"]:
            category["reported_country_matches_selected_market_rows"] += n
        else:
            category["reported_country_matches_neither_rows"] += n
    summary = [
        {"category": category, **{k: (
            len(value) if k == "codes_with_operated_segments" else value)
            for k, value in info.items()}}
        for category, info in sorted(aggregate.items())
    ]
    return {
        "latest_reported_month": int(latest),
        "latest12_cutoff_exclusive": cutoff,
        "segment_endpoint_by_code_year_country": endpoints,
        "hub_origin_us_destination_exposure": hub_rows,
        "summary_by_category": summary,
    }


def audit(con, lookup: Path) -> dict:
    required_tables = {"dim_airport", "fact_segment", "map_citymarket_cbsa"}
    existing = {x[0] for x in con.execute("SHOW TABLES").fetchall()}
    if required_tables - existing:
        raise ValueError("Missing actual warehouse tables: " +
                         ", ".join(sorted(required_tables - existing)))
    rows = project_labels(con, lookup)
    conflict = observed_conflicts(rows)
    data = query_fact_exposure(con, conflict)
    counts = Counter(x["category"] for x in conflict)
    return {
        "scope": "READ-ONLY actual stored-country/selected-market source exposure",
        "airport_dim_rows": len(rows),
        "country_conflicts_total": len(conflict),
        "country_conflicts_by_category": dict(counts),
        "all_country_conflict_codes": conflict,
        **data,
        "original_warehouse_modified": False,
        "numeric_city_market_id_correctness_certified": False,
        "country_conventions_authoritatively_resolved": False,
        "source_stable_airport_ids_fully_recovered": False,
        "screen_outputs_recomputed": False,
        "historical_463_replay_decisions_recomputed": False,
        "warning": ("Endpoint passenger-segment legs include both ends of a "
                    "flight and are NOT unique travelers, ticket OD, loss, "
                    "proven wrong forecasts or changed published verdicts."),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path,
                   default=Path.home() / "Projects" / "network-lab")
    p.add_argument("--output-dir", type=Path)
    args = p.parse_args()
    root = args.root.expanduser().resolve()
    db = root / "data" / "warehouse.duckdb"
    source = root / "data" / "parquet" / "lookups" / "master_coord.parquet"
    for path in (db, source):
        if not path.is_file():
            p.error(f"Missing original source: {path}")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = (args.output_dir or (Path.home() / "Desktop" /
              f"NetworkLab-Country-Fact-Exposure-{stamp}")).resolve()
    if output.exists() or root == output or root in output.parents:
        p.error("Output must be new and outside original project")
    import duckdb
    con = duckdb.connect(str(db), read_only=True)
    try:
        con.execute("SET threads = 2")
        result = audit(con, source)
    finally:
        con.close()
    output.mkdir(parents=True, exist_ok=False)
    (output / "country_fact_exposure.json").write_text(
        json.dumps(result, sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8")
    with (output / "country_endpoint_by_year.csv").open(
            "w", newline="", encoding="utf-8") as f:
        columns = [
            "code", "side", "year", "reported_country",
            "stored_country", "selected_market_country",
            "country_conflict_category", "endpoint_rows",
            "passenger_segment_legs", "departures",
            "latest12_endpoint_rows", "latest12_passenger_segment_legs",
        ]
        w = csv.DictWriter(f, columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(result["segment_endpoint_by_code_year_country"])
    (output / "README.md").write_text(
        "# Read-only actual warehouse country conflict exposure\n\n"
        f"Dimension country disagreements: {result['country_conflicts_total']}; "
        f"classification: {result['country_conflicts_by_category']}.\n"
        f"Current latest-12 cutoff (exclusive): {result['latest12_cutoff_exclusive']}.\n"
        f"Reported segment exposure groups: "
        f"{len(result['segment_endpoint_by_code_year_country'])}.\n\n"
        "**Original Mac DuckDB opened read-only. No facts, models, source "
        "files, outputs or historic replay decisions have been changed.**\n"
        "The reported endpoint legs are exposure only, never a verdict delta.\n",
        encoding="utf-8",
    )
    print("Report folder:", output)
    print("Country disagreements:", result["country_conflicts_by_category"])
    print("No original data or model results were modified.")


if __name__ == "__main__":
    main()
