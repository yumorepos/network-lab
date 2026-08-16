# Milestone A independent adversarial review

**Reviewer.** Independent Claude Code session, no implementation context.
**Review target.** `d514ec2` on `claude/network-lab-finalization`.
**Baseline.** `e5f0e550c62c6ac19044f9c8593c6a55e061cf40`.
**Date.** 2026-08-14.
**Claim under review.** `MILESTONE A READY FOR INDEPENDENT REVIEW`.

No implementation file was modified. The only file this review creates is this
one. `make reproducibility` rewrote the 14 tracked output Parquet files with
float noise as it is designed to; after the content check passed they were
restored with `git checkout -- data/parquet/outputs` and the tree is clean.

---

## 0. Summary

The engineering claims hold up. I could not find a defect that invalidates the
V2 baseline, and several claims are understated rather than overstated: parity
is materially stronger than the parity tests assert, and the leakage guards fire
against real resolver mutations, not only against the demonstration script's
own injections.

Two findings are material enough to rank P1, and neither is a leak that
happened. The first is a leak that **would not be caught**: the corridor-growth
year and the fuel `as_of` are the two vintage paths with the largest numeric
leverage in `snapshot(t)`, and both have zero guard coverage and no provenance
record. I proved this by mutation, not by inspection. The second is that the
WestJet Family 4 headline rests on one of three decision dates, and the frozen
protocol required the per-date breakdown that would have shown this. It was not
published.

On D1, I reached a conclusion the completion report does not state and that
changes the roadmap question. **The corridor-growth term is a pure
multiplicative scalar on transborder demand, so it cannot change the demand
ranking at all.** I verified rank invariance directly. D1 therefore degrades
the treatment (`margin_pct`) while leaving the comparator (`demand_pax_yr`
percentile) untouched. That asymmetry sounds like it should rescue the Family 4
null, and on the per-date numbers it does not: at 2022-01, where growth is
1.057 and D1 is absent, the model minus demand difference is already exactly
0.000 at k=10 and -0.200 at k=5.

| | verdict |
|---|---|
| **Milestone A** | see section 18 |
| **Roadmap** | see section 18 |

---

## 1. Repository and gate verification

| check | result |
|---|---|
| `HEAD` | `d514ec2681d4f45f7adda9039c52692f511990f6` |
| `e5f0e55` is an ancestor of `d514ec2` | yes |
| branch | `claude/network-lab-finalization` |
| working tree at review start | clean |
| files changed `e5f0e55..d514ec2` | 24 files, +4,745 / -50 |
| source cache committed or modified | no; `git ls-files data/` returns the same 27 output artifacts plus `data/reference/`, all unchanged |
| `config/assumptions.yaml` | sha256 `65fe6b2ce6311dd9ad9ccda48b487b745ad23fa59f6053c289608f7d5529113d`, byte identical to the V1 freeze commit `bd7d4dd` and matching the hash recorded in `docs/W1.4_baseline_freeze.md` |
| model defaults | untouched; no study config changed |

Independently run, from the frozen cache, no network:

| gate | reported | measured |
|---|---|---|
| `make test` | 94 passed | **94 passed in 164.40s** |
| `make reproducibility` | 27 artifacts identical | **27 artifacts identical, exit 0** |
| `scripts/demo_leakage_tests.py` | 10 of 10 fired | **10 of 10 fired** |

`make data` was not run. Nothing was downloaded.

---

## 2. The three production refactors

All three preserve production behaviour, and I verified this at the artifact
level rather than by reading the defaults.

- `models/catchment.py:metro_anchor_points(con, seats_year=2024, metro_override=None)`.
  Defaults reproduce the original SQL exactly. The historical path is reachable
  only by passing `metro_override`, which no production caller does.
- `models/economics.py:fuel_price_base(con, as_of=None)`. The `as_of is None`
  branch is the original statement verbatim.
- `models/demand.py:anchor_finder(con, hub, year="2018")`. The inline block was
  extracted, not duplicated; the old copy is deleted. `REF_DATE='2018'` became a
  parameter bound to `"2018"` by default.

No conditional branch changes current behaviour, and no duplicated
implementation remains that could drift. `make reproducibility` at 27 artifacts
identical, run against a full warehouse rebuild, is the load-bearing evidence.

Two cosmetic notes, neither behavioural: `metro_pit_override` is registered on
the shared connection and never unregistered, and the emitted column is still
named `anchor_2018_pax` when the anchor year is not 2018.

---

## 3. Point-in-time correctness of `snapshot(t)`

I recomputed the vintage table from `replay/vintage.py` against
`config/replay_protocol.yaml` and reproduced the protocol's section 1.2 table
exactly.

| cutoff | T-100 through | DB1B | Form 41 | BEA | StatCan CMA | anchor | gravity | seats |
|---|---|---|---|---|---|---|---|---|
| 2022-01 | 2021-10 | 2019 | 2019 | 2020 | 2020 | 2018 | pre2022 | 2019 |
| 2023-01 | 2022-10 | 2021 | 2021 | 2021 | 2021 | 2018 | pre2022 | 2021 |
| 2024-01 | 2023-10 | 2022 | 2022 | 2022 | 2022 | 2018 | pre2022 | 2022 |

Checked and clean:

- **Gravity.** `gravity_pre2022.yaml` records `years: [2018, 2019]`, so the
  calibration data is genuinely pre-cutoff. `current` (2023-2024) is refused at
  all three cutoffs by the publication test, not by a hardcoded choice.
- **Seats.** `seats_year` is the latest complete T-100 year inside the permitted
  window, not the production 2024.
- **T-100 windows.** Both the served-market window in `build_candidates` and the
  competition window in `build_share` are bounded above by `v.t100_max_ym`.
- **Fuel.** `fuel_as_of` is set to the cutoff date and passed through.
- **Anchor.** The StatCan table stops at reference year 2018, so the stale
  anchor is real and is recorded as `stale_historical_anchor`.

Disclosed residual lookaheads, all three correctly declared and all three
irreducible offline: BEA and StatCan revisions, the 2023 CBSA delineation before
its 2023-07 release, and the carrier brand map's fixed DB1B year.

**Two gaps in the provenance claim.** `replay/vintage.py`'s docstring states
that every historical observation a snapshot reads carries a provenance record
and that the snapshot fails closed if any of the six questions is unanswerable.
That is not true of two inputs:

1. **EIA jet fuel.** `resolve_vintages` emits no `Provenance` for `fact_fuel`.
   The fuel vintage is applied but never recorded.
2. **The corridor-growth year.** `build_transfer` derives `latest_full` from
   `v.t100_max_ym` inside the function. It is the single most influential number
   in transborder demand and it produces no provenance row.

Both are covered further in section 6, where I show neither is guarded either.

**Undisclosed component of the brand-map lookahead.** `models/carriers.segment_brands`
resolves brands over `_segment_window(con)`, which is the **panel-end** trailing
twelve months (202604), at every historical cutoff. The declared exception names
the fixed DB1B year but not the T-100 window. Measured at the 2022-01 cutoff:
4,924 regional-operator segment triples exist in the vintaged window with no
brand-map row at all, 25 of them touching SEA. Those fall back to the operating
certificate, so a metro flown by a wholly owned regional can read as unserved.
This is the exact leak class the production code fixed for Horizon and Alaska.
**WestJet is unaffected** (verified in section 9), so the headline cell does not
inherit it.

