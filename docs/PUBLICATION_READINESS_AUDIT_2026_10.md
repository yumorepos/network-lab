# Network Lab publication readiness and mapping audit (2026-10-28)

**Disposition: PARTIAL VERIFICATION, NOT A FULL ACCURACY CERTIFICATE.**
A green warehouse-free test suite is not proof that every BTS/StatCan source
record arrived, every airport has a correct historical identity, every
carrier's marketing brand is correctly allocated, or the published replay
would remain unchanged after a corrected lookup. Existing output data are
preserved and no dashboard or generated report has been hand-edited.

The audit provides two reusable scripts:
`scripts/audit_airport_join_exposure.py` and
`scripts/audit_publication_readiness.py`, each tested against negative
controls. Run from the repository root:

```bash
python -m scripts.audit_airport_join_exposure
python -m scripts.audit_publication_readiness
pytest tests/test_airport_join_exposure.py tests/test_publication_readiness_audit.py tests/test_warehouse_mapping_audit.py -q
```

## Published CSV-versus-Parquet parity now checked

October 28 [PR #11](https://github.com/yumorepos/network-lab/pull/11)
merged a warehouse-free check comparing **every field** of the three tracked
study CSV and Parquet outputs, including keysets, nulls, numeric consistency
and the generated headline counts. It passed in CI (123 passed, 141 skipped).
This closes the **committed artifact** parity sub-check, but the public app
deployment has not been independently captured and the original warehouse
has not been re-audited against source files.

The previous October 20 local-storage inventory confirms the preservation
location at `~/Projects/network-lab/data/warehouse.duckdb` on the Mac.
The read-only, private diagnostic handoff and execution procedure are now in
[LOCAL_WAREHOUSE_AUDIT_HANDOFF_2026_10.md](LOCAL_WAREHOUSE_AUDIT_HANDOFF_2026_10.md).
The runner must be executed on the Mac holding those bytes; GitHub/partial
Drive access alone cannot certify warehouse completeness.

## Additional warehouse audit (requires local source data)

The new `scripts/audit_warehouse_mapping.py` opens a built DuckDB warehouse
**read-only**. It reports ambiguous airport codes, city-market-to-CBSA
cardinality, unmatched U.S. airport codes and passenger/seat/departure exposure,
unmapped destination-metro traffic, PBI/DJT by source year, T-100 monthly
coverage and current Master Coordinate code collisions. It cannot recover
historical AirportIDs missing from the production slim T-100 Parquet.

```bash
python -m scripts.audit_warehouse_mapping --output /tmp/network_mapping_audit.json
```

The warehouse-dependent production run **has not been completed** in this
GitHub-only audit. CI exercises its SQL with a **synthetic DuckDB fixture**
that deliberately has a two-CBSA fanout, a missing PBI airport join and an
ambiguous reused SAW code, and verifies all are detected. This is evidence
that the diagnostic can catch those defect classes, **not proof** the full
warehouse lacks them. A real output is required for publication sign-off.

## A. Tracked artifacts: supported facts

| Check | Evidence | Result and meaning |
|---|---|---|
| Study CSV count, unique metro and airport per study | `screen_{westjet_yyc,alaska_sea,porter_yyz}.csv` | **200 rows** (76 + 45 + 79); no duplicated metro name or destination airport **within each study** |
| LAUNCH/MONITOR/PASS consistency | `headline_metrics.yaml`, same CSVs | WestJet **0/0/76**, Alaska **0/0/45**, Porter **1/1/77** |
| Market names for positive verdicts | Same | Porter Boston LAUNCH, Hartford MONITOR; no other positive verdict |
| Economics columns | Same | Recompute margin from BELF / load factor; prevent nonfinite, out-of-range share/load, missing numeric fields, or optimistic negative-margin verdict |
| Provenance and required fields | Same | Check every committed row for required demand method/source, driver, uncertainty and key assumptions |
| Survey anchor metadata | Same | **118 of 200** rows have no 2018 market anchor value: 52 WestJet, 45 Alaska and 21 Porter. This is not evidence of a missing ingestion: Alaska uses DB1B observed domestic O&D, and unanchored transborder markets cannot legitimately acquire a direct 2018 anchor |
| Competition completeness flag | WestJet Spokane-Spokane Valley | **1 row** has blank `top_competitor` and modeled **100%** share; `share_uncertainty=True`. It must be presented as **uncertain modeled share**, not measured market monopoly |
| Carrier-family reference | `data/reference/carrier_families.csv` | **14 operators:** 10 static single-brand mappings, 4 multi-brand per-segment mappings; check unique operator keys, nonempty evidence, and valid partner/resolution rules |
| Data output serving | `app/streamlit_app.py` | The app reads precomputed Parquet, **not** the checked CSV alone; CSV checks cannot establish Parquet-vs-CSV row-by-row identity or deployed Streamlit content |

These are **contract checks for the committed artifacts**. Passing them does
not show that rows were not previously dropped by a warehouse join. The
existing `tests/test_consistency.py` also guards selected reader-facing
headlines, but several warehouse-dependent tests skip in hosted CI.

## B. Wider mapping risks found in code

| Exposure | Root cause / vintage problem | Status |
|---|---|---|
| Airport code changes | `ingest/bts_t100.py` persists airport labels only; `warehouse/build_marts.py` builds `dim_airport` from latest IATA codes with `max(CITY_MARKET_ID)` | **Confirmed risk**, actual production effect unmeasured; see [PBI analysis](AIRPORT_IDENTITY_CONSUMER_AUDIT_2026_10.md) and [issue #7](https://github.com/yumorepos/network-lab/issues/7) |
| Airport code reuse | BTS Master Coordinate showed **18** ambiguous current three-character codes, three of which occurred in the July T-100 sample (ISL, SAW, T4X; six segment rows) | **Observed in isolated BTS research**, not yet quantified in production |
| BTS city market to Census CBSA | `warehouse/metro_map.py` uses name/token matching, manual overrides, and chooses the highest-population CBSA when candidates tie; it does not fail on all ambiguous heuristic matches | **Needs collision, coverage and counterfactual audit** on the built warehouse |
| Duplicate / renamed city market rows | Mapping source selects distinct `(CITY_MARKET_ID, DISPLAY_CITY_MARKET_NAME_FULL)`, which can hold multiple names for the same stable city-market ID; downstream joins assume one mapping per ID | **Cardinality not established** for the current raw lookup |
| Canadian airport to CMA | A hand-maintained list and prefix join is used. There is an existing explicit uniqueness assertion to prevent the historical Ottawa-Gatineau three-record defect | **Guard exists**, but full data must be rebuilt to prove current population and geographic coverage |
| Operating certificate to marketing brand | Regional operators are resolved from static reference or DB1B sold nonstop tickets; multi-brand routes can remain unresolved | **Coverage incomplete by design**; unresolved certificate does not justify guessing a brand |
| Time-varying regional contracts | The source reference notes Mesa `YV` also served American until 2023, but current `static` reference maps `YV` to United; any historical use needs a time-valid proof | **Potential vintage hazard**, not proof that the frozen backtest has a changed result |
| Source vintage and boundary | BTS T-100 is nonstop **segment** data; DB1B is ticket market **O&D**; DB1C uses a revised sample, issuer and fare definitions; StatCan transborder O&D anchors stop in 2018 | **Structural limits**, do not merge counts across grains or silently substitute newer files |
| Published report parity | `app/streamlit_app.py` reads committed Parquet; `reports/` are generator-owned | **Not audited end-to-end** by this branch; do not modify a generated report by hand |

## C. What must be checked before saying "all data is complete"

**Gate 1: source inventory and completeness.** Record actual download
manifest, BTS/StatCan publication and data vintage, source file digests,
expected years/months, rows and carrier coverage by vintage; explicitly
disclose foreign carriers withheld or revised, survey population and
Canadian domestic/2018-transborder blind spots. Missing expected months must
be categorized as not published, not in scope, failed download, or dropped at
a join. Do not use an unverified zero.

**Gate 2: historical identifier reconciliation.** For every observed T-100
airport ID and city market, measure unmatched/ambiguous mappings and fanout
by year and source. Use stable identifiers and effective dates where available.
Compare current `dim_airport` / `map_citymarket_cbsa` / `dim_metro` to
source IDs. Require uniqueness at consumer join grains and record unmapped
passengers, seats, flights and candidate exposures, **not just code counts**.

**Gate 3: brand and customer geography.** Quantify unresolved operating
carriers, verify one- versus multi-brand code and validity dates, and validate
CA CMA / US CBSA city-market keys against source geography. Use a negative
control for code reuse and ambiguous metro matches; no arbitrary
`max(CITY_MARKET_ID)` or biggest-CBSA mapping as an undocumented fix.

**Gate 4: production replay parity.** With a full archived warehouse, hold
input snapshots fixed, run `make all`, `make test` and
`make reproducibility`; compare CSV and Parquet rows, dashboard fields and
every reader-facing generated report; then rerun the proposed mapping change
side by side and report every movement. Until this is done, **no claim** about
changed or unchanged route verdicts is supported.

**Gate 5: final scope and publication sign-off.** Reconcile headline totals
and named market verdicts with `headline_metrics.yaml`, preserve the
bounded negative predictive finding and its resolution limits, make modeling
uncertainty visible, inspect deployment with current production artifacts,
and document unresolved coverage and assumptions in the portfolio case study.

## Decision

Current green tests can support: **the committed screening tables are
internally coherent and mapped fields are present, with known provenance
and documented gaps.**

They cannot support: **all official data are complete, airport and airline
brand assignments are correct for every vintage, the replay was regenerated,
or the live dashboard reports are fully independently verified.**

**Recommendation:** treat full publication certification as blocked pending
warehouse-backed join/coverage audit. This branch adds detection, documented
source risk, and negative controls only. Do not patch `models/`, `warehouse/`,
`replay/`, assumptions, existing outputs or historical documents without
a measured consumer-impact report.
