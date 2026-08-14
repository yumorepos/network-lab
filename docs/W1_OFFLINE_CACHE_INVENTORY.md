# W1 offline cache inventory

**Date.** 2026-08-14
**Method.** Filesystem inventory and hashing of the frozen local cache, plus
read-only queries against the existing warehouse. **No network call was made.**
`make data` was not run and no government source was refreshed.

**Why this exists.** A historical replay is only possible from data already on
this disk. This document establishes, per source, what is actually here, which
historical columns survive, and where the processed layer has discarded history
that the raw layer still holds.

Hashes are sha256, first 16 hex characters. Where a source is a set of files, a
**set hash** is the sha256 of the concatenated per-file digests in filename
order, which is stable and identifies the collection.

---

## 1. Summary table

| source | path | size | hash | coverage | historical columns | offline transform | blocking effect |
|---|---|---|---|---|---|---|---|
| BTS T-100 Segment | `data/raw/t100/*.zip` (36) | 131 MB | `cae8e07c40e08c56` | 1990 to 2026, 2020 absent | full monthly panel | **feasible** | none |
| BTS DB1B Market | `data/raw/db1b/*.zip` (26) | 2.3 GB | `1a29bea879e1907a` | 2018Q1 to 2025Q2, 2020 absent | quarterly | **feasible** | **binds the replay start to 2018** |
| BTS DB1B Coupon | not cached | - | - | none | - | not possible offline | W2.1, Milestone B only |
| BTS DB1B Ticket | not cached | - | - | none | - | not possible offline | W2.1, Milestone B only |
| BTS Form 41 P-5.2 / P-1.2 | `data/raw/form41/*.zip` (14) | 2.7 MB | `be8b500fd42e69df` | 2018 to 2025, 2020 absent | annual | **feasible** | **binds cost replay to 2018** |
| EIA jet fuel spot | `data/raw/eia/jet_gulf_weekly.xls` | 132 KB | `d83248c77eee4389` | 1990-04-06 to 2026-07-10 | 1,893 weekly obs | **feasible** | none |
| BEA CAINC1 income and population | `data/raw/bea/CAINC1.zip` + `CAINC1_x/` | 3.3 MB | `e1465c8b0e7e75f5` | **1969 to 2024, 56 annual columns** | **all retained in raw** | **feasible** | none |
| BEA CAGDP2 GDP | `data/raw/bea/CAGDP2.zip` + `CAGDP2_x/` | 15 MB | `3e5d727915f3160f` | **2001 to 2024, 24 annual columns** | **all retained in raw** | **feasible** | none |
| Census CBSA delineation | `data/raw/census/list1_2023.xlsx` | 144 KB | `952c4b1e78acbb54` | **2023 vintage only** | none | not possible offline | **geography cannot be vintaged** |
| StatCan 23-10-0256 transborder O&D | `data/raw/statcan/23100256.zip` | 372 KB | `0a9a041cc3ce3c18` | **1997 to 2018, 22 annual vintages** | **all retained in raw and in Parquet** | **feasible** | none within 1997 to 2018 |
| StatCan 17-10-0135 CMA population | `data/raw/statcan/17100135.zip` | 16 MB | `571b784a635905b8` | 2001 to 2022, 22 vintages | **all retained in raw and in Parquet** | **feasible** | none within 2001 to 2022 |
| StatCan 23-10-0253 airport traffic | `data/parquet/statcan/sc_23100253.parquet` | 273 KB | see set | 2008 to 2024, 17 vintages | retained | **feasible** | none |
| OurAirports | `data/raw/ourairports/airports.csv` | 12 MB | `24e3d9369632b0a6` | current snapshot | none | feasible, but single vintage | minor; coordinates are stable |
| BTS lookups (carrier, aircraft, coords) | `data/raw/lookups/*.zip` | 800 KB | - | current snapshot | none | feasible, single vintage | see carrier lineage below |
| Carrier lineage reference | `data/reference/carrier_codes.csv`, `carrier_families.csv` | 5.5 KB | tracked in git | 5 register carriers, 14 certificates | **none: not effective-dated** | n/a | **blocks historical competitive reconstruction** |
| Route-spell register | derived by `warehouse/route_spells.py` | not persisted | n/a | 1990 to 2026 | derived on demand, about 10 s | **feasible** | none |
| Warehouse | `data/warehouse.duckdb` | 4.8 GB | rebuilt by gate | see marts below | - | present and green | none |

