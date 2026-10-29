"""Exact-field projection research must reject wrong source data or filters."""
from __future__ import annotations
import csv
import io
import zipfile

import pytest

from scripts.research_t100_projection_snapshot import ingest_fields, summarize


FIELDS = [
    "YEAR", "QUARTER", "MONTH", "UNIQUE_CARRIER", "ORIGIN",
    "ORIGIN_COUNTRY", "DEST", "DEST_COUNTRY", "SEATS", "PASSENGERS",
    "DEPARTURES_PERFORMED", "DISTANCE", "AIRCRAFT_TYPE", "CLASS",
]


def sample_archive(tmp_path, rows, fields=FIELDS):
    p = tmp_path / "source.zip"
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("T_T100_SEGMENT_ALL_CARRIER.csv", out.getvalue())
    return p


def record(year=2024, month=1, service="F", deps=1):
    return dict.fromkeys(FIELDS, "0") | {
        "YEAR": str(year), "MONTH": str(month), "CLASS": service,
        "DEPARTURES_PERFORMED": str(deps),
    }


def test_exact_projection_is_extracted_without_executing_ingest(tmp_path):
    p = tmp_path / "ingest.py"
    p.write_text("FIELDS = " + repr(FIELDS) +
                 "\nraise RuntimeError('should not execute')\n")
    assert ingest_fields(p) == FIELDS


def test_2024_monthly_counts_respect_scheduled_service_and_departures(tmp_path):
    p = sample_archive(tmp_path, [record(), record(service="G"),
                                  record(month=2, deps=0),
                                  record(month=3, service="L", deps=4)])
    result = summarize(p, 2024, FIELDS)
    assert result["source_rows"] == 4
    assert result["scheduled_fl_positive_departure_rows"] == 2
    assert result["scheduled_monthly_rows"] == {1: 1, 3: 1}


def test_missing_required_field_rejected(tmp_path):
    p = sample_archive(tmp_path, [record()],
                       [f for f in FIELDS if f != "DEPARTURES_PERFORMED"])
    with pytest.raises(ValueError, match="exact 14"):
        summarize(p, 2024, FIELDS)


def test_wrong_year_and_month_rejected(tmp_path):
    p = sample_archive(tmp_path, [record(year=2025)])
    with pytest.raises(ValueError, match="Mixed source years"):
        summarize(p, 2024, FIELDS)
    q = sample_archive(tmp_path, [record(month=13)])
    with pytest.raises(ValueError, match="Invalid monthly"):
        summarize(q, 2024, FIELDS)
