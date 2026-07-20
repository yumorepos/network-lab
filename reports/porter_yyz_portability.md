# Porter YYZ: portability demonstration

Same engine, different config: carrier PD, hub YYZ, E195-E2 economics (B6
E190 proxy with the documented E2 fuel adjustment), YYZ competitive set.
Ranked table only by design; no full business cases.

Verdicts: {'PASS': 74, 'MONITOR': 4, 'LAUNCH': 2}

| metro_name                                     | verdict   |   margin_pct |     belf |   proposed_share | share_uncertainty   | demand_method      |    demand_pax_yr |   n_nonstop_incumbents | top_competitor   |
|:-----------------------------------------------|:----------|-------------:|---------:|-----------------:|:--------------------|:-------------------|-----------------:|-----------------------:|:-----------------|
| New York-Newark-Jersey City, NY-NJ             | LAUNCH    |     38.6547  | 0.580228 |        0.0410961 | False               | anchor_x_growth    |      1.48072e+06 |                     12 | YX               |
| Boston-Cambridge-Newton, MA-NH                 | LAUNCH    |     34.7303  | 0.619638 |        0.213056  | False               | anchor_x_growth    | 291197           |                      2 | YX               |
| Albany-Schenectady-Troy, NY                    | MONITOR   |     33.1037  | 0.545734 |        0.905258  | True                | gravity_x_transfer |  45957.5         |                      0 | PT               |
| Chicago-Naperville-Elgin, IL-IN                | MONITOR   |     13.0556  | 0.615053 |        0.0861345 | False               | anchor_x_growth    | 399883           |                      6 | YX               |
| Washington-Arlington-Alexandria, DC-VA-MD-WV   | MONITOR   |      7.05704 | 0.570402 |        0.123409  | False               | anchor_x_growth    | 239424           |                      4 | YX               |
| Atlanta-Sandy Springs-Roswell, GA              | MONITOR   |      3.11402 | 0.747856 |        0.17113   | False               | anchor_x_growth    | 224256           |                      3 | DL               |
| Dayton-Kettering-Beavercreek, OH               | PASS      |     -2.63095 | 0.573105 |        0.932544  | True                | gravity_x_transfer |  28782.8         |                      0 | OO               |
| Hartford-West Hartford-East Hartford, CT       | PASS      |     -4.50634 | 0.583304 |        0.861836  | True                | anchor_x_growth    |  31129.6         |                      0 | OH               |
| Portland-South Portland, ME                    | PASS      |     -7.32469 | 0.629689 |        0.684807  | False               | gravity_x_transfer |  41205.4         |                      0 | YX               |
| Philadelphia-Camden-Wilmington, PA-NJ-DE-MD    | PASS      |    -13.1532  | 0.570367 |        0.173622  | False               | anchor_x_growth    | 139500           |                      5 | PT               |
| Milwaukee-Waukesha, WI                         | PASS      |    -23.2001  | 0.606853 |        0.908604  | True                | anchor_x_growth    |  26048.5         |                      0 | OO               |
| Dallas-Fort Worth-Arlington, TX                | PASS      |    -30.367   | 0.901999 |        0.186597  | False               | anchor_x_growth    | 179990           |                      3 | DL               |
| Cincinnati, OH-KY-IN                           | PASS      |    -56.0793  | 0.603998 |        0.395554  | False               | anchor_x_growth    |  47006.6         |                      1 | 9E               |
| Fort Wayne, IN                                 | PASS      |    -56.8332  | 0.566793 |        0.895287  | True                | gravity_x_transfer |  19395.4         |                      0 | OO               |
| Nashville-Davidson--Murfreesboro--Franklin, TN | PASS      |    -67.0034  | 0.707967 |        0.21026   | False               | anchor_x_growth    |  96873.6         |                      4 | YX               |
| Raleigh-Cary, NC                               | PASS      |    -75.6097  | 0.664361 |        0.315082  | False               | anchor_x_growth    |  57690.8         |                      2 | YX               |
| Houston-Pasadena-The Woodlands, TX             | PASS      |    -76.3661  | 0.925183 |        0.202728  | False               | anchor_x_growth    | 124343           |                      2 | DL               |
| Minneapolis-St. Paul-Bloomington, MN-WI        | PASS      |    -79.9332  | 0.722618 |        0.170237  | False               | anchor_x_growth    | 113349           |                      6 | MQ               |
| Indianapolis-Carmel-Greenwood, IN              | PASS      |    -80.3182  | 0.61695  |        0.489945  | False               | anchor_x_growth    |  33553.5         |                      1 | 9E               |
| New Orleans-Metairie, LA                       | PASS      |    -84.6975  | 0.876055 |        0.357437  | False               | anchor_x_growth    |  63760.1         |                      2 | DL               |
