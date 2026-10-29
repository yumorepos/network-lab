# Limitations

Stated up front because each one shaped a design decision, not discovered
after the fact.

The product this document scopes is **fixed-gauge route screening**. What the
project does and does not claim is frozen in
[FINAL_SCOPE_CONTRACT.md](FINAL_SCOPE_CONTRACT.md); this document is the
evidence boundary behind it.

## 0. What is observed, what is not

Every quantity that carries weight in a verdict, and its evidentiary status. A
reader who wants to know how much to trust a number should start here.

| quantity | status | note |
|---|---|---|
| US domestic O&D demand | OBSERVED | DB1B, a 10% ticket sample |
| Canada-US demand, anchored markets | ESTIMATED from OBSERVED | the market's own 2018 StatCan actual times observed T-100 corridor growth |
| Canada-US demand, unanchored markets | CENSORED and ESTIMATED | absent from the 2018 survey means at most ~4,000 pax that year by construction; capped there, see item 13 and D3A |
| Canadian domestic demand | OUT OF EVIDENTIARY REACH | excluded from candidacy rather than scored uncheckably, item 1 |
| competitor nonstop service | OBSERVED | T-100 segments |
| competitor one-stop itineraries | PROXIED | reconstructed from T-100 frequencies, item 3; VALIDATED for the screening scope, see "Connection and share validation" |
| Air Canada one-stops from Canadian hubs | NOT OBSERVABLE | T-100 carries no Canadian domestic segments, item 14 |
| carrier share | ESTIMATED | QSI-lite; validated against observed DB1B shares at SEA |
| US domestic fares | OBSERVED | DB1B |
| transborder fares | PROXIED | distance-matched US fares times a premium assumption, item 4 |
| direct aircraft operating cost | OBSERVED, comparator | Form 41 P-5.2, fuel rebuilt at scenario prices |
| indirect cost burden | DERIVED | comparator's own P-1.2 over P-5.2 ratio, not assumed |
| airport and nav fees | ASSUMED | flat proxy, low confidence, +/-30% sensitivity, item 5 |
| jet fuel price | OBSERVED | EIA |
| US income | OBSERVED, substituted | BEA per-capita personal income standing in for ACS median household income, item 6 |
| hurdle, BELF cap, load-factor floor | ASSUMED | thresholds in assumptions.yaml with source, confidence and sensitivity |
| schedule selection | NOT VALIDATED, RETIRED | item 11 and D2 |
| incremental predictive ranking value | UNDERPOWERED, NOT DETECTED | see "Predictive evidence and its resolution" |
| launch backtest scores | LOOKAHEAD-AFFECTED | single pre-2022 model, item 7 |
| historical replay inputs | LOOKAHEAD-AFFECTED | five declared residual exceptions, see "Point-in-time provenance" |
| W2.1, W2.2, W2.4, W2.5 | REJECTED | closed as not justified, see "Closed and rejected research" |

## The limitations

Numbering is stable: `PHASE_5_6_PLAN.md` cites these items by number, so items
are never renumbered even when one is rewritten.

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

13. **Unanchored transborder demand is capped at the survey ceiling.** A
    Canada-US market absent from the 2018 StatCan >4,000 city-pair table had
    at most ~4,000 O&D passengers that year by construction. The US-calibrated
    gravity model over-predicts these small markets (routinely 5-8x the
    ceiling), so their demand is capped at 4,000 x corridor growth (~4,660 for
    YYC) - a generous upper bound. This keeps the screen from manufacturing
    launch verdicts out of gravity noise on markets known to be tiny. Anchored
    markets keep their own observed value; the cap only touches the negative
    space where the model has no ground truth to lean on.

    The cap is a censoring rule, not a calibrated estimate. Its consequences
    are separated into D3A and D3B below, which are different problems and are
    not to be conflated.

14. **Air Canada connecting itineraries out of Canadian hubs are invisible.**
    T-100 carries no Canadian domestic segments, so an Air Canada one-stop
    from YYZ over YUL or YVR cannot be reconstructed: leg two is in the data
    and leg one never is. Air Canada appears in the Porter competitive set
    only where it flies a US nonstop from YYZ (23 of 79 candidate metros,
    median 10.4 weekly frequencies once AC, Jazz and Rouge are rolled into one
    brand) and never as a connecting competitor. This understates the real
    incumbent at exactly the hub the portability study is about, and there is
    no open source that fixes it.

