"""Regression tests for the three P0 defects found in the 2026-07-27 audit.

Each defect below shipped in a released version of this repo, survived a full
test suite, and changed the headline result. The tests here exist so that none
of them can come back silently. INTEGRITY_REPORT.md Round 4 records what each
one was and what it cost.

P0-1  bidirectional demand divided by one-directional departures (2x loads)
P0-2  one-stop competitors joined on operating certificate, not marketing brand
P0-3  the incumbent cross-check file was a dump of the code it was checking

Tests that need the DuckDB warehouse skip when it is absent, so CI (which never
runs `make data`) still exercises everything that reads committed artifacts.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

OUT = Path("data/parquet/outputs")
REF = Path("data/reference/incumbent_network_202604.csv")
WAREHOUSE = Path("data/warehouse.duckdb")
STUDIES = ("westjet_yyc", "alaska_sea", "porter_yyz")


def _load(name):
    p = OUT / name
    if not p.exists():
        pytest.skip(f"{name} not built yet")
    return pd.read_parquet(p)


def _con():
    if not WAREHOUSE.exists():
        pytest.skip("warehouse not built (make data)")
    from models.common import connect
    return connect(read_only=True)


# P0-1: units. demand_pax_yr is bidirectional; freq_wk is one-way from the hub.

# Ground truth, BTS T-100 segment, trailing 12 reported months to 2026-04,
# Seattle to Wichita, both directions. Reproduce with:
#   SELECT carrier, origin, dest, sum(departures), sum(passengers)
#   FROM fact_segment
#   WHERE service_class IN ('F','L') AND (year*100+month) > 202604 - 100
#     AND ((origin='SEA' AND dest='ICT') OR (origin='ICT' AND dest='SEA'))
#   GROUP BY 1,2,3
# Horizon (QX), flying as Alaska, is the only scheduled operator:
#   SEA->ICT 341 departures / 21,580 passengers
#   ICT->SEA 338 departures / 21,949 passengers
SEA_ICT_DEPS_BOTH_DIRECTIONS = 679.0
SEA_ICT_ONBOARD_PAX = 43_529.0
SEA_ICT_OBSERVED_PAX_PER_DEP = SEA_ICT_ONBOARD_PAX / SEA_ICT_DEPS_BOTH_DIRECTIONS

# BTS DB1B Market 2024, SEA-ICT city pair, both directions, all itineraries.
# This is the same quantity the demand module emits as demand_pax_yr.
SEA_ICT_OD_PAX_BIDIRECTIONAL = 45_680.0


def test_bidirectional_demand_over_both_direction_departures_matches_t100():
    """The corrected units reproduce the load Horizon actually flies; the old
    one-way denominator does not, and is wrong by very close to exactly 2x."""
    from models import economics

    freq_wk_one_way = SEA_ICT_DEPS_BOTH_DIRECTIONS / 52 / 2
    corrected = SEA_ICT_OD_PAX_BIDIRECTIONAL / (
        freq_wk_one_way * 52 * economics.DIRECTIONS_PER_ROUTE)
    shipped_before_fix = SEA_ICT_OD_PAX_BIDIRECTIONAL / (freq_wk_one_way * 52)

    # O&D and onboard are not the same quantity (onboard drops passengers who
    # connect beyond either end and adds flow connecting at SEA), so this is a
    # magnitude check, not an identity. Measured gap is +5.0%.
    assert corrected == pytest.approx(SEA_ICT_OBSERVED_PAX_PER_DEP, rel=0.10), (
        f"corrected {corrected:.1f} pax/dep vs observed "
        f"{SEA_ICT_OBSERVED_PAX_PER_DEP:.1f}")
    assert shipped_before_fix > 1.9 * SEA_ICT_OBSERVED_PAX_PER_DEP, (
        f"the one-way denominator gives {shipped_before_fix:.1f} pax/dep "
        f"against an observed {SEA_ICT_OBSERVED_PAX_PER_DEP:.1f}")


@pytest.mark.parametrize("sid", STUDIES)
def test_annual_contribution_uses_both_direction_departures(sid):
    """Pins the shipped artifact, not just the constant: reverting deps_yr to
    freq_wk * 52 breaks this."""
    eco = _load(f"economics_{sid}.parquet")
    per_dep = eco["revenue_dep"] - eco["cost_dep"]
    both = eco["freq_wk"] * 52 * 2 * per_dep
    one_way = eco["freq_wk"] * 52 * per_dep
    assert np.allclose(eco["annual_contribution"], both), (
        f"{sid}: annual_contribution does not equal "
        "freq_wk * 52 * 2 * (revenue_dep - cost_dep)")
    assert not np.allclose(eco["annual_contribution"], one_way)


def test_units_hold_against_observed_loads_across_the_alaska_network():
    """The single-route golden test above, run at network scale.

    On a route where one brand flies essentially all the departures, the local
    O&D the market generates cannot be much more than the passengers actually
    carried: total onboard is local traffic plus connecting flow, so local
    alone should sit at or below it. Under the one-way denominator, modeled
    local demand exceeded every passenger the route carried on 54% of Alaska's
    Seattle spokes, by up to 3.03x. That is not a calibration disagreement, it
    is an arithmetic impossibility, and it was visible in data the project
    already had.
    """
    con = _con()
    from models.carriers import register_segment_brands
    register_segment_brands(con, min_deps=1)
    win = con.execute("""
        SELECT max(year::INT*100+month) FROM fact_segment
        WHERE service_class IN ('F','L')
    """).fetchone()[0]
    seg = con.execute(f"""
        WITH s AS (
          SELECT s.dest, coalesce(b.brand, s.carrier) AS brand,
                 sum(s.departures) AS deps, sum(s.passengers) AS pax
          FROM fact_segment s
          LEFT JOIN map_segment_brand b
                 ON b.op_carrier = s.carrier
                AND b.origin = s.origin AND b.dest = s.dest
          WHERE s.origin = 'SEA' AND s.service_class IN ('F','L')
            AND (s.year::INT*100+s.month) > {win} - 100 AND s.departures > 0
          GROUP BY 1,2),
        tot AS (SELECT dest, sum(deps) AS all_deps FROM s GROUP BY 1)
        SELECT s.dest, s.deps, s.pax FROM s JOIN tot t USING(dest)
        WHERE s.brand = 'AS' AND s.deps / t.all_deps > 0.90 AND s.deps >= 100
    """).df()
    od = con.execute("""
        SELECT CASE WHEN origin='SEA' THEN dest ELSE origin END AS dest,
               sum(passengers_est) AS od_pax
        FROM fact_od_market
        WHERE year = 2024 AND (origin='SEA' OR dest='SEA')
        GROUP BY 1
    """).df()
    con.close()

    m = seg.merge(od, on="dest")
    assert len(m) > 30, "too few sole-operator routes to test against"
    onboard_per_dep = m["pax"] / m["deps"]
    corrected = m["od_pax"] / (m["deps"] * 2)
    one_way = m["od_pax"] / m["deps"]

    over_corrected = (corrected > onboard_per_dep).mean()
    over_one_way = (one_way > onboard_per_dep).mean()
    assert over_corrected < 0.20, (
        f"corrected units still imply more local demand than the route carries "
        f"on {100*over_corrected:.0f}% of routes")
    assert over_one_way > 2 * over_corrected, (
        "the one-way denominator is meant to be visibly worse against observed "
        "loads; if it is not, this test has stopped discriminating")


@pytest.mark.parametrize("sid", STUDIES)
def test_carried_passengers_never_exceed_bidirectional_demand(sid):
    """Dimensional sanity: boardings summed over a year's departures cannot
    exceed the market's own demand times the modeled share. The 2x error
    violated this on every row it touched."""
    eco = _load(f"economics_{sid}.parquet")
    deps_yr = eco["freq_wk"] * 52 * 2
    carried = eco["pax_per_dep"] * deps_yr
    ceiling = eco["demand_pax_yr"] * eco["proposed_share"]
    assert (carried <= ceiling + 1e-6).all(), (
        f"{sid}: {(carried > ceiling + 1e-6).sum()} rows board more passengers "
        "than the market supplies")


# P0-2: competitors are marketing brands, not operating certificates.

def _single_brand_certificates() -> dict:
    fam = pd.read_csv("data/reference/carrier_families.csv")
    fam = fam[fam["resolution"] == "static"]
    return dict(zip(fam["operating_carrier"], fam["brand_partners"]))


def test_carrier_family_reference_covers_the_known_regionals():
    m = _single_brand_certificates()
    for cert, brand in (("QX", "AS"), ("MQ", "AA"), ("OH", "AA"),
                        ("9E", "DL"), ("QK", "AC"), ("RV", "AC")):
        assert m.get(cert) == brand, f"{cert} should resolve to {brand}"


@pytest.mark.parametrize("sid", STUDIES)
def test_competition_names_brands_not_operating_certificates(sid):
    """No wholly-owned or single-partner regional may appear as a competitor.
    Before the fix `top_competitor` read MQ, YX, OH and OO on 29 of 79 Porter
    markets: those are operating certificates, not airlines a planner competes
    against."""
    comp = _load(f"competition_{sid}.parquet")
    certs = set(_single_brand_certificates())
    found = certs & set(comp["carrier"].dropna())
    assert not found, (
        f"{sid}: operating certificates surfaced as competitor brands: {found}")


def test_air_canada_is_visible_as_one_brand_at_yyz():
    """Air Canada operates YYZ under three codes (AC mainline, QK Jazz as Air
    Canada Express, RV Rouge). Split across certificates it was three small
    competitors; Porter's real incumbent is one large one."""
    comp = _load("competition_porter_yyz.parquet")
    brands = set(comp["carrier"].dropna())
    assert "AC" in brands, "Air Canada absent from the Porter competitive set"
    assert not ({"QK", "RV"} & brands), (
        "Jazz or Rouge still counted as carriers separate from Air Canada")
    ac = comp[comp["carrier"] == "AC"]
    assert ac["op_carriers"].str.contains("QK|RV", regex=True).any(), (
        "no Air Canada itinerary draws on Jazz or Rouge metal, so the brand "
        "rollup is not actually doing anything")


