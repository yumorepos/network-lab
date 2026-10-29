"""T-100 source-ID research controls; all tests use tiny synthetic ZIPs."""
import csv
import io
import zipfile

import pytest

from scripts.research_t100_source_ids import profile


HEADERS = [
    "YEAR", "MONTH", "ORIGIN", "DEST",
    "ORIGIN_COUNTRY", "DEST_COUNTRY",
    "ORIGIN_AIRPORT_ID", "DEST_AIRPORT_ID",
    "ORIGIN_CITY_MARKET_ID", "DEST_CITY_MARKET_ID",
    "PASSENGERS", "DEPARTURES_PERFORMED", "CLASS",
]


def sample(year=2026, month=7, origin="PBI", dest="YYZ",
           origin_id=14301, dest_id=15500, origin_cm=33100, dest_cm=15500):
    return {
        "YEAR": year, "MONTH": month, "ORIGIN": origin, "DEST": dest,
        "ORIGIN_COUNTRY": "US", "DEST_COUNTRY": "CA",
        "ORIGIN_AIRPORT_ID": origin_id, "DEST_AIRPORT_ID": dest_id,
        "ORIGIN_CITY_MARKET_ID": origin_cm,
        "DEST_CITY_MARKET_ID": dest_cm,
        "PASSENGERS": 100, "DEPARTURES_PERFORMED": 1, "CLASS": "F",
    }


def archive(tmp_path, rows, header=HEADERS):
    zip_path = tmp_path / "source.zip"
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=header, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    with zipfile.ZipFile(zip_path, "w") as file:
        file.writestr("Documentation.csv", "documentation\n")
        file.writestr("T_T100_SEGMENT_ALL_CARRIER.csv", out.getvalue())
    return zip_path


def test_stable_id_persists_across_code_rename(tmp_path):
    rows = [sample(), sample(origin="DJT", month=8)]
    r = profile(archive(tmp_path, rows), 2026)
    assert r["scheduled_passenger_rows"] == 2
    assert r["distinct_airport_ids"] == 2
    assert r["airport_ids_with_multiple_codes_within_year"] == [
        {"airport_id": 14301, "codes": ["DJT", "PBI"]}
    ]
    assert r["warehouse_join_impact_measured"] is False


def test_reused_code_exposes_two_distinct_stable_ids(tmp_path):
    rows = [sample(origin="SAW", origin_id=1, origin_cm=22),
            sample(origin="SAW", origin_id=2, origin_cm=33)]
    r = profile(archive(tmp_path, rows), 2026)
    assert r["ambiguous_codes_within_year"] == [{
        "code": "SAW", "airport_ids": [1, 2],
        "endpoint_segment_passenger_legs": 200,
        "endpoint_departures": 2,
    }]


def test_avoids_imputing_absent_source_id(tmp_path):
    r = profile(archive(tmp_path, [sample(origin_id="")]), 2026)
    assert r["missing_source_id_endpoints"] == 1
    assert r["distinct_airport_ids"] == 1


def test_rejects_legacy_archive_without_source_id_fields(tmp_path):
    path = archive(tmp_path, [sample()], [x for x in HEADERS
                                           if not x.endswith("_AIRPORT_ID")])
    with pytest.raises(ValueError, match="Required source IDs"):
        profile(path, 2026)


def test_wrong_source_year_fails_closed(tmp_path):
    with pytest.raises(ValueError, match="Unexpected source year"):
        profile(archive(tmp_path, [sample(year=2025)]), 2026)


def test_rejects_negative_passenger_counts(tmp_path):
    row = sample()
    row["PASSENGERS"] = -1
    with pytest.raises(ValueError, match="Negative passenger"):
        profile(archive(tmp_path, [row]), 2026)


def test_stable_id_market_change_reported_not_inferred(tmp_path):
    r = profile(archive(tmp_path, [sample(),
                                  sample(origin_cm=33200, month=8)]), 2026)
    assert r["airport_ids_with_multiple_city_markets_within_year"] == [
        {"airport_id": 14301, "city_market_ids": [33100, 33200]}
    ]
    assert r["published_screen_or_replay_delta_measured"] is False
