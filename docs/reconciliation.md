# Reconciliation: computed vs published

Every check states the expected relationship derived from the
definitions, then reports the computed ratio as-is. Residuals
outside the stated band are flagged, not massaged.

## A. National transborder passengers

T-100 CA-US onboard passengers (both directions, scheduled
classes) vs StatCan 23-10-0253 transborder enplaned+deplaned.
Expected ratio ~1.0 (band (0.85, 1.15)); each transborder
passenger is counted once at a Canadian airport and once on a
T-100 segment.

| year | T-100 CA-US pax | StatCan transborder E+D | ratio |
|---|---|---|---|
| 2018 | 31,675,610 | 31,459,469 | 1.007 |
| 2019 | 31,996,223 | 32,192,583 | 0.994 |
| 2023 | 28,977,908 | 28,801,198 | 1.006 |
| 2024 | 31,957,941 | 31,806,161 | 1.005 |

## B. Airport-level transborder (2024)

Same construction per airport. Band (0.8, 1.2); airport-
level coverage differences (charter mix, preclearance edge
cases) are wider than the national ledger.

| airport | T-100 CA-US pax | StatCan transborder E+D | ratio |
|---|---|---|---|
| YYZ | 12,562,782 | 12,527,626 | 1.003 |
| YVR | 6,542,902 | 6,491,556 | 1.008 |
| YYC | 3,877,388 | 3,843,149 | 1.009 |
| YUL | 5,087,099 | 5,054,235 | 1.007 |

## C. DB1B journeys vs T-100 US domestic boardings

T-100 domestic boardings divided by DB1B expanded O&D
journeys. Expected (1.05, 1.6) (connections put one
journey on more than one segment; DB1B excludes bulk/
abnormal fares filtered at ingest).

| year | T-100 dom boardings | DB1B journeys x10 | ratio |
|---|---|---|---|
| 2018 | 787,922,331 | 511,290,430 | 1.541 |
| 2019 | 821,070,480 | 258,976,640 | 3.170  OUTSIDE BAND |

## D. The Canadian domestic gap, stated plainly

StatCan reports Canadian domestic E+D (about 2x journeys by
construction). T-100 contains no Canadian domestic segments,
DB1B contains no Canadian fares, and the StatCan domestic O&D
program is discontinued. There is no public demand truth for
Canadian domestic markets; this project's evidentiary reach is
therefore transborder (for Canadian hubs) and full domestic
(for US hubs), and Canadian domestic is out of scope by
design rather than by omission.

## Result summary

9/10 checks inside their stated bands.

Outside band (reported, not adjusted):
- db1b vs t100 2019: ratio 3.170