Warehouse marts as rebuilt during this session: `dim_airport` 8,802,
`dim_carrier` 1,776, `fact_segment` 13,630,379, `fact_od_market` 173,741,663,
`fact_costs` 15,618, `fact_fuel` 1,893.

## 2. The two findings that change the plan

### 2.1 The StatCan transborder anchor is a 22-year panel, not a single year

This is the most consequential result in this inventory and it was not known to
any prior document.

`docs/W1.4_baseline_freeze.md` records the source as "frozen circa 2018,
25,952 rows, the anchor; no successor exists". `docs/LIMITATIONS.md` item 2 says
"the transborder demand anchor is frozen at 2018". **Both statements are true
about the forward direction and both are silent about the backward direction.**
The table stopped updating after 2018. It did not start in 2018.

Verified by query against `fact_od_transborder_2018`, restricted to the estimate
`models/demand.py` actually consumes ("Number of outbound and inbound
passengers"):

| REF_DATE | city pairs | REF_DATE | city pairs |
|---|---|---|---|
| 1997 | 364 | 2008 | 433 |
| 1998 | 378 | 2009 | 447 |
| 1999 | 393 | 2010 | 425 |
| 2000 | 402 | 2011 | 449 |
| 2001 | 412 | 2012 | 465 |
| 2002 | 409 | 2013 | 486 |
| 2003 | 404 | 2014 | 491 |
| 2004 | 417 | 2015 | 494 |
| 2005 | 446 | 2016 | 493 |
| 2006 | 447 | 2017 | 499 |
| 2007 | 451 | **2018** | **523** |

Hub coverage is continuous across the whole span: Calgary carries 46 to 53
published city pairs in every year, Toronto 80 to 100.

`models/demand.py:105` filters `WHERE REF_DATE='2018'`. Twenty-one further
annual vintages are present in the warehouse and in
`data/parquet/statcan/sc_23100256.parquet` (25,952 rows, REF_DATE 1997 to 2018)
and are discarded at query time.

**Consequence.** Point-in-time transborder demand anchors are available offline
for any decision date from roughly 1998 to 2019. This removes what would
otherwise have been the hardest blocker for the two transborder studies, and it
means the transfer factor can in principle be estimated at vintage rather than
once. It does not require new ingestion.

**Caveat, and the policy that follows from it.** The survey publication floor is
not a constant 4,000. Minimum published values by vintage run from 280 to 3,090
and the 1st percentile runs 2,650 to 3,920. The negative-space cap in
`models/demand.py` uses a single `SURVEY_THRESHOLD = 4000.0`.

This is a **newly discovered defect in the frozen baseline** and it is **not
fixed during Milestone A.** Stage 1 measures the frozen model; changing it while
measuring it would produce a baseline that moved while it was being built.

The split adopted, stated fully in `docs/W1_REPLAY_FEASIBILITY.md` section 5b:
point-in-time reconstruction **uses the historically appropriate anchor value**,
because that is data at a date; the **frozen `SURVEY_THRESHOLD = 4000.0` and all
frozen cap behaviour are retained**, because that is a model parameter. A
vintage-specific floor may be computed as a labelled sensitivity only, and the
resolution is carried to W3.4 under a change report.

### 2.2 BEA history survives in raw but not in Parquet, exactly as the W1.3 audit predicted

**Confirmed.** The raw extracts carry the full annual series:

```
CAINC1__ALL_AREAS_1969_2024.csv    GeoFIPS GeoName Region TableName LineCode
                                    ... 1969 1970 ... 2023 2024   (56 columns)
CAGDP2__ALL_AREAS_2001_2024.csv    ... 2001 2002 ... 2023 2024   (24 columns)
```

**Confirmed discarded downstream.** `ingest/census_bea_eia.py:53` computes
`sorted(years)[-1]` and keeps that column alone. The processed artifacts carry
no year at all:

```
data/parquet/census/metro_pop_income.parquet   935 rows
  columns: cbsa, name, population, income, income_measure
data/parquet/bea/metro_gdp.parquet             935 rows
  columns: cbsa, name, gdp_kusd
```

**Consequence.** Recovering 56 years of point-in-time US metro covariates
requires no download and no new source. It requires a new offline transform that
reads the already-extracted CSVs and keeps every year column. This is the W1.3
audit's fix 1, and it remains the highest value per hour available.

The same pattern holds on the Canadian side: `sc_17100135.parquet` retains 2001
to 2022 with `REF_DATE`, while the warehouse `dim_metro_ca` keeps 37 rows with
columns `cma` and `population` only, no year and no income.

## 3. What is genuinely missing offline

### 3.1 Historical CBSA delineations

`data/raw/census/` contains exactly one file, `list1_2023.xlsx`. Census redrew
metropolitan boundaries in 2013 and 2023 among others, and counties move between
CBSAs. There is no cached 2003, 2009, 2013, 2018 or 2020 delineation.

Every historical snapshot must therefore roll counties up to **2023 metro
boundaries**, whatever the reference period. That is leakage vector L4 from the
W1.3 audit and it **cannot be removed offline**. It has to be disclosed per
snapshot rather than smoothed over, and it is a permanent limitation of any
replay built under the no-network rule.

The effect is bounded but not zero: it distorts the covariates of metros whose
county composition changed, and it changes the airport-to-metro rollup for the
same metros.

### 3.2 DB1B before 2018

The cache starts at 2018Q1. There is no 2017 or earlier DB1B. This is the
binding constraint on the replay window, discussed in
`docs/W1_REPLAY_FEASIBILITY.md`.

### 3.3 DB1B Coupon and Ticket entirely

Not cached in any year. These are W2.1 and belong to Milestone B. Their absence
does not block Milestone A.

### 3.4 Effective-dated carrier identity

`carrier_codes.csv` and `carrier_families.csv` carry no effective dates.
`models/carriers.segment_brands()` resolves multi-brand regionals using DB1B
year 2024 and applies that map to every year. Air Wisconsin flew for American
until 2023 and United after; Mesa's American agreement ended in 2023. This is
leakage vector L3 and it is a **code and reference-data** gap, not a data-cache
gap: the underlying DB1B years needed to resolve brand per vintage are cached
for 2018 to 2025.

## 4. Offline transform feasibility, and one defect to fix in Stage 1

Every transform needed for the feasible replay window can run from this cache.

**But the ingest layer currently fails open to the network, not closed.**
`ingest/common.download_file` skips the network when the destination file exists
and otherwise **downloads**. `ingest/census_bea_eia.delineation()` and
`_county_bea()` both call it unconditionally. A new offline transform that
reuses those helpers would silently reach the internet the moment a cached file
were missing or renamed.

That is directly contrary to the standing rule for this work. **Stage 1B must
provide offline-only entry points that raise when a cached input is absent and
never call a downloader**, rather than relying on the cache happening to be
populated. Recorded here as a required Stage 1 deliverable, not fixed in Stage 0
(Stage 0 changes no code).

## 5. Reproducibility evidence for this inventory

```
make test              45 passed
make reproducibility   reproducible: 27 artifacts identical across a warehouse rebuild
```

Both run on 2026-08-14 from the frozen cache, before any Stage 0 document was
written. The rebuild consumed only cached Parquet. No source was refreshed.