---

## 4. Fail-closed offline behaviour

Proven independently, not read.

- I replaced `requests.get`, `requests.post`, `requests.Session.request` and
  `ingest.common.download_file` with functions that raise, then ran
  `snapshot("westjet_yyc", 202301)`. It completed normally: 80 candidates, 80
  PASS. No network path is on the replay's critical path.
- With `pit_metros.PIT_DIR` redirected to an empty temp directory and `CAINC1`
  pointed at a nonexistent file, `build_us(force=True)` raised `CacheMissing`.
  The subsequent `resolve_vintages` call in my own harness also died with
  `CacheMissing` rather than substituting a current file, which is itself the
  behaviour under test.
- `grep` confirms no module under `replay/` imports or calls a downloader; only
  the `ROOT` / `DATA_RAW` / `DATA_PARQUET` path constants come from
  `ingest.common`.

`ingest.common.download_file` does fail **open** to the network when a cached
file is absent, exactly as the docstring warns, which is why the separation
matters.

---

## 5. Current-cutoff parity: what is and is not proven

The 15 committed parity tests cover the candidate set, verdict market by
market, `chosen_freq_wk`, `demand_pax_yr` to 1e-9, and the headline totals.

I ran a production-pinned snapshot myself and compared **every** numeric and
categorical field against the committed screens, including the fields the tests
do not touch.

| field | WestJet | Alaska | Porter |
|---|---|---|---|
| `margin_pct` | max rel 7.8e-16 | 4.1e-16 | 1.1e-15 |
| `fare_down_margin` | 7.5e-16 | 5.7e-16 | 7.3e-16 |
| `fuel_down_margin` | 7.0e-16 | 4.4e-16 | 9.8e-16 |
| `belf` | 4.9e-16 | 4.2e-16 | 5.7e-16 |
| `load_factor`, `proposed_share`, `demand_pax_yr`, `chosen_freq_wk`, `chosen_seats`, `n_nonstop_incumbents` | exact | exact | exact |
| `annual_contribution` | 2.6e-16 | 2.1e-16 | 9.0e-16 |
| `verdict`, `chosen_gauge`, `confidence`, `top_competitor` | 0 mismatches | 0 | 0 |

**Parity is proven for the whole chain, not only for verdicts.** The claim in
the completion report understates what actually holds.

What parity does **not** prove: that the vintage-sensitive query rewrites are
correct at a historical cutoff. Parity pins the replay to production vintages,
so it exercises the `v.label == "production"` branches. The historical branches
of `build_candidates`, `build_transfer` and `build_demand` are covered by the
leakage tests and by the behavioural Porter check, not by parity. That
separation is stated correctly in the module docstring.

**One coverage gap worth closing.** `margin_pct` is the frozen Family 1 and
Family 4 ranking score, and it has no parity assertion. It matches today, to
8e-16, so nothing is wrong; but the field that drives the headline metric is the
one field the guard does not watch, and verdict equality is a coarse proxy for
it because verdicts are thresholded.

---

## 6. Do the leakage tests catch what they claim?

I did not accept the demonstration script as evidence. Six of its ten injections
mutate a `Vintages` dataclass field after resolution and then re-assert an
**inline copy** of the guard's assertion. That proves the arithmetic of the
assertion, not that the committed test would fail against a defective
implementation, and the duplicated assertions can drift from the tests they
mirror. Injection 9 is close to tautological: it computes both sides of the
comparison from `production_vintages()`, so the values are identical by
construction. Injections 4, 6, 8 and 10 do exercise real code paths and are
sound.

So I ran my own mutation suite: five **real implementation defects** patched
into the source functions, with the committed
`tests/test_replay_leakage.py` run unmodified against each.

| mutation | defect class | committed guards |
|---|---|---|
| `_latest_complete_year` ignores publication lag, returns newest cached year <= cutoff year | resolver ignores publication date | **9 failed**, 27 passed |
| `t100_max_ym` returns the cutoff with no lag | T-100 window reaches the cutoff | **3 failed**, 33 passed |
| `seats_year` pinned to the production 2024 | current source year selected | **3 failed**, 33 passed |
| `build_transfer` takes the growth year from the panel end (202604) | future T-100 drives the demand level | **0 failed, 36 passed** |
| `build_economics` calls `fuel_price_base(con, None)` | fuel price not vintaged | **0 failed, 36 passed** |

The first three confirm the guards are not tautological: they bite against
genuine resolver defects, not only against post-hoc field mutation. This is
stronger evidence than the demonstration script provides.

The last two are the P1 finding. Impact, measured:

| leak | 2022-01 | 2023-01 | 2024-01 |
|---|---|---|---|
| growth year from the panel end | 1.06x demand level | **5.73x demand level** | 1.52x demand level |
| fuel price not vintaged | **+43.0%** ($1.849 to $2.644/gal) | -21.6% | -2.1% |

Both defects are plausible implementation slips, both change the primary metric
substantially, and both pass every guard the project has. The code is correct
today. The guard is missing.

Vectors that are guarded and do fire: publication-date-ignoring resolvers,
current or future source years, future geography, future gravity calibration,
future incumbent network (the Porter behavioural test is the strongest single
guard in the suite), and offline fail-closed behaviour. Brand and fleet vintage
leakage is **disclosed but not guarded**, and section 3 shows the disclosure is
incomplete.

---

## 7. Prospective protocol timeline

Verified from git, not from the report.

| commit | time | contents |
|---|---|---|
| `3c22797` | 19:12:56 | Stage 0 feasibility |
| `a20a9a0` | 19:25:06 | Stage 0 correction, 2020 and 2021 excluded |
| `411d604` | 19:30:15 | W1.4 criterion amendment |
| `fcaf56b` | 19:57:59 | `replay/` machinery, `config/replay_protocol.yaml`, both test files |
| `e6ea62e` | 20:00:05 | **`docs/W1.4_REPLAY_PROTOCOL.md` only** |
| `999f4f5` | 20:26:42 | `run_replay.py`, `report.py`, `diagnostics.py`, results doc |
| `d514ec2` | 20:49:45 | V2 freeze, completion report |

- `git ls-tree e6ea62e -- replay/` returns `__init__.py`, `pit_metros.py`,
  `snapshot.py`, `vintage.py` and **not** `run_replay.py` or `report.py`. The
  metric code did not exist when the protocol was frozen. The claim is true.
- `docs/W1.4_REPLAY_PROTOCOL.md` appears in exactly one commit, `e6ea62e`. It
  was never edited after results were seen.
- `config/replay_protocol.yaml` appears in exactly one commit, `fcaf56b`, before
  the protocol document and before any replay ran. The frozen frequency proxy
  therefore predates the document that cites it.
- The feasibility classifications were fixed at `a20a9a0` and are hardcoded in
  `replay/report.py:FEASIBILITY`, matching section 6 of the protocol.

