# Validation

## Gravity model (holdout, prediction variant)

### current (2023-2024)
- markets: 6092, R2 0.492, holdout median APE 0.62

| size band (pax/yr) | n | median APE | mean APE |
|---|---|---|---|
| 4,000-25,000 | 765 | 0.69 | 1.35 |
| 25,000-100,000 | 265 | 0.40 | 0.46 |
| 100,000-500,000 | 144 | 0.66 | 0.63 |
| 500,000-inf | 40 | 0.84 | 0.82 |

### pre2022 (2018-2019)
- markets: 6002, R2 0.509, holdout median APE 0.60

| size band (pax/yr) | n | median APE | mean APE |
|---|---|---|---|
| 4,000-25,000 | 764 | 0.63 | 1.03 |
| 25,000-100,000 | 261 | 0.44 | 0.53 |
| 100,000-500,000 | 142 | 0.67 | 0.63 |
| 500,000-inf | 38 | 0.80 | 0.79 |

## Transfer factor (2018 anchor)

- pairs: 87, median 0.82, IQR [0.55, 2.04], range [0.27, 8.78]
- per-hub medians: YEG 1.58, YHZ 1.20, YOW 0.82, YUL 0.59, YVR 0.83, YWG 1.94, YYC 1.28, YYZ 0.78
- the dispersion is the honest uncertainty of transferring a US-calibrated model across the border; business cases carry it

## Share model vs observed DB1B shares (SEA, 2024)

- market-carrier rows: 503, MAE 7.0 share points

| market structure | n | MAE (pts) |
|---|---|---|
| 0 nonstop | 17 | 3.4 |
| 1 nonstop | 120 | 7.5 |
| 2 nonstop | 132 | 6.3 |
| 3+ nonstop | 234 | 7.3 |

## Alaska SEA end-to-end note

The alaska_sea study runs the identical chain with demand and
fares observed rather than modeled; its screen output plus the
share MAE above constitute the ground-truth check on the
machinery that scores Canadian transborder candidates.
