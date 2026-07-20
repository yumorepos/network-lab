# Porter YYZ: portability demonstration

Same engine, different config: carrier PD, hub YYZ, E195-E2 economics (B6
E190 proxy with the documented E2 fuel adjustment), YYZ competitive set.
Ranked table only by design; no full business cases.

Each market is right-sized: the engine picks the frequency (3x/7x/14x weekly)
that maximizes annual contribution at a feasible load factor, then judges that
schedule. Verdicts: {'PASS': 71, 'LAUNCH': 5, 'MONITOR': 3}. Every LAUNCH is
an anchor-backed large market entered at modest share against real incumbents -
the low-cost entry logic of taking a slice of a big market, not owning a small
one.

| metro_name                                     | verdict   |   chosen_freq_wk |   margin_pct |     belf |   proposed_share | demand_method   |   demand_pax_yr |   n_nonstop_incumbents | top_competitor   |
|:-----------------------------------------------|:----------|-----------------:|-------------:|---------:|-----------------:|:----------------|----------------:|-----------------------:|:-----------------|
| Hartford-West Hartford-East Hartford, CT       | MONITOR   |                3 |    37.5183   | 0.583304 |        0.789555  | anchor_x_growth |         31129.6 |                      0 | OH               |
| Milwaukee-Waukesha, WI                         | MONITOR   |                3 |    33.1576   | 0.606853 |        0.856723  | anchor_x_growth |         26048.5 |                      0 | OO               |
| Washington-Arlington-Alexandria, DC-VA-MD-WV   | LAUNCH    |                3 |    32.0158   | 0.570402 |        0.078066  | anchor_x_growth |        239424   |                      4 | YX               |
| Chicago-Naperville-Elgin, IL-IN                | LAUNCH    |                3 |    31.2874   | 0.615053 |        0.0536489 | anchor_x_growth |        399883   |                      6 | YX               |
| Boston-Cambridge-Newton, MA-NH                 | LAUNCH    |               14 |    24.887    | 0.619638 |        0.290962  | anchor_x_growth |        291197   |                      2 | YX               |
| Philadelphia-Camden-Wilmington, PA-NJ-DE-MD    | LAUNCH    |                3 |    23.2206   | 0.570367 |        0.112191  | anchor_x_growth |        139500   |                      5 | PT               |
| Atlanta-Sandy Springs-Roswell, GA              | LAUNCH    |                3 |    20.0433   | 0.747856 |        0.110463  | anchor_x_growth |        224256   |                      3 | DL               |
| Cincinnati, OH-KY-IN                           | MONITOR   |                3 |     5.95182  | 0.603998 |        0.282438  | anchor_x_growth |         47006.6 |                      1 | 9E               |
| Dallas-Fort Worth-Arlington, TX                | PASS      |                3 |    -0.130071 | 0.901999 |        0.121249  | anchor_x_growth |        179990   |                      3 | DL               |
| Indianapolis-Carmel-Greenwood, IN              | PASS      |                3 |    -3.52681  | 0.61695  |        0.366188  | anchor_x_growth |         33553.5 |                      1 | 9E               |
| Nashville-Davidson--Murfreesboro--Franklin, TN | PASS      |                3 |    -9.49425  | 0.707967 |        0.138032  | anchor_x_growth |         96873.6 |                      4 | YX               |
| Raleigh-Cary, NC                               | PASS      |                3 |    -9.59828  | 0.664361 |        0.216727  | anchor_x_growth |         57690.8 |                      2 | YX               |
| New Orleans-Metairie, LA                       | PASS      |                3 |   -15.9783   | 0.876055 |        0.2507    | anchor_x_growth |         63760.1 |                      2 | DL               |
| Houston-Pasadena-The Woodlands, TX             | PASS      |                3 |   -19.6063   | 0.925183 |        0.132652  | anchor_x_growth |        124343   |                      2 | DL               |
| Minneapolis-St. Paul-Bloomington, MN-WI        | PASS      |                3 |   -19.6973   | 0.722618 |        0.109845  | anchor_x_growth |        113349   |                      6 | MQ               |
| Denver-Aurora-Centennial, CO                   | PASS      |                3 |   -26.8962   | 0.93393  |        0.155436  | anchor_x_growth |         99538.1 |                      2 | DL               |
| Kansas City, MO-KS                             | PASS      |                3 |   -27.9378   | 0.783928 |        0.395577  | anchor_x_growth |         31959.3 |                      0 | DL               |
| Portland-Vancouver-Hillsboro, OR-WA            | PASS      |                3 |   -31.0869   | 1.10674  |        0.514731  | anchor_x_growth |         36723.4 |                      0 | UA               |
| Austin-Round Rock-San Marcos, TX               | PASS      |                3 |   -33.8247   | 0.946221 |        0.222223  | anchor_x_growth |         66389.2 |                      2 | DL               |
| Seattle-Tacoma-Bellevue, WA                    | PASS      |                3 |   -36.8082   | 1.10005  |        0.20022   | anchor_x_growth |         87077   |                      2 | UA               |
