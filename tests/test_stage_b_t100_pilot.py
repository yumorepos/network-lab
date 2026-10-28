"""Offline tests and negative controls for the isolated T-100 freshness pilot."""
from __future__ import annotations

import csv
import zipfile
from pathlib import Path

import pytest

from ingest.bts_t100 import FIELDS
from scripts.stage_b_t100_pilot import (
    compare, read_month_zip, run, stats,
)


def record(year=2026, month=7, pax=80, deps=2, origin="YYC", dest="SEA"):
    return dict(zip(FIELDS, [
        str(year), "3", str(month), "WS", origin, "CA" if origin == "YYC" else "US",
        dest, "CA" if dest == "YYC" else "US", "348", str(pax),
        str(deps), "420", "614", "F",
    ]))


def zipped(tmp_path: Path, name: str, records, fields=FIELDS):
    path = tmp_path / name
    body = tmp_path / (name + ".csv")
    with body.open("w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    with zipfile.ZipFile(path, "w") as archive:
        archive.write(body, "records.csv")
    return path


def test_july_filter_and_directionality(tmp_path):
    path = zipped(tmp_path, "test.zip", [
        record(), record(origin="SEA", dest="YYC"),
        record(month=6), record(deps=0),
    ])
    df = read_month_zip(path, 2026, 7)
    assert len(df) == 2
    report = stats(df)
    assert report["canada_to_us_rows"] == 1
    assert report["us_to_canada_rows"] == 1
    assert report["no_us_endpoint_rows"] == 0


def test_negative_control_missing_required_column(tmp_path):
    fields = [field for field in FIELDS if field != "PASSENGERS"]
    path = zipped(tmp_path, "missing.zip", [record()], fields=fields)
    with pytest.raises(ValueError, match="Missing official T-100 fields"):
        read_month_zip(path, 2026, 7)


def test_negative_control_negative_passengers(tmp_path):
    path = zipped(tmp_path, "negative.zip", [record(pax=-9)])
    with pytest.raises(ValueError, match="negative PASSENGERS"):
        read_month_zip(path, 2026, 7)


def test_directional_comparison_and_isolation(tmp_path):
    zip26 = zipped(tmp_path, "current.zip", [
        record(), record(origin="SEA", dest="YYC", pax=64),
    ])
    zip25 = zipped(tmp_path, "prior.zip", [
        record(year=2025, pax=70),
        record(year=2025, origin="SEA", dest="YYC", pax=55),
    ])

    def fake_downloader(table, year, fields, dest):
        assert table == 293 and fields == FIELDS
        return zip26 if year == 2026 else zip25

    result_dir = tmp_path / "isolated"
    summary = run(result_dir, downloader=fake_downloader)
    assert summary["target"]["passengers"] == 144
    assert summary["control"]["passengers"] == 125
    assert summary["metro_crosswalk_verified"] is False
    assert (result_dir / "stage_b_t100.duckdb").is_file()
    assert (result_dir / "summary.json").is_file()
    assert (result_dir / "july_yoy_operator_segment.csv").is_file()
    current = read_month_zip(zip26, 2026, 7)
    previous = read_month_zip(zip25, 2025, 7)
    diff = compare(current, previous)
    assert len(diff) == 2  # opposite directions are NOT collapsed
    assert set(diff["ORIGIN"]) == {"YYC", "SEA"}


def test_negative_control_no_us_endpoint_is_rejected(tmp_path):
    # All-carrier T-100 scope does not include Canadian domestic flying.
    path26 = zipped(tmp_path, "foreign.zip",
                    [record(origin="YYC", dest="YYC")])
    path25 = zipped(tmp_path, "prior.zip", [record(year=2025)])

    def fake_downloader(table, year, fields, dest):
        return path26 if year == 2026 else path25

    with pytest.raises(ValueError, match="without a US endpoint"):
        run(tmp_path / "isolated", downloader=fake_downloader)


def test_duplicate_grain_is_reported_not_silently_deduplicated(tmp_path):
    path = zipped(tmp_path, "dupe.zip", [record(), record()])
    frame = read_month_zip(path, 2026, 7)
    report = stats(frame)
    assert report["rows"] == 2
    assert report["exact_duplicate_rows"] == 1
    assert report["collisions_at_selected_key"] == 1
