"""Historical execution coverage for the snapshot(t) chain.

`tests/test_replay_leakage.py` guards the vintage RESOLVERS, and
`tests/test_replay_parity.py` pins the chain to PRODUCTION vintages. Between
them they left a gap the Milestone A independent review found by mutation
(docs/MILESTONE_A_INDEPENDENT_REVIEW.md, addendum A.2): a hard failure placed in
the historical branch of `build_transfer` left all 94 tests passing. The leakage
suite calls `build_candidates` and nothing else, and the parity suite takes the
`v.label == "production"` early return at `replay/snapshot.py:199`, so it never
reaches the historical branch at all.

Five of the six build layers therefore had no historical execution coverage, and
the two vintage paths with the largest numeric leverage, the corridor growth year
and the fuel `as_of`, carried no guard because nothing ran them. A guard on a
path no test executes cannot fire. That is finding P1-1.

This file closes it. It executes the whole chain at the approved historical
cells and asserts invariants about what each layer read: that the layer ran, that
the vintage it selected is legal for the cutoff, and that the vintage was
actually passed through rather than defaulted. It deliberately does not assert
today's output values. Production equivalence is the parity suite's job and the
frozen numbers live in docs/W1.4_predictive_baseline_v2.md; a golden test here
would freeze the very numbers Milestone B is meant to move.

Both mutations from the review were re-run against this file and both fail it:

    build_transfer growth year taken from the panel end (2025 instead of 2021)
        -> test_corridor_growth_year_is_a_complete_year_within_the_t100_window
        -> test_corridor_growth_year_is_the_latest_permitted_complete_year
    build_economics calling fuel_price_base(con, None)
        -> test_fuel_price_is_requested_at_the_cutoff_vintage
"""
from __future__ import annotations

import pytest

from models.common import connect
from models.economics import fuel_price_base
from replay import snapshot as S

CUTOFFS = [202201, 202301, 202401]

# The chain in call order. `build_screen` takes no vintage, but it turns
# economics into verdicts and was equally unexecuted at a historical cutoff.
LAYERS = ("build_candidates", "build_transfer", "build_demand",
          "build_share", "build_economics", "build_screen")

# westjet_yyc is the only FULL feasibility cell and is the study that exercises
# the transborder anchor and corridor-growth path. porter_yyz at 2024-01 adds
# the second hub (YYZ, the other corridor-growth key) and is the only other
# approved historical cell that yields candidates.
CASES = [("westjet_yyc", c) for c in CUTOFFS] + [("porter_yyz", 202401)]


@pytest.fixture(scope="module")
def con():
    c = connect(read_only=True)
    yield c
    c.close()


@pytest.fixture(scope="module")
def run():
    """Execute the full chain at every approved historical cell.

    Records which layers actually ran and what `as_of` each `fuel_price_base`
    call received, so a layer that is skipped or a vintage that is defaulted
    away is observable rather than invisible.
    """
    ran: dict[tuple, list[str]] = {}
    fuel_seen: dict[tuple, list] = {}
    originals = {n: getattr(S, n) for n in LAYERS}
    original_fuel = S.fuel_price_base
    current: dict = {}

    def wrap_layer(name, fn):
        def inner(*args, **kwargs):
            ran.setdefault(current["case"], []).append(name)
            return fn(*args, **kwargs)
        return inner

    def wrap_fuel(connection, as_of=None):
        fuel_seen.setdefault(current["case"], []).append(as_of)
        return original_fuel(connection, as_of)

    for name, fn in originals.items():
        setattr(S, name, wrap_layer(name, fn))
    S.fuel_price_base = wrap_fuel
    connection = connect(read_only=True)
    try:
        snaps = {}
        for study_id, cutoff in CASES:
            current["case"] = (study_id, cutoff)
            snaps[current["case"]] = S.snapshot(study_id, cutoff, connection)
    finally:
        for name, fn in originals.items():
            setattr(S, name, fn)
        S.fuel_price_base = original_fuel
        connection.close()
    return snaps, ran, fuel_seen


# --------------------------------------------------------- layer execution
def test_every_build_layer_executes_at_every_historical_cutoff(run):
    """The P1-1 closer.

    Demonstrated to fail by inserting `raise AssertionError` at the top of any
    historical layer, which before this file left all 94 tests green.
    """
    _, ran, _ = run
    missing = {}
    for case in CASES:
        executed = set(ran.get(case, []))
        gap = [layer for layer in LAYERS if layer not in executed]
        if gap:
            missing[f"{case[0]}@{case[1]}"] = gap
    assert not missing, (
        "historical layers never executed: " + repr(missing)
        + ". A guard on an unexecuted path cannot fire.")


@pytest.mark.parametrize("study_id,cutoff", CASES)
def test_the_historical_chain_yields_a_verdict_for_every_candidate(
        run, study_id, cutoff):
    """End to end, not layer by layer: candidates in, verdicts out."""
    snaps, _, _ = run
    r = snaps[(study_id, cutoff)]
    assert len(r["candidates"]) > 0, f"{study_id}@{cutoff}: no candidates"
    assert set(r["screen"]["cbsa"]) == set(r["candidates"]["cbsa"]), (
        f"{study_id}@{cutoff}: screen and candidate sets differ")
    assert r["screen"]["verdict"].notna().all()


