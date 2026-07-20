"""Reconciliation: computed totals vs published figures, differences explained.

Expected relationships are derived from definitions BEFORE comparing, and the
actual residuals are reported as computed. Nothing here tunes a tolerance to
force a pass; a failed band is reported as a failed band.

Definitional groundwork:
- T-100 counts onboard passengers per SEGMENT, once per direction.
- StatCan 23-10-0253 counts passengers ENPLANED AND DEPLANED at Canadian
  airports. A transborder passenger touches exactly one Canadian airport per
  one-way journey, so national transborder E+D should approximate T-100
  CA-US onboard passengers summed over both directions (ratio ~ 1.0).
  A Canadian DOMESTIC passenger touches two Canadian airports, so domestic
  E+D is ~2x journeys - that sector has no T-100 counterpart at all (Canadian
  domestic segments never touch the US), which is exactly the data gap this
  project's transfer-factor design works around.
- DB1B counts O&D JOURNEYS (10% sample, expanded); T-100 counts segment
  boardings. Connections put one journey on 2+ segments, so
  T-100 domestic boardings / DB1B journeys should sit around 1.1-1.5.
"""
from __future__ import annotations

import duckdb

from ingest.common import ROOT, WAREHOUSE_DB, log

OUT = ROOT / "docs" / "reconciliation.md"

AIRPORT_GEO = {
    "YYZ": "Toronto/Lester B Pearson",
    "YVR": "Vancouver International",
    "YYC": "Calgary International",
    "YUL": "Montréal/Pierre Elliott Trudeau",
}

NATIONAL_BAND = (0.85, 1.15)
AIRPORT_BAND = (0.80, 1.20)
DB1B_BAND = (1.05, 1.60)


