"""Cross-vintage control: a code is not a stable airport identifier."""
import copy

import pytest

from scripts.compare_t100_source_ids import compare


def report(year, pairs):
    return {
        "source_year": year, "observed_months": [1, 2],
        "source_zip_sha256": "a" * 64 if year == 2024 else "b" * 64,
        "source_airport_identity_pairs": [
            {"code": code, "airport_id": aid, "city_market_id": market,
             "country": country, "endpoint_rows": 1,
             "endpoint_segment_passenger_legs": 100,
             "endpoint_departures": 1}
            for code, aid, market, country in pairs
        ],
    }


def test_reused_code_detected_even_with_individually_unambiguous_years():
    a = report(2024, [("AAA", 1, 10, "US")])
    b = report(2026, [("AAA", 2, 20, "US")])
    result = compare(a, b)
    assert result["same_code_different_published_airport_ids"] == [
        {"code": "AAA", "earlier_airport_ids": [1],
         "later_airport_ids": [2],
         "earlier_endpoint_traffic": {"legs": 100, "departures": 1, "rows": 1},
         "later_endpoint_traffic": {"legs": 100, "departures": 1, "rows": 1}}
    ]
    assert result["historical_warehouse_mapping_impact_established"] is False


def test_rename_same_id_is_not_code_reuse():
    a = report(2024, [("PBI", 100, 10, "US")])
    b = report(2026, [("DJT", 100, 10, "US")])
    result = compare(a, b)
    assert result["same_code_different_published_airport_ids"] == []
    assert result["same_airport_id_different_observed_codes"] == [
        {"stable_airport_id": 100,
         "earlier_codes": ["PBI"], "later_codes": ["DJT"]}
    ]


def test_same_airport_can_have_changed_city_market_without_imputation():
    a = report(2024, [("AAA", 100, 10, "US")])
    b = report(2026, [("AAA", 100, 20, "US")])
    r = compare(a, b)
    assert r["stable_airport_market_or_country_changed"][0]["later_markets"] == [20]
    assert r["same_code_different_published_airport_ids"] == []


def test_rejects_absent_pair_inventory():
    with pytest.raises(ValueError, match="pair inventory"):
        compare(report(2024, [("AAA", 1, 10, "US")]),
                {"source_year": 2026, "observed_months": [1],
                 "source_zip_sha256": "b" * 64})


def test_rejects_nonchronological_comparison():
    a = report(2026, [("AAA", 1, 10, "US")])
    with pytest.raises(ValueError, match="increasing"):
        compare(a, copy.deepcopy(a))
