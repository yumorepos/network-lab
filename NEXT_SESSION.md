# Network Lab: next-session kickoff (Claude Code)

Paste everything below the line into a fresh Claude Code session started from the
repo root (`/Users/yumo/Projects/network-lab`). It carries full context so work
resumes cleanly. House style: no em dashes, no en dashes, no double hyphens in
any generated text, comment, or doc (spaced hyphens only). Never relax a test to
make it pass; if a test fails, report the failing values.

---

## Who you are and what this repo is

You are continuing Network Lab: an airline route-evaluation platform built
entirely on open government data (BTS T-100 / DB1B / Form 41, StatCan, BEA, EIA,
OurAirports). One config-driven engine runs three studies:

- Flagship: WestJet (WS) transborder opportunities from Calgary (YYC).
- Validation: Alaska (AS) at Seattle (SEA), the one config where demand, share,
  and fare are all observed, so the whole chain is checked against truth.
- Portability: Porter (PD) at Toronto Pearson (YYZ), ranked table only.

Pipeline: `ingest/` -> `warehouse/` (DuckDB marts) -> `models/` (catchment ->
demand -> competition -> QSI-lite share -> spill -> 3x3 economics -> screen) ->
`backtest/` -> `reports/` -> `app/streamlit_app.py`. Reproducible via `make
data && make all && make test`. Data lives under `data/` and is gitignored
except `data/reference/`.

## Canonical numbers (verified against computed outputs 2026-07-23)

Read these from the artifacts, never hardcode. Current truth:

- Porter YYZ screen: 5 LAUNCH / 3 MONITOR / 71 PASS (79 candidates).
  LAUNCHes: Washington, Chicago, Boston, Philadelphia, Atlanta.
- WestJet YYC screen: 0 LAUNCH / 0 MONITOR / 76 PASS. Deliberate honest negative.
- Alaska SEA screen: 48 PASS / 1 MONITOR (Fayetteville-Springdale-Rogers,
  margin +0.17%, which is positive but below the 8% hurdle, hence MONITOR).
  It is NOT all-PASS. Any doc that says "all-PASS" for Alaska is wrong.
- Transfer factor: median 0.80, IQR [0.55, 2.02], 87 anchored pairs.
- Share model MAE: 7.0 share points (503 rows at SEA).
- Backtest: N = 48 launched-and-resolved; operating 0.89 vs ceased 0.86 median
  percentile (weak separation, disclosed).
- Gravity: 6,002 markets (2018-19 vintage), 6,092 (2023-24 fit), R2 0.50.

`make test` currently passes 11/11. Do not let it go red without reporting why.

## What is already done (do not rebuild)

Full ingest + reconciliation (14/14 within 1%), warehouse, all models with
frequency/gauge right-sizing (`min_feasible_load_factor` 0.50 with a documented
fallback to the highest-LF option), unanchored-demand cap (4,000 x corridor
growth), metro-level served-market exclusion (`served_market_min_deps_yr` 26),
share guard (>70% modeled share + 0 nonstops caps to MONITOR), deterministic
fits, backtest, three report families, two post-mortems, docs, Streamlit app,
CI, consistency test.

## The single most important verified fact

The metro-level served-market exclusion (models/candidates.py:33-51) works: it
correctly drops New York from Porter (PD-LGA is in T-100) and Las Vegas. Porter's
actual YYZ->US network in T-100 (trailing 12mo to 2026-04) is LGA, LAS, FLL, MCO,
LAX, PHX, SFO, RSW, TPA, MIA, PBI, PSP, SAN. None of the five LAUNCH markets are
in it. So the five Porter LAUNCHes are genuinely unserved-by-Porter markets.
The one soft spot is Chicago: `data/reference/launches.csv:52` claims Porter
operates YYZ-MDW, but that row is low confidence and T-100 shows zero Porter
Chicago service ever; Porter's Chicago history is YTZ (Billy Bishop) turboprop, a
different airport and gauge, out of this study's YYZ mainline scope. This must be
stated on the page, not left implicit.

---

## Objectives, in priority order

### P0: correctness and honesty (do first; roughly 6 to 10 hours)