---

## Defects found during development, and their disposition

Four defects were found by auditing and replaying the model rather than by it
failing. Each is recorded with what was wrong, how it surfaced, and what was
done, because the disposition is part of the result.

### D1. The corridor-growth vintage. FOUND AND FIXED.

**What was wrong.** The corridor-growth resolver in `replay/vintage.py` was the
one vintage selection applying no exclusion set while every sibling applied
one. A declared structural break year could therefore serve as the numerator of
a growth ratio, so at a 2023-01 decision date the growth term read 0.196 at YYC
and collapsed median anchored WestJet demand from 13,156 to 2,023.

**How it surfaced.** Only the point-in-time replay could expose it. Run at the
current vintage the model never selects a break year, so no amount of testing
the shipped configuration would have found it; it took reconstructing the model
at historical decision dates to make the resolver choose badly.

**How it was repaired.** The smallest rule that removes the inconsistency: the
numerator is the latest complete T-100 year in the permitted window that is not
a declared structural break. It deliberately does not reach the seats vintage,
which is a level input whose exclusion would move the candidate set. The
protocol, including eight falsifiable predictions, was frozen at `7b3a7db`
before the fix existed at `54155d7`.

**What it changed.** Demand levels and economics at one decision date. All
eight predictions held. **Zero verdicts changed in 463 decision rows and both
rankings were identical everywhere.** WestJet ranking and verdict metrics are
unchanged, and Families 1, 3 and 4 are unchanged to three decimals including
bootstrap intervals.

**What is preserved.** The V2 predictive baseline is **immutable** and was not
recomputed. It remains the pre-repair scoreboard, so the before and after can
be compared rather than asserted. See
`docs/change_reports/D1_corridor_growth_vintage.md` and
`docs/W1.4_POST_D1_COMPARISON.md`.

Porter's six predicted verdict changes did **not** occur, exactly as the
protocol declared in advance: Stage 2R.4 had measured a broader counterfactual
than the repair actually made. That is recorded rather than quietly dropped.

### D2. The right-sizing claim. RETIRED, NOT REPAIRED.

Covered in full at item 11. The component was presented as choosing a frequency
and a gauge, and was measured to be effectively degenerate under the tested
candidate universe. The claim was narrowed rather than the model expanded,
because repairing it would need gauges the studied carriers do not fly on these
routes, schedules below a real operation, and a fleet-assignment layer.

### D3A. Survey censoring and downstream asymmetry. DOCUMENTED LIMITATION.

**Keep this separate from D3B.** They are different problems with different
fixes, and treating them as one produced a wrong preliminary conclusion once
already.

A missing StatCan anchor observation is treated as **censored below a
publication floor**, not as a measurement. Every market absent from the 2018
table is assigned the same ceiling value, so capped markets form **tied demand
blocks**: 51, 50 and 49 rows at a single value across the three decision dates.

The asymmetry is between the demand ranking and what happens downstream:

- the tied block sits in the tail: its best demand rank is **50** at WestJet,
  so it reaches **no demand top 20** at any decision date;
- the capped WestJet rows contain **no observed launch**, in rows or in events;
- but the margin score nevertheless pulls part of the block into **its own top
  10 and top 20** (1 and 4 respectively across the three dates, against zero
  for the demand ranking), because cost per departure falls with distance
  faster than fare does, so a short thin market can out-rank a long thicker one
  on margin while ranking far below it on demand. Since the block contains no
  WestJet launch, every such promotion can only cost agreement.

One correction belongs here rather than being quietly dropped: the roadmap's
preliminary note said no capped row is an observed launch anywhere. That holds
for WestJet only. **Porter has one capped row that is a positive**, on one
distinct launch event.

That last point is why this is a real limitation rather than a curiosity: a
tied, censored input can reach a published ordering through a downstream layer.

It is **not established as the primary predictive bottleneck**. Under a
feasibility-gated ordering the block cannot appear at all: **0 of 172
survey-ceiling rows clear the feasibility floor** in the measured Stage 2R
universe, the highest reaching a load factor of 0.078. That measurement is what
makes D3A a documentation item instead of a required fix, and it is guarded by
`tests/test_stage2r_decision.py::
test_no_survey_ceiling_row_clears_the_feasibility_floor`, which fails if a
ceiling row ever clears the floor and D3A becomes a live ranking problem again.

