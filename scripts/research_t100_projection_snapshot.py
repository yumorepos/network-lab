"""Research-only exact-field BTS T-100 2024 source comparison.

Uses the live ingest/bts_t100.py 14-field projection verbatim, downloads to a
separate, ephemeral CI workspace and writes a manifest. Never updates source
cache, Parquet, DuckDB, model, replay or published outputs. An official public
ZIP is a temporary CI evidence artifact and is not committed to Git.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile


def ingest_fields(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "FIELDS" for t in node.targets
        ):
            fields = ast.literal_eval(node.value)
            if (not isinstance(fields, list) or len(fields) != 14
                or len(fields) != len(set(fields))
                or any(not isinstance(f, str) for f in fields)
                or "YEAR" not in fields or "MONTH" not in fields):
                raise ValueError("Unexpected official 14-field ingest projection")
            return fields
    raise ValueError("14-field ingest projection not found")


def summarize(path: Path, year: int, fields: list[str]) -> dict:
    checksum = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            checksum.update(chunk)
    months = Counter()
    eligible_months = Counter()
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError("Source ZIP CRC failed")
        members = [x for x in archive.namelist()
                   if x.lower().endswith(".csv") and
                   "documentation" not in x.lower()]
        if len(members) != 1:
            raise ValueError("Expected one source CSV")
        with archive.open(members[0]) as raw:
            rows = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig"))
            if set(rows.fieldnames or []) != set(fields):
                raise ValueError("Source export does not match exact 14 ingest fields")
            for row in rows:
                if int(row["YEAR"]) != year:
                    raise ValueError("Mixed source years")
                month = int(row["MONTH"])
                if not 1 <= month <= 12:
                    raise ValueError("Invalid monthly partition")
                months[month] += 1
                if (row["CLASS"] in ("F", "L")
                    and float(row["DEPARTURES_PERFORMED"] or 0) > 0):
                    eligible_months[month] += 1
    return {
        "source": "BTS TranStats Table 293, current official 14-field projection",
        "source_year": year,
        "fields": fields,
        "zip_sha256": checksum.hexdigest(),
        "source_rows": sum(months.values()),
        "scheduled_fl_positive_departure_rows": sum(eligible_months.values()),
        "raw_monthly_rows": dict(sorted(months.items())),
        "scheduled_monthly_rows": dict(sorted(eligible_months.items())),
        "source_vintage": "download at CI execution date; inspect run metadata",
        "archived_source_updated": False,
        "warehouse_or_verdict_changed": False,
        "full_archive_row_multiset_compared": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--year", type=int, choices=[2024], default=2024)
    p.add_argument("--output-zip", type=Path, required=True)
    p.add_argument("--output-json", type=Path, required=True)
    args = p.parse_args()
    zip_path = args.output_zip.resolve()
    json_path = args.output_json.resolve()
    if zip_path == json_path or zip_path.exists() or json_path.exists():
        p.error("Source evidence outputs must be distinct, new paths")
    fields = ingest_fields(Path(__file__).resolve().parents[1]
                           / "ingest" / "bts_t100.py")
    from ingest.transtats import download_table_year, T100_SEGMENT_ALL
    # No shared DATA_RAW or DATA_PARQUET path: CI scratch workspace only.
    download_table_year(T100_SEGMENT_ALL, args.year, fields, zip_path)
    manifest = summarize(zip_path, args.year, fields)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    print(json.dumps({"source_rows": manifest["source_rows"],
                      "scheduled_rows": manifest["scheduled_fl_positive_departure_rows"],
                      "zip_sha256": manifest["zip_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
