"""Tests for the source-only CBSA preflight. No real warehouse or source download."""
from __future__ import annotations

from scripts.audit_metro_source_preflight import choose, examine, overrides_from_source


def metro(cbsa, name, pop):
    return {"cbsa": cbsa, "name": name, "population": pop}


def test_ambiguous_greenville_source_chooses_population_but_discloses_alternative():
    candidates = [metro("24860", "Greenville-Anderson-Greer, SC", 996680),
                  metro("43900", "Spartanburg, SC", 395934)]
    status, hits, chosen = choose("Greenville/Spartanburg, SC", candidates, {})
    assert status == "ambiguous_population_choice"
    assert len(hits) == 2
    assert chosen["cbsa"] == "24860"


def test_legacy_explicit_override_has_priority():
    rows = [metro("39580", "Raleigh-Cary, NC", 200),
            metro("20500", "Durham-Chapel Hill, NC", 300)]
    status, hits, chosen = choose(
        "Raleigh/Durham, NC", rows,
        {"Raleigh/Durham, NC": "Raleigh-Cary"})
    assert status == "override"
    assert chosen["cbsa"] == "39580"


def test_prefix_override_ambiguity_is_not_silently_selected():
    rows = [metro("1", "Foo-Bar, SC", 10), metro("2", "Foo-Baz, SC", 20)]
    status, hits, chosen = choose("Foo City, SC", rows,
                                  {"Foo City, SC": "Foo-"})
    assert status == "ambiguous_override"
    assert chosen is None
    assert len(hits) == 2


def test_missing_override_is_flagged_not_imputed():
    status, hits, chosen = choose("Aspen, CO",
                                  [metro("3", "Glenville, CO", 10)],
                                  {"Aspen, CO": "Glenwood Springs"})
    assert status == "missing_override"
    assert hits == [] and chosen is None


def test_equal_population_cannot_be_assigned_by_row_order():
    rows = [metro("1", "Midland, TX", 10), metro("2", "Odessa, TX", 10)]
    status, hits, chosen = choose("Midland/Odessa, TX", rows, {})
    assert status == "population_tie"
    assert chosen is None


def test_source_id_multi_name_and_collisions_reported():
    lookups = [{"city_market_id": 1, "name": "Greenville/Spartanburg, SC",
                "country": "US", "latest": True},
               {"city_market_id": 1, "name": "Greenville, SC",
                "country": "US", "latest": True},
               {"city_market_id": 3, "name": "Toronto, ON",
                "country": "CA", "latest": True}]
    rows = [metro("24860", "Greenville-Anderson-Greer, SC", 996680),
            metro("43900", "Spartanburg, SC", 395934)]
    result = examine(lookups, rows, {})
    assert result["unique_source_city_market_ids"] == 1
    assert len(result["source_id_multiple_names"]) == 1
    assert any(c["status"] == "ambiguous_population_choice"
               for c in result["ambiguous_or_override_cases"])
    assert result["production_verdict_change_verified"] is False


def test_override_dictionary_read_as_literal_without_executing_file(tmp_path):
    src = tmp_path / "metro_map.py"
    src.write_text("OVERRIDES = {'Aspen, CO': 'Glenwood Springs'}\n"
                   "raise RuntimeError('must not execute')\n")
    assert overrides_from_source(src) == {"Aspen, CO": "Glenwood Springs"}
