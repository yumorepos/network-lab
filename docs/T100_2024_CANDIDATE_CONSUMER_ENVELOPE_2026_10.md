# 2024 T-100 source-vintage consumer envelope — independently tested 2026-10-29

**Scope: read-only reconstruction of specific candidate-input decisions. Not a full model or warehouse replay.** The archived and fresh 2024 BTS T-100 14-field sources differ by 94 frozen-only versus 162 current-only complete records. This exercise tests whether those source changes alter 2024 **airport seats used by** `models/catchment.py::metro_anchor_points` and `models/candidates.py::generate`.

## Source-vintage inputs

- Frozen T-100 2024 ZIP: SHA-256 `a423f65baa9b4cc2a26e0742d3436888c24cca248f88a76eaecd4771054fa29d`.
- Fresh current T-100 2024 with the **same 14 fields**: SHA-256 `e4d326e7162fee5a4abf9f91ab5f57132fa87e61ae9da93ff16f0941be549fa2`; official source extraction in [GitHub run 40949046897](https://github.com/yumorepos/network-lab/actions/runs/40949046897).
- BTS July 2026-era Master Coordinate ZIP and archived OurAirports `airports.csv` source.
- `NetworkLab_CBSA_Source_Audit_2026-10-29.sqlite`, the **independent 935-CBSA audit copy**, not the original `map_citymarket_cbsa` DuckDB table. It contains 649 CBSAs with available mapped U.S. airport anchors in the reconstructed source universe.
- Study distance limits from `config/studies/{westjet_yyc,alaska_sea,porter_yyz}.yaml`; shared floor/satellite thresholds from `config/assumptions.yaml` — population >=400,000, annual scheduled airport seats >=250,000, satellites within 60 miles of airports with >=5x seats. No historical study parameters were changed.

## What changed in the raw 2024 aircraft-seat inputs

Nine **selected U.S. anchor airports** have different 2024 scheduled seats under the fresh source:

| CBSA | Airport | Frozen scheduled seats | Current scheduled seats | Difference |
|---|---|---:|---:|---:|
| Seattle | SEA | 30,580,207 | 30,633,351 | +53,144 |
| Boston | BOS | 25,622,733 | 25,648,078 | +25,345 |
| Miami | MIA | 32,228,725 | 32,208,117 | −20,608 |
| New York | JFK | 37,909,794 | 37,891,646 | −18,148 |
| Los Angeles | LAX | 45,394,174 | 45,403,827 | +9,653 |
| Chicago | ORD | 46,578,408 | 46,569,009 | −9,399 |
| San Francisco | SFO | 30,410,988 | 30,403,268 | −7,720 |
| Dallas–Fort Worth | DFW | 50,705,858 | 50,698,294 | −7,564 |
| Philadelphia | PHL | 18,597,700 | 18,597,992 | +292 |

These changes directly affect the **reported annual seats** at selected airports, but not their selection as airport anchors under the reconstructed source-based mapping. Absolute seat changes should not be conflated with changed market demand or route-level margins.

## Verified source-reconstruction negative result

| Consumer rule | Frozen vs current 2024 result |
|---|---|
| U.S. CBSAs with source-reconstructed anchors | **649** |
| Selected CBSA anchor airport code changes | **0** |
| 250,000 annual-seat threshold crossings | **0** |
| 60mi/5x satellite-airport flag changes | **0** |
| YYC pre-served-market eligible CBSA set | 99 -> 99; **0 membership changes** |
| SEA pre-served-market eligible CBSA set | 97 -> 97; **0 membership changes** |
| YYZ pre-served-market eligible CBSA set | 90 -> 90; **0 membership changes** |

The source-side reconstruction uses fixed code->latest CityMarketID and the independently derived 2023 CBSA selection. It sorts equal seats by airport code **for reproducibility** rather than claiming the same unspecified tie ordering as DuckDB `row_number()`. Unresolved *zero-seat CBSA ties* are explicitly counted in the machine report, not certified.

The 2024 source comparison also found **identical direct U.S.–Canada scheduled traffic totals in both archives**, at **17,714 records, 31,957,941 segment passenger legs, 38,457,493 seats and 333,648 departures**. This supports invariance of the specific 2024 numerator of transborder growth from `models/transfer.py`, not certification of all demand inputs.

## How to reproduce privately

Use the previously delivered compact CBSA source-audit database and source ZIPs. **None of these large or private source files are committed to GitHub.** With `numpy` and `pandas` installed:

```bash
python -m pytest -q tests/test_audit_t100_2024_candidate_envelope.py
python -m scripts.audit_t100_2024_candidate_envelope \
  --archived /private/t100_2024.zip \
  --current /tmp/research_2024_current_14_fields.zip \
  --ourairports /private/airports.csv \
  --master-zip /private/master_coord.zip \
  --cbsa-sqlite /private/NetworkLab_CBSA_Source_Audit_2026-10-29.sqlite \
  --output /tmp/networklab_candidate_envelope_2024.json
```

Inputs are read-only; output must not exist. Negative-control tests deliberately perturb anchor rankings, seat cutoff decisions, satellite ratios and CBSA bridge cardinality to verify that the audit can detect a change when one occurs.

## What is NOT certified

- The original 4.8 GiB DuckDB `dim_airport`, `map_citymarket_cbsa`, `fact_segment` and exact `dim_metro_us` are **not read back**. Original output parity and point-in-time replay are untested. CBSA mappings from the compact source audit are not an official geographic ground-truth crosswalk.
- The **served-by-brand non-stop exclusion** relies on later T-100 vintages plus historical brand resolution; it is not reconstructed by this audit. Thus the 99/97/90 sets are **pre-service exclusion**, not final candidate counts of the three studies.
- Competition uses the **latest 12 reported months** of T-100. With 2026 Jan–Apr as the frozen latest month, this window excludes 2024; the 2024 revision alone cannot change this particular window's source rows. Other year-specific consumers and historical replays remain to be audited.
- No changed candidate population/income, gravity factor, contribution margin, route verdict, marketing-brand attribution or replay decision is established by these negative results.

**Decision:** Preserve frozen T-100 and published results. The observed 2024 row differences alone do not justify re-ingesting historical data or altering a route decision. The remaining stop gate is independent source-fixed warehouse consumer and 463-row replay readback. See [issue #23](https://github.com/yumorepos/network-lab/issues/23), [issue #7](https://github.com/yumorepos/network-lab/issues/7) and [issue #14](https://github.com/yumorepos/network-lab/issues/14).
