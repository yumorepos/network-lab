# 2024 BTS T-100: frozen versus current exact 14-field source reconciliation

**Date:** 2026-10-29. **Disposition:** source vintage differs, preserve frozen source; no model changes.

## Evidence and controls

The archived raw ZIP `t100_2024.zip` (Drive backup) was compared byte-independently with a current official TranStats Table 293 export fetched with **exactly** the same 14 fields as `ingest/bts_t100.py` by GitHub Actions [run 40949046897](https://github.com/yumorepos/network-lab/actions/runs/40949046897). All 14 CSV fields were matched by name, all rows were retained (including duplicates), and full-row 192-bit BLAKE2b fingerprints were compared as **multisets** to avoid mistaking different sort order for revisions.

| Measure | Frozen archive | Current exact-field official export |
|---|---:|---:|
| SHA-256 | `a423f65baa9b4cc2a26e0742d3436888c24cca248f88a76eaecd4771054fa29d` | `e4d326e7162fee5a4abf9f91ab5f57132fa87e61ae9da93ff16f0941be549fa2` |
| Raw source records | 549,731 | 549,799 |
| Scheduled F/L positive-departure records | 488,806 | 488,872 |
| Records exclusively in this vintage | 94 | 162 |

The raw-row net difference is **+68**, but **256 nonmatching row occurrences** were found across the two versions (94 archived-only; 162 current-only), so row-count-only checks **understate revision exposure**. This proves nonidentical content under identical exported fields; it does *not* independently establish which BTS filing, correction process, or source release caused the differences.

## Segment-level aggregate sensitivity (current minus frozen)

- Sum of F/L operated segment passengers, across the full **2024** source year: **−5,400 passenger-segment legs** net; seats **−1,728** and departures **+89**. Large offsetting values are hidden by the annual net.
- October F/L passenger total: **−179,447** compared with frozen, although other months offset most of the difference.
- Changed record differences by operating carrier code: **IB** net −193,353 passenger legs; **HU** +119,935; **OS** +78,967; **BF** −10,949. These code labels are reported *as filed* and not reassigned to a marketing brand.
- **SEA** (Alaska study hub): 37 current-only changed records with a combined 87,134 reported segment passenger legs touch SEA; no archived-only changed records touch SEA. **YYC and YYZ** had no directly touched changed records under these two source ZIPs.
- Source-change classification contained no changed record with an origin/destination country combination of **US–CA or CA–US**. This is a narrow direct-segment finding, **not** proof of zero downstream influence on the models, served network or replay. Other source aggregates may change.

All counts above concern individual BTS **operated segment records**, not traveler itineraries or ticket O&D. A changed source record is **not** a measured changed study verdict. Records may be adjusted for historical reporting as later vintage data becomes available.

## Reproduce without overwriting project files

1. Acquire fresh official ZIP and manifest from the linked CI run artifact (available for seven days only); the actual current official ZIP was *never committed to Git*.
2. Privately use the preserved archived raw ZIP on your own system.
3. Run:

```bash
python -m pytest -q tests/test_audit_t100_2024_vintage_diff.py
python -m scripts.audit_t100_2024_vintage_diff \
  --archived /private/source/t100_2024.zip \
  --current /tmp/research_2024_current_14_fields.zip \
  --output /tmp/2024_t100_vintage_difference.json
```

The comparison is a read-only stream audit, keeps all duplicate row occurrences, and refuses to overwrite an existing report. **Never upload the private archived source ZIP to the public repository.**

## Required production follow-up

- Persist frozen source hashes and release cutoffs. Do not re-download 2024 directly into any historical replay input or use a modern extracted copy as if it were the original source vintage.
- Where model dependencies are demonstrated, reconstruct historical source-fixed candidates separately, classify changed features/competitor capacities by affected row/metro and event time, then run 200-screen and 463-replay before/after decision-delta checks with full reproducibility gates.
- Do not claim that the source drift invalidates a verdict unless a specific affected input/decision has been independently demonstrated.
- See [issue #23](https://github.com/yumorepos/network-lab/issues/23), [airport identity issue #7](https://github.com/yumorepos/network-lab/issues/7), [geography issue #14](https://github.com/yumorepos/network-lab/issues/14).