# ------------------------------------------------------- corridor growth year
@pytest.mark.parametrize("study_id,cutoff", CASES)
def test_corridor_growth_year_is_a_complete_year_within_the_t100_window(
        run, study_id, cutoff):
    """The corridor growth ratio is the largest single lever on transborder
    demand, and its source year must be a complete year the T-100 window
    permits.

    Demonstrated to fail by deriving the year from the panel end
    (`max(year::INT*100+month) FROM fact_segment`, 2026-04), which selects 2025
    at every cutoff and multiplies 2023-01 demand by 5.73 at YYC.
    """
    snaps, _, _ = run
    r = snaps[(study_id, cutoff)]
    v, growth_year = r["vintages"], r["transfer"]["growth_year"]
    assert growth_year * 100 + 12 <= v.t100_max_ym, (
        f"{study_id}@{cutoff}: corridor growth year {growth_year} is not "
        f"complete within the permitted T-100 window {v.t100_max_ym}")
    assert growth_year < cutoff // 100, (
        f"{study_id}@{cutoff}: corridor growth year {growth_year} is not "
        f"strictly before the decision year")


@pytest.mark.parametrize("study_id,cutoff", CASES)
def test_corridor_growth_year_is_the_latest_permitted_complete_year(
        run, con, study_id, cutoff):
    """Bounding the year from above is not enough: silently reaching further
    back would change the demand level just as much, in the other direction."""
    snaps, _, _ = run
    r = snaps[(study_id, cutoff)]
    v = r["vintages"]
    want = max(y for y in S.cached_years(con)["t100"]
               if y * 100 + 12 <= v.t100_max_ym)
    assert r["transfer"]["growth_year"] == want, (
        f"{study_id}@{cutoff}: corridor growth year "
        f"{r['transfer']['growth_year']}, latest permitted complete year {want}")


@pytest.mark.parametrize("study_id,cutoff", CASES)
def test_corridor_growth_is_applied_from_the_hub_of_the_study(
        run, study_id, cutoff):
    """The growth map is keyed by hub. A missing hub key silently falls back to
    1.0 in `build_demand`, which is a different defect with the same shape."""
    snaps, _, _ = run
    r = snaps[(study_id, cutoff)]
    from models.common import study as study_cfg
    hub = study_cfg(study_id)["hub"]
    growth = r["transfer"]["growth_t100"]
    assert hub in growth and growth[hub], (
        f"{study_id}@{cutoff}: no corridor growth for hub {hub}; "
        f"build_demand would silently use 1.0")


# ------------------------------------------------------------- fuel vintage
@pytest.mark.parametrize("study_id,cutoff", CASES)
def test_fuel_price_is_requested_at_the_cutoff_vintage(
        run, study_id, cutoff):
    """`fuel_price_base` defaults to the current price when `as_of` is None, so
    the vintage must be passed explicitly on every historical call.

    Demonstrated to fail by calling `fuel_price_base(con, None)` in
    `build_economics`, which moves the 2022-01 price by +43.0%.
    """
    snaps, _, fuel_seen = run
    v = snaps[(study_id, cutoff)]["vintages"]
    seen = fuel_seen.get((study_id, cutoff), [])
    assert seen, (
        f"{study_id}@{cutoff}: build_economics never called fuel_price_base")
    assert all(a is not None for a in seen), (
        f"{study_id}@{cutoff}: fuel price requested with as_of=None, which "
        f"returns the current price regardless of the decision date")
    assert all(a == v.fuel_as_of for a in seen), (
        f"{study_id}@{cutoff}: fuel as_of {set(seen)}, expected "
        f"{v.fuel_as_of}")


def test_the_vintaged_fuel_price_is_materially_different_from_production(con):
    """Why the guard above matters. If the EIA series were flat the leak would
    be harmless; it is not. 2022-01 is the widest of the three cutoffs.

    Deliberately a loose threshold on the SERIES, not an assertion on today's
    model outputs.
    """
    v = S.resolve_vintages(202201, con)
    at_cutoff = fuel_price_base(con, v.fuel_as_of)
    production = fuel_price_base(con, None)
    rel = abs(production - at_cutoff) / at_cutoff
    assert rel > 0.10, (
        f"vintaged fuel {at_cutoff:.4f} vs production {production:.4f} "
        f"({100 * rel:.1f}%): if this ever falls below 10% the fuel-vintage "
        f"guard has stopped being load bearing and should be re-justified")


# --------------------------------------------------------- cutoff legality
@pytest.mark.parametrize("study_id,cutoff", CASES)
def test_no_layer_reads_a_vintage_at_or_after_the_cutoff(
        run, study_id, cutoff):
    """One place a reader can see every vintage the executed chain used."""
    snaps, _, _ = run
    r = snaps[(study_id, cutoff)]
    v, tf = r["vintages"], r["transfer"]
    assert v.t100_max_ym < cutoff
    assert v.seats_year * 100 + 12 <= v.t100_max_ym
    assert tf["growth_year"] * 100 + 12 <= v.t100_max_ym
    assert tf["anchor_year"] * 100 + 12 < cutoff
    assert v.db1b_year * 100 + 12 < cutoff
    assert v.form41_year * 100 + 12 < cutoff
    assert v.fuel_as_of == f"{cutoff // 100}-{cutoff % 100:02d}-01"
    lo, hi = S.GRAVITY_WINDOWS[v.gravity_vintage]
    assert hi * 100 + 12 < cutoff, (
        f"{study_id}@{cutoff}: gravity vintage {v.gravity_vintage} "
        f"calibrated through {hi}, which is not before the cutoff")
