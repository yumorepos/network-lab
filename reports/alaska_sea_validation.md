# Alaska SEA: end-to-end validation study

US domestic is the one arena where demand, share, and fare are all observed.
The ground-truth check that matters is the share model: the same QSI-lite
machinery that scores Canadian candidates, scored here against observed DB1B
carrier shares.

## The ground-truth result

- **Share model MAE: 7.0 share points** across 503 market-carrier
  rows at SEA, reported by market structure in docs/validation.md.
- Demand for screened candidates is observed DB1B (45 of 49
  markets); every gravity-filled row is flagged `modeled`.

## Reading the screen honestly

The screen resolves the 49 unserved candidates to 1 MONITOR, 48 PASS: effectively
no new-market opportunity at a mature hub. The one exception is Fayetteville-Springdale-Rogers, which screens MONITOR rather than PASS: its best-fit margin is +0.2%, positive but below the 8% launch hurdle, so the rule holds it for watching rather than launching or rejecting. This holds after
right-sizing: each market was tested at 3x, 7x, and 14x weekly (a single
178-seat mainline gauge, which is what Alaska flies from SEA), and none cleared
its best-fit schedule on the launch hurdle. So the earlier "fixed-gauge
artifact" caveat is partly resolved (lowering frequency did not rescue these
markets), and what remains is a genuine gauge limitation: a regional-jet gauge
(which Alaska operates through Horizon/SkyWest but is out of this study's
mainline scope) would be the honest next test for the thinnest markets. The
near-uniform PASS shows the screen does not invent opportunities at a mature
hub where the observed network already holds the markets that fit mainline
economics - a negative check on the machinery, stated no more strongly than
that.

## Ranked screen (top 15 by margin)
| metro_name                               | verdict   |   chosen_freq_wk |   margin_pct |     belf |   load_factor |   proposed_share | demand_source   |   n_nonstop_incumbents |
|:-----------------------------------------|:----------|-----------------:|-------------:|---------:|--------------:|-----------------:|:----------------|-----------------------:|
| Fayetteville-Springdale-Rogers, AR       | MONITOR   |                3 |     0.173902 | 0.856787 |      0.85828  |         0.545925 | modeled         |                      0 |
| Des Moines-West Des Moines, IA           | PASS      |                3 |   -29.732    | 0.807623 |      0.622532 |         0.507458 | observed        |                      0 |
| Springfield, MO                          | PASS      |                3 |   -41.3514   | 0.658658 |      0.465972 |         0.88868  | observed        |                      0 |
| Grand Rapids-Wyoming-Kentwood, MI        | PASS      |                3 |   -43.0253   | 0.876613 |      0.612908 |         0.412302 | observed        |                      0 |
| Albany-Schenectady-Troy, NY              | PASS      |                3 |   -44.7492   | 0.971266 |      0.670999 |         0.407129 | modeled         |                      0 |
| Madison, WI                              | PASS      |                3 |   -48.5454   | 0.819074 |      0.551397 |         0.562257 | observed        |                      0 |
| Little Rock-North Little Rock-Conway, AR | PASS      |                3 |   -49.1119   | 0.860618 |      0.577163 |         0.49824  | observed        |                      0 |
| El Paso, TX                              | PASS      |                3 |   -58.2271   | 0.88158  |      0.557161 |         0.222053 | observed        |                      1 |
| Rochester, NY                            | PASS      |                3 |   -60.0277   | 0.979403 |      0.612021 |         0.564943 | observed        |                      0 |
| Virginia Beach-Chesapeake-Norfolk, VA-NC | PASS      |                3 |   -63.8394   | 1.00123  |      0.611104 |         0.250385 | observed        |                      0 |
| Syracuse, NY                             | PASS      |                3 |   -70.9995   | 0.967946 |      0.566052 |         0.474251 | observed        |                      0 |
| Buffalo-Cheektowaga, NY                  | PASS      |                3 |   -75.2288   | 1.03163  |      0.588734 |         0.430086 | observed        |                      0 |
| Huntsville, AL                           | PASS      |                3 |   -75.6549   | 0.790344 |      0.449941 |         0.611551 | observed        |                      0 |
| Gulfport-Biloxi, MS                      | PASS      |                3 |   -84.1733   | 0.938658 |      0.50966  |         0.741567 | modeled         |                      0 |
| Memphis, TN-MS-AR                        | PASS      |                3 |   -88.3215   | 0.913605 |      0.485131 |         0.278046 | observed        |                      0 |
