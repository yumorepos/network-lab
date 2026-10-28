# Demo script (2-3 minutes)

A storyboard for an interview walkthrough or screen recording. This script
reflects the **final fixed-gauge scope** and must be checked against the
published README and canonical artifacts before recording. The Streamlit app
reads precomputed outputs; it **does not recompute model assumptions live**.

## 0:00-0:20 - The question

"How can someone screen potential airline routes without proprietary booking
and schedule feeds? I assembled public BTS, StatCan and economic data, with
observed-versus-modeled demand and traceable assumptions, to produce research
screening verdicts. It is not a route-success predictor or a network optimizer."

## 0:20-1:00 - Route screen: corrected results

Open **Route screen**, select **Porter YYZ**.

"The final Porter screen has **1 LAUNCH (Boston), 1 MONITOR (Hartford) and
77 PASS**. Boston is evaluated on the study's configured aircraft size and
schedule menu, with about **16% modeled share**. An earlier version reported
five LAUNCH markets, but that result was withdrawn when I corrected demand
directionality and airline-brand competitor mapping."

Switch the study selector to **WestJet YYC**.

"WestJet has **0 LAUNCH, 0 MONITOR and 76 PASS** in the final screen. That is a
valid result, not a reason to adjust the model until it recommends something.
This is fixed-gauge screening, not a recommendation to open a route or choose
an aircraft or flight frequency."

## 1:00-1:35 - One scenario: market detail

Open **Market detail** for **WestJet YYC**, then **Dallas-Fort Worth**.

"The engine evaluates the configured 3x, 7x and 14x weekly schedules on one
aircraft gauge. Here no tested option clears the load-factor floor. The shown
frequency is an infeasibility fallback, not a validated flight schedule.
The model estimates about **23% share** against competition including
American's Dallas hub. The fare-by-fuel grid illustrates uncertainty; it does
not turn a hypothetical scenario into a forecast."

Do not promise to change an assumption in the hosted dashboard: the deployed
app displays precomputed outputs, not interactive re-estimation.

## 1:35-2:05 - Validation

Open **Validation**.

"I reconciled calculated transborder totals against published StatCan figures:
the comparisons were within **1%** in the documented tests. For the original
SEA carrier-share validation, the model's **unweighted MAE was 5.7 share
points across 503 market-carrier rows**; passenger-weighted error was
**10.9 share points**. Those are different metrics, and both limitations
matter. The one-stop-only regime also has a separately documented stratified
validation."

## 2:05-2:40 - Historical evidence: two different tests

Open **Backtest**.

"The older fixed-vintage launch-versus-survival comparison involved **48**
resolved launches. Demand percentile did not meaningfully separate operating
from ceased routes; it also carries a disclosed vintage/lookahead limitation.

"The separate point-in-time WestJet Calgary replay used **three decision
vintages**, with **15 positive rows representing 10 distinct launch events**.
The full engine showed **no detectable incremental ranking value over
demand-only at effects larger than the study's resolution**; **smaller effects
remain unresolved**. This does not establish equivalence or predictive
superiority. The optimistic detectability floor was roughly five net events
across at least two vintages."

## 2:40-3:00 - Close

"The strongest result is the audit trail: I found and fixed material errors,
tested the complex ranking against a simple baseline, and narrowed the claims
when evidence did not support the original ambition. This is a reproducible
research-screening workflow, not commercial airline planning advice."

## Optional close - post-mortem

If time allows, discuss the separate Flair and Lynx YYC-LAS post-mortems:
the two airlines exited the same market under different circumstances.
Do not treat Lynx's carrier-wide shutdown as evidence that the particular
route was economically unviable.

## Pre-interview demonstration checks

- Confirm the hosted URL loads and all four views work; otherwise use
  repository screenshots and a local recording. The GitHub link alone does
  not prove the deployed instance is healthy.
- Compare Porter and WestJet counts with README and the screen artifacts.
- Compare 5.7 and 10.9 share-point error with docs/validation.md.
- Keep the 48-route fixed-vintage backtest separate from the 10-event
  point-in-time WestJet replay.
- Never describe the fixed menu as aircraft/frequency optimization.
