# Demo script (2-3 minutes)

A storyboard for a live walkthrough or a screen-recorded demo. Keep it to the
question, one interactive moment, one route, and the two credibility numbers.

## 0:00-0:20 - The question
"Airline network planners decide where to fly next. The data they use - MIDT
bookings, OAG schedules - is priced for airlines, not portfolios. I built the
whole evaluation chain on open government data, and the hard part is Canada:
there's no public domestic O&D, no transborder fares, and the transborder
survey froze in 2018. So I calibrate where truth exists - US markets - and
transfer across the border with an anchored correction factor."

## 0:20-1:00 - Opportunity ranking (Route screen)
Open the dashboard on **Porter YYZ**. Point at the LAUNCH rows.
"Five launch candidates - Washington, Chicago, Boston, Philadelphia, Atlanta.
Every one is a large market anchored to its own 2018 actual, entered at
single-digit share against real incumbents. That's low-cost entry logic:
take a slice of a big market, don't try to own a small one."
Switch the study selector to **WestJet YYC**.
"WestJet comes back all-PASS - and that's the useful answer. It already flies
its viable Calgary transborder markets; what's left is too small or held by a
US hub. Which is exactly why WestJet's real growth went to Edmonton and
Vancouver. A tool that only says 'launch' is a cheerleader."

## 1:00-1:40 - One route, one live assumption (Market detail)
Open **Market detail -> Dallas-Fort Worth** (WestJet).
"Here's the right-sizing: the engine tested 3x, 7x, and 14x weekly and picked
the best - and it still fails, because against American's Dallas hub the
modeled share is 23%." Show the fare x fuel margin heatmap.
"Every cell is a scenario, never a single point estimate."
Then change one assumption live if scripted (e.g. transborder fare premium in
`config/assumptions.yaml`) and re-run `make models` to show a verdict move -
or just narrate that every number traces to one YAML file with a source.

## 1:40-2:20 - The two credibility numbers (Validation + Backtest)
Open **Validation**.
"Two things make a hiring manager trust this. First, reconciliation: my
computed transborder totals match StatCan's published figures within 1%, and
I derived the expected relationship from definitions before comparing. Second,
the share model is 7.0 mean-absolute-error share points against observed DB1B
carrier shares."
Open **Backtest**.
"I scored 48 real launches with a pre-2022 model. Survivors and ceased routes
both sit in the top demand decile - 0.89 versus 0.86 - and the honest finding
is that demand rank alone doesn't predict survival. Most failures were Flair
route cuts in big markets, not the Lynx shutdown. I publish that rather than
overclaim signal."

## 2:20-2:40 - One honest limitation (close)
"The one I'd flag first: the backtest uses a single fixed-vintage model, so it
carries mild lookahead for later launches. A production version refits per
decision date - I disclose it wherever the number appears. Matching engineering
effort to the stakes is the point."

## Optional close - post-mortem
If time allows, open `reports/postmortem_f8_yyc_las.md`: "Same market, YYC-Las
Vegas. WestJet held it at 90% load factor for years; both Lynx and Flair tried
and left. The model saw a big market. It couldn't see that the market was
already efficiently owned - which is the whole lesson."
