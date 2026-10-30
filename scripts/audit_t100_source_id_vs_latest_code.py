"""Read-only source-published BTS AirportID vs legacy latest-code market audit.

Input: official all-field T-100 *profile JSON* from research_t100_source_ids,
plus a dated BTS Master Coordinate ZIP. Compares source CityMarketIDs to the
warehouse builder's code-only max(CITY_MARKET_ID) lookup, WITHOUT executing the
warehouse, rebuilding input Parquet, or claiming changed model verdicts.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile


def file_sha256(path: Path):
    d = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            d.update(chunk)
    return d.hexdigest()


def current_code_lookup(master_zip: Path):
    records = defaultdict(list)
    with zipfile.ZipFile(master_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("Master Coordinate ZIP CRC failed")
        if "T_MASTER_CORD.csv" not in archive.namelist():
            raise ValueError("Expected T_MASTER_CORD.csv")
        with archive.open("T_MASTER_CORD.csv") as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig"))
            required = {"AIRPORT", "AIRPORT_ID", "CITY_MARKET_ID",
                        "AIRPORT_IS_LATEST"}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError("Master Coordinate identity columns missing")
            for row in reader:
                if str(row["AIRPORT_IS_LATEST"]).lower() not in ("1", "true"):
                    continue
                code, airport_id, citymarket = (
                    row["AIRPORT"], row["AIRPORT_ID"], row["CITY_MARKET_ID"])
                if code and airport_id and citymarket:
                    records[code].append((int(airport_id), int(citymarket)))
    return records


def compare_profiles(profiles: list[dict], lookup: dict):
    observed = set()
    results = []
    for p in sorted(profiles, key=lambda x: x["source_year"]):
        year = p["source_year"]
        if year in observed or not isinstance(year, int):
            raise ValueError("Source years must be unique integers")
        observed.add(year)
        if (p.get("missing_source_id_endpoints") != 0
                or not p.get("source_zip_sha256")
                or not p.get("source_airport_identity_pairs")
                or not p.get("observed_months")):
            raise ValueError("Required published source-ID profile incomplete")
        summary = {key: {"source_identity_pairs": 0, "endpoint_rows": 0,
                         "endpoint_segment_passenger_legs": 0,
                         "endpoint_departures": 0}
                   for key in ("matched", "different_market", "missing_code")}
        anomalies = []
        for row in p["source_airport_identity_pairs"]:
            code, aid, cmid = row["code"], int(row["airport_id"]), int(row["city_market_id"])
            if not code or aid <= 0 or cmid <= 0:
                raise ValueError("Invalid source-published identity")
            matches = lookup.get(code, ())
            legacy = max((m for _, m in matches), default=None)
            status = ("missing_code" if legacy is None else
                      "matched" if legacy == cmid else "different_market")
            stats = summary[status]
            stats["source_identity_pairs"] += 1
            for key, source_key in (
                ("endpoint_rows", "endpoint_rows"),
                ("endpoint_segment_passenger_legs",
                 "endpoint_segment_passenger_legs"),
                ("endpoint_departures", "endpoint_departures"),
            ):
                count = row[source_key]
                if not isinstance(count, int) or count < 0:
                    raise ValueError("Invalid observed endpoint totals")
                stats[key] += count
            if status != "matched":
                anomalies.append({
                    "airport_code": code,
                    "source_airport_id": aid,
                    "source_city_market_id": cmid,
                    "legacy_latest_code_max_city_market_id": legacy,
                    "source_id_found_in_latest_lookup": any(
                        ident == aid for ident, _ in matches),
                    "status": status,
                    "endpoint_rows": row["endpoint_rows"],
                    "endpoint_segment_passenger_legs":
                        row["endpoint_segment_passenger_legs"],
                    "endpoint_departures": row["endpoint_departures"],
                })
        results.append({
            "year": year,
            "source_observed_months": p["observed_months"],
            "official_source_zip_sha256": p["source_zip_sha256"],
            "scheduled_source_rows": p["scheduled_passenger_rows"],
            "status_counts": summary,
            "anomalies": sorted(anomalies, key=lambda x: (
                -x["endpoint_segment_passenger_legs"], x["airport_code"])),
        })
    return {
        "scope": "Official source-ID to archived latest-code MAX market simulation only",
        "source_profiles": results,
        "latest_lookup_code_count": len(lookup),
        "source_identifiers_imputed": False,
        "warehouse_facts_or_consumer_results_read": False,
        "published_verdict_or_replay_delta_measured": False,
        "caution": ("Endpoint passenger-segment legs may count both sides of the "
                    "same flight and are NOT unique travelers, ticket O&D, "
                    "production passenger losses, or model verdict changes."),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master-zip", type=Path, required=True)
    parser.add_argument("--source-profile", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sources = [args.master_zip, *args.source_profile]
    output = args.output.resolve()
    if output.exists() or any(output == s.resolve() for s in sources):
        parser.error("Output must be new and cannot overwrite evidence")
    profiles = [json.loads(p.read_text(encoding="utf-8"))
                for p in args.source_profile]
    result = compare_profiles(profiles, current_code_lookup(args.master_zip))
    result["lookup_sha256"] = file_sha256(args.master_zip)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    for year in result["source_profiles"]:
        status = year["status_counts"]
        print(year["year"], {
            s: status[s]["endpoint_rows"] for s in status
        })


if __name__ == "__main__":
    main()
