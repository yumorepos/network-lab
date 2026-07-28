# Porter YYZ: portability demonstration

Same engine, different config: carrier PD, hub YYZ, E195-E2 economics (B6
E190 proxy with the documented E2 fuel adjustment), YYZ competitive set.
Ranked table only by design; no full business cases.

Each market is right-sized: the engine picks the frequency (3x/7x/14x weekly)
that maximizes annual contribution at a feasible load factor, then judges that
schedule. Verdicts: **1 LAUNCH / 1 MONITOR / 77 PASS**. Every LAUNCH is an anchor-backed large market
entered at modest share against real incumbents - the low-cost entry logic of
taking a slice of a big market, not owning a small one.

## What "unserved" means here

Candidates are filtered to metros Porter does not already serve nonstop from
YYZ, measured at the metro level from T-100 (any airport in the metro, trailing
twelve months, at least roughly weekly). This correctly removes New York
(Porter flies YYZ-LGA) and Las Vegas from the candidate set. One LAUNCH deserves
an explicit caveat: Chicago. Porter has served Chicago historically from Billy
Bishop (YTZ) with Dash-8 turboprops, a different airport and gauge that sits
outside this YYZ mainline-jet study; T-100 shows no Porter YYZ-Chicago jet
service, so Chicago is treated here as a genuine new-market candidate for the
E195-E2 rather than an existing route. The verified incumbent-network reference
file (data/reference/) records each carrier's current nonstop map so this
filter can be audited independently of the T-100 join.

| metro_name                                     | verdict   |   chosen_freq_wk |   margin_pct |     belf |   proposed_share | demand_method   |   demand_pax_yr |   n_nonstop_incumbents | top_competitor   |
|:-----------------------------------------------|:----------|-----------------:|-------------:|---------:|-----------------:|:----------------|----------------:|-----------------------:|:-----------------|
| Boston-Cambridge-Newton, MA-NH                 | LAUNCH    |                3 |     32.5731  | 0.619638 |        0.159255  | anchor_x_growth |        291197   |                      1 | DL               |
| Hartford-West Hartford-East Hartford, CT       | MONITOR   |                3 |      4.85303 | 0.583304 |        0.812673  | anchor_x_growth |         31129.6 |                      0 | AA               |
| Chicago-Naperville-Elgin, IL-IN                | PASS      |                3 |    -11.0759  | 0.615053 |        0.0570471 | anchor_x_growth |        399883   |                      5 | AC               |
| Atlanta-Sandy Springs-Roswell, GA              | PASS      |                3 |    -22.7986  | 0.747856 |        0.112043  | anchor_x_growth |        224256   |                      2 | DL               |
| Milwaukee-Waukesha, WI                         | PASS      |                3 |    -26.1694  | 0.606853 |        0.760467  | anchor_x_growth |         26048.5 |                      0 | DL               |
| Washington-Arlington-Alexandria, DC-VA-MD-WV   | PASS      |                3 |    -27.4769  | 0.570402 |        0.076968  | anchor_x_growth |        239424   |                      4 | DL               |
| Philadelphia-Camden-Wilmington, PA-NJ-DE-MD    | PASS      |                3 |    -30.1686  | 0.570367 |        0.12936   | anchor_x_growth |        139500   |                      3 | DL               |
| Cincinnati, OH-KY-IN                           | PASS      |                3 |    -71.2147  | 0.603998 |        0.309075  | anchor_x_growth |         47006.6 |                      1 | DL               |
| Nashville-Davidson--Murfreesboro--Franklin, TN | PASS      |                3 |    -79.3853  | 0.707967 |        0.167783  | anchor_x_growth |         96873.6 |                      2 | DL               |
| Indianapolis-Carmel-Greenwood, IN              | PASS      |                3 |    -82.4607  | 0.61695  |        0.415022  | anchor_x_growth |         33553.5 |                      1 | DL               |
| Dallas-Fort Worth-Arlington, TX                | PASS      |                3 |    -91.0351  | 0.901999 |        0.108038  | anchor_x_growth |        179990   |                      2 | DL               |
| Raleigh-Cary, NC                               | PASS      |                3 |   -103.107   | 0.664361 |        0.233508  | anchor_x_growth |         57690.8 |                      1 | DL               |
| Minneapolis-St. Paul-Bloomington, MN-WI        | PASS      |                3 |   -114.794   | 0.722618 |        0.122235  | anchor_x_growth |        113349   |                      4 | DL               |
| New Orleans-Metairie, LA                       | PASS      |                3 |   -152.4     | 0.876055 |        0.224192  | anchor_x_growth |         63760.1 |                      1 | DL               |
| Houston-Pasadena-The Woodlands, TX             | PASS      |                3 |   -171.907   | 0.925183 |        0.112698  | anchor_x_growth |        124343   |                      2 | DL               |
| Kansas City, MO-KS                             | PASS      |                3 |   -173.286   | 0.783928 |        0.369649  | anchor_x_growth |         31959.3 |                      0 | DL               |
| Columbus, OH                                   | PASS      |                3 |   -176.939   | 0.548022 |        0.342939  | anchor_x_growth |         23764.4 |                      1 | DL               |
| Charlotte-Concord-Gastonia, NC-SC              | PASS      |                3 |   -181.644   | 0.685671 |        0.126225  | anchor_x_growth |         79432.1 |                      2 | DL               |
| St. Louis, MO-IL                               | PASS      |                3 |   -192.398   | 0.712918 |        0.230091  | anchor_x_growth |         43641   |                      1 | DL               |
| Denver-Aurora-Centennial, CO                   | PASS      |                3 |   -204.344   | 0.93393  |        0.126966  | anchor_x_growth |         99538.1 |                      2 | DL               |