The section 8.1 disclosure is adequate for what it names. I looked for anything
else that should have been in `known_before_protocol` and found one candidate:
the 2022-01 candidate counts are disclosed for WestJet and Porter but not for
Alaska, and the 2024-01 verdict counts are disclosed for all three. Neither
omission could have biased a design choice, because the ranking score, k values,
bootstrap unit, horizons, frequency proxy and metric definitions are all
independent of candidate counts. I found no evidence of post-hoc alteration of
any of those.

The disclosure of Porter's 2 LAUNCH at 2024-01 is handled correctly: named as
the one item that could bias a later choice, with the affected design decisions
listed as already frozen.

---

## 8. Independent reproduction of Family 1 and Family 4

Recomputed from `decision_rows.parquet` with my own implementations of
agreement@k and recall@k, not the project's.

| metric | reported | reproduced |
|---|---|---|
| model agreement@10 | 0.333 | **0.3333** |
| demand agreement@10 | 0.300 | **0.3000** |
| model recall@10 | 0.679 | **0.6794** |
| demand recall@10 | 0.568 | **0.5683** |

Sample sizes reproduce exactly: WestJet 244 rows / 89 metros / 15 positives
(7, 5, 3 by date); Alaska 131 / 45 / 1; Porter 88 / 88 / 6; 463 and 22 in total.

Construction checks:

- **Denominator.** The candidate set generated at the cutoff, 88 / 80 / 76 for
  WestJet. Correct.
- **Positive labels.** Built as `first_ym` in `(t, t+24]`, set semantics per
  metro. For WestJet, **7 of 7, 5 of 5 and 3 of 3 launched metros are inside the
  candidate set**; nothing is silently dropped from the recall denominator.
- **Already-served exclusion.** For every one of the 15 WestJet positives I
  checked whether the metro was served by any WestJet-family certificate
  (WS, WO, WR) at >= 26 departures in the vintaged trailing window. None was.
  The register contains only WS spells for YYC to US, so the brand-map gap of
  section 3 does not reach this cell.
- **Repeated markets.** A metro appears at up to three dates; the bootstrap
  clusters on `cbsa` so its rows travel together. Re-entries count once.
- **Ties.** No tie straddles any reported k boundary in any study or cutoff, so
  the arbitrary `nlargest` tie-break does not affect a single published number.
- **Identical rows.** Both scores are computed on the same frame in the same
  loop. Confirmed.
- **Positive-unlabeled.** Correctly stated in the protocol, the results document
  and the V2 freeze. No precision figure is reported. Good.

One structural fact the documents do not state, and it is the mechanism behind
the null:

| study | cutoff | Spearman(`margin_pct`, demand pct) | top-10 overlap |
|---|---|---|---|
| westjet_yyc | 2022-01 | +0.866 | 8 of 10 |
| westjet_yyc | 2023-01 | +0.788 | 8 of 10 |
| westjet_yyc | 2024-01 | +0.771 | 7 of 10 |
| alaska_sea | 2022-01 | +0.917 | 8 of 10 |
| porter_yyz | 2024-01 | +0.939 | 9 of 10 |

**The full engine's ranking score is largely a monotone re-expression of its own
demand estimate.** Family 4 is not measuring two different models; it is
measuring how much the share, fare and cost layers perturb a demand ordering,
and the answer is: enough to move two or three markets in a top ten.

A second structural fact: 51 of 88, 50 of 80 and 49 of 76 WestJet rows carry
**identical** demand, the capped survey ceiling. The demand comparator can only
rank the anchored minority. It does not affect the reported k values (the ties
sit below the k=20 boundary) but it means the comparator is degenerate over
about 62% of the candidate set.

---

## 9. Temporal-uncertainty review (required diagnostic)

This is the concern that motivated the review, and it is justified.

The bootstrap resamples metros. Every resampled metro carries all of its rows
across all three dates, so the **set of decision dates is never resampled**. The
intervals are conditional on the three vintages actually drawn. Any shock common
to a date, and D1 is proof that such shocks exist and are large, is invisible to
them.

### 9a. Family 1 and Family 4 by decision date (WestJet)

Required by the frozen protocol sections 3 and 5. Not published. Computed here.

| cutoff | n | pos | agree@10 model | agree@10 demand | diff | recall@10 model | recall@10 demand | diff |
|---|---|---|---|---|---|---|---|---|
| 2022-01 | 88 | 7 | 0.400 | 0.400 | **0.000** | 0.571 | 0.571 | **0.000** |
| 2023-01 | 80 | 5 | 0.400 | 0.400 | **0.000** | 0.800 | 0.800 | **0.000** |
| 2024-01 | 76 | 3 | 0.200 | 0.100 | **+0.100** | 0.667 | 0.333 | **+0.333** |

At k=5 and k=20 the differences are 0.000 at every date except k=5 at 2022-01,
where the model is **worse** (-0.200 agreement, -0.143 recall).

### 9b. Leave one decision date out

| subset | n | pos | diff agree@10 | diff recall@10 |
|---|---|---|---|---|
| exclude 2022-01 | 156 | 8 | +0.050 | +0.167 |
| exclude 2023-01 | 164 | 10 | +0.050 | +0.167 |
| **exclude 2024-01** | 168 | 12 | **0.000** | **0.000** |
| all three (published) | 244 | 15 | +0.033 | +0.111 |

### 9c. Reading

**The entire pooled positive difference comes from 2024-01.** Drop that one
date and both differences are exactly zero. Drop either other date and the
result is unchanged in direction and roughly 50% larger.

At 2024-01 the difference is one market: Anchorage sits tenth by `margin_pct`
and outside the top ten by demand, and it launched. The published headline
"+0.111 recall@10" is one market at one decision date.

Do the metro-cluster intervals overstate precision? **Yes, but the headline is
not the place it bites.** `diff recall@10` is already reported as
`+0.111 [-0.333, 0.333]`, which spans zero comfortably; a date-aware interval
would only widen it. Where it bites is the level estimates that the V2 document
calls "THE SCOREBOARD": `agreement@10 = 0.333 [0.133, 0.500]` and
`recall@10 = 0.679 [0.325, 0.953]` are intervals over metros within three fixed
vintages, and the per-date values (0.400, 0.400, 0.200 and 0.571, 0.800, 0.667)
show real date-to-date movement that the interval does not represent. A future
change scored against those bounds could look significant on vintage variation
alone.

I have deliberately not manufactured a confidence interval from three temporal
blocks. Three is not enough, and the decomposition above is more informative
than any interval derived from it would be.

**Classification: limitation, not blocker.** The Family 4 conclusion is
unchanged, because the only date that produces a positive difference produces it
from one market, and two of three dates produce exactly zero. The limitation is
that the published intervals must not be read as sampling variability across
decision vintages, and the per-date table above must accompany the pooled
figure.

---

## 10. D1: the COVID corridor-growth defect

### 10a. Verified from source

Recomputed the T-100 corridor ratio directly from `fact_segment`, transborder
pax against reference year 2018:

