"""Research-only official T-100 stable AirportID / CityMarketID audit.

No warehouse, model, prior raw ZIP, or published output is modified. Downloads
a fresh isolated BTS table into a temporary directory only on --download-year.
Source IDs are never inferred from airport codes. This is NOT an archive replay.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile

REQUIRED = {
    "YEAR", "MONTH", "ORIGIN", "DEST", "ORIGIN_COUNTRY", "DEST_COUNTRY",
    "ORIGIN_AIRPORT_ID", "DEST_AIRPORT_ID",
    "ORIGIN_CITY_MARKET_ID", "DEST_CITY_MARKET_ID",
    "PASSENGERS", "DEPARTURES_PERFORMED", "CLASS",
}


def input_csv(archive: zipfile.ZipFile):
    candidates = [x for x in archive.namelist()
                  if x.lower().endswith(".csv") and "documentation" not in x.lower()]
    if len(candidates) != 1:
        raise ValueError(f"Expected exactly one T-100 source CSV, got {candidates}")
    return candidates[0]


def _integer(value):
    if value is None or not str(value).strip():
        return None
    return int(float(value))


def profile(zip_path: Path, year: int) -> dict:
    """Stream official source; do not store, infer, or overwrite any identifier."""
    if year < 1990 or year > 2100:
        raise ValueError("Invalid year")
    endpoint_rows = 0
    scheduled_rows = 0
    source_rows = 0
    missing_source_ids = 0
    code_ids = defaultdict(set)
    id_codes = defaultdict(set)
    id_markets = defaultdict(set)
    code_traffic = defaultdict(lambda: [0, 0])
    airport_country = defaultdict(set)
    periods = set()
    digest = hashlib.sha256()
    with zip_path.open("rb") as inp:
        for chunk in iter(lambda: inp.read(1 << 20), b""):
            digest.update(chunk)
    with zipfile.ZipFile(zip_path) as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC failed")
        name = input_csv(archive)
        import io
        with archive.open(name) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig"))
            missing = REQUIRED - set(reader.fieldnames or ())
            if missing:
                raise ValueError(f"Required source IDs or metrics missing: {sorted(missing)}")
            for row in reader:
                source_rows += 1
                if _integer(row["YEAR"]) != year:
                    raise ValueError(f"Unexpected source year at CSV row {source_rows}")
                month = _integer(row["MONTH"])
                if month is None or not 1 <= month <= 12:
                    raise ValueError(f"Invalid month at source row {source_rows}")
                periods.add(month)
                departures = _integer(row["DEPARTURES_PERFORMED"])
                if departures is None or departures <= 0 or row["CLASS"] not in ("F", "L"):
                    continue
                scheduled_rows += 1
                pax = _integer(row["PASSENGERS"]) or 0
                if pax < 0:
                    raise ValueError("Negative passenger count")
                for side in ("ORIGIN", "DEST"):
                    endpoint_rows += 1
                    code = (row[side] or "").strip()
                    airport_id = _integer(row[f"{side}_AIRPORT_ID"])
                    citymarket = _integer(row[f"{side}_CITY_MARKET_ID"])
                    country = (row[f"{side}_COUNTRY"] or "").strip()
                    if not code or airport_id is None or citymarket is None:
                        missing_source_ids += 1
                        continue
                    code_ids[code].add(airport_id)
                    id_codes[airport_id].add(code)
                    id_markets[airport_id].add(citymarket)
                    airport_country[airport_id].add(country)
                    code_traffic[code][0] += pax
                    code_traffic[code][1] += departures
    ambiguous = []
    for code, ids in sorted(code_ids.items()):
        if len(ids) > 1:
            ambiguous.append({
                "code": code, "airport_ids": sorted(ids),
                "endpoint_segment_passenger_legs": code_traffic[code][0],
                "endpoint_departures": code_traffic[code][1],
            })
    reused_ids = [{
        "airport_id": airport_id, "codes": sorted(codes)
    } for airport_id, codes in sorted(id_codes.items()) if len(codes) > 1]
    multi_market_ids = [{
        "airport_id": airport_id, "city_market_ids": sorted(markets)
    } for airport_id, markets in sorted(id_markets.items()) if len(markets) > 1]
    conflicting_country_ids = [{
        "airport_id": airport_id, "countries": sorted(countries)
    } for airport_id, countries in sorted(airport_country.items())
        if len(countries) > 1]
    return {
        "audit_mode": "official T-100 source-identity only; no reference lookup or production model",
        "source": "BTS TranStats table 293, as downloaded at execution time",
        "source_year": year,
        "source_zip_sha256": digest.hexdigest(),
        "source_rows": source_rows,
        "scheduled_passenger_rows": scheduled_rows,
        "observed_months": sorted(periods),
        "scheduled_origin_dest_endpoints": endpoint_rows,
        "missing_source_id_endpoints": missing_source_ids,
        "distinct_airport_ids": len(id_codes),
        "ambiguous_codes_within_year": ambiguous,
        "airport_ids_with_multiple_codes_within_year": reused_ids,
        "airport_ids_with_multiple_city_markets_within_year": multi_market_ids,
        "airport_ids_with_multiple_countries_within_year": conflicting_country_ids,
        "warehouse_join_impact_measured": False,
        "published_screen_or_replay_delta_measured": False,
        "contains_ticket_origin_destination_data": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--zip", type=Path)
    src.add_argument("--download-year", type=int)
    parser.add_argument("--year", type=int, help="Required when --zip is used")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if output.exists():
        parser.error(f"Refusing to overwrite prior evidence: {output}")
    if args.zip:
        if args.year is None:
            parser.error("--year required with --zip")
        report = profile(args.zip, args.year)
    else:
        from ingest.transtats import (ALL_FIELDS, T100_SEGMENT_ALL,
                                      download_table_year)
        # Separate ephemeral source download; do not use or overwrite ingest cache.
        with tempfile.TemporaryDirectory(prefix="t100-stable-id-audit-") as tmp:
            archive = Path(tmp) / f"source_{args.download_year}.zip"
            download_table_year(T100_SEGMENT_ALL, args.download_year, ALL_FIELDS,
                                archive)
            report = profile(archive, args.download_year)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                      encoding="utf-8")
    print(f"Research-only AirportID audit saved: {output} "
          f"({report['scheduled_passenger_rows']} scheduled records)")
    if report["missing_source_id_endpoints"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