1. Fix the `top_risk` string bug. In `models/screen.py:30-43`, the branch
   `if row["demand_source"] == "modeled"` returns "gravity x transfer demand
   estimate; no current O&D truth for this market" for every non-DB1B row,
   including `demand_method == "anchor_x_growth"` rows. That is wrong: anchor
   rows are pinned to the market's own 2018 StatCan actual. Add an
   `anchor_x_growth` branch with an honest risk string (for example: "demand
   anchored to the 2018 StatCan actual and scaled by T-100 corridor growth; no
   post-2018 transborder O&D truth exists to confirm the level"). This currently
   mislabels all five Porter LAUNCHes and the WestJet report closings. Then
   regenerate reports (`make reports`) and confirm the LAUNCH rows no longer read
   "gravity x transfer".

2. Fix the Alaska "all-PASS" falsehood. `reports/generate.py:133` hardcodes
   "All {len(scr)} remaining unserved candidates screen PASS"; it is 48 PASS and
   1 MONITOR. Derive the verdict distribution from the screen and state it
   honestly, and explain the one MONITOR (positive margin below the 8% hurdle).
   Fix the matching claim in `README.md` (the "Alaska SEA stays all-PASS" line).

3. Write the two post-mortem syntheses and differentiate them. Both
   `reports/postmortem_f8_yyc_las.md` and `reports/postmortem_y9_yyc_las.md` end
   with an identical "Human synthesis (TO COMPLETE)" placeholder and share about
   90% boilerplate. Write real, distinct synthesis for each: Flair sustained
   0.68 to 0.70 load factor for two years on YYC-LAS against WestJet's defended
   ~0.90, then made a route-level cut citing competition (a cost-structure
   failure on a route the incumbent defends); Lynx flew one year at 0.53 load
   factor and died in a corporate shutdown before the route could prove itself
   (the route never got a fair test). Keep the shared "what the model could and
   could not see" framing but make the conclusions carrier-specific. Consider
   generating both from `backtest/postmortem.py` so the divergent narrative is
   data-driven, not hand-pasted.

4. Re-pin the progress and plan docs, and close the consistency-test holes.
   `PROGRESS.md` Phase 5 ("2 LAUNCH / 3 MONITOR / 72 PASS", "PD YYZ 10 / 5 / 65"),
   Phase 6 ("61 transborder launches", "0.90"), and the integrity bullet
   ("transfer 0.82") are pre-round-3 and contradict the canonical numbers above.
   `PLAN.md` Non-goals still says "no determinism tests" though the consistency
   test exists, and it never describes right-sizing, the demand cap, or metro
   exclusion. Fix both. Then extend `tests/test_consistency.py` to (a) assert
   each study's verdict distribution matches the computed screen, (b) fail if any
   doc asserts "all-PASS"/"all PASS" for a study that is not, and (c) close the
   stale-string hole: it currently forbids "median 0.82" but PROGRESS.md said
   "transfer 0.82", a different string that slipped through. Scan every markdown
   file at repo root and under `docs/` and `reports/`.

5. State the Chicago edge case. Add one explicit sentence to
   `reports/porter_yyz_portability.md` explaining that Porter's Chicago presence
   is YTZ turboprop (out of the YYZ mainline scope) and that T-100 shows no
   Porter YYZ-Chicago jet service, so Chicago is a genuine LAUNCH candidate. Add
   a one-line note in `docs/LIMITATIONS.md` that the served-market exclusion
   trusts the T-100 join and names the residual risk.

### P1: credibility and story (roughly 10 to 16 hours)

6. Rewrite `README.md` as a written case study, not a manual. Lead with the
   decision (Porter's 5 LAUNCHes; the honest WestJet negative; the two
   post-mortems as the intellectual centerpiece), then the evidence, then the
   machinery. Put the live Streamlit link in line one once it exists.

7. Add a verified incumbent-network reference file. Build
   `data/reference/incumbent_network_202604.csv` for WS, AS, PD from published
   schedules, dated and sourced per row, and add a test that fails if any LAUNCH
   market appears in the study carrier's incumbent list. This is a
   belt-and-suspenders credibility layer over the T-100 join, and it lets the
   Porter report cite Chicago with a source rather than resting on a silent join.

8. Document the verdict decision tree as one ordered table in the README: every
   threshold and guard in sequence (hurdle 8%, BELF <= 0.85, fare-down > 0, LF
   floor 0.50 and its fallback, the >70%-share guard, the unanchored demand cap),
   so any verdict is traceable by a reader in one pass.

9. Commit outputs and deploy. Run the `git add -f data/parquet/outputs/*`
   sequence from `docs/deploy.md` (the outputs are 668 KB total; the 4.5 GB
   duckdb stays out), confirm `make app` boots locally against only the committed
   parquet (the app reads outputs only, no warehouse), push, and deploy to
   Streamlit Community Cloud.

10. Add a current `CLAUDE.md` at repo root. The only existing copy is a stale
    M0-M1 snapshot on the Desktop that says "hard stop at P5, no modeling"; the
    repo has none. Write a fresh one from the real conventions (stack, the hard
    rules on constants and columns and grains, the no-dash house style, the
    definition of done).

11. Optional scope build (only if a positive WestJet headline is wanted):
    reclassify the YYC markets WestJet already serves as add-frequency and
    upgauge evaluations. Share is frequency-sensitive and economics already loops
    the frequency grid, so the machinery exists. This converts the flagship's
    "nothing to launch" into the real conclusion: at Calgary the transborder
    opportunity is depth, not breadth. Roughly 8 to 12 hours; skip if leading
    with Porter plus the honest negative is preferred.

### P2: packaging (roughly 8 to 12 hours; some needs the user's accounts)

12. Record a 3-minute demo video from `docs/demo_script.md`; embed in README.
13. Draft three LinkedIn posts (the YYC negative finding, the post-mortem
    contrast, the tool) and a final resume-bullet pass against canonical numbers.

## Coding standards (from the project CLAUDE.md, enforce them)

- Never invent a numeric constant. Every non-derived value lives in
  `config/assumptions.yaml` with source, confidence, and sensitivity. Missing
  value means stop and ask.
- Never invent a column name; read the record layout first.
- Never commit anything under `data/` except `data/reference/`.
- Demand carries an observed/modeled flag on every row; the source path is
  recorded.
- If a test fails, report the failing values. Never relax an assertion, widen a
  tolerance, or edit an expected value to make a test pass.
- Reader-facing numbers are read from computed artifacts, never hardcoded.
  Regenerate reports with `make reports`; do not hand-edit generated markdown.
- No em dashes, en dashes, or double hyphens in any generated text.
- Keep diffs reviewable; update `PROGRESS.md` as you go.

## Definition of done for this pass

`make all && make test` is green; every P0 item is fixed and verified against
regenerated outputs; PROGRESS.md and PLAN.md match the canonical numbers; the
consistency test now guards verdict distributions and claim strings; the README
reads as a case study; the app is committed and deploys. Report what was fixed
with the before and after numbers, the same way `INTEGRITY_REPORT.md` does.
