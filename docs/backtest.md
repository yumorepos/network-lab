# Backtest: pre-2022 model vs 2021-2025 launches

Single fixed-vintage model (gravity 2018-19 x 2018 transfer
anchor, no growth term). Lookahead disclosure in the module
docstring and validation.md. Percentile = where the launched
market ranks among all in-range US metros from that hub.

**Headline N = 48**: routes that actually launched and have a known terminal status (operating/seasonal or ceased). Never-launched and unknown-status routes are reported separately below and are not part of that count.

| group | n | median pctile | mean pctile |
|---|---|---|---|
| ceased | 21 | 0.86 | 0.86 |
| never_launched (excluded from N) | 2 | 0.99 | 0.99 |
| operating | 27 | 0.89 | 0.88 |
| unknown (excluded from N) | 11 | 0.93 | 0.91 |

## Ceased routes by carrier and cause

| carrier | n | cause | informative about route selection? |
|---|---|---|---|
| F8 | 12 | route-level cut by a carrier that kept operating | yes |
| Y9 | 9 | corporate shutdown 2024-02-26 (Lynx ceased all operations at once) | no |

## Separation, computed three ways

| comparison | operating median | ceased median | gap |
|---|---|---|---|
| vs all ceased (n=21) | 0.89 | 0.86 | +0.03 |
| vs ceased excl. Lynx (n=12) | 0.89 | 0.86 | +0.03 |
| vs Lynx-only ceased (n=9) | 0.89 | 0.86 | +0.03 |

## Reading the result, as pre-committed

Separation is weak in every cut, including the one that matters most: most ceased routes (12 of 21) were genuine route-level cuts by Flair, a carrier that kept operating, not casualties of the Lynx shutdown. Those genuine failures (the leisure-market cuts: Mesa, Sanford, Burbank, Las Vegas, Denver, Nashville) also scored in the top demand decile. Three things this actually shows:

1. Nearly every real launch sits in the top decile of modeled demand - carriers do not need a gravity model to find big markets, and a demand screen alone does not predict route survival.
2. Demand ranking did not flag the genuine route-level failures. Flair's cut routes were big leisure markets that failed on economics, competitive response, and fit - layers a demand percentile cannot see. The Lynx rows are separately uninformative: a corporate shutdown says nothing about the routes.
3. Discriminating survival would need the economics and competitive-response layers evaluated at launch vintage - the production refit this project deliberately traded away and discloses.

## Named routes

| carrier | route | launched | status | model pctile |
|---|---|---|---|---|
| WS | YEG-SFO | 2024-06-20 | seasonal | 0.99 |
| F8 | YYZ-SFO | 2022 | unknown | 0.99 |
| PD | YYZ-SFO | 2024-01 | operating | 0.99 |
| Y9 | YYZ-SFO | nan | never_launched | 0.99 |
| Y9 | YYC-LAX | 2023-02-16 | ceased | 0.99 |
| F8 | YEG-BUR | 2021-12-16 | ceased | 0.99 |
| Y9 | YYZ-BOS | nan | never_launched | 0.99 |
| Y9 | YYZ-LAX | 2023-08-24 | ceased | 0.98 |
| PD | YYZ-LAX | 2024-01-16 | operating | 0.98 |
| WS | YEG-ORD | 2025 | unknown | 0.98 |
| WS | YVR-BOS | 2025-06-09 | seasonal | 0.98 |
| PD | YYZ-MDW | 2024 | operating | 0.98 |
| PD | YYZ-PBI | nan | operating | 0.97 |
| PD | YYZ-MIA | nan | operating | 0.97 |
| PD | YYZ-FLL | nan | operating | 0.97 |
| F8 | YKF-FLL | 2021-12-16 | unknown | 0.97 |
| F8 | YUL-FLL | 2021-12-15 | unknown | 0.96 |
| WS | YYC-IAD | 2023-06-02 | unknown | 0.95 |
| WS | YEG-MSP | 2023-06-02 | seasonal | 0.93 |
| WS | YXE-MSP | 2023-06-19 | unknown | 0.93 |
| WS | YEG-ATL | 2024-04-29 | operating | 0.92 |
| F8 | YYZ-DEN | 2022 | ceased | 0.91 |
| F8 | YVR-AZA | 2021-12-17 | ceased | 0.91 |
| Y9 | YYC-PHX | 2023-02-07 | ceased | 0.91 |
| F8 | YEG-AZA | 2021-12-17 | ceased | 0.91 |
| F8 | YYC-AZA | 2021-12-17 | ceased | 0.91 |
| PD | YYZ-SAN | nan | operating | 0.90 |
| WS | YYC-AUS | 2022 | operating | 0.90 |
| F8 | YYZ-BNA | 2022 | ceased | 0.90 |
| WS | YVR-DTW | 2024-04-28 | operating | 0.90 |
| WS | YYC-DTW | 2023-05-26 | seasonal | 0.89 |
| PD | YYZ-PHX | 2024-10 | operating | 0.89 |
| Y9 | YYZ-PHX | 2023-10-12 | ceased | 0.89 |
| WS | YEG-BNA | 2024-05-02 | seasonal | 0.88 |
| AC | YVR-BNA | 2025-06 | operating | 0.88 |
| F8 | YVR-PSP | 2021-12-17 | unknown | 0.86 |
| PD | YYZ-TPA | 2023-11-01 | operating | 0.86 |
| Y9 | YYZ-TPA | 2023-11-16 | ceased | 0.86 |
| WS | YVR-TPA | 2025-06-14 | operating | 0.85 |
| AC | YVR-TPA | 2025-06-03 | operating | 0.85 |
| F8 | YXX-LAS | 2021-12-16 | unknown | 0.85 |
| F8 | YEG-PSP | 2021-12-17 | unknown | 0.85 |
| F8 | YVR-LAS | 2021-12-15 | unknown | 0.84 |
| F8 | YYC-LAS | 2021-12-16 | ceased | 0.83 |
| Y9 | YYC-LAS | 2023-02-24 | ceased | 0.83 |
| F8 | YEG-LAS | 2021-12-16 | ceased | 0.82 |
| PD | YYZ-MCO | 2023-11 | operating | 0.80 |
| Y9 | YYZ-MCO | 2023-01-27 | ceased | 0.80 |
| F8 | YKF-SFB | 2021-12-17 | ceased | 0.80 |
| WS | YYC-RDU | 2025-06-09 | operating | 0.79 |
| F8 | YHZ-SFB | 2021-12-17 | ceased | 0.79 |
| PD | YYZ-PSP | nan | operating | 0.79 |
| F8 | YYZ-PSP | 2021-12-18 | unknown | 0.79 |
| AC | YVR-RDU | 2025-06-04 | seasonal | 0.79 |
| F8 | YUL-SFB | 2021-12-16 | ceased | 0.79 |
| WS | YEG-SLC | 2025-05-15 | operating | 0.79 |
| F8 | YOW-SFB | 2021-12-17 | ceased | 0.79 |
| PD | YOW-MCO | 2023-11 | operating | 0.79 |
| Y9 | YUL-LAS | 2023-08-31 | ceased | 0.77 |
| Y9 | YYZ-RSW | 2023-12-14 | ceased | 0.64 |
| PD | YYZ-RSW | 2023-11 | operating | 0.64 |

Canadian domestic launches are out of model scope (see launches.csv); no public demand truth exists for them.
