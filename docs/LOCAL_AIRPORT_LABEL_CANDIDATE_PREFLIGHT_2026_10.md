# Local Mac: verify deterministic airport-label repair without rebuilding DuckDB

**Scope:** read-only preflight against the original preserved `warehouse.duckdb` plus the **same** archived `master_coord.parquet` used by that warehouse. The tool does *not* modify either source, build a second warehouse, recompute historical decisions, or declare a full model parity certificate.

## Verified input evidence (user-provided 2026-10-29 audit ZIP)

- Actual `dim_airport`: **8,802** airport-code rows, no duplicate codes.
- **10 stored CityMarketID / display-name mismatches**: BAT, BDN, BGN, ISL, KMC, LAC, LOM, NEU, SAW and TIC. Every stored CityMarketID matches **exactly one** archived Master Coordinate display name under the **same code and ID**.
- Three Mac published `screen_*.csv` SHA-256s match the previously independently recovered archived CSVs byte for byte; together they contain **200** rows.
- Actual Mac table counts: `fact_segment` **13,630,379**, `fact_od_market` **173,741,663**; original Mac warehouse 5,192,560,640 bytes. The *full* source-fixed model and 463 historical replay decisions have not been rerun.

## What the new preflight does

`scripts/audit_airport_label_candidate.py` opens the original database using `duckdb.connect(..., read_only=True)`; it executes a single SELECT query over `dim_airport` and the archived Master Coordinate Parquet. Its window ordering is the **identical candidate selection proposed in [draft PR #28](https://github.com/yumorepos/network-lab/pull/28)**:

```sql
ROW_NUMBER() OVER (
  PARTITION BY AIRPORT
  ORDER BY CITY_MARKET_ID DESC NULLS LAST,
           DISPLAY_CITY_MARKET_NAME_FULL ASC NULLS LAST,
           AIRPORT_ID DESC NULLS LAST
)
```

It compares the candidate *ID and name* with **every** original stored airport, checks the prior 10 confirmed names (unexpected additions or omissions are flagged), checks duplicate IATA keys and missing source IDs, fingerprints the local three screen CSVs and checks all 200 published row counts and direct affected destination codes. It writes a small `candidate_label_audit.json`, `candidate_label_changes.csv` and `README.md` in a **new Desktop output folder**. Tests include actual in-memory DuckDB/Parquet query execution and negative controls for changed numeric IDs, unexpected labels, direct candidate airports, duplicated source codes and absent screen files.

## Run against original local warehouse

```bash
cd "$HOME/Desktop/network-lab-audit-runner"
"$HOME/Projects/network-lab/.venv/bin/python" -m scripts.audit_airport_label_candidate \
  --root "$HOME/Projects/network-lab"
```

The review code must be **current main** (this script only exists after PR is merged). Use a **separate Desktop code clone**, never pull/rebase or rebuild your original `~/Projects/network-lab`.

## Interpreting the result

- `PASS_DIMENSION_PROJECTION`: exactly 8,802 codes were projected, **zero numeric CityMarketID changes**, the 10 previously measured labels are the only proposed display-name changes, and the original CSV inventory has 200 records with no directly mislabeled destination codes. This is a **narrow dimension-projection gate only**.
- `REVIEW_REQUIRED`: numeric IDs would move, expected labels are not matched, an unexpected name changes, screen files are missing, or duplicate code/airport issues appear. **Do not rebuild** before investigating.

Even after a dimension pass, actual production adoption requires an **isolated candidate build** plus downstream consumer checks and fixed-snapshot **200-screen/463-replay** parity. The output of this script **does not certify** those steps. Original database should remain untouched. Keep [issue #7](https://github.com/yumorepos/network-lab/issues/7) open; [draft PR #28](https://github.com/yumorepos/network-lab/pull/28) remains unmerged until the candidate evidence is reviewed.