**No claim is made that the cap is statistically optimal.** It is a defensible
upper bound on markets known to be small, chosen because the US-calibrated
gravity model over-predicts them by 5 to 8 times, and nothing more than that.

### D3B. The fixed historical floor. ACCEPTED DOCUMENTED APPROXIMATION.

A separate issue from D3A, and separately disposed of.

The StatCan publication floor **varied historically**. The frozen model uses a
single `SURVEY_THRESHOLD = 4000.0` (`models/demand.py`, and the replay's own
copy in `replay/snapshot.py`) at every decision date, so at vintages where the
real floor differed, the wrong ceiling is applied.

What correcting it would and would not do:

- it **would** move the capped block up or down relative to anchored rows,
  because the ceiling value itself would change;
- it **would not** remove the within-block tie structure. The tie group is the
  same size at every floor from 280 to 4,000 and gets **larger** as the floor
  falls, so a floor correction cannot be sold as removing the compression.

Stage 2R accepted this as an explicit historical approximation rather than a
required final repair, on the grounds that it changes a level rather than the
structure that matters, and that no archived vintage of the floor is available
offline to correct it against.

---

## Point-in-time provenance, and the lookahead that remains

The historical replay reconstructs the full verdict chain at a decision date
from offline point-in-time data, guarded by leakage tests in which all ten
injected leaks were demonstrated to fire. Every vintage carries a provenance
record naming the value actually used.

Five residual lookaheads are **declared rather than eliminated**. They are
generated into `docs/W1.4_replay_results.md` section 6 from the provenance
records themselves, so the list cannot go stale:

1. **BEA CAINC1 and CAGDP2.** BEA revises. The 2020 value read is the revision
   present in the 2026-07-20 file, not the estimate published at the time.
   Irreducible without archived vintages.
2. **StatCan 23-10-0256.** Discontinued after reference year 2018. A planner at
   2022-01 would have wanted 2021 and could only have had 2018. This is the
   frozen model's own anchor limitation, reproduced faithfully at vintage.
3. **EIA jet fuel spot price.** The weekly window ends on the decision date
   itself, so the final observation would in practice have published a few days
   later. One observation of roughly 52 in a trailing average. EIA spot prices
   do not revise, so nothing earlier in the window is affected.
4. **Census CBSA delineation.** The 2023 delineation is the only one cached, so
   counties are rolled up to 2023 metro boundaries at every decision date,
   including dates before it was published.
5. **Carrier operating-to-brand map.** `carrier_families.csv` and
   `carrier_codes.csv` carry no effective dates and brands resolve from a fixed
   DB1B year. Air Wisconsin flew for United through early June 2023, then American March 2023-April 2025; Mesa's
   American agreement ended 2023.

**Revised historical information is not contemporaneously known information.**
Items 1 and 4 in particular read values a decision maker at the time could not
have had, and are described that way rather than as point-in-time inputs.

The separate launch backtest carries its own, larger, disclosed lookahead: a
single pre-2022 model scores every launch (item 7).

---

## Predictive evidence and its resolution

**The claim, in full:**

> On the WestJet Calgary historical replay, the full engine showed no
> detectable incremental ranking value over a demand-only baseline at effects
> larger than the study's resolution. Smaller effects remain unresolved.

**What bounds it.** The resolution of the comparison was measured before the
comparison was interpreted, in `docs/STAGE_2R0_RESOLUTION.md`:

- **15 positive rows rest on only 10 distinct launch events**, five of which
  are scored at two decision dates. Any count treating the positive rows as
  independent observations overstates the evidence by half.
- **3 decision vintages.**
- An improvement worth about **5 or more net launch events, spread across at
  least two of the three vintages, would usually be visible**. Four or fewer
  cannot be distinguished from zero.
- **The largest observed difference is one event.** Every non-zero number in
  the frozen Family 4 headline is a single launch label changing at a single
  date, and the whole six-number headline rests on two such changes.
- **An improvement confined to one vintage is never detected**, at any
  magnitude this sample permits. That is exactly the shape of the observed
  k=10 result.