| hub | 2019 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|
| YYC | 1.057 | **0.196** | 0.739 | 1.084 | 1.165 |
| YYZ | 1.014 | **0.166** | 0.665 | 0.867 | 0.932 |

`build_transfer` selects the latest complete T-100 year inside the permitted
window, which is 2019, **2021** and 2022 at the three cutoffs. The reported
0.196 and 0.166 are correct. Median anchored WestJet demand at 2023-01 is 2,023,
matching the report; at the 2019 ratio the same rows would sit at 10,924.

### 10b. Rows and labels affected

| cutoff | rows | anchored | capped | positives |
|---|---|---|---|---|
| 2022-01 | 88 | 37 | 51 | 7 |
| 2023-01 | 80 | 30 | 50 | **5** |
| 2024-01 | 76 | 26 | 49 (+1 gravity) | 3 |

All 80 rows and all 5 positives at 2023-01 are affected, and all 88 Porter rows
at 2024-01 carry the 0.665 YYZ ratio. That is 80 of 463 decision rows and 5 of
22 positives at the severe value, one third of the WestJet cell.

### 10c. The finding the completion report does not make

Anchored demand is `anchor x growth`, and unanchored demand is
`min(gravity x factor x growth, 4000 x growth)`, which factorises to
`growth x min(gravity x factor, 4000)`. **Growth is a strictly positive common
scalar on every row.** I verified rank invariance directly: at all three
cutoffs, `rank(demand)` and `rank(demand / growth)` are identical.

Consequences:

- **`score_demand` is exactly unaffected by D1.** The Family 4 comparator cannot
  move, at any cutoff, for any value of growth.
- **`score_model` is affected**, because `margin_pct` depends on the demand
  level through spill, the load-factor floor and service selection.
- At 2023-01 the collapse drives every market deep into the linear spill regime
  and every service choice to the minimum option, which makes `margin_pct` a
  near-monotone function of demand. The measured difference at that date is
  0.000 at every k. **D1 degrades the treatment towards the comparator.**

So D1 does bias Family 4 against the full engine, exactly as suspected. But the
size of that bias is bounded by what the clean dates show, and they show the
same zero: at 2022-01, growth 1.057, the difference is 0.000 at k=10 and
**negative** at k=5.

### 10d. Effect on verdicts and margins

At 2023-01, WestJet is 80 PASS out of 80 and median margin is about -3,800%.
At 2022-01, the same engine returns 1 LAUNCH, 6 MONITOR, 81 PASS. The verdict
distribution at 2023-01 is an artifact of D1 and carries no information.

### 10e. Classification

**B. Usable only with a major qualification.**

Not A, because one third of the WestJet evidence is uninformative by
construction: at 2023-01 the model is not being tested, it is being asked to
rank markets it believes have shrunk by 80%, and it degenerates into the
comparator.

Not C, because D1 cannot explain the null. The comparator is provably immune to
it, the null holds at the two dates where D1 is absent or mild, and the one
positive difference in the whole study comes from 2024-01, the second least
affected date. Fixing D1 removes a corrupted cell; it does not obviously create
a difference where the clean cells show none.

The qualification that must accompany every future use of this baseline: the
WestJet cell is effectively **two** informative decision dates, not three.

---

## 11. Right-sizing

The paired sample reproduces exactly. I rebuilt the T-100 monthly panel,
re-derived spells, recomputed all three approved proxies and repeated the
pairing rule independently: **18 pairs, 10 WestJet / 2 Alaska / 6 Porter**, and
`first3_max` reproduces the register's `initial_freq_wk` to 0.00e+00.

Convention checks all pass: `initial_freq_wk` is one-way weekly
(`max(deps_one_way over the first three active months) / 4.348`), matching
`chosen_freq_wk`, which counts one-way departures from the hub. Pairing takes
the last decision date strictly preceding `first_ym`. Matching is metro to
metro. Re-entries pair on their own spell.

`chosen_freq_wk == 3` on 18 of 18 pairs and 461 of 463 decision rows. The
configured option list is `[3, 7, 14]` in all three studies, so 3 is genuinely
the minimum. **"The frequency selector is effectively constant" is supported.**

### 11a. The frozen protocol required the secondaries, and they change the story

Protocol section 5 froze `first3_max` as primary and required `first_month` and
`first3_median` to be **reported as secondaries**, on the stated grounds that the
three proxies move the target by 28% to 46%. Neither secondary is computed in
`run_replay.family_3` or printed by `replay/report.py`. Supplying them:

| proxy | study | n | median obs | median ratio | median bias | mean bias | MAE |
|---|---|---|---|---|---|---|---|
| **first3_max** | westjet_yyc | 10 | 2.99 | 1.003 | +0.010 | +0.010 | 0.922 |
| | alaska_sea | 2 | 7.01 | 0.428 | -4.014 | -4.014 | 4.014 |
| | porter_yyz | 6 | 6.55 | 0.461 | -3.554 | -4.896 | 4.899 |
| | pooled | 18 | 4.14 | 0.725 | -1.140 | -2.072 | 2.591 |
| **first3_median** | westjet_yyc | 10 | 2.99 | 1.003 | +0.010 | +0.309 | 0.717 |
| | alaska_sea | 2 | 6.09 | 0.507 | -3.094 | -3.094 | 3.094 |
| | porter_yyz | 6 | 6.32 | 0.478 | -3.324 | -4.474 | 4.554 |
| | pooled | 18 | 3.56 | 0.842 | -0.565 | -1.663 | 2.260 |
| **first_month** | westjet_yyc | 10 | 1.61 | **1.902** | **+1.390** | +1.390 | 1.390 |
| | alaska_sea | 2 | 3.22 | **0.932** | -0.220 | -0.220 | 0.220 |
| | porter_yyz | 6 | 4.60 | 0.743 | -1.600 | -3.593 | 4.370 |
| | pooled | 18 | 2.18 | **1.377** | +0.815 | -0.450 | 2.253 |

Under `first_month` the pooled direction **flips** from under-sizing (0.725) to
over-sizing (1.377), WestJet goes from calibrated-looking to nearly double, and
Alaska's factor-of-two under-sizing shrinks to 0.932. The primary remains the
primary and I am not proposing to change it. But the frozen protocol required
these numbers precisely so a reader could see this, and without them the
statement "Alaska and Porter under-size by roughly a factor of two" reads as more
robust than it is.

### 11b. The seasonal split was also required and not published

| split | n | median observed | median ratio | MAE |
|---|---|---|---|---|
| westjet_yyc, seasonal | 8 | 3.10 | 0.968 | 1.064 |
| westjet_yyc, year-round | 2 | 2.64 | 1.154 | 0.355 |
| porter_yyz, seasonal | 2 | 4.48 | 0.753 | 1.495 |
| porter_yyz, year-round | 4 | 7.13 | 0.421 | 6.602 |
| alaska_sea, year-round | 2 | 7.01 | 0.428 | 4.014 |
| **pooled, seasonal** | 10 | 3.10 | 0.968 | 1.150 |
| **pooled, year-round** | 8 | 7.01 | 0.428 | 4.393 |

