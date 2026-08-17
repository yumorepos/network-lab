"""D1 regression guards: a structural-break year may never be the endpoint of
the corridor growth ratio.

`docs/change_reports/D1_corridor_growth_vintage.md`, acceptance test A2. The
defect was not a wrong constant; it was that
`replay/vintage.py:_t100_complete_year` applied no exclusion set while every
sibling resolver in the file applied one. A test that only pinned the year at
the three approved cutoffs would pass again if the exclusion were deleted and
the cached years happened to hide it, so the tests below drive the resolver at
constructed cutoffs where the naive rule and the corrected rule disagree.

The mirror guard matters as much: seats must still admit a break year. Applying
the exclusion there would move the candidate set at 2023-01, which is a
different change from D1 and was explicitly out of scope.
"""
import pytest

from models.common import connect
from replay import snapshot as S
from replay import vintage as V

APPROVED = [202201, 202301, 202401]
# The window at 2023-01 admits 2021, which is the case that produced D1.
BREAK_CUTOFF = 202301


@pytest.fixture(scope="module")
def con():
    c = connect(read_only=True)
    yield c
    c.close()


@pytest.fixture(scope="module")
def cached(con):
    return S.cached_years(con)["t100"]


def test_structural_break_years_come_from_the_protocol_file():
    """Not a literal in the resolver. If the policy moves, the rule moves."""
    import yaml
    proto = yaml.safe_load(V.PROTOCOL_PATH.read_text())
    entry = proto["exclusions"]["structural_break_years"]
    assert set(entry["value"]) == V.structural_break_years()
    for field in ("source", "rationale"):
        assert entry.get(field), f"structural_break_years has no {field}"
    assert V.structural_break_years(), "the break set may not be empty"


def test_corridor_growth_year_is_never_a_structural_break_year(con, cached):
    """The rule, at every approved cutoff."""
    breaks = V.structural_break_years()
    for cut in APPROVED:
        v = S.resolve_vintages(cut, con)
        assert v.growth_year not in breaks, (
            f"cutoff {cut} selected corridor growth year {v.growth_year}, "
            f"which is a declared structural break {sorted(breaks)}")


def test_the_repair_actually_binds_at_the_cutoff_that_exposed_it(con, cached):
    """Without the exclusion the 2023-01 window resolves to a break year.

    This is the test that would fail if the exclusion were removed, and it
    fails for the right reason: it compares the corrected selection against the
    naive one on the same window rather than pinning a literal.
    """
    c = V.Cutoff(BREAK_CUTOFF)
    max_ym = c.t100_max_ym()
    naive = c._t100_complete_year(cached, max_ym)
    fixed = c._t100_complete_year(cached, max_ym, V.structural_break_years())
    assert naive in V.structural_break_years(), (
        f"the 2023-01 window no longer admits a break year (naive={naive}); "
        "this guard has stopped testing anything and needs a new cutoff")
    assert fixed not in V.structural_break_years()
    assert fixed < naive, "the corrected year must be earlier, not later"


def test_resolver_skips_a_break_year_at_any_constructed_cutoff(cached):
    """Drive the resolver across a decade of cutoffs, not only the approved
    three. A future protocol change that admits a new decision vintage must
    not be able to reintroduce the defect quietly."""
    breaks = V.structural_break_years()
    for ym in [y * 100 + 1 for y in range(2022, 2027)]:
        c = V.Cutoff(ym)
        y = c.t100_corridor_growth_year(cached, c.t100_max_ym())
        assert y not in breaks, f"cutoff {ym} selected break year {y}"


def test_seats_year_still_admits_a_structural_break_year(con):
    """The mirror guard. Over-applying the fix would change the candidate set,
    which the change report placed out of scope. At 2023-01 the seats vintage
    is a break year and must stay one."""
    v = S.resolve_vintages(BREAK_CUTOFF, con)
    assert v.seats_year in V.structural_break_years(), (
        f"seats year at {BREAK_CUTOFF} is {v.seats_year}; the exclusion has "
        "leaked from the growth ratio into the seat totals, which moves the "
        "candidate set")


def test_growth_and_seats_years_are_now_two_rules(con):
    """Before the repair the two shared one selection and always agreed. They
    must be able to differ, and at 2023-01 they do."""
    v = S.resolve_vintages(BREAK_CUTOFF, con)
    assert v.growth_year != v.seats_year


def test_the_corridor_growth_year_still_carries_provenance(con):
    """Milestone A finding P1-1: every vintage names the value actually used.
    The repair must not drop the record it added."""
    for cut in APPROVED:
        v = S.resolve_vintages(cut, con)
        pf = v.provenance_frame()
        rows = pf[pf["source"].str.contains("corridor growth", case=False)]
        assert len(rows) == 1, f"cutoff {cut} has {len(rows)} growth records"
        assert rows.iloc[0]["reference_period"] == str(v.growth_year)


def test_resolver_fails_closed_when_every_candidate_year_is_excluded(cached):
    """The exclusion must not silently reach past the window for a later
    year. With everything excluded the resolver raises."""
    c = V.Cutoff(202301)
    with pytest.raises(LookupError):
        c._t100_complete_year(cached, c.t100_max_ym(), set(cached))
