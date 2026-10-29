"""Read-only complete-row comparison of two BTS T-100 14-field ZIP vintages.

Never overwrites either ZIP, and does not mutate the warehouse or model. A
BLAKE2b-192 digest represents all 14 raw field strings at a row-multiset grain;
archive SHA-256 and examples remain available for independent verification.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile


FIELDS = (
    "YEAR", "QUARTER", "MONTH", "UNIQUE_CARRIER", "ORIGIN", "ORIGIN_COUNTRY",
    "DEST", "DEST_COUNTRY", "SEATS", "PASSENGERS", "DEPARTURES_PERFORMED",
    "DISTANCE", "AIRCRAFT_TYPE", "CLASS",
)


def rows(path):
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None:
            raise ValueError("Source ZIP CRC failed")
        files = [x for x in z.namelist() if x.lower().endswith(".csv")
                 and "documentation" not in x.lower()]
        if len(files) != 1:
            raise ValueError("Missing or ambiguous source CSV")
        with z.open(files[0]) as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
            if set(reader.fieldnames or []) != set(FIELDS):
                raise ValueError("Expected exactly the original 14 source fields")
            yield from reader


def digest(row):
    return hashlib.blake2b(json.dumps(
        [row[k] for k in FIELDS], ensure_ascii=False,
        separators=(",", ":")).encode(), digest_size=24).digest()


def profile(path):
    counts = Counter()
    metadata = {}
    partitions = Counter()
    scheduled = Counter()
    for row in rows(path):
        if row["YEAR"] != "2024":
            raise ValueError("Unexpected year")
        month = int(row["MONTH"])
        if not 1 <= month <= 12:
            raise ValueError("Invalid month")
        signature = digest(row)
        counts[signature] += 1
        partitions[month] += 1
        if row["CLASS"] in ("F", "L") and float(row["DEPARTURES_PERFORMED"] or 0) > 0:
            scheduled[month] += 1
        metadata[signature] = (
            month, row["UNIQUE_CARRIER"], row["ORIGIN"], row["DEST"],
            row["ORIGIN_COUNTRY"], row["DEST_COUNTRY"], row["CLASS"],
            float(row["PASSENGERS"] or 0),
            float(row["SEATS"] or 0),
            float(row["DEPARTURES_PERFORMED"] or 0),
        )
    return counts, metadata, partitions, scheduled


def sha(path):
    d = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            d.update(block)
    return d.hexdigest()


def compare(archived, current):
    left, left_meta, left_month, left_fl = profile(archived)
    right, right_meta, right_month, right_fl = profile(current)
    diffs = [left - right, right - left]
    classes = Counter()
    sector = defaultdict(Counter)
    carrier = defaultdict(Counter)
    hubs = defaultdict(Counter)
    total_diff = Counter()
    for side, diff, meta in zip(("archived_only", "current_only"),
                                diffs, (left_meta, right_meta)):
        for h, count in diff.items():
            month, code, origin, dest, oc, dc, kind, pax, seats, deps = meta[h]
            total_diff[side] += count
            classes[(side, month, kind)] += count
            tag = ("CA-US" if oc == "CA" and dc == "US" else
                   "US-CA" if oc == "US" and dc == "CA" else
                   "US-US" if oc == "US" and dc == "US" else "Other")
            for group, key in ((sector, tag), (carrier, code)):
                g = group[(side, key)]
                g["rows"] += count
                g["passenger_legs"] += count * pax
                g["departures"] += count * deps
                g["seats"] += count * seats
            for hub in ("YYC", "YYZ", "SEA"):
                if hub in (origin, dest):
                    g = hubs[(side, hub)]
                    g["rows"] += count
                    g["passenger_legs"] += count * pax
                    g["departures"] += count * deps
    return {
        "scope": "Identical 14-column, full-row multiset comparison, no model rerun",
        "archived_sha256": sha(archived),
        "current_sha256": sha(current),
        "archived_rows": sum(left.values()),
        "current_rows": sum(right.values()),
        "archived_scheduled_rows": sum(left_fl.values()),
        "current_scheduled_rows": sum(right_fl.values()),
        "archived_only_occurrences": total_diff["archived_only"],
        "current_only_occurrences": total_diff["current_only"],
        "archived_only_distinct_row_signatures": len(diffs[0]),
        "current_only_distinct_row_signatures": len(diffs[1]),
        "monthly_raw_deltas": {
            str(m): right_month[m] - left_month[m] for m in range(1, 13)
        },
        "monthly_scheduled_deltas": {
            str(m): right_fl[m] - left_fl[m] for m in range(1, 13)
        },
        "changed_rows_by_month_class": {
            f"{side}:{month}:{kind}": n
            for (side, month, kind), n in sorted(classes.items())
        },
        "changed_rows_by_sector": {
            f"{side}:{tag}": dict(value)
            for (side, tag), value in sorted(sector.items())
        },
        "changed_rows_by_carrier": {
            f"{side}:{code}": dict(value)
            for (side, code), value in sorted(carrier.items())
        },
        "changed_rows_touching_study_hubs": {
            f"{side}:{hub}": dict(value)
            for (side, hub), value in sorted(hubs.items())
        },
        "different_source_vintages_confirmed": bool(diffs[0] or diffs[1]),
        "production_impact_or_verdict_change_verified": False,
        "note": ("Changed rows are BTS operated segments, not ticket O&D. "
                 "No source is overwritten and no historical replay is rerun."),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archived", type=Path, required=True)
    p.add_argument("--current", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    dest = args.output.resolve()
    if dest.exists() or dest in (args.archived.resolve(), args.current.resolve()):
        p.error("Refusing to overwrite a source or prior evidence")
    result = compare(args.archived, args.current)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print("Archived-only occurrences:", result["archived_only_occurrences"])
    print("Current-only occurrences:", result["current_only_occurrences"])
    print("Verified model changes:", result["production_impact_or_verdict_change_verified"])


if __name__ == "__main__":
    main()