Eight of WestJet's ten pairs are seasonal. Its median observed opening of 2.99
weekly is a seasonal-route statistic, and the under-sizing is concentrated
entirely in year-round launches. This strengthens the D2 conclusion rather than
weakening it, but it should have been published.

### 11c. Minor implementation defect

`share_chose_minimum_option` is computed as
`(chosen == chosen.min()).mean()`, the minimum of the **observed chosen values**
in the group, not the minimum of the configured option list as the protocol
words it. Because every chosen value is 3 and 3 is the list minimum, the
published 100% is correct today. The metric would silently become meaningless
the moment the selector stops being constant, which is exactly when it matters.

---

## 12. Survival description

All six cells reproduce exactly: WestJet 24m 9 eligible / 1 event and 36m 4 / 1;
Alaska 24m **22 / 12** and 36m **11 / 5**; Porter 24m 3 / 0 and 36m 0 / 0.

Definitions check out. Eligibility is `first_ym + h <= 2026-04`. An event is a
spell ending before `first_ym + h` and more than `REPORTING_LAG_MONTHS = 2`
before the panel end, otherwise censored. The 2020 and 2021 launch-cohort
exclusion is applied correctly. The seasonal split is present and the pooled
figure is never reported alone, as the protocol required. Corporate-shutdown
events are zero and the field is retained rather than dropped, which is correct:
all three carriers still operate.

**No Cox or Fine-Gray model was fitted.** With 12 events pooled across three
studies and 21 of 35 eligible launches seasonal, that decision is correct on the
data and was frozen before results.

Two things a reader should be told and currently is not:

- **Four of Alaska's 12 events are one-month spells** (DFW twice, FAI, SAN).
  A single month above the four-departure floor entering and leaving the panel
  is a charter, a seasonal probe or an irregular-operations artifact, not a route
  that failed.
- **Three of the 12 restart on the same airport pair** after 14, 16 and 24
  months (ABQ, SAN, DFW). Those "events" are gaps longer than the 12-month
  seasonality period, not exits.

Alaska's headline 12 of 22 within 24 months therefore overstates route failure
materially. The cell is DESCRIPTIVE_ONLY, so nothing inferential rests on it,
but the description itself is misleading as written.

---

## 13. The V2 freeze document

