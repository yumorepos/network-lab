"""Map BTS city markets to Census CBSAs.

DB1B demand lives at city-market granularity ("Seattle, WA", id 30559); metro
demographics live at CBSA granularity ("Seattle-Tacoma-Bellevue, WA"). The
join is name-based: a city market matches a CBSA when one of its city tokens
equals one of the CBSA's principal-city tokens and the state matches. Ties go
to the larger CBSA. A handful of known mismatches are pinned manually.
Unmatched city markets that actually carry traffic are logged loudly - silent
mapping loss would bias the gravity calibration toward well-named metros.
"""
from __future__ import annotations

import re

import duckdb
import pandas as pd

from ingest.common import DATA_PARQUET, WAREHOUSE_DB, log

# city_market_name -> CBSA title prefix (unambiguous manual pins)
OVERRIDES = {
    "New York City, NY (Metropolitan Area)": "New York-Newark-Jersey City",
    "Washington, DC (Metropolitan Area)": "Washington-Arlington-Alexandria",
    "Norfolk, VA (Metropolitan Area)": "Virginia Beach-Chesapeake-Norfolk",
    "Raleigh/Durham, NC": "Raleigh-Cary",
    "West Palm Beach/Palm Beach, FL": "Miami-Fort Lauderdale-West Palm Beach",
    "Sarasota/Bradenton, FL": "North Port-Bradenton-Sarasota",
    "Greensboro/High Point, NC": "Greensboro-High Point",
    "Bloomington/Normal, IL": "Bloomington",
    "Champaign/Urbana, IL": "Champaign-Urbana",
    "Dallas/Fort Worth, TX": "Dallas-Fort Worth",
    "Houston, TX": "Houston",
    "Minneapolis/St. Paul, MN": "Minneapolis-St. Paul",
    "Honolulu, HI": "Urban Honolulu",
    "Palm Springs, CA": "Riverside-San Bernardino-Ontario",
    "Louisville, KY": "Louisville/Jefferson County",
    "Boise, ID": "Boise City",
    "Valparaiso, FL": "Crestview-Fort Walton Beach-Destin",
    "Quad Cities, IL (Metropolitan Area)": "Davenport-Moline-Rock Island",
    "Bristol/Johnson City/Kingsport, TN": "Kingsport-Bristol",
    "Ithaca/Cortland, NY": "Ithaca",
    "Saginaw/Bay City/Midland, MI": "Saginaw",
    "Kona, HI": "Hilo",                      # Hawaii County micro CBSA
    "Lihue, HI": "Kapaa",                    # Kauai County micro CBSA
    "Everett, WA": "Seattle-Tacoma-Bellevue",  # Snohomish County
    "Aspen, CO": "Glenwood Springs",
    "Eagle, CO": "Edwards",
    "Belleville, IL": "St. Louis",
    "Hattiesburg/Laurel, MS": "Hattiesburg",
}


def _city_tokens(cm_name: str) -> tuple[list[str], str]:
    name = re.sub(r"\s*\(Metropolitan Area\)", "", cm_name).strip()
    if "," not in name:
        return [name.lower()], ""
    city, state = name.rsplit(",", 1)
    return [t.strip().lower() for t in city.split("/")], state.strip()


def _cbsa_tokens(title: str) -> tuple[list[str], list[str]]:
    if "," not in title:
        return [title.lower()], []
    cities, states = title.rsplit(",", 1)
    return ([t.strip().lower() for t in cities.split("-")],
            [s.strip() for s in states.split("-")])


def build_map(con: duckdb.DuckDBPyConnection) -> None:
    cms = con.execute("""
        SELECT DISTINCT CITY_MARKET_ID AS city_market_id,
               DISPLAY_CITY_MARKET_NAME_FULL AS cm_name
        FROM read_parquet(?)
        WHERE AIRPORT_COUNTRY_CODE_ISO = 'US'
          AND (AIRPORT_IS_LATEST = 'true' OR AIRPORT_IS_LATEST = '1')
    """, [str(DATA_PARQUET / "lookups" / "master_coord.parquet")]).df()
    metros = con.execute("SELECT cbsa, name, population FROM dim_metro_us").df()
    metros[["mtokens", "mstates"]] = metros["name"].apply(
        lambda t: pd.Series(_cbsa_tokens(t), index=["mtokens", "mstates"]))

    rows = []
    for _, cm in cms.iterrows():
        name = cm["cm_name"]
        if name in OVERRIDES:
            hit = metros[metros["name"].str.startswith(OVERRIDES[name])]
            if len(hit):
                rows.append((cm["city_market_id"], name,
                             hit.iloc[0]["cbsa"], hit.iloc[0]["name"], "override"))
                continue
        tokens, state = _city_tokens(name)
        cand = metros[metros.apply(
            lambda m: (not state or state in m["mstates"])
            and any(t in m["mtokens"] for t in tokens), axis=1)]
        if len(cand):
            best = cand.sort_values("population", ascending=False).iloc[0]
            rows.append((cm["city_market_id"], name, best["cbsa"],
                         best["name"], "token"))
    mapped = pd.DataFrame(rows, columns=[
        "city_market_id", "cm_name", "cbsa", "cbsa_name", "method"])
    mapped["city_market_id"] = mapped["city_market_id"].astype("int64")
    con.register("mapped_df", mapped)
    con.execute("CREATE OR REPLACE TABLE map_citymarket_cbsa AS "
                "SELECT * FROM mapped_df")

    # visibility: unmatched city markets that carry current scheduled traffic
    unmatched = con.execute("""
        WITH traffic AS (
          SELECT a.city_market_id, sum(s.passengers) AS pax
          FROM fact_segment s
          JOIN dim_airport a ON a.iata_code = s.origin
          WHERE s.year >= 2023 AND s.origin_country = 'US'
            AND s.service_class IN ('F','L')
          GROUP BY 1
        )
        SELECT t.city_market_id, any_value(a.city_market_name) AS name,
               sum(t.pax) AS pax
        FROM traffic t
        JOIN dim_airport a USING (city_market_id)
        LEFT JOIN map_citymarket_cbsa m USING (city_market_id)
        WHERE m.city_market_id IS NULL
        GROUP BY 1 ORDER BY pax DESC LIMIT 25
    """).df()
    log(f"city market -> CBSA: {len(mapped)} mapped")
    if len(unmatched):
        log("UNMATCHED city markets with traffic (top):")
        for _, r in unmatched.head(12).iterrows():
            log(f"  {r['city_market_id']} {r['name']}: {int(r['pax']):,} pax")


if __name__ == "__main__":
    con = duckdb.connect(str(WAREHOUSE_DB))
    build_map(con)
