# Preserved Network Lab warehouse: private, read-only verification handoff

**Date:** 2026-10-28
**Status:** A runner and synthetic controls are available. **The 4.836 GiB
warehouse has not been opened from this ChatGPT session.** Do not certify raw
source completeness, geography/brand coverage, replay parity or changed route
verdicts until the original Mac warehouse returns measured results.

## Where the data actually are

The user's October 20 local project inventory reports:

| Preserved original | Size in source inventory |
|---|---:|
| `~/Projects/network-lab/data/warehouse.duckdb` | **4.836 GiB** |
| `~/Projects/network-lab/data/raw/` | **2.758 GiB** |
| `~/Projects/network-lab/data/parquet/` | **1.064 GiB** |

The inventory recorded filenames and sizes, **not** full byte hashes or
current access. The connected Google Drive upload was interrupted and lacks
several important source/data files. On October 28, the Drive connector could
not retrieve the previously known Projects folder. GitHub intentionally
does not contain the full warehouse and large source files. No source bytes
from the Mac have been accessed in this review.

## Safe execution on the Mac (does not update your original repository)

Run the following in Terminal **on the Mac with the preserved files**.
Review the commands before running. This creates a separate small code clone
on the Desktop but does not modify `~/Projects/network-lab`:

```bash
cd "$HOME/Desktop"
git clone https://github.com/yumorepos/network-lab.git network-lab-audit-runner
cd network-lab-audit-runner
"$HOME/Projects/network-lab/.venv/bin/python" -m scripts.audit_preserved_warehouse \
  --root "$HOME/Projects/network-lab"
```

If a `network-lab-audit-runner` folder already exists, choose a new name
rather than overwriting it. If the original virtual environment is absent,
create a new venv **in the separate runner directory**, install requirements
there, then use that interpreter; do not rebuild source data. Keep any
existing project-level Git changes and historical `data/` intact.

The runner opens `warehouse.duckdb` with `read_only=True`, runs only
SELECT diagnostics, never executes `make data`, `make all`, or
`make reproducibility`, and does **not** upload the database. It writes
exactly two small files to a new `~/Desktop/NetworkLab-Audit-*` folder:

- `audit_summary.md`: readable scope, inventory, join and coverage results.
- `audit_diagnostics.json`: the measured values, anomalies and important
  verification flags, suitable for uploading privately to this conversation.

**Privacy:** the JSON contains project aggregate traffic and airport codes,
not individual passenger bookings. Review it before sharing. Never upload
the warehouse, private raw ZIPs or unpublished files to public GitHub.

## What the report can and cannot prove

Reports rows and metadata from the actual preserved warehouse, T-100 by-month
coverage, unresolved airport-code endpoint joins, CBSA fanout, current
Master Coordinate code ambiguity, PBI/DJT source-year exposure, and local
raw/Parquet file counts/sizes. It inventories table counts and fingerprints
only small, tracked public output artifacts.

It does **not** prove that every official BTS/StatCan extract was downloaded,
recreate vanished stable AirportIDs from code-only rows, certify historical
regional-airline marketing brands, rerun the frozen model, or measure a
counterfactual route verdict delta. A zero anomaly count cannot replace
independent external source-vintage checks.

After retrieving `audit_diagnostics.json`, review:
1. Missing months and expected source-vintage coverage.
2. Ambiguous CBSA and Canadian CMA mappings, unmatched endpoint passenger
   legs, and PBI/DJT by year.
3. Carrier-brand resolution and time-dependent codes.
4. Snapshot-fixed reproducibility, regenerated report/dashboard parity,
   and a before/after model evaluation only if a defect is demonstrated.

Do not modify or delete the preserved files to make these checks pass.

## Completed public-file verification

GitHub [PR #11](https://github.com/yumorepos/network-lab/pull/11) passed
**123 tests, 141 warehouse-dependent skips** and merged a check that
every field in the three public CSV screen files agrees with the corresponding
Parquet files served by the dashboard, including null patterns and 1e-6
absolute tolerance for float values. This establishes committed reader-facing
artifact agreement **only**, not a live Streamlit deployment byte-for-byte
snapshot or underlying source completeness.

See [publication audit](PUBLICATION_READINESS_AUDIT_2026_10.md),
[airport mapping issue #7](https://github.com/yumorepos/network-lab/issues/7)
and [DB1C data-contract issue #9](https://github.com/yumorepos/network-lab/issues/9).
