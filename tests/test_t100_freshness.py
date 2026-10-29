"""Read-only monthly coverage policy and parser controls."""
import csv
import io
import zipfile
import pytest
from scripts.audit_t100_freshness import observed_months, freshness_gate


def make_zip(path, rows):
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=["YEAR", "MONTH"])
    writer.writeheader()
    writer.writerows(rows)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("T_T100_SEGMENT_ALL_CARRIER.csv", stream.getvalue())


def test_stale_part_year_fails_closed(tmp_path):
    path = tmp_path / "t100_2026.zip"
    make_zip(path, [{"YEAR": 2026, "MONTH": m} for m in range(1, 5)])
    result = freshness_gate(observed_months(path, 2026), 7)
    assert result["missing_published_months"] == [5, 6, 7]
    assert result["safe_to_treat_cached_year_as_complete"] is False


def test_complete_scope_passes_only_coverage(tmp_path):
    path = tmp_path / "t100_2026.zip"
    make_zip(path, [{"YEAR": 2026, "MONTH": m} for m in range(1, 8)])
    result = freshness_gate(observed_months(path, 2026), 7)
    assert result["safe_to_treat_cached_year_as_complete"] is True
    assert "contents" in result["recommendation"]


def test_wrong_year_rejected(tmp_path):
    path = tmp_path / "t100_2026.zip"
    make_zip(path, [{"YEAR": 2025, "MONTH": 1}])
    with pytest.raises(ValueError, match="Unexpected"):
        observed_months(path, 2026)


def test_missing_member_rejected(tmp_path):
    path = tmp_path / "t100_2026.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("other.csv", "x\n")
    with pytest.raises(ValueError, match="missing"):
        observed_months(path, 2026)


def test_bad_published_month_rejected():
    with pytest.raises(ValueError, match="1..12"):
        freshness_gate({"observed_months": []}, 13)
