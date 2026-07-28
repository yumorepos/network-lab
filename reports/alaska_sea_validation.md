# Alaska SEA: end-to-end validation study

US domestic is the one arena where demand, share, and fare are all observed.
The ground-truth check that matters is the share model: the same QSI-lite
machinery that scores Canadian candidates, scored here against observed DB1B
carrier shares.

## The ground-truth result

- **Share model MAE: 5.7 share points** across 503 market-carrier
  rows at SEA, reported by market structure in docs/validation.md.
- Demand for screened candidates is observed DB1B (45 of 45
  markets); every gravity-filled row is flagged `modeled`.

## Reading the screen honestly

The screen resolves the 45 unserved candidates to 45 PASS: effectively
no new-market opportunity at a mature hub. This holds after
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
| Des Moines-West Des Moines, IA           | PASS      |                3 |     -224.641 | 0.807623 |      0.248774 |        0.404565  | observed        |                      0 |
| Charlotte-Concord-Gastonia, NC-SC        | PASS      |                3 |     -239.867 | 1.06733  |      0.314045 |        0.0992477 | observed        |                      1 |
| Grand Rapids-Wyoming-Kentwood, MI        | PASS      |                3 |     -279.099 | 0.876613 |      0.231236 |        0.310491  | observed        |                      0 |
| Colorado Springs, CO                     | PASS      |                3 |     -299.006 | 0.813316 |      0.203836 |        0.452085  | observed        |                      0 |
| Madison, WI                              | PASS      |                3 |     -337.314 | 0.819074 |      0.187297 |        0.381854  | observed        |                      0 |
| Jacksonville, FL                         | PASS      |                3 |     -358.191 | 1.02537  |      0.223786 |        0.177647  | observed        |                      0 |
| Fayetteville-Springdale-Rogers, AR       | PASS      |                3 |     -383.551 | 0.66967  |      0.13849  |        0.33324   | observed        |                      0 |
| Little Rock-North Little Rock-Conway, AR | PASS      |                3 |     -384.621 | 0.860618 |      0.177586 |        0.306381  | observed        |                      0 |
| Memphis, TN-MS-AR                        | PASS      |                3 |     -402.945 | 0.913605 |      0.181651 |        0.208218  | observed        |                      0 |
| Virginia Beach-Chesapeake-Norfolk, VA-NC | PASS      |                3 |     -408.312 | 1.00123  |      0.196971 |        0.161104  | observed        |                      0 |
| Pensacola-Ferry Pass-Brent, FL           | PASS      |                3 |     -471.501 | 0.94992  |      0.166215 |        0.279894  | observed        |                      0 |
| Hartford-West Hartford-East Hartford, CT | PASS      |                3 |     -472.904 | 0.9864   |      0.172176 |        0.213436  | observed        |                      0 |
| Buffalo-Cheektowaga, NY                  | PASS      |                3 |     -486.594 | 1.03163  |      0.175868 |        0.256689  | observed        |                      0 |
| Louisville/Jefferson County, KY-IN       | PASS      |                3 |     -490.068 | 0.917485 |      0.155488 |        0.215933  | observed        |                      0 |
| Springfield, MO                          | PASS      |                3 |     -490.962 | 0.658658 |      0.111455 |        0.425123  | observed        |                      0 |
