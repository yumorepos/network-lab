"""Synthetic U.S. hub-month DB1C fixture and defect-injection tests.

All numbers and airport IDs are demonstration values, NOT observed traffic.
The fixtures test structure only; live BTS data have not been imported.
"""
from __future__ import annotations

import pandas as pd
import pytest

from scripts.stage_c_db1c_compat import validate_fixture


def frames():
    ticket = pd.DataFrame([
        dict(ItinID="A", RpYear=2025, RpMonth=7, IssuingCarrier="AS",
             Passengers=1, RoundTrip=1, TotalAmount=600, TaxAmount=120),
        dict(ItinID="B", RpYear=2025, RpMonth=7, IssuingCarrier="AS",
             Passengers=1, RoundTrip=0, TotalAmount=200, TaxAmount=40),
    ])
    market = pd.DataFrame([
        dict(ItinID="A", MktID="A1", RpYear=2025, RpMonth=7,
             OriginCityMarketID=101, DestCityMarketID=102, Passengers=1,
             MktAmout=300, MktTax=60, MktCoupons=1),
        dict(ItinID="A", MktID="A2", RpYear=2025, RpMonth=7,
             OriginCityMarketID=102, DestCityMarketID=101, Passengers=1,
             MktAmout=300, MktTax=60, MktCoupons=1),
        dict(ItinID="B", MktID="B1", RpYear=2025, RpMonth=7,
             OriginCityMarketID=101, DestCityMarketID=103, Passengers=1,
             MktAmout=200, MktTax=40, MktCoupons=1),
    ])
    coupon = pd.DataFrame([
        dict(ItinID="A", MktID="A1", SeqNum=1, RpYear=2025, RpMonth=7,
             OriginAirportID=11, DestAirportID=12, Viapoint="LAX"),
        dict(ItinID="A", MktID="A2", SeqNum=2, RpYear=2025, RpMonth=7,
             OriginAirportID=12, DestAirportID=11, Viapoint=""),
        dict(ItinID="B", MktID="B1", SeqNum=1, RpYear=2025, RpMonth=7,
             OriginAirportID=11, DestAirportID=13, Viapoint=None),
    ])
    segment = pd.DataFrame([
        dict(ItinID="A", MktID="A1", SeqNum=1, SegmentID=1,
             RpYear=2025, RpMonth=7),
        dict(ItinID="A", MktID="A1", SeqNum=1, SegmentID=2,
             RpYear=2025, RpMonth=7),
    ])
    return ticket, market, coupon, segment


def test_one_hub_month_validates_grain_and_prevents_double_counting():
    result = validate_fixture(*frames())
    assert result["ticket_rows"] == 2
    assert result["market_rows"] == 3
    assert result["coupon_rows"] == 3
    assert result["via_point_segment_rows"] == 2
    assert result["direct_coupon_rows"] == 2
    assert result["materialized_leg_rows"] == 4
    assert result["ticket_passengers_sample"] == 2
    assert result["market_passenger_records_sample"] == 3
    assert result["sample_expansion_applied"] is False
    assert result["market_fare_equivalent_to_db1b"] is False


def test_negative_control_duplicate_ticket_inflates_market_join():
    t, m, c, s = frames()
    t = pd.concat([t, t.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="ticket: duplicate key"):
        validate_fixture(t, m, c, s)


def test_negative_control_orphan_market_id():
    t, m, c, s = frames()
    m.loc[0, "ItinID"] = "NOT_AN_ITINERARY"
    with pytest.raises(ValueError, match="market: orphan itinerary"):
        validate_fixture(t, m, c, s)


def test_negative_control_coupon_to_nonexistent_market():
    t, m, c, s = frames()
    c.loc[2, "MktID"] = "NOT_A_MARKET"
    with pytest.raises(ValueError, match="coupon: orphan market"):
        validate_fixture(t, m, c, s)


def test_negative_control_segment_for_direct_coupon_double_counts():
    t, m, c, s = frames()
    s.loc[1, ["ItinID", "MktID", "SeqNum"]] = ["B", "B1", 1]
    with pytest.raises(ValueError, match="segment: coupon without via point"):
        validate_fixture(t, m, c, s)


def test_negative_control_via_point_coupon_missing_segment():
    t, m, c, s = frames()
    s = s.iloc[:0].copy()
    # A non-empty invalid segment is required by the input schema guard.
    s = pd.DataFrame([dict(ItinID="B", MktID="B1", SeqNum=1, SegmentID=1,
                           RpYear=2025, RpMonth=7)])
    with pytest.raises(ValueError, match="segment: coupon without via point"):
        validate_fixture(t, m, c, s)


def test_negative_control_market_gross_amount_is_not_old_mktfare_field():
    t, m, c, s = frames()
    m = m.rename(columns={"MktAmout": "MktFare"})
    with pytest.raises(ValueError, match="market: missing fields"):
        validate_fixture(t, m, c, s)


def test_negative_control_invalid_month():
    t, m, c, s = frames()
    t.loc[0, "RpMonth"] = 8
    with pytest.raises(ValueError, match="ticket: mixed reporting months"):
        validate_fixture(t, m, c, s)


def test_negative_control_unknown_segment_coupon():
    t, m, c, s = frames()
    s.loc[1, "SeqNum"] = 999
    with pytest.raises(ValueError, match="segment: orphan coupon"):
        validate_fixture(t, m, c, s)


def test_negative_control_via_coupon_without_any_segment_expansion():
    t, m, c, s = frames()
    c.loc[2, "Viapoint"] = "SLC"
    # Segment for ticket B is now mandatory but absent.
    with pytest.raises(ValueError, match="coupon: via point missing segment expansion"):
        validate_fixture(t, m, c, s)
