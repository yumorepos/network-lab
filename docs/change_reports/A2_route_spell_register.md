# Change report: mechanical route-spell register and its validation

**Task.** W1.2 from PHASE_5_6_PLAN.md
**Date.** 2026-07-28
**Baseline.** Pre-baseline (Milestone A).

## What was done

`warehouse/route_spells.py` derives a route-spell register from the full T-100
panel: one row per (carrier, unordered airport pair, spell) with first and last
month, initial and peak one-way weekly frequency, seasonal flag and status.

**89,502 spells** across 657 carriers and 19,442 airport pairs, against the 74
rows of the hand-compiled register. Launches by decade: 17,217 in the 1990s,
27,495 in the 2000s, 27,883 in the 2010s, 16,907 since 2020.

## Validation against the hand register

The gate is at least 90% of hand-compiled launches reproduced within one month,
with every disagreement explained rather than tuned away.

| | rows |
|---|---|
| register rows with a parseable launch date | 67 |
| excluded, no US endpoint | 13 |
| **reproducible rows** | **54** |
| matched to a derived spell | 51 |
| **reproduced within tolerance** | **49 (90.7%)** |

Encoded as `validate_against_register()` and two tests in
`tests/test_p0_regressions.py`. `make test` is 34 of 34.

### Two translations the comparison needed

**Carrier codes, and this was a real defect.** The register uses IATA codes;
T-100 uses BTS unique carrier codes. **Flair files as `07Q`.** The IATA code
`F8` belongs in BTS to Freedom Airlines d/b/a HP Express, a defunct US regional
that filed 277,230 departures between 2002 and 2010. Matching on `F8` silently
returns a different airline, which is why the first validation run scored 46.3%.
With the translation applied the same extractor scores 90.7%.

Two further lineage facts surfaced while building the mapping, both checked for
leaks of the kind Round 4 found:

- **Porter has two BTS certificates.** `PD` (Porter Airlines Limited) is the
  YYZ mainline jet operation the study scopes to; `P3` (Porter Airlines Inc.) is
  the Billy Bishop turboprop operation, 29,365 departures on 14 pairs since 2024.
  **Checked: `P3` flies nothing from YYZ, so zero candidates leak.** The existing
  study scoping in `incumbent_network_NOTES.md` is correct.
- **Swoop (`WO`) folded into WestJet** in October 2023, 3,904 departures
  2021-2023. Defunct in the current window so no effect on served-market tests,
  but it matters for any historical snapshot.

Recorded in `data/reference/carrier_codes.csv` with sources.

**Date precision.** Some register rows carry a year only. Those are credited for
a match anywhere in that calendar year rather than failed for not landing in
January.

### Rows T-100 structurally cannot contain

T-100 records segments touching the United States. 13 register rows have no US
endpoint: 12 Lynx Canadian domestic routes (hard rule 5) and Lynx YYC to Cancun.
These are excluded from the denominator, not scored as failures. No extractor
can recover a record that was never filed.

### The five remaining disagreements, each explained

| route | register | derived | explanation |
|---|---|---|---|
| F8 YHZ-SFB | 2021-12-17 | 2022-03 | **Genuine floor artifact.** T-100 shows 2 departures in Dec 2021, below the measured activity floor of 4 per month, then real service from March. The register is right and the derived launch is 3 months late. This is the documented cost of the floor. |
| WS YYC-AUS | 2022 | 2023-05 | **Hand register wrong.** T-100 has no 2022 rows at all; service starts May 2023. The register appears to record the announcement year. |
| PD YYZ-MDW | 2024 | none | **Hand register wrong.** Porter's Chicago service is YTZ to MDW (P3 1,527 and PD 743 departures), not YYZ. Wrong origin airport. |
| F8 YYZ-SFO | 2022 | none | **Announced, never flown.** Zero T-100 departures ever under 07Q. |
| F8 YYZ-DEN | 2022 | none | **Announced, never flown.** Zero T-100 departures ever under 07Q. |

**Four of the five are errors in the hand register that the derived register
gets right.** Only one is a limitation of the extractor. That inverts the
expected direction of the check and is the strongest available argument for
moving the backtest onto the derived register.

## 1. Metric impact

No W1.4 metric family exists yet. The relevant quantity is sample size for the
backtest.

| metric | before | after |
|---|---|---|
| launches available to the backtest | 48 scored, 74 compiled | 89,502 spells |
| launches with an initial frequency | 34 | 89,502 |
| earliest launch observable | 2021 | 1990 |

## 2. Verdict changes

None. This task adds a table and a test; no model input changed.

| study | LAUNCH | MONITOR | PASS |
|---|---|---|---|
| westjet_yyc | 0 / 0 | 0 / 0 | 76 / 76 |
| alaska_sea | 0 / 0 | 0 / 0 | 45 / 45 |
| porter_yyz | 1 / 1 | 1 / 1 | 77 / 77 |

## 3. Regression risk

**Guarded by.** `test_derived_route_spells_reproduce_hand_register` fails below
90% and prints every disagreement. `test_flair_carrier_code_is_not_the_iata_code`
fails if the translation table is reverted or if BTS reassigns the code. The
hand register is retained as the independent cross-check rather than replaced.

**Would still slip through.** The 90% gate is measured against 54 rows, all from
five Canadian carriers between 2021 and 2025. Nothing validates spell extraction
for US carriers, for the 1990s, or across a merger, and those are 99.9% of the
derived rows. A systematic error in, say, 1990s code reuse would not be caught.
The seasonal flag and the ceased/operating split are entirely unvalidated.

## 4. Statistical meaningfulness

49 of 54 is a point estimate on a small, non-random sample: the hand register
covers Canadian ULCCs in the 2021-2025 window, which is where the project's
post-mortems focus. The Wilson 95% interval on 49/54 is roughly [80%, 96%], so
"above 90%" is not established with confidence, only "consistent with 90%". This
is adequate as a sanity gate on the extractor and inadequate as a claim about
the 89,502 derived spells. Stated here rather than discovered later.

## 5. Assumptions touched

None added or changed in this task. `route_spell_min_deps_month` (value 4) was
added with the extractor and is unchanged; the F8 YHZ-SFB disagreement is its
one observed cost.

## Follow-ups created

1. Validate spell extraction on US carriers and pre-2018 vintages, where the
   hand register offers no coverage. Candidate approach: cross-check derived
   exits against known carrier shutdowns and merger dates.
2. `dim_carrier_lineage` is still only a translation table for five carriers.
   Mergers over 35 years (and code reuse like F8) need systematic treatment
   before W1.3 point-in-time snapshots are trustworthy.
