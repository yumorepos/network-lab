# Network Lab 2026 upgrade: research-led, gated

**Decision (2026-10-28):** Keep the existing fixed-gauge route screen, its precommitted point-in-time replay, and published predictive scope frozen. This upgrade is for **traceability and independent data experiments**, not to manufacture an improved ranking. Preserve the black/amber UI; typography can be revisited separately.

## Evidence from how airlines actually work

There are two distinct industry problems:

1. **Strategic network planning**: demand and route economics are prepared, commercial teams evaluate opportunities and opportunity costs, schedules are checked against aircraft, connection banks, slots, airport curfews, maintenance, and crew restrictions, then cross-functional stakeholders iterate and approve. IATA: https://www.iata.org/en/publications/newsletters/iata-knowledge-hub/how-to-work-in-airline-network-planning/
2. **Day-of-operations disruption recovery**: the operations control center observes schedule and resource changes, builds feasible candidates, optimizes aircraft/crew/passenger alternatives, compares costs and downstream impacts, and a controller approves an actionable plan. Google/Lufthansa/SWISS's OPSD is a documented daily-use example, not a template we can reproduce with public data. https://pubsonline.informs.org/doi/10.1287/inte.2025.0296 and https://cloud.google.com/customers/swiss

**Engineering lesson:** Predictive/ML components estimate unknown costs, durations, demand, or disruption risk. Constrained optimization (MIP, CP-SAT, heuristics) chooses among *feasible* actions. Human approval remains separate. Never call a LLM-generated answer a valid optimized schedule without checking all constraints.

## Stage A — Explainability and artifact guard (NOW; 3–4 focused hours)

**Deliverables**

- Add per-market evidence under an expandable dashboard panel: demand source/method; modeled confidence; last observed anchor; competitive-share uncertainty; route risk; key assumptions; verdict drivers. All fields already exist in `screen_*.csv/parquet`.
- Automatically verify committed `screen_<study>.csv` rows and verdict counts against the generated `headline_metrics.yaml`, and that every displayed record has required provenance columns. CI can run this guard without a DuckDB warehouse.
- Do not change `models/`, `replay/`, assumptions, or output artifacts. Existing Porter (1/1/77), WestJet (0/0/76), Alaska (0/0/45) counts must remain intact.

**Gate A:** CI passes; no differences in model-generated artifacts; reviewer can explain Boston versus Hartford directly from stored evidence. Stop if UI complicates the mobile layout.

## Stage B — Data freshness assessment (3–4 focused hours, isolated branch)

**Deliverables**

- Produce a source inventory with **publication date**, **data reference vintage**, coverage/grain, directionality, and any reporting-carrier caveat.
- Re-ingest *one* controlled T-100 month into an isolated research table, checking airline-brand mapping, airport/metro crosswalks, duplicates, US-only reporting scope and changes versus the old period.
- Compare observational differences; do not rewrite existing 2018 transborder anchors or historical replays.

**Gate B:** Any change is source-verified and materially affects a consumer-visible decision or supports a substantive data-quality lesson. Otherwise publish a short negative result and stop.

## Stage C — DB1C compatibility spike (4–6 focused hours, isolated branch)

US BTS replaced quarterly 10% DB1B sampling with monthly 40% DB1C, with new issuer-carrier semantics and added itinerary/segment fields from 2025-07. Sources: https://www.bts.gov/OD-40 and https://www.bts.gov/topics/airlines-and-airports/origin-and-destination-survey-data-segment

**Deliverables:** one U.S. market or hub-month fixture; documented field crosswalk; record grain; ticket/coupon/market/segment join cardinality; sample-expansion policy; fare units and round-trip treatment; guard against double-counting via-point segments. Compare with historical DB1B only after defining *comparable* metrics.

**Gate C:** No unverified merges of DB1B and DB1C. No Canadian transborder fare claim. Retain only if reproducible and useful; otherwise a standalone memo.

## Stage D — Separate, genuine optimization portfolio project (later)

**Candidate:** *Airline disruption recovery*, in a separate repository, initially **aircraft-only with simulated resource state**. This is **not** a repaired frequency selector inside Network Lab.

1. Build an explicit miniature timetable: 10–30 flights, 3–5 aircraft, departure/arrival airports, aircraft position, minimum turnaround, curfew, aircraft type and permitted delay/cancel actions. Mark synthetic inputs.
2. Generate actions and costs; enforce at most one action per flight, aircraft movement continuity, turnaround and resource availability. Prefer a small MILP/CP-SAT solver (see https://developers.google.com/optimization/).
3. Compare to a documented simple greedy baseline on **identical feasible scenarios**. Objective: weighted delay minutes + cancellation penalties + repositioning cost. Do not make up operational crew-rule or compensation amounts and call them authoritative.
4. Present a flight-leg timeline, proposed recovery plan, unserved legs, binding constraints, objective value, baseline gap, and solve time. Keep a human approval step. Later add passenger misconnections only with suitable data.
5. For realism, sample *distributions* from U.S. BTS on-time performance, while aircraft tails, crews, turn times, fares and passenger connections remain synthetic unless independently validated. Source: https://www.transtats.bts.gov/TableInfo.asp?QO_fu146_anzr=b0-gvzr&gnoyr_VQ=FGJ

**Gate D:** Both approaches feasible on the same scenarios; report gap and runtime across multiple seeds; never promise enterprise-grade accuracy or deploy decisions for real operations.

## Concrete, illustrative decision

Assume aircraft A is unavailable for 90 minutes and a morning flight has connecting passengers. Candidates: delay it; swap to an aircraft already at the origin; or cancel the flight. A real optimizer must confirm that the swap will not make the replacement aircraft's downstream flights impossible. A naive lowest-immediate-delay rule can move the problem to another airport. The output should show a *feasible chain* of actions and full-day penalty, not just 'swap A for B'. This scenario is **hypothetical**, not a tested result or actual-airline operational data.

## Success criteria and stop rule

A + B + C target budget **10–14 hours**, with stage-gated stop decisions. The goal is reproducible evidence and clearer explanations, not new route recommendations. Defer D to its own bounded project after Network Lab upgrades are packaged. No model parameter retuning unless a separately approved, prespecified protocol and sufficient held-out resolution justify it.

### Verified baseline references

- `docs/FINAL_SCOPE_CONTRACT.md`
- `docs/STAGE_2R0_RESOLUTION.md`
- `docs/change_reports/T3_connection_share_validation.md`
- `data/parquet/outputs/headline_metrics.yaml`

**Important limitation:** New DB1C U.S. ticket samples and T-100 schedules do not restore Canada's discontinued 2018 transborder city-pair truth or disclose Canadian airline commercial fares. Public data cannot reproduce SWISS's proprietary operations-control inputs.
