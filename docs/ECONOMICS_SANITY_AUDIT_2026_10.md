# Economics sanity audit — 2026-10-28

**Status:** Published-output arithmetic checked; **no evidence of a margin-formula defect in the committed screens**. This is not a revalidation of proprietary airline operating costs, independent fares, or missing Canadian O&D truth. The model, assumptions, scenario grids, historical replay and Streamlit design remain unchanged.

## Why Albany's displayed −1,108.7% margin is possible

Canonical input: `data/parquet/outputs/screen_westjet_yyc.csv`, row `Albany-Schenectady-Troy, NY`. Source code: `models/economics.py`, `models/spill.py`, and `models/screen.py`.

| Published input or calculated result | Albany |
|---|---:|
| Annual bidirectional market demand (modeled, unanchored, capped) | 4,659.016 pax |
| Modeled proposed-service share | 71.3716% |
| Implied annual captured passengers, before spill | 3,325.216 |
| Evaluated schedule (not a feasible proposal) | 3 one-way hub departures/week, 174 seats |
| Annual total departures, both directions | 3 × 52 × 2 = **312** |
| Implied passengers/departure | **10.658** |
| Model load factor | **6.1251%** |
| Modeled break-even load factor | **74.0339%** |
| Cost/revenue per departure (BELF / LF) | **12.0869×** |
| Implied revenue/departure (from committed annual contribution and ratio) | **US$4,249.13** |
| Implied fully allocated cost/departure (same derivation) | **US$51,358.76** |
| Published annual contribution (312 departures) | **−US$14,698,205.82** |
| Published margin (revenue-denominator definition) | **−1,108.689%** |

The economics code uses `margin_pct = 100 * (revenue_dep - cost_dep) / revenue_dep` and `belf = cost_dep / (fare * seats)`, while `load_factor = pax_per_dep / seats` and `revenue_dep = fare * pax_per_dep`. Therefore, when revenue is positive:

```text
margin_pct = 100 * (1 - belf / load_factor)
           = 100 * (1 - 0.740338868884 / 0.061251395737)
           = -1108.688977578
```

An operating margin on **revenue** can be much less than −100% when cost exceeds revenue by many times. A modeled **71% market share** is not a 71% **aircraft load factor**. All the displayed numbers reconcile using the committed source row. The nearly empty cabin is why the ratio looks extreme. This arithmetic check does not imply the assumptions are empirically accurate.

**Confidence caveat:** Albany has `demand_source=modeled`, `demand_method=unanchored_capped_at_ceiling`, no observed 2018 city-pair anchor, and no nonstop incumbent in the reconstruction. The 71% share is explicitly flagged uncertain. It is not a measured capture rate.

## Portfolio-wide committed-artifact check

The 200 rows of the three committed `screen_*.csv` outputs were checked for the identity `margin_pct = 100 * (1 - belf/load_factor)`. **Zero mismatches** at tolerance 1e-5 percentage points. Load factors were within [0,1], and no LAUNCH/MONITOR row appeared below the 50% floor.

| Study | Rows | LF below 50% | Margin below −1,000% | Most negative displayed margin |
|---|---:|---:|---:|---:|
| WestJet YYC | 76 | 76 | 46 | −1,971.6% |
| Alaska SEA | 45 | 45 | 18 | −2,093.9% |
| Porter YYZ | 79 | 75 | 29 | −2,576.0% |
| **Total** | **200** | **196** | **93** | — |

This is **not** 93 independent cost-model defects. It is a recurring consequence of applying fully allocated per-departure cost to a large fixed aircraft while captured passenger volumes are tiny.

## Findings, limits and disposition

1. **Arithmetic: consistent in published output.** The Albany margin, LF, BELF, modeled demand, annual contribution and frequency reconcile. The verified unit contract correctly uses **both directions** in the annual departure denominator.
2. **Economic meaning: interpret cautiously.** A strongly negative percentage here describes a very low denominator, not a forecast that a real airline loses exactly that percentage. Report the absolute annual contribution and passengers/departure alongside the percentage when explaining it.
3. **Share uncertainty: material, already disclosed.** Albany's modeled 71.37% share is flagged as low confidence; do not treat it as observed adoption.
4. **Verdict vocabulary: potential UX issue.** In this product, `PASS` means **pass on the opportunity / do not launch**, not that an evaluated schedule *passed* the 50% feasibility floor. This is defined in `README.md` and `models/screen.py`, but could be misread on cards. This audit makes **no UI change**; a later presentation-only patch could label it `DO NOT LAUNCH` with a glossary while preserving stored `PASS` values.
5. **Cost assumptions unverified by this audit.** The committed screens cannot independently prove the 2024 Form 41 comparator rates, indirect allocation, fuel prices, modeled transborder fares, fee proxy, aircraft suitability, or true market demand. Validating these requires the full warehouse, documented raw-source checks, and a separately scoped protocol. No tuning is justified from the margin size alone.

## Regression coverage and acceptance gate

`tests/test_economics_sanity_audit.py` is a warehouse-free test of the *published* margin/LF/BELF identity for all three studies, valid finite inputs, verdict sign/floor consistency, and Albany's bidirectional annual departure arithmetic. It does not alter economic calculations.

**Acceptance gate:** CI must pass on this audit branch, output CSV/Parquet and model source must remain unchanged, and the PR can be reviewed before any merge. No main-branch or Streamlit deployment is intended from the audit itself. After closing this stage, the next agreed separate task is mobile readability, then Stage B data freshness on an isolated branch.
