# launches.csv companion notes

Draft compiled 2026-07-20 by Claude (sanctioned AI use per spec Appendix C: field extraction
from press releases and news only; no model recommendations touched). Status column reflects
best knowledge as of 2026-07-20. Every row requires human verification before the backtest
runs; the confidence column tells you where to spend that effort.

## Row counts

74 rows total: Lynx 24, WestJet 14, Porter 13, Air Canada 3, Flair 20.
57 rows have in-window launches (2022-2025). The 17 Flair rows launched 2021-12-15 to
2021-12-18 are flagged pre-window in notes; decide whether to backtest them at a 2021
vintage or drop them. Recommendation: keep them. Their outcomes (Sanford, Mesa, Burbank
all terminated; two Vegas routes cut Apr 2025) are the densest cluster of negative
samples in the register.

## Column conventions

- Dates are ISO. Precision degrades honestly: YYYY-MM-DD verified to the day, YYYY-MM
  verified to the month, bare YYYY believed year only. Blank means unknown.
- announce_date drives vintage year V (spec 7.3). Where blank, default V to launch year
  minus 1 and flag in the audit record.
- status: operating | seasonal | ceased | never_launched | unknown. "seasonal" means
  launched as summer/winter seasonal; renewal in later seasons not confirmed unless noted.
- initial_weekly_freq is one-way departures per week at launch. 2.5 on the Lynx
  Halifax rows reflects 5x weekly split across alternating YYZ/YHM.
- confidence: high = pair and date verified against a source this session.
  medium = date or pair partially verified (month-level, or origin inferred).
  low = memory or inference; verify before the row enters any backtest.

## Verification priorities

1. All rows with confidence low (12 rows), especially Lynx domestic route pairs. Lynx
   destination entry dates are solid (Wikipedia); which city pairs the aircraft actually
   flew is the weak spot. Check Ishrion Aviation, CPTDB wiki (blocked to bots, fine in a
   browser), or archived Lynx booking pages on the Wayback Machine.
2. WestJet 2023 seasonal routes (YYC-IAD, YXE-MSP, YEG-MSP, YYC-DTW): confirm whether
   each returned in summer 2024 and 2025. A quiet non-renewal is a negative outcome the
   register must capture; T-100 will show it once ingested (P1-P3), which doubles as a
   register-vs-T-100 reconciliation check.
3. Porter exact launch days for MCO/RSW/FLL/MIA/SFO/PHX/PBI/SAN/PSP/MDW. Porter's own
   newsroom (newswire.ca/news/porter-airlines-inc.) has inaugural releases for most.
4. Flair end dates for terminated destinations (SFB, AZA, BUR, DEN); Wikipedia confirms
   termination but not when. T-100 last-reported-month is the cleanest source once ingested.

## Known gaps (not yet rows)

- Lynx announced four domestic city entries in early 2024 that never launched due to the
  Feb 26 shutdown: Ottawa (planned 2024-05-17), Charlottetown (2024-05-30), Quebec City
  (2024-06-06), Regina (2024-06-20). Route pairs unconfirmed, so they are recorded here
  rather than as CSV rows. Promote them once pairs are verified; never-launched domestic
  rows are still scoreable by the model even without outcome truth.
- Porter possible additional YOW/YHZ US routes beyond YOW-MCO (check YOW-FLL, YHZ-FLL).
- Porter YYZ-BOS if it exists (YTZ-BOS is legacy Dash-8, out of window).
- Flair YYZ-JFK appears as a current seasonal destination on Wikipedia; if launched in
  2025 it belongs in the register, if 2026 it falls outside the window. Verify.
- WestJet 2022: confirm whether any transborder launches beyond YYC-AUS exist in 2022
  (mediaroom archive sweep).
- Air Canada 2022-2024 was restoration-heavy; genuinely new airport pairs appear to start
  with the summer 2025 YVR slate. The 2026 Billy Bishop wave (LGA/ORD/IAD from YTZ,
  YUL-CLE, YUL-CMH, YYZ-SAT) is outside the window but worth a register_v2 tab.

## Post-mortem candidates (for postmortems.csv, spec 5.9, pick 6-8)

1. Lynx YYC-LAS: ULCC into WestJet's fortress hub against Flair on the same pair; ceased
   with shutdown. Three-carrier dynamics fully observable in T-100.
2. Lynx YYC-YYJ: cut Jan 2023, 13 months before the shutdown, so a genuine route-level
   failure rather than a corporate one. Domestic, so capacity-side analysis only.
3. Lynx YYZ-BOS / YYZ-SFO: never launched. What does the model say at the 2023 vintage?
4. Flair YYC-LAS: launched pre-window, cut Apr 2025 citing WestJet competition; the full
   arc (entry, fare war, exit) sits inside the T-100/DB1B observation window.
5. Flair YYZ-BNA: cut Mar 2025 with both WS and AC serving the market.
6. WestJet YYC-IAD: seasonal experiment, renewal unconfirmed; if quietly dropped, a
   textbook silent negative.
7. WestJet YXE-MSP: thinnest route in the register (3x weekly from a secondary city into
   a Delta hub). Feed-driven launches are exactly what the gravity model does not see.
8. WestJet YEG-ATL vs Porter YYZ-LAX: two positives for contrast, one JV-adjacent
   year-round play, one E2 transcon bet. Both operating.

## Sources

- wikipedia_lynx: en.wikipedia.org/wiki/Lynx_Air (destination entry/exit dates, shutdown)
- aviationweek_lynx_yhz: aviationweek.com "Lynx Air Expands From Halifax And St. John's"
  plus newswire.ca Lynx Halifax inaugural release (alternating YYZ/YHM detail)
- simpleflying_lynx_us: simpleflying.com "Canada's Lynx Air Adds Its 1st US Routes"
- globenewswire_2023-07-06: Lynx "New US Sun Destinations from Toronto and Montreal"
- globenewswire_2023-12-20: Lynx "summer network expansion... Boston and San Francisco"
- thriftytraveler_westjet: thriftytraveler.com/news/airlines/westjet-new-us-routes/
- westjet_mediaroom_2023-11-07: westjet.mediaroom.com summer 2024 transborder release
- aviationa2z_2024-11-16: aviationa2z.com "WestJet Adds Three New US Destinations"
- websearch_porter: aggregated from newswire.ca Porter releases and trade press;
  per-route releases at newswire.ca/news/porter-airlines-inc.
- newswire_porter_lax: newswire.ca Porter YYZ-LAX inaugural release
- openjaw_2024-10-04: openjaw.com Porter Phoenix inaugural
- businesswire_2024-10-24: Porter winter 2024-25 expansion release
- wikipedia_porter: en.wikipedia.org Porter destinations table (MDW end / ORD start 2026)
- aircanada_media_yvr: aircanada.com/media YVR summer 2025 transborder release
- openjaw_2021-12-17: openjaw.com "Flair Airlines Announces 17 New U.S. Routes"
- airlinegeeks_2025-03-06: airlinegeeks.com "Flair Cuts Three U.S. Routes"
- globeandmail_flair: theglobeandmail.com Flair 14-route 2022 expansion
- memory: model recall, unverified this session