`docs/W1.4_predictive_baseline_v2.md` is the strongest document in the set. It
freezes commit, study and date universe, samples, labels, cutoff rules, vintage
policy, known lookaheads, model defaults, metric definitions, results,
uncertainty procedure, limitations and the NOT_ESTIMABLE cells with reasons. Its
section 1 states what the baseline may not be used for before it states any
number, and section 5 rule 5 ("an improvement inside an interval that spans zero
is not an improvement") is the right guard.

Every number in it that I checked reproduces. It does not overclaim: it confines
the predictive claim to WestJet Families 1 and 4, refuses an Alaska claim on one
positive, refuses a Porter interval on one decision date, and refuses every
survival interval.

Three amendments are needed before it can serve as a scoreboard:

1. The per-date decomposition of section 9a, because "recall@10 0.679" is not
   reproducible as a stable target without it.
2. The statement that the intervals are conditional on three fixed decision
   vintages and are not sampling variability across vintages.
3. The Family 3 secondaries and seasonal split of section 11.

Section 6 ("Unfreezing") already provides the right mechanism: a defect found in
the replay itself requires a new freeze document. Findings P1-1 and P1-2 below
are replay-side findings, and adding the missing reports is a strict addition to
the same numbers, not a change to them.

---

## 14. The defect register

| id | correctness defect or limitation | affects V2 | affects production | severity | recommended phase |
|---|---|---|---|---|---|
| **D1** corridor growth collapses at a COVID vintage | **correctness defect**: a single-year ratio treated as a permanent level shift | **yes**, dominates 2023-01, 80 rows and 5 positives | **latent**: production reads 2024 (growth 1.165) and escapes by luck, not by design | **high** | next; see section 18 |
| **D2** frequency selection is constant | model limitation, and a real one: 461 of 463 | yes, Family 3 in full | **yes**, 200 of 200 current candidates | high | after D1 |
| **D3** fixed `SURVEY_THRESHOLD = 4000` vs a vintage floor of 280 to 3,090 | correctness defect in the cap, deliberately retained | yes, sets the demand of 49 to 51 of ~80 WestJet rows exactly | **yes**, `models/demand.py:180` | medium | W3.4 as planned |
| **D4** Stage 0 floor derived without publication lag | process defect, already corrected | no, corrected before the replay | no | low | closed |
| **D5** `metro_anchor_points` pinned to 2024 seats | production staleness (W1.3 vector L10) | no: the replay vintages `seats_year` correctly | **yes**, against a panel running to 2026-04 | low to medium | Phase 6 |

Two additions the register should carry, from this review:

| id | description | severity |
|---|---|---|
| **D6** | The corridor-growth year and the EIA fuel `as_of` have no provenance record and no leakage guard; injected leaks of 5.73x demand and +43% fuel pass all 36 tests | P1 |
| **D7** | `segment_brands` builds the brand map over the panel-end T-100 window at every historical cutoff; 4,924 regional triples in the 2022-01 window carry no brand row | P2 |

None was fixed during this review.

---

## 15. Findings

### P0

None.

### P1-1. Two high-leverage vintage paths have no guard and no provenance

- **Where.** `replay/snapshot.py:build_transfer` (the `latest_full` growth year)
  and `replay/snapshot.py:build_economics` (`fuel_price_base(con, v.fuel_as_of)`).
  Provenance is emitted in `replay/snapshot.py:resolve_vintages`, which records
  neither.
- **Evidence.** Section 6. Two real implementation defects patched into the
  source leave all 36 leakage tests green.
- **Reproduction.**
  ```
  NL_MUT=M4_growth_from_panel_end pytest tests/test_replay_leakage.py
  NL_MUT=M5_fuel_not_vintaged     pytest tests/test_replay_leakage.py
  ```
  with `build_transfer` receiving `t100_max_ym = 202604` and `build_economics`
  receiving `fuel_as_of = None` respectively. Both report 36 passed.
- **Impact.** The undetected growth leak multiplies 2023-01 demand by 5.73. The
  undetected fuel leak moves the 2022-01 fuel price by +43.0%. Both feed
  `margin_pct` directly, which is the frozen ranking score. `replay/vintage.py`'s
  docstring claims every source a snapshot reads carries a provenance record; it
  is false for these two.
- **Required resolution.** Add a `Provenance` record for EIA fuel and for the
  corridor-growth year, and a guard per path asserting the selected year and
  date lie at or before the permitted cutoff. Demonstrate each by injection,
  per the project's own round-4 rule.

### P1-2. The headline is a one-date result, and the required per-date breakdown was not published

- **Where.** `replay/report.py` (Family 1 and Family 4 sections);
  `docs/W1.4_replay_results.md`; `docs/W1.4_predictive_baseline_v2.md` section 3.
- **Evidence.** Section 9. `docs/W1.4_REPLAY_PROTOCOL.md` section 3 item 1 and
  section 5 both require "a per-date breakdown is reported alongside". Only
  `positives_by_date` is emitted.
- **Reproduction.** Group `decision_rows.parquet` by `cutoff` and apply
  `_agreement_at_k` and `_recall_at_k` per date. Differences are 0.000 at
  2022-01 and 2023-01 at every k except k=5 at 2022-01, where the model is
  worse; the entire pooled positive difference comes from 2024-01 and from one
  market.
- **Impact.** Does not change the Family 4 conclusion, which is a null and
  remains a null. It does change how the Family 1 "scoreboard" may be used: the
  intervals in the V2 document are conditional on three fixed vintages, and a
  future change scored against them could look significant on vintage variation
  alone.
- **Required resolution.** Emit the per-date table from `replay/report.py`, add
  it and the leave-one-date-out table to the V2 document, and state explicitly
  that the intervals do not represent variation across decision vintages. This
  is a reporting addition to unchanged numbers, so it does not disturb the
  freeze.

### P2

1. **Metro-cluster bootstrap conditions on the three observed dates.** Section 9.
   Limitation, must be labelled, must not be re-derived from three blocks.
2. **Family 3 secondaries and seasonal split not published**, though frozen as
   required. Section 11. Supplying them flips the pooled direction under
   `first_month`.
3. **`margin_pct` has no parity assertion**, though it is the ranking score of
   the headline family. Section 5. It matches to 8e-16 today.
4. **Alaska's "one positive" is definitional, not a sample-size fact.** Section 8
   and the label audit: 14 of 15, 15 of 15 and 13 of 13 launched metros fall
   outside the candidate universe because Alaska overwhelmingly re-enters
   markets it already serves. The V2 document presents this as "one positive
   event", which reads as low activity rather than as an outcome definition
   misaligned with a metro-level candidate universe.
5. **Alaska's survival description overstates route failure.** Section 12: four
   one-month spells and three re-entries among the 12 events.
6. **Brand map built over the panel-end window at historical cutoffs.**
   Section 3. Disclosed in part, not guarded, does not reach WestJet.
7. **The demonstration script re-asserts inline copies of six guards** rather
   than exercising them. Section 6. The guards themselves are sound, proven by
   my own resolver mutations; the "10 of 10" claim is weaker than it sounds and
   the duplicated assertions can drift.

### P3

1. `PHASE_5_6_PLAN.md:135` still says "**eight** study-by-date pairs"; the
   corrected number is seven. `docs/W1_REPLAY_FEASIBILITY.md:631` still says
   "bootstrap over **four** decision dates"; it is three. Both predate or
   survived the `a20a9a0` correction. Reported, not fixed.
2. `AGENTS.md` section 9 states the active branch is
   `phase5/milestone-a-integrity`; it is `claude/network-lab-finalization`.
3. `share_chose_minimum_option` uses the observed minimum, not the option-list
   minimum. Section 11c.
4. `build_demand` (us_domestic) silently retains current `dim_metro_us` values
   if the hub CBSA is missing from the PIT frame. It does not fire: SEA is
   present at BEA 2020, 2021 and 2022. A fail-closed lookup would match the rest
   of the module.
5. The EIA trailing window ends exactly at the cutoff date, including a few days
   that would not yet have been published. Immaterial at 365 days.
6. `pit_metros._read_bea` uses `on_bad_lines="skip"`, dropping malformed rows
   silently; the 10,000-row floor is the only backstop.
7. `metro_pit_override` is registered on the shared connection and never
   unregistered; `anchor_2018_pax` keeps its 2018 name at every vintage.

---

## 16. What I could not fault

Recorded because an adversarial review that lists only problems is not a fair
report.

- Parity is stronger than claimed, across the whole chain (section 5).
- The guards bite against real resolver defects, at 9, 3 and 3 failures for
  three separate mutations (section 6).
- Fail-closed behaviour is genuine and I proved it two independent ways
  (section 4).
- The protocol freeze ordering is verifiable in git and holds (section 7).
- Every published number I recomputed matched, across all four families.
- The positive-unlabeled caveat, the NOT_ESTIMABLE discipline, the refusal to
  fit an underpowered survival model, and the refusal to upgrade a feasibility
  classification are all honoured in the artifacts, not only in the prose.
- `assumptions.yaml` is byte identical to the V1 freeze. Nothing drifted while
  the baseline was being built.
- The Family 4 null was pre-committed as publishable and was published.

---

## 17. What the evidence says about the roadmap

Three facts, each independently verified in this review, bear on the sequencing
question.

**First, D1 cannot explain the Family 4 null.** The comparator is provably
immune to the growth term (section 10c). At 2022-01, where growth is 1.057 and
D1 is absent, the difference is already 0.000 at k=10 and negative at k=5. The
hypothesis that a repaired D1 would reveal incremental value is directly tested
by the clean date and is not supported. Fixing D1 removes a corrupted cell and
restores one third of the WestJet evidence; it is very unlikely to move the
verdict.

**Second, the layers Milestone B would calibrate are not currently
distinguishable from demand.** `margin_pct` and the demand percentile are
Spearman 0.77 to 0.94 correlated at every study and date, with 7 to 9 of 10
markets shared in the top ten. Calibrating QSI weights, connection heuristics
and fare structure changes the perturbation around a demand ordering. On the one
cell where the question is answerable, that perturbation currently moves two or
three markets in a top ten and produces a null.

**Third, the measurement instrument cannot resolve what Milestone B would
deliver.** Fifteen positives, on one study, over what is effectively two
informative decision dates, with 62% of the candidate set tied at the survey
ceiling and a frequency selector that returns a constant on 461 of 463 rows.
`docs/W1_REPLAY_FEASIBILITY.md` reached the same conclusion prospectively.

Those three together do not point at "proceed as planned", and they do not point
at "fix D1 and re-measure" either, because the re-measurement would be performed
with the same underpowered instrument on a cell whose clean dates already read
zero.

They point at a different order of work, which I would characterise as: repair
the demand layer's known defects (D1, and D3 which pins 49 to 51 of about 80
WestJet markets to a single identical value), repair or replace the service
selector (D2), and only then decide how much of W2.2 to W2.5 is worth doing,
because until the demand layer stops being degenerate the share and fare layers
cannot be shown to matter. Widening the measurement instrument, for example by
adding the 2025-01 decision date once T-100 reaches 2027-01, or by finding a
study whose launches are not mostly re-entries into already-served metros,
belongs in the same conversation.

That is a redesign, not a resequencing, and it is not mine to author. What I can
say with the evidence in hand is that following W2.1 to W2.5 in order, and
gating them on a D1 re-run whose outcome the clean dates already predict, would
both be sequencing on a premise this review tested and did not confirm.

---

## 18. Verdicts

### Milestone A

**APPROVE WITH NONBLOCKING FINDINGS**

No P0. The V2 baseline reproduces exactly, the gates are green independently,
parity is stronger than claimed, the guards bite against real defects, the
offline discipline is genuine, and the protocol freeze is verifiable in git. The
two P1 findings are a missing guard on code that is currently correct, and a
missing required breakdown of a number that is currently correct. Both must be
resolved before this baseline is used to score a change; neither invalidates it,
and neither requires `d514ec2` to be altered or the V2 baseline to be replaced.

