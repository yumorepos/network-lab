"""Negative controls for the preserved warehouse's label-only counterfactual."""
from __future__ import annotations

import csv

import duckdb

from scripts.audit_airport_label_candidate import (
    EXPECTED_PREVIOUS_MISMATCH_CODES,
    STUDY_COUNTS,
    analyze_rows,
    project_labels,
)


def test_real_sql_candidate_picks_label_from_same_id_without_writing(tmp_path):
    con = duckdb.connect()
    con.execute("""
        CREATE TABLE dim_airport (
          iata_code VARCHAR, city_market_id VARCHAR, city_market_name VARCHAR,
          iso_country VARCHAR
        )
    """)
    con.execute("""
        INSERT INTO dim_airport VALUES
          ('SAW','33459','Istanbul, Turkey','TR'),
          ('ISL','32395','Isabel Pass, AK','TR'),
          ('SEA','30559','Seattle, WA','US')
    """)
    con.execute("""
        CREATE TABLE source (
          AIRPORT VARCHAR, CITY_MARKET_ID VARCHAR,
          DISPLAY_CITY_MARKET_NAME_FULL VARCHAR,
          AIRPORT_ID VARCHAR, AIRPORT_IS_LATEST VARCHAR,
          AIRPORT_COUNTRY_CODE_ISO VARCHAR
        )
    """)
    con.execute("""
        INSERT INTO source VALUES
          ('SAW','32395','Istanbul, Turkey','100','true','TR'),
          ('SAW','33459','Marquette, MI','200','true','US'),
          ('ISL','32395','Istanbul, Turkey','300','1','TR'),
          ('ISL','12345','Isabel Pass, AK','400','true','US'),
          ('SEA','30559','Seattle, WA','500','true','US'),
          ('SEA','99999','Wrong vintage','600','false','CA')
    """)
    lookup = tmp_path / "master_coord.parquet"
    con.execute(f"COPY source TO '{lookup}' (FORMAT PARQUET)")
    before = con.execute("SELECT * FROM dim_airport ORDER BY 1").fetchall()
    got = project_labels(con, lookup)
    assert len(got) == 3
    by = {r["iata_code"]: r for r in got}
    assert (by["SAW"]["candidate_market_id"],
            by["SAW"]["candidate_market_name"]) == ("33459", "Marquette, MI")
    assert (by["ISL"]["candidate_market_id"],
            by["ISL"]["candidate_market_name"]) == ("32395", "Istanbul, Turkey")
    assert by["SEA"]["stored_market_name"] == by["SEA"]["candidate_market_name"]
    assert by["SAW"]["stored_country"] == "TR"
    assert by["SAW"]["candidate_country"] == "US"
    assert before == con.execute("SELECT * FROM dim_airport ORDER BY 1").fetchall()
    con.close()


def fixture(tmp_path):
    root = tmp_path
    outputs = root / "data/parquet/outputs"
    outputs.mkdir(parents=True)
    for study, n in STUDY_COUNTS.items():
        with (outputs / f"screen_{study}.csv").open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["dest_airport"])
            writer.writeheader()
            writer.writerows({"dest_airport": "JFK"} for _ in range(n))
    wh = root / "warehouse.duckdb"
    wh.write_bytes(b"synthetic-only")
    lookup = root / "master.parquet"
    lookup.write_bytes(b"synthetic-source-hash-only")
    rows = [
        {"iata_code": f"C{i:05d}",
         "stored_market_id": str(i), "candidate_market_id": str(i),
         "stored_market_name": f"Name {i}", "candidate_market_name": f"Name {i}"}
        for i in range(8792)
    ]
    for idx, code in enumerate(sorted(EXPECTED_PREVIOUS_MISMATCH_CODES)):
        rows.append({
            "iata_code": code, "stored_market_id": str(32000 + idx),
            "candidate_market_id": str(32000 + idx),
            "stored_market_name": f"Incorrect {code}",
            "candidate_market_name": f"Correct {code}",
        })
    return root, wh, lookup, rows


