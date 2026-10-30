"""Synthetic negative controls for nonconsecutive source-vintage AirportID reuse."""
import copy

import pytest

from scripts.research_t100_multivintage_identity import summarize


def sample(year, code, airport_id, market, country="US", months=None,
           leg_pax=50):
    return {
        "source_year": year,
        "source_zip_sha256": "a" * 64,
        "observed_months": months if months is not None else list(range(1, 13)),
        "source_rows": 1, "scheduled_passenger_rows": 1,
        "scheduled_origin_dest_endpoints": 1,
        "missing_source_id_endpoints": 0,
        "source_airport_identity_pairs": [{
            "code": code, "airport_id": airport_id,
            "city_market_id": market, "country": country,
            "endpoint_rows": 1,
            "endpoint_segment_passenger_legs": leg_pax,
            "endpoint_departures": 1,
        }],
    }


def test_historic_code_reuse_without_consecutive_overlap_detected():
    a = sample(1990, "AAA", 111, 22)
    b = sample(2018, "AAA", 222, 33)
    result = summarize([b, a])
    assert result["sampled_years"] == [1990, 2018]
    assert result["code_reused_by_distinct_stable_ids"] == [{
        "code": "AAA",
        "airport_ids_all_sampled_years": [111, 222],
        "years": [
            {"year": 1990, "airport_ids": [111],
             "endpoint_segment_passenger_legs": 50, "endpoint_departures": 1},
            {"year": 2018, "airport_ids": [222],
             "endpoint_segment_passenger_legs": 50, "endpoint_departures": 1},
        ],
    }]
    assert result["original_warehouse_compared"] is False


def test_same_airport_id_code_rename_is_separate_from_reuse():
    r = summarize([sample(2022, "PBI", 14301, 33100),
                   sample(2026, "DJT", 14301, 33100,
                          months=list(range(1, 8)))])
    assert not r["code_reused_by_distinct_stable_ids"]
    assert len(r["same_stable_airport_id_different_codes"]) == 1


def test_stable_id_market_drift_reported_not_hidden():
    r = summarize([sample(2018, "XYZ", 9, 10),
                   sample(2024, "XYZ", 9, 20)])
    assert len(r["same_stable_airport_id_different_city_markets"]) == 1
    assert r["same_stable_airport_id_different_countries"] == []


def test_missing_stable_ids_fail_closed():
    a = sample(2018, "XYZ", 9, 10)
    a["missing_source_id_endpoints"] = 1
    with pytest.raises(ValueError, match="Missing published"):
        summarize([a, sample(2024, "XYZ", 9, 10)])


def test_duplicate_year_fails_closed():
    a = sample(2018, "XYZ", 9, 10)
    with pytest.raises(ValueError, match="Unique integer"):
        summarize([a, copy.deepcopy(a)])


def test_incomplete_month_vintage_fails_closed():
    a = sample(2018, "XYZ", 9, 10, months=[1, 2])
    b = sample(2024, "XYZ", 9, 10)
    with pytest.raises(ValueError, match="source-month"):
        summarize([a, b], expected_months={
            2018: list(range(1, 13)), 2024: list(range(1, 13))})


def test_invalid_missing_or_noninteger_traffic_fails_closed():
    a = sample(2018, "XYZ", 9, 10)
    a["source_airport_identity_pairs"][0]["endpoint_departures"] = -2
    with pytest.raises(ValueError, match="traffic"):
        summarize([a, sample(2024, "XYZ", 9, 10)])


def test_absent_source_pair_inventory_fails_closed():
    a = sample(2018, "XYZ", 9, 10)
    del a["source_airport_identity_pairs"]
    with pytest.raises(ValueError, match="provenance"):
        summarize([a, sample(2024, "XYZ", 9, 10)])


def test_historical_country_missing_is_reported_without_invented_country():
    a = sample(1990, "PRG", 14239, 34239, country="", leg_pax=22260)
    b = sample(2018, "PRG", 14239, 34239, country="CZ", leg_pax=22300)
    result = summarize([a, b])
    assert result["source_pairs_with_missing_published_country"] == [{
        "year": 1990, "code": "PRG", "airport_id": 14239,
        "city_market_id": 34239, "endpoint_rows": 1,
        "endpoint_segment_passenger_legs": 22260,
    }]
    assert result["same_stable_airport_id_different_countries"] == []
    assert result["missing_source_country_not_imputed"] is True
