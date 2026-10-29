# T-100 partial-year cache freshness gate (2026-10-29)

**Mode:** read-only, research-only; no overwrite of `data/parquet/`, no network access, no live warehouse.

The existing `ingest/bts_t100.py` caches every `t100_{year}.parquet` indefinitely if it exists; it does not compare the cached source's observed last month with the published release. For the preserved `t100_2026.zip`, the latest month is April 2026. The official TranStats release log documented July 2026 available by October 29, 2026. This creates a known staleness risk on a production refresh, *not* an invalid historical decision-date snapshot.

To check explicitly after consulting the authoritative release log:

```bash
python -m pytest tests/test_t100_freshness.py -q
python -m scripts.audit_t100_freshness --archive '/path/to/t100_2026.zip' --expected-year 2026 --published-through-month 7
```

The script is a fail-closed gate: returns process code 2 if any month in January through the specified official cutoff is missing, emits JSON to standard output, never assumes the newest year is complete, and never fetches or edits sources. Synthetic controls check missing months, wrong year, wrong member, invalid published cutoff and a complete scoped sample.

Observed on archived 2026 ZIP: January 48,143 source rows; February 45,006; March 48,967; April 46,134; source total 188,250. The gate reports **May, June, July missing**, and `safe_to_treat_cached_year_as_complete=false`.

**Do not automatically refresh frozen files.** The next production change should add an explicit research/source-vintage manifest (release timestamp, year/month coverage, SHA-256, extraction fields, publication cutoff); isolate a candidate refresh, require source ID fields and new source contract checks, and run source-fixed comparison before any `data/parquet` or historical replay replacement.

Published source: [BTS TranStats release log](https://www.transtats.bts.gov/releaseinfo.asp). See [issue #7](https://github.com/yumorepos/network-lab/issues/7) for identity provenance and [publication audit](PUBLICATION_READINESS_AUDIT_2026_10.md) for unresolved full-warehouse checks.
