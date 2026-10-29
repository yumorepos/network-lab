"""Adversarial offline tests; never accesses the production warehouse."""
import datetime as dt
import unittest
from scripts.audit_archived_airport_identity import resolve_candidates


class HistoricalIdentityTests(unittest.TestCase):
    @staticmethod
    def item(airport_id, market, country, start=None, end=None):
        return {"airport_id": airport_id, "city_market_id": market,
                "country": country,
                "start": dt.date.fromisoformat(start) if start else None,
                "end": dt.date.fromisoformat(end) if end else None}

    def test_cross_country_code_reuse(self):
        rows = [self.item(1, 33459, "US", "1950-01-01", "2002-01-31"),
                self.item(2, 32395, "TR", "2023-01-01")]
        matched, why = resolve_candidates(rows, "TR", 2026, 3)
        self.assertEqual(why, "unique_country_date_candidate")
        self.assertEqual(matched["city_market_id"], 32395)
        self.assertNotEqual(max(r["city_market_id"] for r in rows), matched["city_market_id"])

    def test_time_disambiguates_same_country(self):
        rows = [self.item(3, 10, "US", "2000-01-01", "2015-12-31"),
                self.item(4, 20, "US", "2016-01-01")]
        self.assertEqual(resolve_candidates(rows, "US", 2025, 1)[0]["city_market_id"], 20)

    def test_unresolved_overlap_fails_closed(self):
        rows = [self.item(3, 10, "US"), self.item(4, 20, "US")]
        self.assertEqual(resolve_candidates(rows, "US", 2025, 1), (None, "ambiguous_candidates"))

    def test_missing_code_fails_closed(self):
        self.assertEqual(resolve_candidates([], "US", 2025, 1), (None, "unknown_code"))

    def test_wrong_vintage_fails_closed(self):
        rows = [self.item(3, 10, "US", "2026-01-01")]
        self.assertEqual(resolve_candidates(rows, "US", 2025, 1), (None, "no_valid_candidate"))


if __name__ == "__main__":
    unittest.main()
