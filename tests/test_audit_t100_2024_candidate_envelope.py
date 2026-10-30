"""Synthetic negative controls for 2024 source-vintage candidate envelope."""
import pandas as pd
import pytest

from scripts.audit_t100_2024_candidate_envelope import compare, prepare_geo


def fixture():
    hubs = pd.DataFrame([
        {"iata_code": "YYC", "latitude_deg": 51.1, "longitude_deg": -114.0},
        {"iata_code": "SEA", "latitude_deg": 47.5, "longitude_deg": -122.3},
        {"iata_code": "YYZ", "latitude_deg": 43.7, "longitude_deg": -79.6}])
    geo = pd.DataFrame([
        {"iata_code": "AAA", "selected_cbsa": "00001",
         "latitude_deg": 44.0, "longitude_deg": -117.0, "population": 500000},
        {"iata_code": "BBB", "selected_cbsa": "00001",
         "latitude_deg": 44.1, "longitude_deg": -117.1, "population": 500000}])
    return hubs, geo


def test_counterexample_anchor_airport_switch_detected():
    hubs, geo = fixture()
    result = compare(hubs, geo, {"AAA": 300000, "BBB": 200000},
                     {"AAA": 200000, "BBB": 310000})
    assert result["anchor_airport_changes"] == 1
    assert result["model_or_historical_replay_rerun"] is False


def test_counterexample_seat_floor_crossing_detected():
    hubs, geo = fixture()
    result = compare(hubs, geo.iloc[:1], {"AAA": 249999}, {"AAA": 250001})
    assert result["seat_floor_crossings"] == 1


def test_counterexample_satellite_flag_crossing_detected():
    hubs, geo = fixture()
    geo.loc[1, "selected_cbsa"] = "00002"
    result = compare(hubs, geo, {"AAA": 300000, "BBB": 1499999},
                     {"AAA": 300000, "BBB": 1500000})
    assert result["satellite_flag_changes"] == 1


def test_duplicate_ourairports_code_fails_closed():
    hubs, _ = fixture()
    ap = pd.concat([hubs, hubs.iloc[:1]], ignore_index=True)
    master = pd.DataFrame([{"AIRPORT": "AAA", "AIRPORT_IS_LATEST": "true",
                            "CITY_MARKET_ID": 123}])
    selection = pd.DataFrame([{"city_market_id": 123,
                               "selected_cbsa": "00001"}])
    cbsa = pd.DataFrame([{"code": "00001", "population": 500000}])
    with pytest.raises(ValueError, match="code duplicates"):
        prepare_geo(ap, master, selection, cbsa)


def test_explicit_duplicate_citymarket_bridge_fails_closed():
    hubs, _ = fixture()
    master = pd.DataFrame([{"AIRPORT": "SEA", "AIRPORT_IS_LATEST": "true",
                            "CITY_MARKET_ID": 123}])
    selection = pd.DataFrame([{"city_market_id": 123,
                               "selected_cbsa": "00001"},
                              {"city_market_id": 123,
                               "selected_cbsa": "00002"}])
    cbsa = pd.DataFrame([{"code": "00001", "population": 500000},
                          {"code": "00002", "population": 510000}])
    with pytest.raises(ValueError, match="duplicate city-market"):
        prepare_geo(hubs, master, selection, cbsa)
