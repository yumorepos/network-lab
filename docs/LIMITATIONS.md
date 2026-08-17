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
   from T-100 segment frequencies (same marketing brand, corridor within
   min(nonstop+700mi, 2.0x nonstop), min leg frequency). The wide absolute
   allowance exists because hub connects run far off great-circle
   (YYC-Sacramento via Denver is 1.77x). It overstates connectivity where
   banks don't align and misses interline paths. Residual risk on thin
   markets is handled downstream: any market with modeled share above
   70% and zero nonstop incumbents is flagged high-uncertainty and capped
   at MONITOR, never LAUNCH.

   Direction of error, measured rather than assumed. Through Round 3 this
   entry claimed the reconstruction overstated connectivity and so was
   conservative about the proposed service's share. That was backwards. The
   join matched on the OPERATING carrier, so no mainline-plus-regional
   itinerary was visible at all and competition was understated. Correcting
   the join to the marketing brand moved the median modeled share down by
   24 points at Porter (0.586 to 0.345) and 35 points at Alaska (0.613 to
   0.268), and cut the share-uncertainty guard from 38 to 19 markets at
   WestJet. See INTEGRITY_REPORT.md Round 4.

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

11. **There is no validated right-sizing claim. The schedule step is a fixed
    menu evaluation.** The screen evaluates the study's configured weekly
    frequencies against its configured gauge and reports the best option
    clearing the load-factor floor (assumptions.yaml
    min_feasible_load_factor), or, when none clears it, the highest-load-factor
    option as a fallback. It does not select an aircraft, assign fleet, design
    a schedule, or set departure times, day-of-week banks or seasonality. Each
    study here operates a single transborder or domestic mainline gauge, so no
    gauge comparison occurs in any shipped study; a regional-gauge option was
    NOT invented for WestJet, which flies 737s transborder.

    This component was previously described as frequency and gauge
    right-sizing. That description was **retired rather than repaired**. The
    historical replay measured the step effectively degenerate under the tested
    candidate universe: the menu begins at 3x weekly on one gauge, the great
    majority of decisions reach no schedule comparison at all because no tested
    option is feasible, and the fallback branch returns the highest load
    factor, which on this menu is arithmetically the smallest frequency. A
    reported frequency is therefore not evidence that a comparison happened.
    Counts, the control transition showing the step does not reorder markets,
    and the retirement decision are in `docs/STAGE_2R_DECISION.md`; the
    mechanism is in `docs/STAGE_2R_DIAGNOSTICS.md`. Repairing the claim would
    require gauges the studied carriers do not fly on these routes, schedules
    below a real operation, and a fleet-assignment layer, so the claim was
    narrowed instead.

12. **Already-served markets are excluded, not evaluated as add-frequency.**
    A metro the study carrier already serves nonstop from the hub (any airport
    in the metro, >= ~weekly over the trailing 12 months) is dropped from the
    candidate set: this tool answers "which NEW markets", not "add frequency
    or upgauge an existing route". The exclusion is metro-level to stop the
    leak where a carrier serves a secondary airport (WS flies YYC-IAD, so the
    Washington metro is excluded even though its busiest airport is BWI). The
    exclusion is resolved to the marketing brand, so a metro flown by a wholly
    owned regional counts as served by its mainline; before Round 4 it matched
    the operating carrier and four Horizon-flown Seattle metros leaked into the
    Alaska candidate set. It is cross-checked by the committed
    `data/reference/incumbent_network_202604.csv`, which since Round 4 is built
    from sources independent of the candidate filter
    (`warehouse/incumbent_reference.py`), and `tests/test_sanity.py` fails if
    any screened metro appears in the carrier's incumbent list. One documented
    edge case: Porter's Chicago and Boston history is Billy Bishop (YTZ)
    turboprop service, a different airport and gauge outside this YYZ
    mainline-jet study.

    For the transborder hubs the cross-check is only partially independent.
    DB1B does not cover Canadian origins and no open source gives
    carrier-level Canadian transborder service, so those rows fall back to
    T-100 read along a different axis (the inbound record set, hub as
    destination) rather than a different source. That catches query, brand and
    rollup errors; it cannot catch T-100 itself being wrong.

14. **Air Canada connecting itineraries out of Canadian hubs are invisible.**
    T-100 carries no Canadian domestic segments, so an Air Canada one-stop
    from YYZ over YUL or YVR cannot be reconstructed: leg two is in the data
    and leg one never is. Air Canada appears in the Porter competitive set
    only where it flies a US nonstop from YYZ (23 of 79 candidate metros,
    median 10.4 weekly frequencies once AC, Jazz and Rouge are rolled into one
    brand) and never as a connecting competitor. This understates the real
    incumbent at exactly the hub the portability study is about, and there is
    no open source that fixes it.

13. **Unanchored transborder demand is capped at the survey ceiling.** A
    Canada-US market absent from the 2018 StatCan >4,000 city-pair table had
    at most ~4,000 O&D passengers that year by construction. The US-calibrated
    gravity model over-predicts these small markets (routinely 5-8x the
    ceiling), so their demand is capped at 4,000 x corridor growth (~4,660 for
    YYC) - a generous upper bound. This keeps the screen from manufacturing
    launch verdicts out of gravity noise on markets known to be tiny. Anchored
    markets keep their own observed value; the cap only touches the negative
    space where the model has no ground truth to lean on.