### Roadmap

**REDESIGN THE REMAINING ROADMAP**

---

## Addendum, 2026-08-15: P1-1 verified by mutation

Added by a second independent reviewer session at the request of the project
owner. The original review text above and both verdicts in section 18 are
preserved unchanged. Nothing in this addendum required them to change.

The purpose of this pass was narrow: take finding P1-1 on section 15, which the
original review reached by patching defects into the source, and re-derive it
independently. It reproduces, and the mechanism turns out to be more serious
than the original finding states.

### A.1 P1-1 CONFIRMED

Both mutations behave as the original review reported.

| mutation | committed leakage suite |
|---|---|
| `build_transfer` takes the corridor-growth year from the panel end rather than the vintaged window | **36 passed**, 0 failed |
| `build_economics` calls `fuel_price_base(con, None)` | **36 passed**, 0 failed |

### A.2 The mechanism is absence of execution, not absence of assertion

Section 15 records these as two vintage paths that "have no guard and no
provenance". That is true but understates the gap. A hard
`raise AssertionError` placed at the top of the historical branch of
`replay/snapshot.py:build_transfer`, immediately after the transfer frame is
built, does not fail a single test:

```
.venv/bin/python -m pytest -q
94 passed in 214.77s
```

The corridor-growth selection is not an unasserted code path. It is an
unexecuted one. Zero of the 94 tests reach it.

The coverage map explains why:

| suite | historical build layers exercised |
|---|---|
| `tests/test_replay_leakage.py` | `build_candidates` only, 4 call sites |
| `tests/test_replay_parity.py` | `snapshot()` at **production** vintages only, 1 call site |

`build_transfer` returns early at `replay/snapshot.py:199` when
`v.label == "production"`, reading the committed
`data/parquet/outputs/transfer_factor.yaml`. The parity suite therefore never
touches the historical branch, which is correct and by design. The leakage
suite never invokes `snapshot()` at a historical cutoff at all. No other test
module does either.

Of the six build layers, five have no end-to-end historical execution coverage:

- `build_transfer`
- `build_demand`
- `build_share`
- `build_economics`
- `build_screen`

Only `build_candidates` is exercised at a historical vintage. This is a
test-coverage defect, not a leak that occurred: the production code is correct
today, and section 5 of the original review establishes that the production
path is verified to 8e-16 across the whole chain.

### A.3 Leak magnitudes, measured from source

| leak | correct value | leaked value | effect |
|---|---|---|---|
| growth year from panel end, 2023-01, YYC | 2021, ratio `0.19573` | 2025, ratio `1.12084` | **5.73x** demand level |
| growth year from panel end, 2023-01, YYZ | 2021, ratio `0.16639` | 2025, ratio `0.83394` | **5.01x** demand level |
| fuel not vintaged, 2022-01 | `$1.8487` per gal | `$2.6445` per gal | **+43.0%** |
| fuel not vintaged, 2023-01 | `$3.3735` | `$2.6445` | -21.6% |
| fuel not vintaged, 2024-01 | `$2.7002` | `$2.6445` | -2.1% |

The YYZ figure is new; the original review reported only YYC. Both feed
`margin_pct`, the frozen Family 1 and Family 4 ranking score.

### A.4 An incidental finding about the mutation itself

The first attempt at the growth-year mutation used `year*100+month` without a
cast. In DuckDB this raises `Overflow in multiplication of INT16` against
`fact_segment`, whose `year` column spans 1990 to 2026. The suite nonetheless
reported 36 passed, and that anomaly is what first exposed the coverage gap: a
mutation that cannot execute without raising, in a path no test executes,
produces no failure at all. Production code at `replay/snapshot.py:142` and
`:146` does cast (`year::INT*100+month`), so the requirement is known in the
codebase.

### A.5 Documentation defect: the parity test count

`tests/test_replay_parity.py` collects **13** tests, not 15:

```
.venv/bin/python -m pytest tests/test_replay_parity.py --collect-only -q
13 tests collected in 3.91s
```

Three reader-facing locations state 15:

- `PROGRESS.md:11`
- `docs/MILESTONE_A_COMPLETION.md:56`
- section 5 of this review, line 179

Under project rule 6, reader-facing counts are read from computed artifacts.
Reported here, not fixed in this pass.

### A.6 What this does not change

- **The V2 baseline is unaffected.** No published number moves. The defect is
  in test coverage of a path whose current output is correct.
- **The rank-invariance proof of section 10c stands**, and is independent of
  test coverage. Verified again here from `replay/snapshot.py:352-366`:
  `anchor_est = anchor x growth`, `gravity_est = gravity x factor x growth`,
  `ceiling = 4000 x growth`, so
  `min(g x f x growth, 4000 x growth) = growth x min(g x f, 4000)`. Growth is
  one scalar per hub and each study has one hub, so it is a common positive
  scalar over every ranked row. The `has_anchor` and capping branches are
  growth-invariant too.
- **The per-date decomposition of section 9a reproduces exactly**, recomputed
  independently from `decision_rows.parquet`: differences of 0.000, 0.000 and
  +0.100 on agreement@10 and 0.000, 0.000 and +0.333 on recall@10, with the
  leave-one-date-out table matching section 9b to three decimals. At k=20 every
  date is 0.000, and at k=5 the 2022-01 model is worse. The single market
  responsible at 2024-01 is Anchorage, AK, confirmed by set difference of the
  two top-ten orderings.

### A.7 Restated resolution for P1-1

Section 15 requires a provenance record and a guard per path. That is necessary
and not sufficient. The resolution must also make the historical chain
**execute** under test, so that a guard placed on it can fail. A guard on a path
no test runs cannot fire.

### A.8 Verification hygiene

All mutations were temporary and reverted with `git checkout -- replay/snapshot.py`.
The tree was confirmed clean (`git diff` empty, `git status --porcelain` showing
only this review document) and `HEAD` confirmed at
`d514ec2681d4f45f7adda9039c52692f511990f6` after every mutation. No assumption,
model default, study config, output artifact or source cache was modified. No
data was downloaded and `make data` was not run.

### A.9 Addendum verdicts

Unchanged from section 18. **APPROVE WITH NONBLOCKING FINDINGS** for Milestone A
and **REDESIGN THE REMAINING ROADMAP** for the roadmap. P1-1 is confirmed and
its required resolution is widened, which strengthens the original finding
rather than contradicting it.


---

## Addendum, 2026-08-15, entry 2: P1-1 CLOSED

Added by the project owner's session after the review and after addendum entry
1. The original review body, its findings, both verdicts in section 18 and
addendum entry 1 are preserved unchanged. This entry records the resolution of
P1-1 and nothing else. No model behaviour was changed.

### B.1 What the resolution had to cover

Section 15 required a `Provenance` record and a guard per path. Addendum A.7
widened that: the historical chain must also **execute** under test, because a
guard on a path no test runs cannot fire.

The execution half closed at commit `4f8dbae` with
`tests/test_replay_historical_chain.py`. The provenance half, which is what
section 15 asked for, closes here.

### B.2 The two records

Both paths now resolve through `replay/vintage.py` and emit a record on the
same contract as the other eight sources:

