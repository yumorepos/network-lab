"""Read-only archived BTS airport-code audit; not a replacement for source AirportID.

Usage: python -m scripts.audit_archived_airport_identity --source-dir DIR --output-dir DIR
Needs master_coord.zip and t100_YYYY.zip files from the same archived data set.
Never mutates a source, warehouse, replay, model, or tracked output.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path


def read_zip_rows(path: Path, name: str):
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError(f"CRC failure: {path}")
        if name not in archive.namelist():
            raise ValueError(f"Missing {name} in {path}")
        with archive.open(name) as data:
            yield from csv.DictReader(io.TextIOWrapper(data, encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


def bts_date(value: str | None) -> dt.date | None:
    if not (value or "").strip():
        return None
    for fmt in ("%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognized BTS date: {value!r}")


def resolve_candidates(rows: list[dict], country: str, year: int, month: int):
    """Conservative code/country/date *simulation*, never imputed stable IDs."""
    beginning = dt.date(year, month, 1)
    end = dt.date(year + (month == 12), month % 12 + 1, 1) - dt.timedelta(days=1)
    valid = [r for r in rows if r["country"] == country
             and (r["start"] is None or r["start"] <= end)
             and (r["end"] is None or r["end"] >= beginning)]
    distinct = {(r["airport_id"], r["city_market_id"]): r for r in valid}
    if len(distinct) == 1:
        return next(iter(distinct.values())), "unique_country_date_candidate"
    if not rows:
        return None, "unknown_code"
    return None, "no_valid_candidate" if not distinct else "ambiguous_candidates"


def audit(master: Path, archives: list[Path]) -> dict:
    history: dict[str, list[dict]] = defaultdict(list)
    latest: dict[str, list[dict]] = defaultdict(list)
    for row in read_zip_rows(master, "T_MASTER_CORD.csv"):
        code = (row.get("AIRPORT") or "").strip()
        airport_id, cm = row.get("AIRPORT_ID"), row.get("CITY_MARKET_ID")
        if not code or not airport_id or not cm:
            continue
        item = {"airport_id": int(airport_id), "city_market_id": int(cm),
                "country": (row.get("AIRPORT_COUNTRY_CODE_ISO") or "").strip(),
                "start": bts_date(row.get("AIRPORT_START_DATE")),
                "end": bts_date(row.get("AIRPORT_THRU_DATE"))}
        history[code].append(item)
        if (row.get("AIRPORT_IS_LATEST") or "").lower() in ("1", "true"):
            latest[code].append(item)
    ambiguous = {code for code, rows in latest.items()
                 if len({r["city_market_id"] for r in rows}) > 1}
    report = {"scope": "Archived source-side code/country/month simulation, NOT BTS stable AirportID resolution or production outcome impact",
              "master_sha256": sha256(master), "ambiguous_latest_codes": len(ambiguous),
              "source_years": {}, "examples": [],
              "stable_airport_id_verified": False,
              "warehouse_consumer_impact_measured": False,
              "model_or_replay_rerun": False}
    for archive in sorted(archives):
        year = int(archive.stem.rsplit("_", 1)[1])
        count, source_count, mismatches, legs = 0, 0, 0, 0
        months: set[int] = set()
        flags = Counter()
        seen_bad_rows = set()
        for index, row in enumerate(read_zip_rows(archive, "T_T100_SEGMENT_ALL_CARRIER.csv")):
            source_count += 1
            if row.get("CLASS") not in ("F", "L") or float(row.get("DEPARTURES_PERFORMED") or 0) <= 0:
                continue
            count += 1
            month = int(row["MONTH"])
            months.add(month)
            for side in ("ORIGIN", "DEST"):
                code = (row.get(side) or "").strip()
                country = (row.get(side + "_COUNTRY") or "").strip()
                candidate, reason = resolve_candidates(history.get(code, []), country, year, month)
                if candidate is None:
                    flags[reason] += 1
                    continue
                legacy = max((r["city_market_id"] for r in latest.get(code, [])), default=None)
                if legacy != candidate["city_market_id"]:
                    mismatches += 1
                    if index not in seen_bad_rows:
                        legs += int(float(row.get("PASSENGERS") or 0))
                        seen_bad_rows.add(index)
                    if len(report["examples"]) < 30:
                        report["examples"].append({"year": year, "month": month,
                            "code": code, "side": side, "country": country,
                            "legacy_market": legacy,
                            "country_date_candidate_market": candidate["city_market_id"],
                            "source_stable_airport_id": None})
        report["source_years"][str(year)] = {"source_file": archive.name,
            "sha256": sha256(archive), "source_rows": source_count,
            "scheduled_passenger_rows": count, "observed_months": sorted(months),
            "candidate_different_endpoint_mappings": mismatches,
            "candidate_different_rows": len(seen_bad_rows),
            "candidate_different_segment_legs": legs,
            "unresolved_endpoint_reasons": dict(flags)}
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    source, output = args.source_dir.resolve(), args.output_dir.resolve()
    if output == source or source in output.parents:
        parser.error("output directory must be outside the source tree")
    master = source / "master_coord.zip"
    files = sorted(source.glob("t100_20??.zip"))
    if not master.is_file() or not files:
        parser.error("master_coord.zip and at least one t100_YYYY.zip required")
    result = audit(master, files)  # Read and verify before creating output directory.
    output.mkdir(parents=True, exist_ok=True)
    dest = output / "archived_airport_identity.json"
    if dest.exists():
        parser.error(f"refusing to overwrite: {dest}")
    dest.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {dest} (simulation only; published verdicts not retested)")


if __name__ == "__main__":
    main()