def main() -> int:
    con = duckdb.connect(str(WAREHOUSE_DB), read_only=True)
    lines = ["# Reconciliation: computed vs published",
             "",
             "Every check states the expected relationship derived from the",
             "definitions, then reports the computed ratio as-is. Residuals",
             "outside the stated band are flagged, not massaged.",
             ""]
    flags = []

    # A. National transborder: T-100 CA-US onboard (both directions) vs
    #    StatCan 23-10-0253 'Transborder sector' E+D. Expect ~1.0.
    lines += ["## A. National transborder passengers",
              "",
              "T-100 CA-US onboard passengers (both directions, scheduled",
              "classes) vs StatCan 23-10-0253 transborder enplaned+deplaned.",
              f"Expected ratio ~1.0 (band {NATIONAL_BAND}); each transborder",
              "passenger is counted once at a Canadian airport and once on a",
              "T-100 segment.",
              "",
              "| year | T-100 CA-US pax | StatCan transborder E+D | ratio |",
              "|---|---|---|---|"]
    rows = con.execute("""
        WITH t100 AS (
          SELECT year, sum(passengers) AS pax
          FROM fact_segment
          WHERE service_class IN ('F','L')
            AND ((origin_country='CA' AND dest_country='US')
              OR (origin_country='US' AND dest_country='CA'))
          GROUP BY year
        ),
        sc AS (
          SELECT try_cast(REF_DATE AS INT) AS year,
                 try_cast(VALUE AS DOUBLE) AS ed
          FROM fact_ca_airport
          WHERE GEO='Canada'
            AND "Air passenger traffic"='Transborder sector'
        )
        SELECT t.year, t.pax, s.ed, t.pax/s.ed AS ratio
        FROM t100 t JOIN sc s USING (year)
        WHERE t.year IN (2018, 2019, 2023, 2024)
        ORDER BY t.year
    """).fetchall()
    for y, pax, ed, ratio in rows:
        ok = NATIONAL_BAND[0] <= ratio <= NATIONAL_BAND[1]
        flags.append(("national transborder " + str(y), ok, ratio))
        lines.append(f"| {y} | {pax:,.0f} | {ed:,.0f} | {ratio:.3f}"
                     f"{'' if ok else '  OUTSIDE BAND'} |")

    # B. Airport-level transborder, latest common year
    lines += ["", "## B. Airport-level transborder (2024)",
              "",
              f"Same construction per airport. Band {AIRPORT_BAND}; airport-",
              "level coverage differences (charter mix, preclearance edge",
              "cases) are wider than the national ledger.",
              "",
              "| airport | T-100 CA-US pax | StatCan transborder E+D | ratio |",
              "|---|---|---|---|"]
    for iata, geo_sub in AIRPORT_GEO.items():
        r = con.execute("""
            WITH t100 AS (
              SELECT sum(passengers) AS pax FROM fact_segment
              WHERE year=2024 AND service_class IN ('F','L')
                AND ((origin=? AND dest_country='US')
                  OR (dest=? AND origin_country='US'))
            ),
            sc AS (
              SELECT try_cast(VALUE AS DOUBLE) AS ed FROM fact_ca_airport
              WHERE REF_DATE='2024' AND GEO LIKE '%' || ? || '%'
                AND "Air passenger traffic"='Transborder sector'
            )
            SELECT t100.pax, sc.ed, t100.pax/sc.ed FROM t100, sc
        """, [iata, iata, geo_sub]).fetchone()
        if r and r[0] and r[1]:
            pax, ed, ratio = r
            ok = AIRPORT_BAND[0] <= ratio <= AIRPORT_BAND[1]
            flags.append((f"airport transborder {iata}", ok, ratio))
            lines.append(f"| {iata} | {pax:,.0f} | {ed:,.0f} | {ratio:.3f}"
                         f"{'' if ok else '  OUTSIDE BAND'} |")

    # C. DB1B journeys vs T-100 domestic boardings
    have = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
    if "fact_od_market" in have:
        lines += ["", "## C. DB1B journeys vs T-100 US domestic boardings",
                  "",
                  "T-100 domestic boardings divided by DB1B expanded O&D",
                  f"journeys. Expected {DB1B_BAND} (connections put one",
                  "journey on more than one segment; DB1B excludes bulk/",
                  "abnormal fares filtered at ingest).",
                  "",
                  "| year | T-100 dom boardings | DB1B journeys x10 | ratio |",
                  "|---|---|---|---|"]
        rows = con.execute("""
            WITH t AS (
              SELECT year, sum(passengers) AS pax FROM fact_segment
              WHERE origin_country='US' AND dest_country='US'
                AND service_class IN ('F','L')
              GROUP BY year
            ),
            d AS (   -- only years where all 4 DB1B quarters are published;
                     -- a full T-100 year vs a partial DB1B year is a units
                     -- mismatch, not a residual
              SELECT year, sum(passengers_est) AS j
              FROM fact_od_market
              GROUP BY year
              HAVING count(DISTINCT quarter) = 4
            )
            SELECT t.year, t.pax, d.j, t.pax/d.j
            FROM t JOIN d USING (year) ORDER BY year
        """).fetchall()
        for y, pax, j, ratio in rows:
            ok = DB1B_BAND[0] <= ratio <= DB1B_BAND[1]
            flags.append((f"db1b vs t100 {y}", ok, ratio))
            lines.append(f"| {y} | {pax:,.0f} | {j:,.0f} | {ratio:.3f}"
                         f"{'' if ok else '  OUTSIDE BAND'} |")

    # D. Written note on the domestic sector gap
    lines += ["", "## D. The Canadian domestic gap, stated plainly",
              "",
              "StatCan reports Canadian domestic E+D (about 2x journeys by",
              "construction). T-100 contains no Canadian domestic segments,",
              "DB1B contains no Canadian fares, and the StatCan domestic O&D",
              "program is discontinued. There is no public demand truth for",
              "Canadian domestic markets; this project's evidentiary reach is",
              "therefore transborder (for Canadian hubs) and full domestic",
              "(for US hubs), and Canadian domestic is out of scope by",
              "design rather than by omission.", ""]

    bad = [f for f in flags if not f[1]]
    lines += ["## Result summary", "",
              f"{len(flags) - len(bad)}/{len(flags)} checks inside their "
              f"stated bands."]
    if bad:
        lines += ["", "Outside band (reported, not adjusted):"]
        lines += [f"- {n}: ratio {r:.3f}" for n, _, r in bad]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    log(f"reconciliation written to {OUT}; "
        f"{len(flags) - len(bad)}/{len(flags)} in band")
    for n, ok, r in flags:
        log(f"  {'PASS ' if ok else 'FLAG '} {n}: {r:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