| resolver | source string | policy | lookahead exception |
|---|---|---|---|
| `Cutoff.t100_corridor_growth_year` | `BTS T-100 Segment (corridor growth year)` | `as_available_by_cutoff` | none |
| `Cutoff.eia_fuel_as_of` | `EIA jet fuel spot price` | `as_available_by_cutoff` | declared, see B.4 |

Emitted values, read from `provenance.parquet` rather than transcribed:

| cutoff | corridor growth year | first available | fuel window |
|---|---|---|---|
| 2022-01 | 2019 | 2020-03 | 365 days ending 2022-01-01 |
| 2023-01 | 2021 | 2022-03 | 365 days ending 2023-01-01 |
| 2024-01 | 2022 | 2023-03 | 365 days ending 2024-01-01 |

The 2023-01 value is 2021, which is the year section A.3 identifies as correct
and against which the 5.73x leak was measured.

`replay/snapshot.py:build_transfer` no longer selects the growth year itself.
It reads `v.growth_year`, the value the record names. That is the point: a
provenance record computed separately from the value in use is a claim that can
drift from the code, which is the defect class P1-1 belongs to.

### B.3 A third gap found while closing this one

`seats_year` was resolved by the same inline `max(...)` expression in
`resolve_vintages` and was equally unrecorded. The review did not name it and
it carries far less leverage than the growth year, but the claim in
`replay/vintage.py`'s docstring is false while any source is missing. It now
resolves through `Cutoff.t100_seats_year` and emits
`BTS T-100 Segment (annual seats)`.

The growth year and the seats year are the same selection over the same window.
They share one private resolver, `_t100_complete_year`, so they cannot drift
apart, and are recorded separately because they are two distinct claims about
what the decision was permitted to read.

### B.4 A disclosure the fuel record adds

`fact_fuel` is a weekly series and the window ends on the decision date itself,
so the final weekly observation in the trailing average would in practice have
been published a few days after the decision. One observation of roughly 52.
It is now declared in the record's `lookahead_exception` rather than absorbed
silently, and appears in section 6 of `docs/W1.4_replay_results.md` alongside
the BEA, StatCan and Census declarations.

This is a new **disclosure**, not a new leak and not a behaviour change: the
selected price is unchanged to the last bit. EIA spot prices do not revise, so
nothing earlier in the window is affected.

### B.5 The guards, and what each kind of test catches

| guard | location | refuses |
|---|---|---|
| resolver | `Cutoff._t100_complete_year` | selecting a T-100 year the window does not permit; raises `LookupError` |
| use site | `build_transfer`, top of the historical branch | a growth year handed in that the window does not permit |
| use site | `build_economics`, before any work | a historical snapshot with no fuel vintage resolved |

The guards and the chain suite's instrumentation catch different failures and
neither subsumes the other. A guard catches a vintage resolved wrongly. The
instrumentation catches a call site that bypasses the resolved vintage
altogether, which is exactly what this review's second mutation did by calling
`fuel_price_base(con, None)` directly.

### B.6 Demonstrated by injection

Per the project's round-4 rule, a test never shown to fail is a test of
nothing. Four mutations were injected into `replay/vintage.py`, each reverted
and checksum-verified before the next:

| mutation | new provenance tests | leakage + parity |
|---|---|---|
| **M6** the corridor-growth record is never recorded | **8 failed**, 14 passed | 49 passed |
| **M7** the EIA fuel record is never recorded | **8 failed**, 14 passed | 49 passed |
| **M8** the growth record names a year `build_transfer` did not use | **4 failed**, 18 passed | 49 passed |
| **M9** the fuel residual lookahead is left undeclared | **4 failed**, 18 passed | 49 passed |

Every pre-existing suite passes under every mutation, which is the same shape
as the original finding: these defects are invisible to everything that existed
before.

The two original mutations are now refused rather than merely detected. M4
cannot be reintroduced through the resolver at all, and is demonstrated in
suite by injecting the panel-end year through `Vintages`; M5 is refused by the
`build_economics` guard.

### B.7 Evidence that nothing moved

| gate | result |
|---|---|
| `make test` | **143 passed**, up from 120 at `4f8dbae` and 94 at `d514ec2` |
| `make reproducibility` | **27 artifacts identical** across a warehouse rebuild |
| replay re-executed end to end | `results.json` **bit-identical**: every Family 1, 2, 3 and 4 metric and every bootstrap interval |

`outcomes.parquet`, `rightsizing_pairs.parquet`,
`vintage_demand_dispersion.parquet` and `vintage_transfer_growth.parquet` are
identical row for row. `provenance.parquet` grows from 63 to 84 rows, three
sources across seven study-by-date snapshots, which is the change rather than a
side effect of it. `docs/W1.4_replay_results.md` gains 10 lines, all of them in
section 6.

`decision_rows.parquet` differs in `margin_pct`, `annual_contribution` and the
`score_model` derived from `margin_pct`, at a maximum of **3.3e-15 relative**.
Zero verdict changes, zero frequency changes, zero rank changes, and identical
top-5, top-10 and top-20 sets at every decision date. `demand_pax_yr`, the
column the corridor-growth path feeds, is bit-identical, which is the direct
evidence that the growth change is inert.

That residual is not attributable to the change. Two runs of **identical** code
in separate processes reproduce the same noise: `margin_pct` differing on 79
rows at 9.1e-12 absolute, `demand_pax_yr` exactly zero. It is the DuckDB
parallel float summation recorded in section 6.1 of
`docs/MILESTONE_A_COMPLETION.md`.

### B.8 Addendum A.5 resolved

The parity test count was corrected from 15 to the collected 13 in
`PROGRESS.md` and `docs/MILESTONE_A_COMPLETION.md` at commit `4f8dbae`. A.5 is
closed.

### B.9 Status

**P1-1: CLOSED.**

**P1-2 remains OPEN**, and this entry does not touch it. Addendum A.6 *verified*
that the per-date decomposition reproduces; it did not *publish* it. The
required resolution in section 15 is a reporting change: emit the per-date and
leave-one-date-out tables from `replay/report.py` into
`docs/W1.4_replay_results.md` and the V2 document, and state that the intervals
do not represent variation across decision vintages. None of that has been
done.

This matters more now than it did at review time. The per-date breakdown is
precisely the evidence the roadmap redesign rests on: that the pooled
agreement@10 advantage is one market at one date, that 2022-01 and 2023-01 are
zero, and that k=5 is negative. A redesign citing numbers that live only in a
review appendix is weaker than one citing generated artifacts. P1-2 should be
closed before or alongside the roadmap document.

Both section 18 verdicts stand: **APPROVE WITH NONBLOCKING FINDINGS** for
Milestone A, and **REDESIGN THE REMAINING ROADMAP** for the roadmap.

### B.10 What did not change

- No value in `config/assumptions.yaml`, no study config, no threshold.
- No model default and no scoring function.
- `docs/W1.4_predictive_baseline_v2.md` is untouched. V2 remains the immutable
  baseline describing the frozen pre-calibration engine.
- No source data. No network call. `make data` was not run.