def test_modeled_carrier_shares_sum_to_one():
    """The invariant that exposes an operating-versus-marketing carrier error
    without needing to know the answer in advance.

    The validation compares modeled shares against DB1B, which reports the
    TICKETING carrier. If the model denominates in operating certificates it
    hands share to codes DB1B never reports, and the modeled shares for the
    carriers DB1B does report no longer sum to 1. They summed to 0.790 before
    the fix: a fifth of Seattle's traffic was credited to certificates rather
    than to the brands that sold it.
    """
    sv = _load("share_validation.parquet")
    per_market = sv.groupby("other_cm")["model_share"].sum()
    assert per_market.mean() > 0.95, (
        f"modeled shares sum to {per_market.mean():.3f} per market, so the "
        "model is attributing traffic to carriers the truth source does not "
        "report")


def test_mainline_plus_regional_onestops_are_reconstructed():
    """The defect in one sentence: a same-certificate join cannot see a
    mainline leg connecting to a regional leg, which is most of what a US
    network carrier actually sells out of a hub."""
    found = False
    for sid in STUDIES:
        comp = _load(f"competition_{sid}.parquet")
        one = comp[comp["itin_type"] == "onestop"]
        if not len(one):
            continue
        legs = one["op_carriers"].fillna("").str.split("/")
        mixed = [len(set(x[0].split("+")) ^ set(x[-1].split("+"))) > 0
                 for x in legs if len(x) == 2]
        if any(mixed):
            found = True
    assert found, ("no reconstructed one-stop connects legs flown by different "
                   "certificates under one brand")


