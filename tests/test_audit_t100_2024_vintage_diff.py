"""Synthetic row-multiset controls: prevent net count masking changed records."""
import csv
import io
import zipfile

import pytest

from scripts.audit_t100_2024_vintage_diff import FIELDS, compare


def record(pax="100.00", origin="SEA", dest="TPE", year="2024"):
    r = dict.fromkeys(FIELDS, "0")
    r.update({
        "YEAR": year, "MONTH": "10", "QUARTER": "4",
        "UNIQUE_CARRIER": "HU", "ORIGIN": origin, "DEST": dest,
        "ORIGIN_COUNTRY": "US", "DEST_COUNTRY": "TW", "CLASS": "F",
        "PASSENGERS": pax, "SEATS": "300.00",
        "DEPARTURES_PERFORMED": "1.00",
    })
    return r


def makezip(tmp_path, filename, rows, fields=FIELDS):
    p = tmp_path / filename
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("Documentation.csv", "not data\n")
        z.writestr("T_T100_SEGMENT_ALL_CARRIER.csv", out.getvalue())
    return p


def test_same_row_counts_can_hide_revisions_and_study_hub_exposure(tmp_path):
    a = makezip(tmp_path, "old.zip", [record("100.00"), record("100.00")])
    b = makezip(tmp_path, "new.zip", [record("100.00"), record("101.00")])
    result = compare(a, b)
    assert result["archived_rows"] == result["current_rows"] == 2
    assert result["archived_only_occurrences"] == 1
    assert result["current_only_occurrences"] == 1
    assert result["different_source_vintages_confirmed"] is True
    assert result["changed_rows_touching_study_hubs"]["current_only:SEA"]["rows"] == 1
    assert result["production_impact_or_verdict_change_verified"] is False


def test_identical_multiset_with_different_row_order_passes(tmp_path):
    a = makezip(tmp_path, "old.zip", [record("1.00"), record("2.00")])
    b = makezip(tmp_path, "new.zip", [record("2.00"), record("1.00")])
    r = compare(a, b)
    assert r["archived_only_occurrences"] == 0
    assert r["current_only_occurrences"] == 0
    assert r["different_source_vintages_confirmed"] is False


def test_wrong_field_set_fails_closed(tmp_path):
    a = makezip(tmp_path, "old.zip", [record()])
    b = makezip(tmp_path, "new.zip", [record()],
                [x for x in FIELDS if x != "AIRCRAFT_TYPE"])
    with pytest.raises(ValueError, match="14"):
        compare(a, b)


def test_wrong_year_fails_closed(tmp_path):
    a = makezip(tmp_path, "old.zip", [record()])
    b = makezip(tmp_path, "new.zip", [record(year="2025")])
    with pytest.raises(ValueError, match="year"):
        compare(a, b)
