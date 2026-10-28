"""Isolated July 2026 T-100 freshness pilot. No production data writes.

Run from the repository root:
    python -m scripts.stage_b_t100_pilot --output-dir /tmp/network-lab-stage-b

Downloads the existing official BTS table 293 year ZIPs, but extracts only
the selected months into a SEPARATE DuckDB file and comparison CSV. Does not
load the production warehouse, alter outputs, or claim a validated forecast.
"""
from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from pathlib import Path

import duckdb
import pandas as pd

from ingest.bts_t100 import FIELDS
from ingest.transtats import T100_SEGMENT_ALL, ALL_FIELDS, download_table_year

TARGET = (2026, 7)
CONTROL = (2025, 7)
COUNTS = ("SEATS", "PASSENGERS", "DEPARTURES_PERFORMED")
# Stable identifiers published with table 293. The production ingest deliberately
# remains at its 14-field contract; only this research download adds IDs.
STABLE_FIELDS = ("ORIGIN_AIRPORT_ID", "DEST_AIRPORT_ID",
                 "ORIGIN_CITY_MARKET_ID", "DEST_CITY_MARKET_ID")
PILOT_FIELDS = [*FIELDS, *STABLE_FIELDS]


def read_month_zip(path: Path, year: int, month: int) -> pd.DataFrame:
    """Read a month from a BTS full-year ZIP without editing any cached data."""
    with zipfile.ZipFile(path) as archive:
        csv_members = [i for i in archive.infolist()
                       if i.filename.lower().endswith(".csv")
                       and not i.filename.lower().endswith("documentation.csv")]
        if not csv_members:
            raise ValueError("No data CSV in T-100 ZIP")
        member = max(csv_members, key=lambda i: i.file_size)
        with archive.open(member) as raw:
            frame = pd.read_csv(raw, usecols=lambda c: c.upper() in PILOT_FIELDS,
                                dtype="string", low_memory=False)
    frame.columns = frame.columns.str.upper()
    missing = sorted(set(PILOT_FIELDS) - set(frame.columns))
    if missing:
        raise ValueError("Missing official T-100 fields: " + ", ".join(missing))
    for col in ("YEAR", "MONTH", *COUNTS):
        frame[col] = pd.to_numeric(frame[col], errors="raise")
    frame = frame.loc[(frame.YEAR == year) & (frame.MONTH == month)
                      & (frame.DEPARTURES_PERFORMED > 0)].copy()
    if frame.empty:
        raise ValueError(f"No positive-departure T-100 records for {year}-{month:02d}")
    for col in COUNTS:
        if frame[col].isna().any() or (frame[col] < 0).any():
            raise ValueError(f"Missing or negative {col} in {year}-{month:02d}")
    for col in ("UNIQUE_CARRIER", "ORIGIN", "DEST", *STABLE_FIELDS):
        if frame[col].isna().any() or (frame[col].str.len() == 0).any():
            raise ValueError(f"Missing {col} in {year}-{month:02d}")
    return frame


def stats(frame: pd.DataFrame) -> dict:
    """Counts and scope checks without treating segment PAX as ticket O&D."""
    us_a = frame.ORIGIN_COUNTRY == "US"
    us_b = frame.DEST_COUNTRY == "US"
    ca_a = frame.ORIGIN_COUNTRY == "CA"
    ca_b = frame.DEST_COUNTRY == "CA"
    key = ["YEAR", "MONTH", "UNIQUE_CARRIER", "ORIGIN", "DEST",
           "AIRCRAFT_TYPE", "CLASS"]
    return {
        "rows": int(len(frame)),
        "carriers": int(frame.UNIQUE_CARRIER.nunique()),
        "airports": int(pd.concat([frame.ORIGIN, frame.DEST]).nunique()),
        "passengers": int(frame.PASSENGERS.sum()),
        "seats": int(frame.SEATS.sum()),
        "departures": int(frame.DEPARTURES_PERFORMED.sum()),
        "exact_duplicate_rows": int(frame.duplicated().sum()),
        "collisions_at_selected_key": int(frame.duplicated(key).sum()),
        "us_domestic_rows": int((us_a & us_b).sum()),
        "us_to_canada_rows": int((us_a & ca_b).sum()),
        "canada_to_us_rows": int((ca_a & us_b).sum()),
        "no_us_endpoint_rows": int((~us_a & ~us_b).sum()),
        "missing_country_rows": int(
            (frame.ORIGIN_COUNTRY.isna() | frame.DEST_COUNTRY.isna()).sum()
        ),
    }