def test_only_expected_ten_label_changes_pass_dimension_projection(tmp_path):
    root, wh, lookup, rows = fixture(tmp_path)
    result = analyze_rows(rows, root, lookup, wh)
    assert result["result"] == "PASS_DIMENSION_PROJECTION"
    assert result["dimension_airport_rows"] == 8802
    assert result["candidate_label_change_count"] == 10
    assert result["numeric_market_id_change_count"] == 0
    assert result["full_200_screen_model_parity_certified"] is False
    assert result["463_historical_replay_decisions_recomputed"] is False


def test_numeric_citymarket_change_blocks_pass_even_when_labels_consistent(tmp_path):
    root, wh, lookup, rows = fixture(tmp_path)
    rows[0]["candidate_market_id"] = "999999"
    result = analyze_rows(rows, root, lookup, wh)
    assert result["result"] == "REVIEW_REQUIRED"
    assert result["numeric_market_id_change_count"] == 1


def test_unexpected_label_delta_blocks_pass(tmp_path):
    root, wh, lookup, rows = fixture(tmp_path)
    rows[0]["candidate_market_name"] = "Unknown new label"
    result = analyze_rows(rows, root, lookup, wh)
    assert result["result"] == "REVIEW_REQUIRED"
    assert result["unexpected_name_changes_vs_oct29_audit"] == ["C00000"]


def test_missing_published_study_blocks_200_row_check(tmp_path):
    root, wh, lookup, rows = fixture(tmp_path)
    (root / "data/parquet/outputs/screen_porter_yyz.csv").unlink()
    result = analyze_rows(rows, root, lookup, wh)
    assert result["result"] == "REVIEW_REQUIRED"
    assert result["screen_direct_destination_exposure"]["porter_yyz"]["checked"] is False


def test_one_direct_changed_screen_destination_blocks_pass(tmp_path):
    root, wh, lookup, rows = fixture(tmp_path)
    screen = root / "data/parquet/outputs/screen_westjet_yyc.csv"
    lines = screen.read_text().splitlines()
    lines[1] = "SAW"
    screen.write_text("\n".join(lines) + "\n")
    result = analyze_rows(rows, root, lookup, wh)
    assert result["result"] == "REVIEW_REQUIRED"
    assert result["screen_direct_destination_exposure"]["westjet_yyc"][
        "direct_changed_destination_codes"] == ["SAW"]


def test_duplicate_airport_code_fails_closed(tmp_path):
    root, wh, lookup, rows = fixture(tmp_path)
    rows[1]["iata_code"] = rows[0]["iata_code"]
    result = analyze_rows(rows, root, lookup, wh)
    assert result["result"] == "REVIEW_REQUIRED"
    assert result["duplicate_nonnull_airport_codes"] == ["C00000"]


def test_original_mac_cross_country_conflict_blocks_label_only_adoption(tmp_path):
    root, wh, lookup, rows = fixture(tmp_path)
    rows[0]["stored_country"] = "TR"
    rows[0]["candidate_country"] = "US"
    report = analyze_rows(rows, root, lookup, wh)
    assert report["result"] == "REVIEW_REQUIRED"
    assert report["unresolved_original_warehouse_country_conflict_count"] == 1
    assert report["unresolved_original_warehouse_country_conflicts"][0]["iata_code"] == "C00000"


def test_territorial_country_code_convention_is_flagged_separately(tmp_path):
    root, wh, lookup, rows = fixture(tmp_path)
    rows[0]["stored_country"] = "PR"
    rows[0]["candidate_country"] = "US"
    report = analyze_rows(rows, root, lookup, wh)
    assert report["result"] == "PASS_DIMENSION_PROJECTION"
    assert report["country_coding_conventions_to_verify"] == ["C00000"]
    assert report["unresolved_original_warehouse_country_conflict_count"] == 0
