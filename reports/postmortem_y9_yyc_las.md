# Route post-mortem: Lynx Air YYC-LAS (corporate shutdown)

**One line:** Lynx Air entered a market WestJet had held for years at ~90% load
factor, and exited; the demand model would have green-lit the market on size
alone. Lynx entered YYC-LAS in early 2023 and ceased ALL operations on 2024-02-26 under creditor protection; the route died with the airline, not on its own economics.

- Launch (register): 2023-02-24   Exit: 2024-02-26
- Fate: **corporate shutdown**
- What the model said at launch vintage: **0.83 percentile of all in-range YYC transborder markets (top 17%)**. YYC-LAS is a large
  market, so a demand screen ranks it near the top - which is exactly the
  trap this post-mortem illustrates.

## Capacity and load-factor timeline (T-100, Lynx Air filed as Y9)
| year | subject deps | subject seats | subject LF | incumbent (WS) deps | incumbent LF |
|---|---|---|---|---|---|
| 2018 | - | - | - | 1092 | 0.90 |
| 2019 | - | - | - | 1109 | 0.93 |
| 2021 | - | - | - | 316 | 0.70 |
| 2022 | - | - | - | 806 | 0.88 |
| 2023 | 166 | 31,374 | 0.53 | 1091 | 0.90 |
| 2024 | 18 | 3,402 | 0.50 | 1081 | 0.89 |
| 2025 | - | - | - | 1016 | 0.82 |
| 2026 | - | - | - | 317 | 0.85 |

*(Data note: rows with fewer than 10 departures in a year are suppressed, so a
carrier's first shown year is its first year of sustained service, which can
lag the register's announced launch date - itself a useful reminder that an
announcement and operated capacity are different facts.)*

## What the incumbent did
WestJet did not blink. Its YYC-LAS departures and load factor held through the
entry and the exit (see the incumbent columns above): a fortress-hub incumbent
already serving the market efficiently at high load factor leaves a narrow,
low-yield gap for an entrant, and can hold capacity rather than cede share.

## What the model could and could not see
- **Could see:** the market is large (top-decile demand) and already served
  nonstop by WestJet at high frequency. The share model, given WestJet's
  nonstop presence, would assign the entrant a modest share - a caution the
  demand rank alone does not carry.
- **Could not see:** the entrant's cost structure versus WestJet's, its
  balance sheet, its network feed into LAS, or loyalty and corporate-contract
  lock-in on a heavily-managed leisure-and-business market. These decided the
  outcome and sit in no public segment table.

## Synthesis: why this exit, specifically
Lynx's exit tells us about Lynx, not about YYC-LAS. It flew the route for a single year at about 0.53 load factor, well below Flair's, then a stub of 2024 before the February 26 shutdown took every Lynx route at once. The low first-year load factor hints the market was hard for a third entrant, but the route never got the chance to prove itself: its cause of death was a balance sheet, not a fare war. Treating this as a failed market would teach the model a false negative, which is why the backtest labels corporate-shutdown casualties separately from genuine route-level cuts. A ceased route is not automatically a failed market, and provenance is the difference.

## Same market, different fate
This market carried three carriers with three outcomes, so the market-level
sections above (incumbent behaviour, what the model could and could not see) are
held constant on purpose: the market is the control, and the carrier is the
variable. A demand screen would have ranked both entrants identically on this
pair, yet one exit was an economic verdict and the other was a corporate
collapse. Compare postmortem_f8_yyc_las.md (Flair, same market, route-level cut).