- **k=20 is arithmetically saturated.** The demand comparator already places
  every positive inside its top 20 at all three dates, so headroom is zero and
  its 0.000 difference is a property of the candidate set rather than a
  measured tie.

**The 5-event floor is a floor, not an estimate.** It was built by an oracle
construction that moves exactly the right rows all the way with no error
elsewhere in the ranking. No real component behaves like that, so a genuine,
honestly scored effect must be larger than that to be detected.

**What this does and does not license.**

- Only large effects are distinguishable.
- **Absence of detected lift does not prove equivalence.** The null is
  underpowered, not empty.
- The metro-cluster bootstrap handles repeated markets and the panel structure,
  but **not** three-date vintage uncertainty; all three dates appear in all
  2,000 resamples by construction.
- **The project does not claim validated predictive superiority**, and it does
  not claim the model has been shown equivalent to demand ranking either.

Two shortenings are wrong and are specifically not used anywhere in this
repository: "the model does not beat demand" asserts an equivalence the design
cannot deliver, and "the model works" asserts a lift never observed.

---

## Connection and share validation

**Verdict: CONNECTION SHARE VALIDATED FOR FINAL SCOPE.**

The competition and share layer is one of only two layers that materially
reorder the candidate ranking, and it rested almost entirely on the one-stop
reconstruction while being validated almost entirely outside that regime: the
published check used a 50,000 passenger floor, and large markets have nonstops,
so the floor selected against the structural regime the flagship study occupies.

The gap was that the check's sampling floor selected against the regime, not
that the regime is unobservable. Lowering the floor to the 4,000 passengers the
demand layer already uses, at the same hub, with no hub added and nothing
refitted, makes the zero-nonstop regime the **largest** stratum. Sample sizes
and metrics are in `docs/change_reports/T3_connection_share_validation.md` and
in `data/parquet/outputs/share_validation_by_stratum.parquet`; the layer beats
an equal-share null on the stratum that matters and tracks the ordering of
observed shares.

**Scope of the claim.** This validates the competition and share layer **for
the scoped fixed-gauge screening use case**, in the structural regime the
flagship study actually occupies. It is not a claim that all airline connection
behaviour is validated, that the reconstruction recovers real itineraries, or
that the layer would hold up in regimes it was not tested in. The known
overstatement of connectivity where banks do not align (item 3) and the
invisibility of Air Canada one-stops (item 14) are unaffected by it.

The protocol, including the strata, sample minimums and the decision rule, was
frozen at `c889a3d` before the stratified check existed, so none of it could
have been chosen to match an outcome. W2.3 is closed with **no refit**.

---

## Closed and rejected research

These are **completed research decisions, not unfinished work**. Each was
evaluated against evidence and closed. None is a backlog item.

| task | disposition | why |
|---|---|---|
| **W2.1** DB1B Coupon and Ticket ingestion | NOT JUSTIFIED | the gate it had to clear was never met |
| **W2.2** additional brand mapping | NOT JUSTIFIED | settled by measurement: unresolved regional flying is under 0.15% of hub-origin departures at all three hubs |
| **W2.3** one-stop reconstruction validation | COMPLETED as validation | closed above, no refit required |
| **W2.4** QSI fitting | NOT JUSTIFIED | the gate was that frequency or competitive responsiveness be the bottleneck. It is not: the frequency exponent sets a crossover the candidate sets never approach, and fitting it changes nothing for the fallback rows |
| **W2.5** fare segmentation | NOT JUSTIFIED | the gate it had to clear was never met |
| right-sizing expansion | REJECTED, DE-SCOPED | would require gauges the carriers do not fly, schedules below a real operation, and a fleet-assignment layer |
| additional airlines | REJECTED | scope expansion; adding carriers to raise N was declined rather than used to manufacture statistical power |
| ADS-B ingestion | DEFERRED, NOT TRIGGERED | its trigger condition never fired |
| further model tuning after the Stage 2R gate | STOPPED | no W2 calibration could be justified by an expected gain in a Family 4 metric, because Stage 2R.0 showed the metric cannot resolve the gains on offer |

The general rule applied at the Stage 2R gate: a calibration task must be
justified by evidence that it addresses a measured bottleneck, and an expected
improvement that the study cannot detect is not a justification.
