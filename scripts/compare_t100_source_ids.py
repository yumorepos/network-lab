"""Compare independently downloaded BTS T-100 source AirportIDs by vintage.

All comparisons use source-published IDs; airport codes are never assumed stable.
No data or warehouse modifications. Output is not production consumer impact.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path


def _index(report):
    if "source_airport_identity_pairs" not in report:
        raise ValueError("Source report omitted stable identity pair inventory")
    codes = defaultdict(set)
    ids = defaultdict(lambda: {"codes": set(), "markets": set(), "countries": set()})
    traffic = defaultdict(lambda: {"legs": 0, "departures": 0, "rows": 0})
    for p in report["source_airport_identity_pairs"]:
        code = p["code"]
        aid = int(p["airport_id"])
        cmid = int(p["city_market_id"])
        if not code or aid <= 0 or cmid <= 0:
            raise ValueError("Missing or invalid source identity")
        codes[code].add(aid)
        ids[aid]["codes"].add(code)
        ids[aid]["markets"].add(cmid)
        ids[aid]["countries"].add(p["country"])
        traffic[code]["legs"] += int(p["endpoint_segment_passenger_legs"])
        traffic[code]["departures"] += int(p["endpoint_departures"])
        traffic[code]["rows"] += int(p["endpoint_rows"])
    if not codes or not ids:
        raise ValueError("No usable source-published airport identities")
    return codes, ids, traffic


def compare(earlier, later):
    first_year, second_year = earlier["source_year"], later["source_year"]
    if first_year >= second_year:
        raise ValueError("Expected strictly increasing source years")
    a_codes, a_ids, a_traffic = _index(earlier)
    b_codes, b_ids, b_traffic = _index(later)
    changed_code_meaning = []
    for code in sorted(set(a_codes) & set(b_codes)):
        if a_codes[code] != b_codes[code]:
            changed_code_meaning.append({
                "code": code,
                "earlier_airport_ids": sorted(a_codes[code]),
                "later_airport_ids": sorted(b_codes[code]),
                "earlier_endpoint_traffic": a_traffic[code],
                "later_endpoint_traffic": b_traffic[code],
            })
    changed_airport_code = []
    changed_airport_market = []
    for aid in sorted(set(a_ids) & set(b_ids)):
        left, right = a_ids[aid], b_ids[aid]
        if left["codes"] != right["codes"]:
            changed_airport_code.append({
                "stable_airport_id": aid,
                "earlier_codes": sorted(left["codes"]),
                "later_codes": sorted(right["codes"]),
            })
        if left["markets"] != right["markets"] or left["countries"] != right["countries"]:
            changed_airport_market.append({
                "stable_airport_id": aid,
                "earlier_markets": sorted(left["markets"]),
                "later_markets": sorted(right["markets"]),
                "earlier_countries": sorted(left["countries"]),
                "later_countries": sorted(right["countries"]),
            })
    return {
        "source": "official BTS table 293, separate source years",
        "earlier_year": first_year,
        "later_year": second_year,
        "earlier_months": earlier["observed_months"],
        "later_months": later["observed_months"],
        "earlier_source_sha256": earlier["source_zip_sha256"],
        "later_source_sha256": later["source_zip_sha256"],
        "airport_ids_common_to_both_source_years": len(set(a_ids) & set(b_ids)),
        "code_strings_common_to_both_source_years": len(set(a_codes) & set(b_codes)),
        "same_code_different_published_airport_ids": changed_code_meaning,
        "same_airport_id_different_observed_codes": changed_airport_code,
        "stable_airport_market_or_country_changed": changed_airport_market,
        "historical_warehouse_mapping_impact_established": False,
        "published_screen_or_replay_delta_measured": False,
        "caution": "Endpoint traffic counts are segment legs; subset years and published coverage are not comparable annual totals.",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--earlier", type=Path, required=True)
    p.add_argument("--later", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    path = args.output.resolve()
    if path.exists() or path in (args.earlier.resolve(), args.later.resolve()):
        p.error("Refusing to overwrite evidence or input")
    result = compare(json.loads(args.earlier.read_text()),
                     json.loads(args.later.read_text()))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("Cross-year code reassignments:",
          len(result["same_code_different_published_airport_ids"]))
    print("Stable-ID airport-code changes:",
          len(result["same_airport_id_different_observed_codes"]))


if __name__ == "__main__":
    main()