# P0-3: the incumbent cross-check must be able to disagree with the model.

def test_incumbent_reference_declares_its_independence():
    inc = pd.read_csv(REF)
    assert "verification_source" in inc.columns, (
        "the reference file must record which source produced each row")
    us = inc[inc["study_id"] == "alaska_sea"]
    assert len(us), "no alaska_sea rows in the incumbent reference"
    assert (us["verification_source"] == "db1b_nonstop_ticket_sales").all(), (
        "the US domestic study's cross-check must come from DB1B, which is "
        "independent of T-100 in survey, grain and carrier concept")
    assert (us["independent_of_candidate_filter"] == "full").all()


def test_incumbent_reference_is_not_a_dump_of_the_candidate_filter():
    """The original file matched the candidate query on all 99 rows with a
    maximum departure delta of 0.0, so the served-market test could not fail.

    The property that guarantees a cross-check can disagree: the independent
    source must see service that the candidate filter's own view of the world
    cannot. Here that is concrete. The old view counted only segments whose
    OPERATING carrier was AS, so every metro flown by Horizon was invisible to
    it; DB1B, which records who sold the ticket, sees them.
    """
    con = _con()
    inc = pd.read_csv(REF)
    # dest_cbsa reads back as int64 from CSV; the warehouse stores CBSA codes
    # as text. Compare as text or the difference is spuriously non-empty.
    independent = set(inc[inc["study_id"] == "alaska_sea"]["dest_cbsa"]
                      .astype(str))
    win = con.execute("""
        SELECT max(year::INT*100+month) FROM fact_segment
        WHERE service_class IN ('F','L')
    """).fetchone()[0]
    # the pre-fix definition, reproduced verbatim: operating carrier only
    old_view = set(con.execute(f"""
        SELECT DISTINCT m.cbsa
        FROM fact_segment s
        JOIN dim_airport a ON a.iata_code = s.dest
        JOIN map_citymarket_cbsa m ON m.city_market_id = a.city_market_id
        WHERE s.origin = 'SEA' AND s.carrier = 'AS'
          AND s.service_class IN ('F','L') AND s.dest_country = 'US'
          AND (s.year::INT*100+s.month) > {win} - 100
        GROUP BY 1 HAVING sum(s.departures) >= 26
    """).df()["cbsa"])
    con.close()
    unseen = independent - old_view
    assert unseen, (
        "the incumbent reference finds nothing the operating-carrier view "
        "missed, which is what a circular dump looks like")


