# Validation

## Gravity model (holdout, prediction variant)

### current (2023-2024)
- markets: 6092, R2 0.493, holdout median APE 0.62

| size band (pax/yr) | n | median APE | mean APE |
|---|---|---|---|
| 4,000-25,000 | 767 | 0.67 | 1.23 |
| 25,000-100,000 | 276 | 0.42 | 0.49 |
| 100,000-500,000 | 130 | 0.63 | 0.61 |
| 500,000-inf | 41 | 0.82 | 0.80 |

### pre2022 (2018-2019)
- markets: 6002, R2 0.521, holdout median APE 0.65

| size band (pax/yr) | n | median APE | mean APE |
|---|---|---|---|
| 4,000-25,000 | 803 | 0.71 | 1.09 |
| 25,000-100,000 | 244 | 0.50 | 0.60 |
| 100,000-500,000 | 120 | 0.70 | 0.66 |
| 500,000-inf | 38 | 0.81 | 0.79 |

## Transfer factor (2018 anchor)

- pairs: 87, median 0.801, IQR [0.53, 1.99], range [0.26, 8.59]
- per-hub medians: YEG 1.53, YHZ 1.21, YOW 0.80, YUL 0.57, YVR 0.80, YWG 1.89, YYC 1.26, YYZ 0.76
- the dispersion is the honest uncertainty of transferring a US-calibrated model across the border; business cases carry it

## Share model vs observed DB1B shares (SEA, 2024)

- market-carrier rows: 503, MAE 6.7 share points

| market structure | n | MAE (pts) |
|---|---|---|
| 0 nonstop | 17 | 3.4 |
| 1 nonstop | 120 | 7.1 |
| 2 nonstop | 132 | 6.1 |
| 3+ nonstop | 234 | 7.1 |

## Alaska SEA end-to-end note

The alaska_sea study runs the identical chain with demand and
fares observed rather than modeled; its screen output plus the
share MAE above constitute the ground-truth check on the
machinery that scores Canadian transborder candidates.