def operator_mapping_diagnostic(frame: pd.DataFrame, families: Path) -> dict:
    """Flag the brand-vs-operator caveat; do not guess a multi-brand operator."""
    ref = pd.read_csv(families, dtype=str).fillna("")
    if ref.operating_carrier.duplicated().any():
        raise ValueError("Duplicated operating carrier in family reference")
    known = set(ref.operating_carrier)
    multi = set(ref.loc[ref.resolution == "db1b_per_segment",
                        "operating_carrier"])
    static = set(ref.loc[ref.resolution == "static", "operating_carrier"])
    return {
        "static_reference_rows": int(frame.UNIQUE_CARRIER.isin(static).sum()),
        "multi_brand_unresolved_rows": int(frame.UNIQUE_CARRIER.isin(multi).sum()),
        "other_operator_rows": int((~frame.UNIQUE_CARRIER.isin(known)).sum()),
        "multi_brand_operators": sorted(
            set(frame.UNIQUE_CARRIER.dropna()) & multi
        ),
    }


def airport_lookup_diagnostic(frame: pd.DataFrame, path: Path) -> dict:
    """Check current BTS airport-to-city-market lookup without silently deduping."""
    needed = {"AIRPORT", "AIRPORT_ID", "CITY_MARKET_ID", "AIRPORT_IS_LATEST"}
    with zipfile.ZipFile(path) as archive:
        members = [i for i in archive.infolist()
                   if i.filename.lower().endswith(".csv")
                   and not i.filename.lower().endswith("documentation.csv")]
        if not members:
            raise ValueError("No BTS Master Coordinate data CSV in ZIP")
        with archive.open(max(members, key=lambda i: i.file_size)) as raw:
            lookup = pd.read_csv(raw, usecols=lambda s: s.upper() in needed,
                                 dtype="string", low_memory=False)
    lookup.columns = lookup.columns.str.upper()
    missing = sorted(needed - set(lookup.columns))
    if missing:
        raise ValueError("Master Coordinate missing fields: " + ", ".join(missing))
    latest = lookup.loc[
        lookup["AIRPORT_IS_LATEST"].str.lower().isin(("true", "1"))
        & lookup["CITY_MARKET_ID"].notna(), ["AIRPORT", "AIRPORT_ID", "CITY_MARKET_ID"]
    ].drop_duplicates()
    if latest.empty:
        raise ValueError("Master Coordinate has no current airport market IDs")
    airports = set(pd.concat([frame.ORIGIN, frame.DEST]).dropna())
    found = set(latest.AIRPORT.dropna())
    ambiguity = (latest.groupby("AIRPORT")["CITY_MARKET_ID"].nunique() > 1)
    ambiguous_codes = set(ambiguity[ambiguity].index)
    missing_codes = airports - found
    touching_missing = frame.ORIGIN.isin(missing_codes) | frame.DEST.isin(missing_codes)
    touching_ambiguous = (
        frame.ORIGIN.isin(ambiguous_codes) | frame.DEST.isin(ambiguous_codes)
    )
    # A three-character code can be reused. Join stable AirportID instead,
    # and compare the source's own July CityMarketID against latest lookup.
    legs = pd.concat([
        frame[["ORIGIN_AIRPORT_ID", "ORIGIN_CITY_MARKET_ID"]].rename(
            columns={"ORIGIN_AIRPORT_ID": "AIRPORT_ID",
                     "ORIGIN_CITY_MARKET_ID": "SOURCE_MARKET_ID"}),
        frame[["DEST_AIRPORT_ID", "DEST_CITY_MARKET_ID"]].rename(
            columns={"DEST_AIRPORT_ID": "AIRPORT_ID",
                     "DEST_CITY_MARKET_ID": "SOURCE_MARKET_ID"}),
    ], ignore_index=True).drop_duplicates()
    by_id = latest[["AIRPORT_ID", "CITY_MARKET_ID"]].drop_duplicates()
    lookup_conflicts_by_id = (
        by_id.groupby("AIRPORT_ID")["CITY_MARKET_ID"].nunique() > 1)
    joined = legs.merge(by_id, on="AIRPORT_ID", how="left",
                        validate="many_to_many", indicator=True)
    matched = joined.loc[joined["_merge"] == "both"]
    conflict_ids = set(lookup_conflicts_by_id[lookup_conflicts_by_id].index)
    stable_disagreements = matched.loc[
        matched.SOURCE_MARKET_ID != matched.CITY_MARKET_ID]
    return {
        "lookup_current_airport_rows": int(len(latest)),
        "source_distinct_airport_id_market_pairs": int(len(legs)),
        "stable_id_lookup_matching_pairs": int(len(matched)),
        "stable_id_lookup_missing_pairs": int((joined["_merge"] != "both").sum()),
        "stable_id_market_disagree_pairs": int(len(stable_disagreements)),
        "stable_id_market_disagree_ids": sorted(
            set(stable_disagreements.AIRPORT_ID.dropna()))[:30],
        "stable_id_with_multiple_latest_market_ids": len(conflict_ids),
        "unique_observed_airports": len(airports),
        "matched_observed_airports": len(airports & found),
        "unmatched_observed_airports": sorted(missing_codes)[:30],
        "unmatched_observed_airport_count": len(missing_codes),
        "unmatched_observed_segment_rows": int(touching_missing.sum()),
        "unmatched_observed_segment_passengers": int(
            frame.loc[touching_missing, "PASSENGERS"].sum()),
        "ambiguous_latest_airport_market_ids": int(ambiguity.sum()),
        "ambiguous_latest_airport_codes": sorted(ambiguous_codes),
        "ambiguous_observed_airport_codes": sorted(ambiguous_codes & airports),
        "ambiguous_observed_segment_rows": int(touching_ambiguous.sum()),
        "lookup_vintage": "latest available as of 2026-10-28; not a historical lookup",
    }


