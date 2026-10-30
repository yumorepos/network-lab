"""Read-only 2024 BTS source-vintage candidate envelope; NOT a warehouse replay.

Needs the two T-100 2024 ZIP vintages, archived OurAirports CSV, BTS Master
Coordinate ZIP and the source-only CBSA SQLite audit from the prior review.
Never changes a source file, DuckDB database, model, replay, or screening output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path
import zipfile

import numpy as np
import pandas as pd

HUBS_NM = {"YYC": 2600, "SEA": 2600, "YYZ": 2200}
NM_TO_MI = 1.15078
POP_FLOOR = 400000
SEAT_FLOOR = 250000
SATELLITE_RADIUS_MI = 60
SATELLITE_SEAT_RATIO = 5


def source_seats(path: Path):
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None:
            raise ValueError("T-100 CRC failure")
        members = [n for n in z.namelist() if n.endswith(".csv")
                   and "Documentation" not in n]
        if len(members) != 1:
            raise ValueError("Expected one T-100 CSV")
        df = pd.read_csv(z.open(members[0]), usecols=[
            "YEAR", "MONTH", "ORIGIN", "DEST", "ORIGIN_COUNTRY",
            "DEST_COUNTRY", "CLASS", "DEPARTURES_PERFORMED", "SEATS",
            "PASSENGERS"])
    if set(df.YEAR.dropna().unique()) != {2024} or not df.MONTH.between(1, 12).all():
        raise ValueError("Wrong year or month")
    operating = df[df.CLASS.isin(("F", "L")) & df.DEPARTURES_PERFORMED.gt(0)]
    seats = operating.groupby("ORIGIN").SEATS.sum().to_dict()
    usca = operating[
        ((operating.ORIGIN_COUNTRY == "US") & (operating.DEST_COUNTRY == "CA")) |
        ((operating.ORIGIN_COUNTRY == "CA") & (operating.DEST_COUNTRY == "US"))]
    metrics = {"records": len(usca), "passenger_segment_legs": int(usca.PASSENGERS.sum()),
               "seats": int(usca.SEATS.sum()),
               "departures": int(usca.DEPARTURES_PERFORMED.sum())}
    return seats, metrics


def prepare_geo(airports, master, selection, cbsa):
    airports = airports[airports.iata_code.notna()].copy()
    if airports.iata_code.duplicated().any():
        raise ValueError("OurAirports code duplicates require resolution")
    latest = master[master.AIRPORT_IS_LATEST.astype(str).str.lower().isin(("true", "1")) &
                    master.AIRPORT.notna()]
    # Reproduces the legacy MAX market-ID choice; not endorsed as stable identity.
    latest = latest.groupby("AIRPORT").CITY_MARKET_ID.max().rename_axis(
        "iata_code").reset_index()
    selection = selection[selection.selected_cbsa.notna()].copy()
    selection["city_market_id"] = pd.to_numeric(selection.city_market_id)
    if selection.city_market_id.duplicated().any():
        raise ValueError("Source CBSA bridge has duplicate city-market IDs")
    joined = airports.merge(latest, on="iata_code", how="left").merge(
        selection, left_on="CITY_MARKET_ID", right_on="city_market_id", how="left")
    joined = joined[(joined.iso_country == "US") & joined.selected_cbsa.notna()]
    cbsa = cbsa.rename(columns={"code": "selected_cbsa"})
    joined = joined.merge(cbsa[["selected_cbsa", "population"]],
                          on="selected_cbsa", how="left")
    if joined[["iata_code", "latitude_deg", "longitude_deg"]].isna().any().any():
        raise ValueError("Missing airport coordinates")
    return joined


def haversine_miles(lat1, lon1, lat2, lon2):
    a, b, c, d = map(np.radians, (lat1, lon1, lat2, lon2))
    x = np.sin((a-c)/2)**2 + np.cos(a)*np.cos(c)*np.sin((b-d)/2)**2
    return 3958.7613*2*np.arcsin(np.sqrt(np.clip(x, 0, 1)))


def compare(airports, geo, before_seats, after_seats):
    geo = geo.copy()
    for key, values in (("before", before_seats), ("after", after_seats)):
        geo[key] = geo.iata_code.map(values).fillna(0)
    anchors = {}
    for key in ("before", "after"):
        anchors[key] = (geo.sort_values(["selected_cbsa", key, "iata_code"],
                                        ascending=[True, False, True])
                        .drop_duplicates("selected_cbsa")
                        .set_index("selected_cbsa")[[
                            "iata_code", "latitude_deg", "longitude_deg",
                            "population", key]])
    both = anchors["before"].join(anchors["after"], lsuffix="_before", rsuffix="_after")
    before, after = both.before.to_numpy(float), both.after.to_numpy(float)
    coords = both[["latitude_deg_before", "longitude_deg_before"]].to_numpy(float)
    distances = haversine_miles(coords[:, 0, None], coords[:, 1, None],
                                 coords[None, :, 0], coords[None, :, 1])
    np.fill_diagonal(distances, np.inf)
    satellites = {}
    for key, seats in (("before", before), ("after", after)):
        satellites[key] = np.any(
            (distances <= SATELLITE_RADIUS_MI) &
            (seats[None, :] >= SATELLITE_SEAT_RATIO*np.maximum(seats[:, None], 1)),
            axis=1)
    candidates = {}
    for hub, maximum_nm in HUBS_NM.items():
        hub_airport = airports[airports.iata_code == hub]
        if len(hub_airport) != 1:
            raise ValueError("Hub must be unique: " + hub)
        h = hub_airport.iloc[0]
        dist = haversine_miles(coords[:, 0], coords[:, 1],
                               float(h.latitude_deg), float(h.longitude_deg))
        in_scope = ((dist >= 250*NM_TO_MI) & (dist <= maximum_nm*NM_TO_MI) &
                    (both.population_before.to_numpy(float) >= POP_FLOOR))
        old_ok = in_scope & (before >= SEAT_FLOOR) & ~satellites["before"]
        new_ok = in_scope & (after >= SEAT_FLOOR) & ~satellites["after"]
        candidates[hub] = {
            "before_count": int(old_ok.sum()),
            "after_count": int(new_ok.sum()),
            "changed_cbsa": sorted(both.index[old_ok != new_ok].astype(str).tolist())}
    changed = both[both.before != both.after]
    tie_groups = geo.groupby("selected_cbsa")
    zero_seat_ties = int(((tie_groups.before.max() == 0) &
                         (tie_groups.iata_code.count() > 1)).sum())
    return {
        "scope": "Source-only eligibility/anchor/satellite reconstruction, NOT warehouse",
        "cbsa_anchors_checked": len(both),
        "anchor_airport_changes": int((both.iata_code_before != both.iata_code_after).sum()),
        "seat_floor_crossings": int(np.count_nonzero(
            (before >= SEAT_FLOOR) != (after >= SEAT_FLOOR))),
        "satellite_flag_changes": int(np.count_nonzero(
            satellites["before"] != satellites["after"])),
        "zero_seat_ties_not_warehouse_resolved": zero_seat_ties,
        "pre_served_candidate_sets": candidates,
        "selected_anchor_seat_changes": [
            {"cbsa": str(k), "airport": r.iata_code_before,
             "before_seats": int(r.before), "after_seats": int(r.after),
             "difference": int(r.after-r.before)}
            for k, r in changed.iterrows()],
        "model_or_historical_replay_rerun": False,
        "carrier_brand_served_exclusion_recomputed": False,
        "production_verdict_changes_established": False}


def checksum(path):
    d = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            d.update(chunk)
    return d.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("archived", "current", "ourairports", "master_zip",
                 "cbsa_sqlite", "output"):
        parser.add_argument("--" + name.replace("_", "-"),
                            type=Path, required=True)
    args = parser.parse_args()
    inputs = [args.archived, args.current, args.ourairports,
              args.master_zip, args.cbsa_sqlite]
    output = args.output.resolve()
    if output.exists() or output in [p.resolve() for p in inputs]:
        parser.error("Refusing to overwrite source or prior evidence")
    old, old_ca_us = source_seats(args.archived)
    new, new_ca_us = source_seats(args.current)
    airports = pd.read_csv(args.ourairports, low_memory=False)
    with zipfile.ZipFile(args.master_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("Master Coordinate CRC failure")
        master = pd.read_csv(archive.open("T_MASTER_CORD.csv"),
                             low_memory=False)
    with sqlite3.connect(args.cbsa_sqlite) as db:
        selected = pd.read_sql_query(
            "SELECT city_market_id, selected_cbsa FROM selection", db)
        cbsa = pd.read_sql_query("SELECT code,population FROM cbsa", db)
    report = compare(airports, prepare_geo(airports, master, selected, cbsa),
                     old, new)
    report["archived_sha256"] = checksum(args.archived)
    report["current_sha256"] = checksum(args.current)
    report["frozen_us_canada_segment_totals"] = old_ca_us
    report["current_us_canada_segment_totals"] = new_ca_us
    report["us_canada_segment_totals_identical"] = old_ca_us == new_ca_us
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: report[k] for k in (
        "cbsa_anchors_checked", "anchor_airport_changes",
        "seat_floor_crossings", "satellite_flag_changes",
        "us_canada_segment_totals_identical", "pre_served_candidate_sets"
    )}, indent=2))


if __name__ == "__main__":
    main()
