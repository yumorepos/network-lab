# BTS T-100 source-published airport identity: 2024 vs Jan–Jul 2026 (2026-10-29)

**Verdict: source identity comparison passes within observed overlap; NOT a production code-only mapping certification.**

## Independent official-source evidence

An ephemeral GitHub Actions runner downloaded BTS TranStats Table 293 with **all published source fields**, including `OriginAirportID`, `DestAirportID`, `OriginCityMarketID` and `DestCityMarketID`. Each source year was saved only temporarily, parsed and CRC-checked, then the source ZIP deleted on runner cleanup. Only source-field audit JSON was retained as the CI artifact. The unit and live download gates passed: [run 40947738178](https://github.com/yumorepos/network-lab/actions/runs/40947738178).

| Source item | Full-year 2024 | Jan–Jul 2026 |
|---|---:|---:|
| Rows in official full-field ZIP | 549,799 | 332,658 |
| F/L positive-departure rows | 488,872 | 299,295 |
| Observed months | 1–12 | 1–7 |
| Source-published missing airport/city-market ID endpoints | 0 | 0 |
| Distinct observed stable AirportIDs | 1,977 | 1,804 |
| Codes with more than one AirportID *within the source year* | 0 | 0 |

**Across the years:** 1,570 AirportIDs and 1,570 airport-code strings were common to both observed periods. There were **zero** shared code strings associated with different source-published AirportID sets; **zero** shared AirportIDs with different observed code sets; **zero** shared AirportIDs with different observed CityMarketID or country sets. These results do not mean there is no earlier historical code reuse, that an airport rename after July 2026 had already appeared in T-100, or that the latest-code reference lookup is correct.

Official source archive SHA-256:
- 2024: `2e18f9491efecdad128887aea8e27fff27a78ceaf88469728a7fad3cc70c8e60`
- Jan–Jul 2026: `469367f22db446f27c970b36ab06a7961b3624cccd785b9f8103646552c78b22`

## New observed source-extract difference; DO NOT overwrite frozen vintages

The preserved **14-field** 2024 T-100 archive has **549,731 source rows** and **488,806 F/L positive-departure rows**. The fresh official **all-field** 2024 extraction has **549,799** and **488,872**, respectively: **68 extra total rows and 66 extra scheduled passenger-service rows**. The extracts have different field projections and creation vintages. The discrepancy is real, but it is **not yet attributed** to BTS historical data revisions versus field-selection/export semantics, because identical-field and record-key reconciliation has not been performed.

**Acceptance requirement:** download the 2024 *same 14-field projection* into an isolated location, compare the complete row multiset including duplicates and monthly/year/class/carrier/route counts against the archived source, and record whether any revisions explain the 68/66 discrepancy. Do not refresh immutable study artifacts or claim the changed totals are model errors.

## Downstream issues still open

- The historical airport-code lookup can reuse codes across much older years or change after the 2026 July source cutoff. Use source-published IDs across the full relevant historical period before issue #7 is considered resolved.
- A source-stable-ID comparison does not validate the city's **CBSA** mapping. Issue #14 still requires source geography and an independent candidate/replay consumer impact analysis.
- No original Mac warehouse, model outputs or 463 decision replay data were recomputed. Outcome and candidate-count changes are *unmeasured*, even though these source checks passed.

Sources: [BTS official T-100 Segment field descriptions](https://www.transtats.bts.gov/Fields.asp?gnoyr_VQ=FMG), [project airport issue #7](https://github.com/yumorepos/network-lab/issues/7).
