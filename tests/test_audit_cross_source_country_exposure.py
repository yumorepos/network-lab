"""Negative controls for archived-source geography convention vs reuse."""
import csv
import io
import zipfile

import pytest

from scripts.audit_cross_source_country_exposure import audit


def sources(tmp_path, our_rows, master_rows, t100_rows=()):
    ours = tmp_path / "airports.csv"
    with ours.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["iata_code", "iso_country", "name"])
        w.writeheader()
        w.writerows(our_rows)
    master = tmp_path / "master_coord.zip"
    buff = io.StringIO()
    w = csv.DictWriter(buff, fieldnames=[
        "AIRPORT", "CITY_MARKET_ID", "AIRPORT_COUNTRY_CODE_ISO",
        "DISPLAY_CITY_MARKET_NAME_FULL", "AIRPORT_IS_LATEST"])
    w.writeheader()
    w.writerows(master_rows)
    with zipfile.ZipFile(master, "w") as z:
        z.writestr("T_MASTER_CORD.csv", buff.getvalue())
    t100 = tmp_path / "t100_2024.zip"
    buff = io.StringIO()
    w = csv.DictWriter(buff, fieldnames=[
        "ORIGIN", "DEST", "CLASS", "DEPARTURES_PERFORMED", "PASSENGERS"])
    w.writeheader()
    w.writerows(t100_rows)
    with zipfile.ZipFile(t100, "w") as z:
        z.writestr("T_T100_SEGMENT_ALL_CARRIER.csv", buff.getvalue())
    return ours, master, t100


def airport(code, country):
    return {"iata_code": code, "iso_country": country, "name": "Fixture"}


def market(code, country, market_id):
    return {"AIRPORT": code, "CITY_MARKET_ID": str(market_id),
            "AIRPORT_COUNTRY_CODE_ISO": country,
            "DISPLAY_CITY_MARKET_NAME_FULL": "Fixture metro",
            "AIRPORT_IS_LATEST": "true"}


def test_territorial_convention_does_not_become_claim_of_error(tmp_path):
    o, m, z = sources(
        tmp_path, [airport("SJU", "PR")],
        [market("SJU", "US", 100)],
        [{"ORIGIN": "SJU", "DEST": "XYZ", "CLASS": "F",
          "DEPARTURES_PERFORMED": 1, "PASSENGERS": 70}])
    result = audit(o, m, [z])
    assert result["classification_counts"] == {
        "administrative_convention_to_verify": 1}
    assert result["t100_endpoint_exposure"]["t100_2024"][
        "by_class"]["administrative_convention_to_verify"]["legs"] == 70
    assert result["country_conventions_authoritatively_validated"] is False


def test_historically_reused_code_is_flagged(tmp_path):
    o, m, z = sources(tmp_path, [airport("SAW", "TR")],
        [market("SAW", "TR", 32395), market("SAW", "US", 33459)],
        [{"ORIGIN": "SAW", "DEST": "XYZ", "CLASS": "F",
          "DEPARTURES_PERFORMED": 1, "PASSENGERS": 7}])
    result = audit(o, m, [z])
    assert result["classification_counts"] == {
        "unresolved_source_country_conflict": 1}
    assert result["findings"][0]["legacy_selected_market_id"] == "33459"
    assert result["t100_endpoint_exposure"]["t100_2024"][
        "by_class"]["unresolved_source_country_conflict"]["legs"] == 7


def test_correct_country_is_not_flagged(tmp_path):
    o, m, z = sources(tmp_path, [airport("SEA", "US")],
                      [market("SEA", "US", 30559)])
    assert audit(o, m, [z])["country_disagreement_count"] == 0


def test_duplicate_iata_fail_closed(tmp_path):
    o, m, z = sources(tmp_path,
                      [airport("SEA", "US"), airport("SEA", "CA")],
                      [market("SEA", "US", 30559)])
    with pytest.raises(ValueError, match="Duplicated"):
        audit(o, m, [z])


def test_missing_master_source_fields_fail_closed(tmp_path):
    o, m, z = sources(tmp_path, [airport("SEA", "US")],
                      [market("SEA", "US", 30559)])
    with zipfile.ZipFile(m, "w") as archive:
        archive.writestr("T_MASTER_CORD.csv", "AIRPORT,CITY_MARKET_ID\nSEA,123\n")
    with pytest.raises(ValueError, match="schema incomplete"):
        audit(o, m, [z])