def test_regional_operated_metros_are_excluded_from_candidates():
    """El Paso, Wichita and Monterey are flown by Horizon as Alaska and DB1B
    shows Alaska selling nonstop tickets in all three. Tulsa launched in March
    2026, after the DB1B year, and is caught by the brand-aware T-100 filter
    instead. All four leaked into the Alaska candidate set before the fix."""
    scr = _load("screen_alaska_sea.parquet")
    metros = set(scr["metro_name"])
    leaked = {m for m in metros
              if m.split(",")[0] in ("El Paso", "Wichita", "Salinas", "Tulsa")}
    assert not leaked, f"Horizon-operated metros still screened as unserved: {leaked}"


def test_brand_resolution_is_corroborated_by_db1b():
    """The static tier of the family map is a claim about the world. Check it
    against data rather than trusting the citation: the permitted brand should
    actually be selling nonstop on the certificate's own segments."""
    con = _con()
    from models.carriers import segment_brands
    seg = segment_brands(con, min_deps=26)
    db = con.execute("""
        SELECT origin, dest, tk_carrier AS brand FROM fact_od_market
        WHERE year = 2024 AND coupons = 1 GROUP BY 1,2,3
    """).df()
    con.close()
    db["a"] = db[["origin", "dest"]].min(axis=1)
    db["b"] = db[["origin", "dest"]].max(axis=1)
    sells = set(map(tuple, db[["a", "b", "brand"]].drop_duplicates().values))
    all_brands = list(db["brand"].unique())

    for cert, brand in (("QX", "AS"), ("MQ", "AA"), ("9E", "DL"), ("C5", "UA")):
        s = seg[seg["op_carrier"] == cert]
        if not len(s):
            continue
        pairs = [(min(o, d), max(o, d)) for o, d in zip(s["origin"], s["dest"])]
        # only pairs DB1B sampled at all can testify either way
        covered = [p for p in pairs
                   if any((p[0], p[1], b) in sells for b in all_brands)]
        hit = sum((p[0], p[1], brand) in sells for p in covered)
        rate = hit / len(covered)
        assert rate > 0.80, (
            f"{cert} is mapped to {brand} but {brand} sells nonstop on only "
            f"{100*rate:.0f}% of {cert}'s segments")


# --------------------------------------------------------------------------
# Milestone A (PHASE_5_6_PLAN.md W1.2): the derived route-spell register must
# reproduce the hand-compiled one. The hand register is retained as the
# independent cross-check precisely so this can fail.
# --------------------------------------------------------------------------

def test_derived_route_spells_reproduce_hand_register():
    """The mechanical register must reproduce >= 90% of the hand-compiled
    launches that T-100 is capable of containing.

    Measured against rows with a US endpoint. T-100 records only segments
    touching the United States, so Canadian domestic (hard rule 5) and Canada
    to Mexico routes are excluded from the denominator rather than counted as
    failures: no extractor can recover a record that was never filed.

    The five known disagreements at 90.7% are documented in
    docs/change_reports/A2_route_spell_register.md. Four of them are errors in
    the HAND register that the derived one gets right.
    """
    from pathlib import Path
    import pytest
    if not Path("data/warehouse.duckdb").exists():
        pytest.skip("warehouse not built")
    from warehouse.route_spells import validate_against_register
    r = validate_against_register()
    assert r["reproducible_rows"] >= 50, (
        f"only {r['reproducible_rows']} reproducible register rows; the "
        "carrier-code translation or the US-endpoint filter has regressed")
    assert r["rate"] >= 0.90, (
        f"derived register reproduces only {100*r['rate']:.1f}% of the "
        f"{r['reproducible_rows']} reproducible hand-compiled launches "
        f"({r['reproduced']} of {r['reproducible_rows']}). Disagreements:\n"
        f"{r['disagreements'].to_string(index=False)}")


