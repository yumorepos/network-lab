"""Read-only OurAirports/BTS country-code disagreement research.

Reports source-vintage exposures, NOT production join failures or lost traffic.
Administrative country-code differences are explicitly classified as
conventions to review, not silently normalized or called mapping errors.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

CONVENTIONS_TO_VERIFY = {
    ("PR","US"), ("GU","US"), ("VI","US"), ("AS","US"), ("MP","US"),
    ("UM","US"), ("GG","GB"), ("JE","GB"), ("IM","GB"), ("FO","DK"),
    ("EH","MA"),
}


def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def zipped_rows(path: Path, member: str):
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None:
            raise ValueError(f"Corrupt ZIP: {path}")
        if member not in z.namelist():
            raise ValueError(f"Missing source member {member}")
        with z.open(member) as stream:
            yield from csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig"))


def audit(ourairports: Path, master: Path, t100: list[Path] = (),
          screens: list[Path] = ()):
    our = {}
    with ourairports.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not {"iata_code", "iso_country", "name"}.issubset(reader.fieldnames or []):
            raise ValueError("OurAirports schema incomplete")
        for r in reader:
            code = (r.get("iata_code") or "").strip()
            if not code:
                continue
            if code in our:
                raise ValueError(f"Duplicated OurAirports IATA code: {code}")
            our[code] = r

    latest = defaultdict(list)
    required = {"AIRPORT", "CITY_MARKET_ID", "AIRPORT_COUNTRY_CODE_ISO",
                "DISPLAY_CITY_MARKET_NAME_FULL", "AIRPORT_IS_LATEST"}
    for r in zipped_rows(master, "T_MASTER_CORD.csv"):
        if not required.issubset(r):
            raise ValueError("Master Coordinate schema incomplete")
        if (r.get("AIRPORT_IS_LATEST") or "").lower() in ("1", "true") and r.get("AIRPORT"):
            latest[r["AIRPORT"]].append(r)
    matched = 0
    findings = {}
    for code, rows in sorted(latest.items()):
        if code not in our:
            continue
        ids = [r["CITY_MARKET_ID"] for r in rows if r.get("CITY_MARKET_ID")]
        if not ids:
            continue
        matched += 1
        selected = max(ids)  # Same VARCHAR MAX semantics as archived builder.
        candidates = [r for r in rows if r["CITY_MARKET_ID"] == selected]
        countries = sorted({r["AIRPORT_COUNTRY_CODE_ISO"] for r in candidates})
        actual = our[code]["iso_country"]
        if countries == [actual]:
            continue
        convention = len(countries) == 1 and (actual, countries[0]) in CONVENTIONS_TO_VERIFY
        findings[code] = {
            "code": code, "ourairports_country": actual,
            "bts_selected_market_country_codes": countries,
            "legacy_selected_market_id": selected,
            "ourairports_name": our[code]["name"],
            "source_market_names": sorted({
                r["DISPLAY_CITY_MARKET_NAME_FULL"] for r in candidates}),
            "classification": ("administrative_convention_to_verify" if convention
                               else "unresolved_source_country_conflict"),
            "observed_traffic_by_archived_year": {},
        }

    traffic = {}
    for path in sorted(t100):
        rows, pax = Counter(), Counter()
        for r in zipped_rows(path, "T_T100_SEGMENT_ALL_CARRIER.csv"):
            if (r.get("CLASS") not in ("F", "L") or
                    float(r.get("DEPARTURES_PERFORMED") or 0) <= 0):
                continue
            for code in (r.get("ORIGIN"), r.get("DEST")):
                if code in findings:
                    rows[code] += 1
                    pax[code] += int(float(r.get("PASSENGERS") or 0))
        by = {"administrative_convention_to_verify": {"endpoints": 0, "legs": 0},
              "unresolved_source_country_conflict": {"endpoints": 0, "legs": 0}}
        for code in rows:
            kind = findings[code]["classification"]
            by[kind]["endpoints"] += rows[code]
            by[kind]["legs"] += pax[code]
            findings[code]["observed_traffic_by_archived_year"][path.stem] = {
                "endpoints": rows[code], "passenger_segment_legs": pax[code]}
        traffic[path.stem] = {"sha256": sha256(path), "by_class": by}

    screen_exposure = {}
    for path in screens:
        with path.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            if "dest_airport" not in (reader.fieldnames or []):
                raise ValueError("Screen destination column absent")
            rows = list(reader)
        screen_exposure[path.stem] = {
            "row_count": len(rows),
            "direct_conflict_destinations": sorted({
                r["dest_airport"] for r in rows if r["dest_airport"] in findings}),
            "sha256": sha256(path),
        }
    return {
        "scope": "ARCHIVED SOURCE ONLY; no original Mac DuckDB or replay readback",
        "ourairports_sha256": sha256(ourairports),
        "master_coordinate_sha256": sha256(master),
        "source_code_matches": matched,
        "country_disagreement_count": len(findings),
        "classification_counts": dict(Counter(
            x["classification"] for x in findings.values())),
        "t100_endpoint_exposure": traffic,
        "screen_direct_exposure": screen_exposure,
        "findings": [findings[k] for k in sorted(findings)],
        "country_conventions_authoritatively_validated": False,
        "production_impact_or_verdict_changes_measured": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ourairports", type=Path, required=True)
    p.add_argument("--master-zip", type=Path, required=True)
    p.add_argument("--t100-zip", type=Path, action="append", default=[])
    p.add_argument("--screen-csv", type=Path, action="append", default=[])
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    sources = [a.ourairports, a.master_zip, *a.t100_zip, *a.screen_csv]
    if a.output.exists() or any(a.output.resolve() == x.resolve() for x in sources):
        p.error("Refusing to overwrite input or existing report")
    result = audit(a.ourairports, a.master_zip, a.t100_zip, a.screen_csv)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("Source country disagreements:", result["classification_counts"])
    print("No original warehouse accessed or modified.")


if __name__ == "__main__":
    main()