def compare(target: pd.DataFrame, control: pd.DataFrame) -> pd.DataFrame:
    """Same-calendar-month operator/airport/direction only, no O&D interpretation."""
    key = ["UNIQUE_CARRIER", "ORIGIN", "DEST"]
    cols = ["PASSENGERS", "SEATS", "DEPARTURES_PERFORMED"]
    left = target.groupby(key, dropna=False)[cols].sum().reset_index()
    right = control.groupby(key, dropna=False)[cols].sum().reset_index()
    out = left.merge(right, on=key, how="outer", suffixes=("_2026", "_2025"),
                     indicator="period_presence")
    return out.sort_values(key, kind="stable").reset_index(drop=True)


def run(output_dir: Path, *, downloader=download_table_year) -> dict:
    """Produce separate research tables and an auditable summary in output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    data = {}
    for year, month in (TARGET, CONTROL):
        z = downloader(T100_SEGMENT_ALL, year, PILOT_FIELDS,
                       output_dir / "raw" / f"t100_table293_{year}.zip")
        data[year] = read_month_zip(z, year, month)
    current, previous = data[TARGET[0]], data[CONTROL[0]]
    lookup_zip = downloader(288, "All", ALL_FIELDS,
                            output_dir / "raw" / "bts_master_coordinate.zip")
    lookup_check = airport_lookup_diagnostic(current, lookup_zip)
    summary = {
        "source": "BTS TranStats T-100 Segment (All Carriers), table 293",
        "comparison": "same month year-over-year, NOT a point-in-time replay",
        "target_month": "2026-07",
        "control_month": "2025-07",
        "target": stats(current),
        "control": stats(previous),
        "operator_mapping": operator_mapping_diagnostic(
            current, Path("data/reference/carrier_families.csv")),
        "airport_city_market_lookup": lookup_check,
        "metro_crosswalk_verified": False,
        "foreign_carrier_filing_complete": "not established",
    }
    if summary["target"]["no_us_endpoint_rows"]:
        raise ValueError("T-100 scope violation: segments without a US endpoint")
    if summary["target"]["missing_country_rows"]:
        raise ValueError("Missing country codes in target month")
    con = duckdb.connect(str(output_dir / "stage_b_t100.duckdb"))
    try:
        for table, frame in [("t100_segment_2026_07", current),
                             ("t100_segment_2025_07", previous)]:
            con.register("research_frame", frame)
            con.execute(f"CREATE OR REPLACE TABLE {table} AS "
                        "SELECT * FROM research_frame")
            con.unregister("research_frame")
        diff = compare(current, previous)
        con.register("comparison_frame", diff)
        con.execute("CREATE OR REPLACE TABLE july_yoy_operator_segment "
                    "AS SELECT * FROM comparison_frame")
        con.unregister("comparison_frame")
        diff.to_csv(output_dir / "july_yoy_operator_segment.csv", index=False)
    finally:
        con.close()
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path,
                        help="Separate research-only output directory")
    args = parser.parse_args()
    if args.output_dir:
        print(json.dumps(run(args.output_dir), indent=2, sort_keys=True))
    else:
        with tempfile.TemporaryDirectory(prefix="networklab_stage_b_") as t:
            print(json.dumps(run(Path(t)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
