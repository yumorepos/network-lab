"""Read-only T-100 release-vintage coverage gate; does not refresh frozen data.

Example: python -m scripts.audit_t100_freshness --archive PATH/t100_2026.zip \
    --expected-year 2026 --published-through-month 7
The expected published month must come from an external BTS release record.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import zipfile
from collections import Counter
from pathlib import Path


def observed_months(path: Path, year: int) -> dict:
    months = Counter()
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError("Corrupted T-100 archive")
        name = "T_T100_SEGMENT_ALL_CARRIER.csv"
        if name not in archive.namelist():
            raise ValueError("T-100 data member missing")
        with archive.open(name) as data:
            reader = csv.DictReader(io.TextIOWrapper(data, encoding="utf-8-sig"))
            required = {"YEAR", "MONTH"}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError("T-100 year/month column missing")
            for row in reader:
                record_year, month = int(row["YEAR"]), int(row["MONTH"])
                if record_year != year or not 1 <= month <= 12:
                    raise ValueError(f"Unexpected T-100 year/month {record_year}/{month}")
                months[month] += 1
    return {"year": year, "monthly_rows": dict(sorted(months.items())),
            "observed_months": sorted(months), "source_rows": sum(months.values())}


def freshness_gate(inventory: dict, published_through_month: int) -> dict:
    if not 1 <= published_through_month <= 12:
        raise ValueError("published month must be 1..12")
    found = set(inventory["observed_months"])
    required = set(range(1, published_through_month + 1))
    missing = sorted(required - found)
    return {**inventory, "published_through_month": published_through_month,
            "missing_published_months": missing,
            "safe_to_treat_cached_year_as_complete": not missing,
            "recommendation": "STOP: cache refresh or source-vintage review required"
                if missing else "PASS: coverage only; record contents and release-vintage still unverified"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--expected-year", type=int, required=True)
    p.add_argument("--published-through-month", type=int, required=True)
    args = p.parse_args()
    result = freshness_gate(observed_months(args.archive, args.expected_year), args.published_through_month)
    print(json.dumps(result, indent=2))
    if result["missing_published_months"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
