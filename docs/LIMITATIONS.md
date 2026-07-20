# Limitations

Stated up front because each one shaped a design decision, not discovered
after the fact.

1. **No public Canadian domestic O&D exists.** StatCan discontinued the
   domestic city-pair program; T-100 never contained Canadian domestic
   segments; DB1B is US-only. The project's evidentiary reach is therefore
   transborder for Canadian hubs and full domestic for US hubs. Canadian
   domestic candidates are excluded rather than scored uncheckably.

2. **The transborder demand anchor is frozen at 2018.** StatCan 23-10-0256
   stopped updating. The transfer factor carries 2018 structure forward,
   scaled by T-100 corridor growth. Post-2018 structural shifts (preclearance
   changes, exchange-rate swings, ULCC entry/exit) are absorbed, not modeled;
   the factor's IQR is reported everywhere it is used.

3. **No MIDT/OAG.** Competitor connecting itineraries are reconstructed
   from T-100 segment frequencies (same carrier, corridor within
   min(nonstop+700mi, 2.0x nonstop), min leg frequency). The wide absolute
   allowance exists because hub connects run far off great-circle
   (YYC-Sacramento via Denver is 1.77x). It overstates connectivity where
   banks don't align and misses interline/codeshare paths. Residual risk on
   thin markets is handled downstream: any market with modeled share above
   70% and zero nonstop incumbents is flagged high-uncertainty and capped
   at MONITOR, never LAUNCH.

4. **DB1B has no transborder fares.** Transborder fares are distance-matched
   US fares times a documented premium assumption (sensitivity-tested in
   every scenario grid). No exceptions.

5. **Costs are a fully-allocated proxy.** Direct aircraft operating expense
   (Form 41 P-5.2, fuel rebuilt at scenario prices) times the comparator's
   own indirect burden (P-1.2 total opex over P-5.2 direct opex - derived,
   not assumed), plus a flat Canadian airport/nav fee proxy (+/-30%
   sensitivity, low confidence). A modest double-count between the burden
   and the fee proxy is possible and sits inside the fee's sensitivity band.

6. **US income is per-capita personal income (BEA), not median household
   income (ACS)** unless a CENSUS_API_KEY is supplied; the ACS API now
   requires a key and zero-config reproducibility won.

7. **The backtest uses a single pre-2022 model.** Calibration data (2018-19)
   predates every scored launch, but covariates are current-vintage and the
   transfer factor was estimated once. Mild lookahead, disclosed wherever
   backtest numbers appear. A production system would refit per decision
   date.

8. **Single currency (USD).** CAD conversion would change levels, not
   rankings, and both cost and fare sources are USD.

9. **2020 is excluded everywhere** (calibration, current state, backtest);
   COVID operations are not informative for any of the three uses.

10. **Load-bearing name matches.** City market to CBSA and StatCan city-pair
    parsing are name-based joins with pinned overrides; unmatched traffic is
    logged loudly rather than silently dropped.

11. **Right-sizing is over frequency and gauge, not the full schedule.** The
    screen picks the weekly frequency (from the study's target list) and gauge
    that maximize annual contribution subject to a load-factor floor
    (assumptions.yaml min_feasible_load_factor). It does not optimize
    departure times, day-of-week banks, or seasonality; a real planner tunes
    those too. Each study here operates a single transborder/domestic mainline
    gauge, so frequency is the active axis; the gauge search runs for any
    study that lists more than one, and a regional-gauge option was NOT
    invented for WestJet, which flies 737s transborder.

12. **Already-served markets are excluded, not evaluated as add-frequency.**
    A metro the study carrier already serves nonstop from the hub (any airport
    in the metro, >= ~weekly over the trailing 12 months) is dropped from the
    candidate set: this tool answers "which NEW markets", not "add frequency
    or upgauge an existing route". The exclusion is metro-level to stop the
    leak where a carrier serves a secondary airport (WS flies YYC-IAD, so the
    Washington metro is excluded even though its busiest airport is BWI).

13. **Unanchored transborder demand is capped at the survey ceiling.** A
    Canada-US market absent from the 2018 StatCan >4,000 city-pair table had
    at most ~4,000 O&D passengers that year by construction. The US-calibrated
    gravity model over-predicts these small markets (routinely 5-8x the
    ceiling), so their demand is capped at 4,000 x corridor growth (~4,660 for
    YYC) - a generous upper bound. This keeps right-sizing from manufacturing
    launch verdicts out of gravity noise on markets known to be tiny. Anchored
    markets keep their own observed value; the cap only touches the negative
    space where the model has no ground truth to lean on.
