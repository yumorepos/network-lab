# Alaska SEA: end-to-end validation study

US domestic is the one arena where demand, share, and fare are all observed,
so the full chain runs here with truth available at every stage.

- Candidates screened: 49 (46 with observed DB1B demand).
- Verdicts: {'PASS': 49}.
- Share-model accuracy vs observed DB1B carrier shares is reported in
  docs/validation.md (MAE by market structure); the same QSI-lite machinery
  scores the Canadian studies.
- Demand for screened candidates is observed; the gravity model is only used
  where DB1B is too thin, and every such row is flagged `modeled`.

## The finding

Every remaining unserved candidate PASSES at daily 737-9 gauge. That is not a
failure of the screen - it is agreement with Alaska's revealed strategy: a
mature hub where everything worth serving at mainline gauge daily is already
served, and what remains needs smaller gauge or lower frequency than this
study's config proposes. A screen that green-lights nothing at a saturated
hub is behaving correctly, and that is exactly the kind of negative result
that makes the positive results at YYC credible.

## Ranked screen (top 15 by margin)
| metro_name                               | verdict   |   margin_pct |     belf |   load_factor |   proposed_share | demand_source   |   n_nonstop_incumbents |
|:-----------------------------------------|:----------|-------------:|---------:|--------------:|-----------------:|:----------------|-----------------------:|
| Des Moines-West Des Moines, IA           | PASS      |     -101.822 | 0.807623 |      0.400167 |         0.759227 | observed        |                      0 |
| El Paso, TX                              | PASS      |     -154.636 | 0.88158  |      0.346211 |         0.321832 | observed        |                      1 |
| Grand Rapids-Wyoming-Kentwood, MI        | PASS      |     -155.059 | 0.876613 |      0.343691 |         0.538405 | observed        |                      0 |
| Albany-Schenectady-Troy, NY              | PASS      |     -159.291 | 0.971266 |      0.374585 |         0.533084 | modeled         |                      0 |
| Fayetteville-Springdale-Rogers, AR       | PASS      |     -162.838 | 0.66967  |      0.254784 |         0.71525  | observed        |                      0 |
| Virginia Beach-Chesapeake-Norfolk, VA-NC | PASS      |     -167.58  | 1.00123  |      0.374179 |         0.357052 | observed        |                      0 |
| Memphis, TN-MS-AR                        | PASS      |     -170.767 | 0.913605 |      0.337414 |         0.451222 | observed        |                      0 |
| Madison, WI                              | PASS      |     -171.162 | 0.819074 |      0.302061 |         0.718472 | observed        |                      0 |
| Little Rock-North Little Rock-Conway, AR | PASS      |     -178.151 | 0.860618 |      0.309407 |         0.622773 | observed        |                      0 |
| Rochester, NY                            | PASS      |     -178.157 | 0.979403 |      0.352105 |         0.75692  | observed        |                      0 |
| Tulsa, OK                                | PASS      |     -202.303 | 0.806142 |      0.266667 |         0.456965 | observed        |                      1 |
| Louisville/Jefferson County, KY-IN       | PASS      |     -202.343 | 0.917485 |      0.303458 |         0.491664 | observed        |                      0 |
| Colorado Springs, CO                     | PASS      |     -203.017 | 0.813316 |      0.268406 |         0.694511 | observed        |                      0 |
| Wichita, KS                              | PASS      |     -204.496 | 0.921646 |      0.302679 |         0.429316 | observed        |                      1 |
| Springfield, MO                          | PASS      |     -215.186 | 0.658658 |      0.208974 |         0.929936 | observed        |                      0 |
