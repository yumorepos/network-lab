# Alaska SEA: end-to-end validation study

US domestic is the one arena where demand, share, and fare are all observed.
The ground-truth check that matters is the share model: the same QSI-lite
machinery that scores Canadian candidates, scored here against observed DB1B
carrier shares.

## The ground-truth result

- **Share model MAE: 7.0 share points** across 503 market-carrier
  rows at SEA, reported by market structure in docs/validation.md.
- Demand for screened candidates is observed DB1B (46 of 49
  markets); every gravity-filled row is flagged `modeled`.

## Reading the all-PASS screen honestly

All 49 remaining unserved candidates screen PASS. That is largely a
fixed-gauge artifact, not proof of hub saturation: this study evaluates one
schedule shape (daily, 178-seat mainline), and the remaining unserved SEA
markets are thin enough that a daily 737-9 loses money by construction. A
frequency-and-gauge optimization step (out of scope here, listed as an
extension) would evaluate 4x-weekly or regional-gauge service and would
plausibly turn some of these into viable candidates. What the uniform PASS
does show is that the screen does not invent opportunities at a mature hub
where the observed network has already taken the markets that fit this
gauge - a useful negative check on the machinery, stated no more strongly
than that.

## Ranked screen (top 15 by margin)
| metro_name                               | verdict   |   margin_pct |     belf |   load_factor |   proposed_share | demand_source   |   n_nonstop_incumbents |
|:-----------------------------------------|:----------|-------------:|---------:|--------------:|-----------------:|:----------------|-----------------------:|
| Des Moines-West Des Moines, IA           | PASS      |     -142.682 | 0.807623 |      0.332791 |         0.631397 | observed        |                      0 |
| El Paso, TX                              | PASS      |     -154.636 | 0.88158  |      0.346211 |         0.321832 | observed        |                      1 |
| Grand Rapids-Wyoming-Kentwood, MI        | PASS      |     -155.059 | 0.876613 |      0.343691 |         0.538405 | observed        |                      0 |
| Albany-Schenectady-Troy, NY              | PASS      |     -159.291 | 0.971266 |      0.374585 |         0.533084 | modeled         |                      0 |
| Virginia Beach-Chesapeake-Norfolk, VA-NC | PASS      |     -167.58  | 1.00123  |      0.374179 |         0.357052 | observed        |                      0 |
| Little Rock-North Little Rock-Conway, AR | PASS      |     -178.151 | 0.860618 |      0.309407 |         0.622773 | observed        |                      0 |
| Fayetteville-Springdale-Rogers, AR       | PASS      |     -182.044 | 0.66967  |      0.237434 |         0.666544 | observed        |                      0 |
| Madison, WI                              | PASS      |     -186.051 | 0.819074 |      0.286338 |         0.681073 | observed        |                      0 |
| Rochester, NY                            | PASS      |     -208.062 | 0.979403 |      0.317923 |         0.68344  | observed        |                      0 |
| Memphis, TN-MS-AR                        | PASS      |     -212.983 | 0.913605 |      0.291903 |         0.39036  | observed        |                      0 |
| Springfield, MO                          | PASS      |     -215.186 | 0.658658 |      0.208974 |         0.929936 | observed        |                      0 |
| Syracuse, NY                             | PASS      |     -215.237 | 0.967946 |      0.307054 |         0.599958 | observed        |                      0 |
| Buffalo-Cheektowaga, NY                  | PASS      |     -215.677 | 1.03163  |      0.326799 |         0.556478 | observed        |                      0 |
| Richmond, VA                             | PASS      |     -235.61  | 1.00744  |      0.300183 |         0.425217 | observed        |                      0 |
| Wichita, KS                              | PASS      |     -235.873 | 0.921646 |      0.274404 |         0.389211 | observed        |                      1 |