def test_flair_carrier_code_is_not_the_iata_code():
    """Flair files to BTS as 07Q. The IATA code F8 belongs to a different,
    defunct airline in BTS, so matching the launch register on IATA codes
    silently returns the wrong carrier. This guards the translation table."""
    from pathlib import Path
    import pandas as pd
    import pytest
    if not Path("data/warehouse.duckdb").exists():
        pytest.skip("warehouse not built")
    codes = pd.read_csv("data/reference/carrier_codes.csv").set_index(
        "register_code")["bts_carriers"]
    assert codes["F8"] == "07Q", "Flair must map to BTS code 07Q, not F8"
    from models.common import connect
    con = connect(read_only=True)
    name = con.execute(
        "SELECT carrier_name FROM dim_carrier WHERE carrier = 'F8'").fetchone()
    con.close()
    assert name and "Flair" not in name[0], (
        f"BTS code F8 now resolves to {name[0]!r}; if BTS has reassigned the "
        "code the translation table must be revisited")


# --------------------------------------------------------------------------
# Milestone A integrity: the baseline must survive a warehouse rebuild.
# Both defects found during the T-100 backfill (the Ottawa CMA prefix match and
# the CBSA-to-city-market dict) were invisible to every existing test because
# they only fire when the warehouse is rebuilt, not when models are re-run
# against a fixed one. These guard the class rather than the two instances.
# --------------------------------------------------------------------------

def test_no_ambiguous_lookup_keys_in_reference_mappings():
    """Every manual pin and prefix match used to resolve a name to a single
    row must resolve to exactly one row. Ambiguity here is silent and produces
    a plausible wrong number rather than an error."""
    from pathlib import Path
    import pytest
    if not Path("data/warehouse.duckdb").exists():
        pytest.skip("warehouse not built")
    from models.common import connect
    from warehouse.metro_map import OVERRIDES
    con = connect(read_only=True)
    metros = con.execute("SELECT cbsa, name FROM dim_metro_us").df()
    ambiguous = {k: metros[metros["name"].str.startswith(v)]["name"].tolist()
                 for k, v in OVERRIDES.items()
                 if len(metros[metros["name"].str.startswith(v)]) > 1}
    assert not ambiguous, f"ambiguous CBSA overrides: {ambiguous}"

    # Canadian CMA pins used by the transfer factor.
    from models.transfer import CA_CITY_HUB, _cma_population
    cma = dict(con.execute(
        "SELECT cma, population FROM dim_metro_ca").fetchall())
    con.close()
    for city, (key, hub) in CA_CITY_HUB.items():
        # raises on ambiguity by design
        _cma_population(cma, key)


def test_cbsa_to_city_market_is_many_to_one_and_aggregated():
    """A CBSA may contain several BTS city markets (Charlotte holds CLT and
    Concord). Demand must aggregate across them, so this asserts the fan-out is
    real and that nothing downstream collapses it to a single arbitrary row."""
    from pathlib import Path
    import pytest
    if not Path("data/warehouse.duckdb").exists():
        pytest.skip("warehouse not built")
    from models.common import connect
    con = connect(read_only=True)
    multi = con.execute("""
        SELECT count(*) FROM (
          SELECT m.cbsa FROM map_citymarket_cbsa m
          JOIN dim_airport a USING (city_market_id)
          GROUP BY 1 HAVING count(DISTINCT a.city_market_id) > 1)
    """).fetchone()[0]
    con.close()
    # If this ever becomes 0 the mapping has been flattened upstream and the
    # aggregation in models/demand.py is silently doing nothing.
    assert multi > 0, "expected multi-city-market CBSAs; mapping may be flattened"

    import pandas as pd
    dem = Path("data/parquet/outputs/demand_alaska_sea.parquet")
    if not dem.exists():
        pytest.skip("demand outputs not built yet")
    d = pd.read_parquet(dem)
    assert not d["cbsa"].duplicated().any(), (
        "demand has duplicate CBSA rows; a merge fanned out instead of "
        "aggregating")
