# LinkedIn posts

Three posts, not a series. Post them a few days apart. The negative-finding post
is the one most likely to be shared, so lead with it. Replace the bracketed link
placeholders with the live Streamlit URL and the GitHub repo URL once deployed.

---

## Post 1: the negative finding (lead with this)

I built an airline route-evaluation engine on open government data and pointed it
at my flagship question: which new US routes should WestJet launch from Calgary?

The answer it gave me was: none.

That is not a bug. Every viable unserved transborder market from YYC is either
already flown by WestJet (New York, the California and Nevada leisure markets,
Houston, the Florida sun routes) or too thin, or too thoroughly held by a US
carrier's hub (Dallas sits at 23% modeled share against American). The model
recommending nothing, and WestJet's own recent growth going to Edmonton and
Vancouver instead, are the same finding from two directions.

A model that only ever says "launch" is a sales tool. The useful part of an
analysis is the markets it rules out and why. Full write-up and a live dashboard
you can click through: [links]

#aviation #dataanalytics #airlineindustry #networkplanning

---

## Post 2: the post-mortem contrast

Two airlines, Flair and Lynx, both launched Calgary to Las Vegas into WestJet's
fortress hub. Both exited. A demand model ranks YYC-LAS in the top 17% of markets
and would have green-lit both.

But the two exits mean completely different things:

- Flair flew it for two and a half years at a 0.59 to 0.70 load factor while
  WestJet held 0.90, then made a route-level economic cut while continuing to
  fly everywhere else. The market beat the entrant.
- Lynx flew it for one year at 0.53 and then vanished in a corporate shutdown
  that took every route at once. The route never got a fair test.

Same market. One economic verdict, one balance-sheet death. If you feed both into
a model as "failed routes," you teach it a false lesson. This is exactly why a
demand-first screen needs an economics and competition layer, and why provenance
on every data point matters. Both post-mortems are built entirely from public
T-100 segment data: [links]

#aviation #dataanalytics #aviationanalytics

---

## Post 3: the tool

Most open-source aviation projects visualize flight data. I wanted to build the
thing behind the recommendation: a config-driven engine that turns raw BTS,
StatCan, BEA, and EIA files into LAUNCH / MONITOR / PASS verdicts for new airline
routes.

What is under the hood:
- A log-linear gravity demand model calibrated on 6,002 US city-market pairs,
  transferred across the border with a factor anchored to Canada's last published
  transborder survey.
- A QSI-lite market-share model validated against observed DB1B carrier shares
  (7.0 share-point error), with competitor connections reconstructed from T-100.
- A fully-allocated route P&L on a fare-by-fuel scenario grid, right-sized across
  frequency and gauge.
- A backtest of 48 real 2021-2025 launches that honestly reports weak demand-only
  separation, and a warehouse that reconciles to published government totals
  within 1%.

Every assumption lives in one file with a source and a sensitivity range. Live
dashboard and code: [links]

#dataengineering #python #aviation #softwareengineering
