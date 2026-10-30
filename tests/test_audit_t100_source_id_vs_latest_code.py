"""Synthetic guards for official BTS AirportID versus latest-code market joins."""
from scripts.audit_t100_source_id_vs_latest_code import compare_profiles


def profile(code, airport_id, citymarket, *, year=2024, pax=20):
    return {
        "source_year": year, "source_zip_sha256": "a" * 64,
        "observed_months": [1], "scheduled_passenger_rows": 1,
        "missing_source_id_endpoints": 0,
        "source_airport_identity_pairs": [{
            "code": code, "airport_id": airport_id,
            "city_market_id": citymarket, "country": "US",
            "endpoint_rows": 1,
            "endpoint_segment_passenger_legs": pax,
            "endpoint_departures": 1,
        }],
    }


def test_reused_code_wrong_max_citymarket_is_detected():
    lookup = {"SAW": [(101, 33459), (202, 32395)]}
    r = compare_profiles([profile("SAW", 202, 32395, pax=9)], lookup)
    item = r["source_profiles"][0]
    assert item["status_counts"]["different_market"]["endpoint_rows"] == 1
    assert item["anomalies"] == [{
        "airport_code": "SAW", "source_airport_id": 202,
        "source_city_market_id": 32395,
        "legacy_latest_code_max_city_market_id": 33459,
        "source_id_found_in_latest_lookup": True,
        "status": "different_market", "endpoint_rows": 1,
        "endpoint_segment_passenger_legs": 9, "endpoint_departures": 1,
    }]
    assert r["published_verdict_or_replay_delta_measured"] is False


def test_current_code_lookup_missing_is_distinct_from_wrong_market():
    r = compare_profiles([profile("W95", 303, 32168, pax=6)], {})
    counts = r["source_profiles"][0]["status_counts"]
    assert counts["missing_code"]["endpoint_segment_passenger_legs"] == 6
    assert counts["different_market"]["endpoint_rows"] == 0


def test_matching_official_market_is_not_falsely_flagged():
    r = compare_profiles([profile("SEA", 411, 30559)], {
        "SEA": [(411, 30559), (420, 20000)]
    })
    assert r["source_profiles"][0]["anomalies"] == []
    assert r["source_profiles"][0]["status_counts"]["matched"]["endpoint_rows"] == 1


def test_missing_source_id_is_not_imputed():
    import pytest
    p = profile("SEA", 411, 30559)
    p["missing_source_id_endpoints"] = 1
    with pytest.raises(ValueError, match="incomplete"):
        compare_profiles([p], {"SEA": [(411, 30559)]})


def test_duplicate_year_fails_closed():
    import pytest
    p = profile("SEA", 411, 30559)
    with pytest.raises(ValueError, match="unique"):
        compare_profiles([p, p], {"SEA": [(411, 30559)]})


def test_empty_or_invalid_traffic_fails_closed():
    import pytest
    p = profile("SEA", 411, 30559)
    p["source_airport_identity_pairs"][0]["endpoint_rows"] = -1
    with pytest.raises(ValueError, match="endpoint"):
        compare_profiles([p], {"SEA": [(411, 30559)]})
