# BC Vote Helper 2026

A free voting helper for the British Columbia provincial election on October 24, 2026. Enter your postal code, answer 16 short questions, and see which party and which candidate in your riding are closest to your answers.

Live site: [votebc.vinceroyer.ca](https://votebc.vinceroyer.ca) (open to people in Canada). This is the only official copy. Anyone can fork this code, so a copy on any other address may have different scores.

![Which party and candidate match your views? 16 short questions, all 93 ridings.](assets/og.png)

This repository holds everything behind the site: every question, every party position, every 0 to 4 score and the reason for it, every source, the scoring code, the bias tests and the server code. If you think a score is wrong, check it here and [open an issue](../../issues) with the source.

- [Features](#features)
- [Scoring](#scoring)
- [Party positions](#party-positions)
- [Authorship and AI use](#authorship-and-ai-use)
- [Privacy](#privacy)
- [Repository layout](#repository-layout)
- [Sources](#sources)
- [Licence](#licence)

## Features

- **Riding lookup:** type a postal code, use your location, or pick from the list of all 93 ridings (2023 boundaries). The tool shows your local candidates and 3 questions about your region.
- **16 questions:** 13 province-wide questions (cost of living, taxes and the deficit, housing, health, DRIPA, SOGI 123, toxic drugs, public safety, economy and tariffs, climate and energy, education and child care, ICBC, government power) plus 3 regional questions. The six regions are Surrey, Metro Vancouver, Fraser Valley, Island and Coast, Interior, and North.
- **Five reading levels:** New to politics, Know the basics, Follow the news a bit, Follow politics, Want every detail. The level changes the wording. Scores stay the same at every level.
- **Groups of up to 4:** a family or group can take turns or answer together on one screen, then see each person's result and where they agree.
- **Results:** party match as a percentage, candidate match for your riding, the questions that drove the result, and a PDF to keep.

Five parties are scored: BC NDP, BC Conservatives, BC Greens, CentreBC and OneBC. They are the parties with seats or a province-wide slate. Candidates from other parties and independents appear under "Also running, not scored", since they have no published platform to score.

## Scoring

Each answer option has a fixed score from 0 to 4 for each party:

| Score | Meaning |
|---|---|
| 4 | This option is the party's position |
| 3 | Close to the party's position |
| 2 | Partly agrees |
| 1 | Mostly disagrees |
| 0 | Opposite of the party's position |

Your match with a party is the share of the points you could have given it:

```
Match(P) = sum( w_q x s_q(P) ) / sum( w_q x 4 )      over the questions you answered
```

- `s_q(P)` is the 0 to 4 score of the option you chose, for party P.
- `w_q` is the importance you set for that question: low 0.5, medium 1, high 2.
- Skipped questions and "Not sure" leave both sums.
- A question where a party has no published position leaves both sums for that party only, so it has no effect on that party's match. This applies to 13 of the 155 party-question pairs.
- Candidates get their party's score, with the 3 regional questions counted double on top of your importance setting. There is no candidate-specific adjustment, because few candidates publish their own positions.
- A gap of 3 percentage points or less between the top two parties shows as close.
- For a group, the result is the average of each person's percentages. A second average covers the members at reading levels 3 to 5.

The scoring code is in [`template.html`](template.html) (search for `alignment`). The same formula is re-implemented in [`audit_scoring.py`](audit_scoring.py) and in [`site/admin_template.html`](site/admin_template.html), the private results dashboard.

## Party positions

All of this is in [`quiz_spec.json`](quiz_spec.json). For every question and every party there is:

- `text`: the party's position in plain words, at three detail levels
- `basis`: `platform` for 2026 promises (96 cells), `record` for what the party did in government or the legislature (8), `both` (44), or `inferred` (7 cells, taken from a stated policy next to the question and labelled as inferred on the page)
- `confidence`: high (73), medium (58) or low (24)
- `sources`: links for that party's position on that question
- `scoring_rationale`, per question: a written reason for every number in the 0 to 4 grid

Rules used for scoring:

- **Record first:** where a party's actions from 2016 to 2026 contradict its 2026 words, the score follows the action and the position text says so. The NDP is scored on pausing new $10-a-day child care spaces and on ending decriminalization.
- **2026 campaign only:** parties are scored on what they say in this campaign. Planks dropped since 2024 do not count.
- **No published position, no score:** as of October 12 the NDP and Conservatives had not released full platforms, so their positions come from announcements and their record. CentreBC released a costed platform on October 10. The Greens' full platform was pending.
- **Neutral wording:** each option is written the way its supporters would put it. The language rules are in `meta.language_rules` in the spec.
- **One top score per party:** each party has exactly one option scored 4 on every question where it has a position, so the number of options written for a party gives it no head start.

The question design, the judgment calls and the audit history are in [`design_notes.md`](design_notes.md). [`audit_scoring.py`](audit_scoring.py) checks schema completeness, an ideal-voter test (each party's own answers must put it first by a clear margin), random-voter bias, how well each question separates the parties, how distinct each pair of parties is, the local formula, and how far the low-confidence and inferred scores move results.

## Authorship and AI use

Vincent Royer built this as a side project, first for his own family, then opened it to the public. It has no affiliation with any party, candidate, Elections BC or media outlet, and no one paid for it.

The research, the position summaries, the 0 to 4 scores and the code were produced with an AI assistant (Anthropic's Claude), working from the sources listed below. Separate AI review passes checked the scores against the sources, the wording for loaded language, and the scoring for bias. Automated browser tests check the site. Vincent reviewed the questions, the wording and the results. He did not re-read all 600+ sources himself, which is why every score has a source and a written rationale here for anyone to check.

Data as of October 12, 2026. Parties are still announcing promises, and the leaders' debates are on October 13 and 14. Positions will be rechecked after the debates, and every change will show in this repository's history.

## Privacy

- No accounts, names, email addresses or tracking cookies. Cloudflare Web Analytics counts visits without cookies. Fonts and scripts are served from this site, so no other company sees your visit. Your progress is saved in your own browser, so a reload keeps your answers.
- Your postal code is used to find your riding and then discarded. The server looks it up with Open North's Represent service, which receives the postal code from the server and never sees your IP address. When Represent is busy or slow, the server answers from its own postal code table instead. The postal code is never stored or logged; request logging is off on the server for this reason. Only the riding code is kept.
- With the "share my answers anonymously" box ticked, the site stores your answers, reading level, riding, and the city and province Cloudflare reports for the connection. No IP address is stored. The IP is used only as a counter key for rate limits.
- Shared answers feed anonymous totals on a private dashboard that only the site owner can open (behind Cloudflare Access).
- All shared answers are deleted automatically on November 23, 2026, 30 days after the election. The cutoff is `DELETE_AFTER` in the Worker config, and a daily scheduled job in [`site/src/worker.js`](site/src/worker.js) runs the delete.
- The quiz is open to visitors connecting from Canada.

The server code is [`site/src/worker.js`](site/src/worker.js) and the database schema is [`site/schema.sql`](site/schema.sql).

## Repository layout

| Path | Contents |
|---|---|
| `spec_parts/` | Source of the question bank: one JSON file per question group, plus meta, ridings and sources |
| `build_spec.py` | Merges `spec_parts/` into `quiz_spec.json` and validates it |
| `quiz_spec.json` | The full question bank: questions, options, scores, positions, rationales, sources, ridings, candidates |
| `merge_ridings.py` | Builds the 93 ridings in `spec_parts/80_ridings.json` from the Elections BC candidate list and `geo/research/` |
| `geo/` | Riding list and boundaries, the Elections BC candidate list, per-region candidate research and local-issue research |
| `research/` | The platform research report and notes (October 9 to 10, 2026) the province-wide positions were written from |
| `template.html` | The app: layout, scoring, results, PDF |
| `build_page.py` | Puts the spec into the template and writes the site to `site/public/` |
| `site/src/worker.js` | Cloudflare Worker: serves the page, riding lookup, anonymous answer storage, private dashboard API |
| `site/admin_template.html` | Private results dashboard |
| `audit_scoring.py`, `sim_random_voters.py`, `check_local_lengths.py` | Bias and quality checks |
| `gen_sources.py` | Writes the source list below from `quiz_spec.json` |
| `tests/` | Browser tests (Playwright) |
| `make_og.py` | Draws the link-preview image |
| `build_geo.py`, `fetch_fonts.py` | Build the riding lookup files and download the self-hosted fonts |

### Build

```
python -I merge_ridings.py      # only if candidate data changed
python -I build_spec.py         # spec_parts/ -> quiz_spec.json, with validation
python -I audit_scoring.py      # bias checks
python -I build_page.py         # writes site/public/
python -I gen_sources.py        # refreshes the source list in this README
```

### Deploy

To run your own copy on Cloudflare: copy `site/wrangler.example.toml` to `site/wrangler.toml`, fill in your D1 database id, domain and Cloudflare Access values, run `site/schema.sql` on the database, then run `npx wrangler deploy` from `site/`.

## Sources

Every link the tool uses, generated from `quiz_spec.json` by `gen_sources.py`. Click a section to expand it.

<!-- SOURCES:START -->
**638 unique links.**

### Party positions, question by question

For each question: the sources behind each party's position. The written reason for every score is in `scoring_rationale` in `quiz_spec.json`.

<details>
<summary><b>Cost of living is the top issue for BC voters. Which approach should the province take to make life more affordable?</b> (Province-wide, <code>q_cost_of_living</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [BC NDP: gas price plan (Oct 1, 2026)](https://www.bcndp.ca/releases/ebys-plan-will-cut-gas-prices-30-cents-litre-crack-down-gouging)
- [BC NDP: ICBC rate freeze to 2030 (Oct 8, 2026)](https://www.bcndp.ca/releases/eby-freeze-car-insurance-rates-another-three-years)
- [Global News: BC pauses $1,000 rebate (Feb 2025)](https://globalnews.ca/news/11017886/bc-pauses-tax-rebate-donald-trump-tariffs/amp)
- [BC Government: Budget 2026 tax changes (5.60% rate, indexation pause)](https://www2.gov.bc.ca/budgettaxchanges)
- [BOE Report: Eby on the cost of the fuel tax cut (Oct 1, 2026)](https://boereport.com/2026/10/01/b-c-s-eby-promises-relief-at-gas-pumps-while-conservative-doerkson-praises-pipeline/amp/)

**BC Conservatives** (basis: platform, confidence: high)

- [Conservative Party of BC: $1,000 tax cut (Oct 8, 2026)](https://conservativebc.ca/conservatives-will-cut-your-taxes-by-1000/)
- [Conservative Party of BC: no new taxes pledge](https://conservativebc.ca/conservative-party-of-bc-pledges-no-new-taxes-on-british-columbians/)
- [Daily Hive: tax cut benefit shape and funding](https://dailyhive.com/vancouver/bc-conservatives-election-annual-income-tax-cut-promise)

**BC Greens** (basis: platform, confidence: high)

- [BC Greens: Our Plan](https://bcgreens.ca/our-plan/)
- [Global News: Green free transit pledge (Oct 9, 2026)](https://globalnews.ca/news/12097726/bc-leaders-campaign-trail-health-care-supporting-seniors-october-9)
- [BC Ballot: BC Green commitments](https://bcballot.ca/platforms/bc-green-party/)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 6-7, 12-13)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [CentreBC: platform landing page](https://www.centrebc.ca/platform/)

**OneBC** (basis: platform, confidence: high)

- [OneBC priorities](https://1bc.ca/priorities)
- [BC Ballot: OneBC commitments](https://bcballot.ca/platforms/)


</details>

<details>
<summary><b>BC is spending far more than it takes in. How should it handle that, and who should pay more or less tax?</b> (Province-wide, <code>q_taxes_deficit</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [BC NDP: top-bracket tax proposal (Oct 4, 2026)](https://www.bcndp.ca/releases/build-bc-strong-eby-will-ask-wealthy-pitch-bit-more)
- [BC Budget 2026 and Fiscal Plan](https://www.bcbudget.gov.bc.ca/2026/pdf/2026_Budget_and_Fiscal_Plan.pdf)
- [Moody's rating action, March 2026](https://www2.gov.bc.ca/assets/gov/british-columbians-our-governments/government-finances/debt-management/moodys-ratings-march-2026.pdf)
- [National Newswatch: Eby defends budget after downgrade](https://nationalnewswatch.com/2026/03/19/premier-eby-defends-budget-after-credit-drop-but-opposition-says-b-c-is-going-broke)

**BC Conservatives** (basis: both, confidence: medium)

- [Conservative Party of BC: $1,000 tax cut](https://conservativebc.ca/conservatives-will-cut-your-taxes-by-1000/)
- [Canadian Press via Medicine Hat News: cost estimates and deficit](https://medicinehatnews.com/news/national-news/2026/10/08/b-c-campaign-trail-conservatives-promise-1000-tax-cut-by-boosting-exemption-level/)
- [Votes and Proceedings, March 5, 2026 (Bill 3 third reading)](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260305.htm)

**BC Greens** (basis: both, confidence: high)

- [BC Greens: Fair Share Act](https://bcgreens.ca/fair-share-act-would-unlock-22-2b-for-childcare-transit-and-housing/)
- [Daily Hive: Green wealth tax details and critiques](https://dailyhive.com/vancouver/bc-greens-wealth-tax-fair-share-act)
- [Votes and Proceedings, March 5, 2026](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260305.htm)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 4, 11-13, 37)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [CentreBC: 'A Blueprint for Bankruptcy' (February 2026 budget response)](https://www.centrebc.ca/news/budget-2026-a-blueprint-for-bankruptcy/)

**OneBC** (basis: platform, confidence: high)

- [OneBC priorities](https://1bc.ca/priorities)
- [BC Ballot: platform comparison](https://bcballot.ca/platforms/)


</details>

<details>
<summary><b>What should the province do about the cost of housing?</b> (Province-wide, <code>q_housing</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [BC NDP: speculation tax increase and Unsold Condo Tax (Sept 25, 2026)](https://www.bcndp.ca/releases/eby-turn-more-empty-condos-homes-people-can-afford)
- [Votes and Proceedings, November 29, 2023 (Bills 44 and 46)](https://lims.leg.bc.ca/pdms/ldp/42nd4th/votes/v231129.htm)
- [Votes and Proceedings, November 22, 2018 (Bill 45 spec tax)](https://lims.leg.bc.ca/pdms/ldp/41st3rd/votes/v181122.htm)
- [CMHC Rental Market Report (Vancouver vacancy)](https://www.cmhc-schl.gc.ca/professionals/housing-markets-data-and-research/market-reports/rental-market-reports-major-centres)
- [Global News: Metro Vancouver 2025 homeless count](https://globalnews.ca/news/11311816/metro-vancouver-2025-homeless-count)

**BC Conservatives** (basis: both, confidence: medium)

- [Conservative Party of BC: statement on the NDP housing tax plan](https://conservativebc.ca/statement-from-interim-leader-lorne-doerkson-on-the-ndps-housing-tax-plan/)
- [Daily Hive: Conservative Metro Vancouver rollback](https://dailyhive.com/vancouver/bc-conservatives-metro-vancouver-regional-district-reform-platform-promise)
- [BC Ballot: Conservative commitments (single housing item)](https://bcballot.ca/platforms/conservative-party/)

**BC Greens** (basis: both, confidence: high)

- [BC Greens: renters plan (Sept 29, 2026)](https://bcgreens.ca/announce-plan-to-support-renters-unveil-two-new-candidates-for-south-island/)
- [Daily Hive: Green vacancy control](https://dailyhive.com/vancouver/bc-greens-vacancy-control-rentals)
- [BC Greens: Our Plan](https://bcgreens.ca/our-plan/)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 7, 12-13, 27)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [CentreBC: platform landing page](https://www.centrebc.ca/platform/)

**OneBC** (basis: platform, confidence: high)

- [OneBC priorities](https://1bc.ca/priorities)
- [BC Ballot: platform comparison](https://bcballot.ca/platforms/)


</details>

<details>
<summary><b>How should the province improve access to family doctors, emergency rooms and surgeries?</b> (Province-wide, <code>q_health</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [BC NDP: wait times and diagnostics (Oct 6, 2026)](https://www.bcndp.ca/releases/getting-care-sooner-eby-will-cut-wait-times-add-new-diagnostic-equipment)
- [Global News: leaders on health care and seniors (Oct 9, 2026)](https://globalnews.ca/news/12097726/bc-leaders-campaign-trail-health-care-supporting-seniors-october-9)
- [The Tyee: family doctor crisis figures (May 31, 2026)](https://thetyee.ca/News/2026/05/31/BC-Family-Doctor-Crisis-Gets-Even-Worse/)
- [BCNU: nurse-patient ratios progress (2026)](https://www.bcnu.org/news-and-events/news/2026/minimum-nurse-patient-ratios-focus-bc-nurses-conference)

**BC Conservatives** (basis: both, confidence: medium)

- [Conservative Party of BC: Keep Emergency Rooms Open (Oct 5, 2026)](https://conservativebc.ca/keep-emergency-rooms-open/)
- [Sitka Media: Conservative seniors plan (Oct 9, 2026)](https://www.sitkamedia.ca/watch-bc-conservatives-unveil-plan-to-support-seniors/)
- [Global News 2024: Conservative hybrid health plan (not repeated in 2026)](https://globalnews.ca/news/10631278/bc-conservatives-hybrid-health-care-system)

**BC Greens** (basis: platform, confidence: high)

- [BC Greens: Our Plan](https://bcgreens.ca/our-plan/)
- [BC Ballot: BC Green health commitments](https://bcballot.ca/platforms/bc-green-party/)
- [CP24: Greens cite undelivered health commitments](https://www.cp24.com/news/canada/2026/02/09/bc-greens-wont-renew-accord-with-ndp-citing-stalled-undelivered-promises/)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 14-19)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [CentreBC: 'Healthcare crisis was never a surprise' (June 2026)](https://www.centrebc.ca/news/opinion-healthcare-crisis-was-never-a-surprise/)

**OneBC** (basis: platform, confidence: high)

- [OneBC priorities](https://1bc.ca/priorities)
- [BC Ballot: platform comparison](https://bcballot.ca/platforms/)


</details>

<details>
<summary><b>After a 2025 court ruling, what should BC do with the Declaration on the Rights of Indigenous Peoples Act?</b> (Province-wide, <code>q_dripa</code>)</summary>

**BC NDP** (basis: both, confidence: medium)

- [The Narwhal: DRIPA in the 2026 election (Oct 7, 2026)](https://thenarwhal.ca/bc-election-2026-dripa/)
- [The Tyee: BC backs off DRIPA amendments (Apr 14, 2026)](https://thetyee.ca/News/2026/04/14/BC-Backs-Off-DRIPA-Amendments/)
- [FNLC and Premier joint statement (Apr 2026)](https://www.fnlc.ca/premiers-first-nations-leadership-council-statement-about-dripa/)
- [BC Government: Eskay Creek approved under first section 7 consent agreement](https://news.gov.bc.ca/releases/2026MCM0008-000078)
- [Votes and Proceedings, November 26, 2019 (Bill 41, 82-0)](https://lims.leg.bc.ca/pdms/ldp/41st4th/votes/v191126.htm)
- [The Narwhal: the rushed DRIPA amendments (April 2026 suspension bill)](https://thenarwhal.ca/bc-declaration-act-rushed-amendments/)

**BC Conservatives** (basis: both, confidence: high)

- [Conservative Party of BC: Repeal DRIPA plan page](https://conservativebc.ca/plan/first-nations-dripa/)
- [The Tyee: Rustad on his 2019 DRIPA vote (Feb 10, 2026)](https://thetyee.ca/News/2026/02/10/First-Nations-Would-Not-Exist-Without-Canada-Rustad/)
- [Votes and Proceedings, October 29, 2025 (Property Rights Protection Act)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251029.htm)
- [The Narwhal: DRIPA explainer (repeal would not end duty to consult)](https://thenarwhal.ca/bc-declaration-act-explainer/)

**BC Greens** (basis: both, confidence: high)

- [BC Ballot: DRIPA and Indigenous relations explainer](https://bcballot.ca/platforms/issues/dripa-and-indigenous-relations/)
- [CP24: Lowan on weakening Indigenous rights (Feb 9, 2026)](https://www.cp24.com/news/canada/2026/02/09/bc-greens-wont-renew-accord-with-ndp-citing-stalled-undelivered-promises/)
- [BC Greens: Our Plan](https://bcgreens.ca/our-plan/)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 8-9, 32, 35-36)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [CentreBC: Reconciliation, Certainty and Prosperity (Aug 13, 2026, superseded)](https://www.centrebc.ca/news/statement-reconciliation-certainty-and-prosperity/)

**OneBC** (basis: both, confidence: high)

- [OneBC priorities](https://1bc.ca/priorities)
- [Wikipedia: OneBC (secondary)](https://en.wikipedia.org/wiki/OneBC_(political_party))
- [Votes and Proceedings, October 29, 2025](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251029.htm)


</details>

<details>
<summary><b>Should the province repeal, step back from, keep or expand SOGI 123, optional school materials on sexual orientation and gender identity?</b> (Province-wide, <code>q_sogi</code>)</summary>

**BC NDP** (basis: both, confidence: medium)

- [CBC via Yahoo: where BC parties stand on SOGI 123 (Sept 28, 2026)](https://ca.news.yahoo.com/where-b-c-provincial-political-130000614.html)
- [Castanet: province ends ARC Foundation funding](https://www.castanetkamloops.net/news/Kamloops/627143/SD73-schools-wont-feel-change-as-province-ends-funding-for-ARC-Foundation-superintendent)
- [Votes and Proceedings, February 26, 2026](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260226.htm)

**BC Conservatives** (basis: both, confidence: high)

- [Conservative Party of BC: Safe Schools plan](https://conservativebc.ca/plan/safe-schools/)
- [CBC via Yahoo: where BC parties stand on SOGI 123 (Doerkson on 'arithmetic and reading')](https://ca.news.yahoo.com/where-b-c-provincial-political-130000614.html)
- [Global News: 2024 Conservative platform (SOGI pledges)](https://globalnews.ca/news/10812384/affordability-safety-scrapping-carbon-price-bc-conservatives-full-platform)
- [Rocky Mountain Goat: Conservatives on the Human Rights Code Repeal Act first reading](https://therockymountaingoat.com/2026/03/bird-conservatives-vote-to-give-first-reading-to-human-rights-code-repeal-act/)
- [Votes and Proceedings, February 19, 2026](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260219.htm)

**BC Greens** (basis: both, confidence: high)

- [CBC via Yahoo: parties on SOGI 123](https://ca.news.yahoo.com/where-b-c-provincial-political-130000614.html)
- [BC Ballot: BC Green education commitments](https://bcballot.ca/platforms/bc-green-party/)

**CentreBC** (basis: both, confidence: medium)

- [CBC via Yahoo: parties on SOGI 123](https://ca.news.yahoo.com/where-b-c-provincial-political-130000614.html)
- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 20-24; no SOGI item)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [Penticton Western News: Sturko on why she cannot return to the Conservatives](https://pentictonwesternnews.com/2026/09/22/surreys-elenore-sturko-is-the-sole-incumbent-mla-for-centrebc-ahead-of-election/)

**OneBC** (basis: both, confidence: high)

- [OneBC priorities](https://1bc.ca/priorities)
- [CTV: puberty blocker bill defeated](https://www.ctvnews.ca/vancouver/article/bc-bill-that-would-have-stopped-doctors-from-providing-puberty-blockers-defeated/)
- [CTV: OneBC stands aside for eight Conservatives](https://www.ctvnews.ca/vancouver/article/onebc-pledges-not-to-run-against-eight-principled-bc-conservative-candidates/)


</details>

<details>
<summary><b>BC's toxic drug emergency is ten years old. What approach should the province take now?</b> (Province-wide, <code>q_drugs</code>)</summary>

**BC NDP** (basis: record, confidence: high)

- [National Newswatch / CP: BC ending decriminalization pilot (Jan 14, 2026)](https://nationalnewswatch.com/2026/01/14/b-c-ending-its-3-year-drug-decriminalization-pilot-project)
- [BCCSU: witnessed dosing required for safer supply](https://www.bccsu.ca/blog/news/b-c-to-require-most-drug-users-receiving-safe-supply-to-have-their-doses-witnessed/)
- [Global News: involuntary care provisions found unconstitutional (Jul 31, 2026)](https://globalnews.ca/news/12005744/sections-bc-involuntary-care-rules-found-unconstitutional/)
- [Kelowna Capital News: Eby on involuntary care and supervised sites (Oct 2, 2026)](https://kelownacapnews.com/2026/10/02/eby-announces-b-c-grocery-price-guard-social-disorder-during-kelowna-visit/)
- [CKPG: 132 involuntary care beds including 60 in Surrey](https://ckpgtoday.ca/2026/07/10/premier-announces-location-of-prince-george-involuntary-care-facility/)

**BC Conservatives** (basis: both, confidence: high)

- [Conservative Party of BC: Safe Streets for BC](https://conservativebc.ca/safe-streets-for-bc/)
- [CBC 2024: Conservatives vow to shut consumption sites (not repeated in 2026)](https://amp.cbc.ca/lite/story/1.7331415)
- [Langley Advance Times: Conservative plan on police and drug use in hospitals](https://langleyadvancetimes.com/2026/10/06/b-c-conservatives-plan-to-hire-more-police-stop-illegal-drug-use-in-hospitals-shelters/)

**BC Greens** (basis: platform, confidence: high)

- [BC Greens Toxic Drugs Policy Brief 2026 (PDF)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Toxic-Drugs-Policy-Brief-2026-1.pdf)
- [BC Greens: toxic drugs policy release with Lisa Lapointe](https://bcgreens.ca/announce-toxic-drugs-policy-alongside-former-chief-coroner-and-candidate-for-saanich-south-lisa-lapointe/)
- [BCCSU: estimate of deaths prevented by supervised sites](https://www.bccsu.ca/blog/news/b-c-conservatives-vow-to-shut-down-safe-consumption-sites/)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 18-19, 25-27)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [Cloverdale Reporter: Sturko's Mental Health Act bill](https://www.cloverdalereporter.com/news/surrey-south-mla-elenore-sturko-introduces-bill-aimed-at-helping-prevent-suicides/)

**OneBC** (basis: platform, confidence: high)

- [OneBC priorities](https://1bc.ca/priorities)
- [Wikipedia: OneBC (secondary)](https://en.wikipedia.org/wiki/OneBC_(political_party))


</details>

<details>
<summary><b>What should the province do about crime and public safety?</b> (Province-wide, <code>q_public_safety</code>)</summary>

**BC NDP** (basis: both, confidence: medium)

- [BC NDP: Jewish community security and extremism summit (Oct 5, 2026)](https://www.bcndp.ca/releases/bc-ndp-commits-jewish-community-security-investment-and-summit-confront-organized-hate)
- [Kelowna Capital News: Eby on repeat property offenders (Oct 2, 2026)](https://kelownacapnews.com/2026/10/02/eby-announces-b-c-grocery-price-guard-social-disorder-during-kelowna-visit/)
- [BC Government: Crime Severity Index release (Jul 22, 2026)](https://archive.news.gov.bc.ca/releases/news_releases_2024-2028/2026PSSG0064-000862.htm)
- [Votes and Proceedings, October 25, 2023 (Bill 36)](https://lims.leg.bc.ca/pdms/ldp/42nd4th/votes/v231025.htm)
- [Justice Canada: Eby and federal bail reform (Oct 2025)](https://www.canada.ca/en/department-justice/news/2025/10/minister-fraser-premier-eby-and-attorney-general-sharma-underscore-collaboration-behind-canadas-new-bail-and-sentencing-reforms.html)

**BC Conservatives** (basis: platform, confidence: high)

- [Conservative Party of BC: Safe Streets for BC](https://conservativebc.ca/safe-streets-for-bc/)
- [Langley Advance Times: Conservative plan to hire more police (Oct 6, 2026)](https://langleyadvancetimes.com/2026/10/06/b-c-conservatives-plan-to-hire-more-police-stop-illegal-drug-use-in-hospitals-shelters/)
- [Fraser Institute: violent crime index commentary](https://www.fraserinstitute.org/commentary/crime-stats-belie-bc-governments-safer-province-claims)

**BC Greens** (no published position)

- [BC Ballot: BC Green commitments (no public safety item)](https://bcballot.ca/platforms/bc-green-party/)
- [BC Greens Toxic Drugs Policy Brief 2026 (PDF)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Toxic-Drugs-Policy-Brief-2026-1.pdf)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 26-29)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [CentreBC: three-step anti-extortion plan (November 2025, not repeated in the platform)](https://www.centrebc.ca/news/news-release/centrebc-unveils-3-step-plan-to-crush-transnational-extortion-terrorizing-surrey/)
- [CentreBC: leader biography](https://www.centrebc.ca/leader/)

**OneBC** (basis: platform, confidence: medium)

- [OneBC priorities](https://1bc.ca/priorities)
- [BC Ballot: platform comparison](https://bcballot.ca/platforms/)


</details>

<details>
<summary><b>With American tariffs and slow growth, what should BC's plan for the economy be?</b> (Province-wide, <code>q_economy_tariffs</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [BC Government: First Quarterly Report 2026-27 (Sept 14, 2026)](https://news.gov.bc.ca/releases/2026FIN0031-001066)
- [BC Government: Look West strategy, delivering major projects faster](https://www2.gov.bc.ca/gov/content/employment-business/look-west-strategy/delivering-major-projects-faster)
- [BC Ballot: BC NDP commitments (procurement, minerals, relief fund)](https://bcballot.ca/platforms/bc-ndp/)
- [Votes and Proceedings, May 28, 2025 (Bills 7, 14, 15)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v250528.htm)
- [CTV / CP: LNG Canada Phase 2 and the campaign](https://www.ctvnews.ca/vancouver/article/ebys-election-campaign-gets-lift-from-lng-canada-announcement/)

**BC Conservatives** (basis: both, confidence: high)

- [Conservative Party of BC: BC Energy Superpower Plan](https://conservativebc.ca/make-british-columbia-an-energy-superpower/)
- [Conservative Party of BC: Supercharge BC's economy](https://conservativebc.ca/supercharge-british-columbias-economy/)
- [Votes and Proceedings, May 28, 2025 (Conservative nay on Bills 14 and 15)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v250528.htm)

**BC Greens** (basis: platform, confidence: high)

- [BC Greens: Economic Vision (PDF)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Economic-Vision.pdf)
- [BC Greens: Our Plan](https://bcgreens.ca/our-plan/)
- [BC Greens: support renewables, not Bill 14 as drafted](https://bcgreens.ca/bc-greens-support-renewable-energy-not-bill-14-as-currently-drafted/)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 8-10, 13, 36-37)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [Surrey Now-Leader: Sturko promises manufacturing boost (Oct 9, 2026)](https://surreynowleader.com/2026/10/09/centrebc-leader-promisesmanufacturing-boost)

**OneBC** (basis: platform, confidence: medium)

- [OneBC priorities](https://1bc.ca/priorities)
- [Wikipedia: OneBC (secondary, 2025 releases)](https://en.wikipedia.org/wiki/OneBC_(political_party))


</details>

<details>
<summary><b>What direction should BC take on climate change and energy?</b> (Province-wide, <code>q_climate_energy</code>)</summary>

**BC NDP** (basis: record, confidence: high)

- [The Tyee: BC admits 2030 climate goal out of reach (May 2025)](https://thetyee.ca/News/2025/05/01/BC-Admits-Climate-Goals/)
- [CBC: BC ends consumer carbon tax (April 2025)](https://www.cbc.ca/lite/story/1.7493181)
- [National Newswatch: BC drops 2035 EV mandate (Nov 2025)](https://nationalnewswatch.com/2025/11/18/b-c-to-redraw-ev-sales-mandate-scrapping-goal-of-100-per-cent-by-2035)
- [BC NDP: LNG capacity figures (Sept 28, 2026)](https://www.bcndp.ca/releases/bc-conservatives-lng-plan-out-step-reality)
- [CTV: Eby open to pipeline if tanker ban remains (2025)](https://www.ctvnews.ca/politics/article/bc-premier-open-to-new-pipeline-if-tanker-ban-remains-in-place/)

**BC Conservatives** (basis: both, confidence: medium)

- [Conservative Party of BC: BC Energy Superpower Plan](https://conservativebc.ca/make-british-columbia-an-energy-superpower/)
- [Conservative Party of BC: welcome LNG Canada Phase 2](https://conservativebc.ca/bc-conservatives-welcome-lng-canada-phase-2-we-will-treat-energy-as-an-urgent-mission/)
- [Western Standard: Rustad calls to axe industrial carbon tax (April 2025)](https://www.westernstandard.news/amp/story/watch/watch-rustad-calls-on-bc-ndp-to-axe-industrial-carbon-tax/63616)
- [Global News: 2024 Conservative platform (LCFS and CleanBC)](https://globalnews.ca/news/10812384/affordability-safety-scrapping-carbon-price-bc-conservatives-full-platform)

**BC Greens** (basis: both, confidence: high)

- [BC Greens: Our Plan](https://bcgreens.ca/our-plan/)
- [BC Greens: Economic Vision (PDF)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Economic-Vision.pdf)
- [BC Government: carbon tax repeal release (Greens' objection noted in coverage)](https://news.gov.bc.ca/releases/2025FIN0014-000280)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 8, 11, 30-33, 39)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [CentreBC: Ottawa and BC moved toward CentreBC pipeline conditions (Jul 2026)](https://www.centrebc.ca/news/ottawa-and-bc-just-moved-toward-centrebc-pipeline-conditions/)

**OneBC** (basis: inferred, confidence: low)

- [OneBC priorities](https://1bc.ca/priorities)
- [BC Ballot: platform comparison](https://bcballot.ca/platforms/)


</details>

<details>
<summary><b>What should the province's priorities be for child care and for schools from kindergarten to Grade 12?</b> (Province-wide, <code>q_education_childcare</code>)</summary>

**BC NDP** (basis: record, confidence: high)

- [Global News: $10-a-day program paused (Feb 2026)](https://globalnews.ca/news/11673463/10-a-day-daycare-program-paused/)
- [Global News: Surrey schools and the NDP's building record](https://globalnews.ca/news/11350841/surrey-schools-ndp-building)
- [BC Government: $10-a-day spaces (2025)](https://news.gov.bc.ca/releases/2025ECC0015-000242)
- [BC Ballot: BC NDP commitments (no education item)](https://bcballot.ca/platforms/bc-ndp/)

**BC Conservatives** (basis: both, confidence: low)

- [Conservative Party of BC: Safe Schools plan](https://conservativebc.ca/plan/safe-schools/)
- [Global News: 2024 Conservative platform (letter grades, exams)](https://globalnews.ca/news/10812384/affordability-safety-scrapping-carbon-price-bc-conservatives-full-platform)
- [BC Ballot: Conservative commitments](https://bcballot.ca/platforms/conservative-party/)

**BC Greens** (basis: platform, confidence: high)

- [BC Greens: lift the freeze on $10-a-day, universal free child care by 2031](https://bcgreens.ca/announce-plan-to-lift-the-freeze-on-10-a-day-daycare-with-universal-free-child-care-by-2031-alongside-new-candidate-for-victoria-swan-lake/)
- [BC Ballot: BC Green education and child care commitments](https://bcballot.ca/platforms/bc-green-party/)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 6, 20-24, 40-41)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [CentreBC: AI strategy vacuum (Jun 2026)](https://www.centrebc.ca/news/ai-strategy-vacuum/)

**OneBC** (basis: platform, confidence: high)

- [OneBC priorities](https://1bc.ca/priorities)
- [BC Ballot: platform comparison](https://bcballot.ca/platforms/)


</details>

<details>
<summary><b>Should BC keep no-fault car insurance, bring back lawsuits for serious injuries, or open insurance to competition?</b> (Province-wide, <code>q_icbc</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [BC NDP: ICBC rate freeze to 2030 (Oct 8, 2026)](https://www.bcndp.ca/releases/eby-freeze-car-insurance-rates-another-three-years)
- [BC Government: ICBC rate freeze release (2025)](https://news.gov.bc.ca/releases/2025AG0063-001064)
- [BC Budget 2025: ICBC service plan (legacy claims)](https://bcbudget.gov.bc.ca/2025/sp/pdf/agency/icbc.pdf)

**BC Conservatives** (basis: platform, confidence: medium)

- [Global News: Conservative plan to end no-fault (leaked letter)](https://globalnews.ca/news/12090331/bc-conservatives-plan-no-fault-insurance-repeal/)
- [CP24: leaked letter details (Oct 6, 2026)](https://www.cp24.com/news/canada/2026/10/06/bc-conservatives-plan-to-end-no-fault-insurance-leaked-letter-shows/)
- [Conservative Party of BC: Insurance plan page](https://conservativebc.ca/plan/insurance/)

**BC Greens** (no published position)

- [BC Ballot: BC Green commitments (no ICBC item)](https://bcballot.ca/platforms/bc-green-party/)
- [BC Greens: Our Plan](https://bcgreens.ca/our-plan/)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 6, 13)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [Canadian Press via Medicine Hat News: Sturko asks for the full Conservative ICBC proposal (Oct 8)](https://medicinehatnews.com/news/national-news/2026/10/08/b-c-campaign-trail-conservatives-promise-1000-tax-cut-by-boosting-exemption-level/)

**OneBC** (basis: platform, confidence: high)

- [OneBC priorities](https://1bc.ca/priorities)


</details>

<details>
<summary><b>How much power should the province use, and should BC change its voting system?</b> (Province-wide, <code>q_democracy_power</code>)</summary>

**BC NDP** (basis: record, confidence: high)

- [The Tyee: NDP defends rushing Bills 14 and 15 (Jun 2025)](https://thetyee.ca/News/2025/06/02/NDP-Defends-Rush-Pass-Bills-Speed-Development/)
- [BIV: NDP weighs changes amid backlash to Bill 7 powers](https://www.biv.com/news/rob-shaw-ndp-weighs-changes-amid-backlash-to-ebys-emergency-powers-bill-10419547)
- [Boundary Creek Times: cabinet order expands Bill 14 scope](https://www.boundarycreektimes.com/news/bc-quietly-expands-scope-of-bill-14-to-include-all-future-wind-and-solar-8131910)
- [Angus Reid: two-thirds say the election came too soon](https://angusreid.org/85168-2/)
- [BC Government: 2017 donation ban release](https://news.gov.bc.ca/releases/2017PREM0084-001592)

**BC Conservatives** (basis: both, confidence: medium)

- [Conservative Party of BC: Supercharge BC's economy (permitting act, red tape law)](https://conservativebc.ca/supercharge-british-columbias-economy/)
- [Votes and Proceedings, May 28, 2025](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v250528.htm)
- [Daily Hive: Metro Vancouver rollback](https://dailyhive.com/vancouver/bc-conservatives-metro-vancouver-regional-district-reform-platform-promise)

**BC Greens** (basis: both, confidence: high)

- [BC Greens: Our Plan (proportional representation)](https://bcgreens.ca/our-plan/)
- [CBC: 2018 electoral reform referendum results](https://www.cbc.ca/news/canada/british-columbia/electoral-reform-referendum-results-1.4954538)
- [Castanet: Greens will not back vague infrastructure bill](https://www.castanetkamloops.net/news/BC/549318/B-C-Greens-wont-back-governments-vague-infrastructure-bill)

**CentreBC** (basis: platform, confidence: medium)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 34-37, 39-41)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [Penticton Western News: Sturko on the snap election](https://pentictonwesternnews.com/2026/09/22/surreys-elenore-sturko-is-the-sole-incumbent-mla-for-centrebc-ahead-of-election/)

**OneBC** (basis: platform, confidence: low)

- [Wikipedia: OneBC (secondary, June 2025 release)](https://en.wikipedia.org/wiki/OneBC_(political_party))
- [OneBC priorities](https://1bc.ca/priorities)


</details>

<details>
<summary><b>How should the province finish the SkyTrain line and fund TransLink, the regional transit agency, after 2028?</b> (Regional: Surrey, <code>q_local_skytrain</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [Surrey-Langley SkyTrain monthly status report (April 2026)](https://surreylangleyskytrain.gov.bc.ca/app/uploads/sites/938/2026/06/SLS_Monthly-Status-Report_April_2026.pdf)
- [Daily Hive: Eby rules out TransLink vehicle levy (Oct 2, 2026)](https://dailyhive.com/vancouver/bc-ndp-david-eby-translink-vehicle-levy)
- [Connect FM: NDP promises to fully complete Surrey-Langley SkyTrain](https://connectfm.ca/en/news/post/bc-ndp-promises-to-fully-complete-surrey-langley-skytrain)
- [Jagrup Brar campaign page (party-authored)](https://jagrupbrar.bcndp.ca)

**BC Conservatives** (basis: both, confidence: low)

- [Global News: Surrey-Langley SkyTrain cost rises to $6B (Aug 2024)](https://globalnews.ca/news/10701039/surrey-langley-skytrain-cost)
- [BC Ballot: Conservative commitments (no transportation item)](https://bcballot.ca/platforms/conservative-party/)
- [Daily Hive: Metro Vancouver rollback](https://dailyhive.com/vancouver/bc-conservatives-metro-vancouver-regional-district-reform-platform-promise)

**BC Greens** (basis: platform, confidence: medium)

- [Global News: Green free transit pledge (Oct 9, 2026)](https://globalnews.ca/news/12097726/bc-leaders-campaign-trail-health-care-supporting-seniors-october-9)
- [BC Greens: Our Plan](https://bcgreens.ca/our-plan/)
- [BC Greens: Tim Binnema candidate page](https://bcgreens.ca/candidates/tim-binnema/)

**CentreBC** (basis: platform, confidence: medium)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 11, 13)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [CentreBC: Paul Brar candidate page](https://centrebc.ca/candidates/paul-brar/)

**OneBC** (no published position)

- [OneBC priorities](https://1bc.ca/priorities)
- [OneBC: Carolyn Hofbauer candidate page](https://1bc.ca/candidates/chofbauer)


</details>

<details>
<summary><b>How should the province respond to extortion, threats demanding money, in Surrey while the city changes police forces?</b> (Regional: Surrey, <code>q_local_extortion</code>)</summary>

**BC NDP** (basis: record, confidence: medium)

- [Surrey Police Service: extortion statistics](https://www.surreypolice.ca/extortions)
- [Global News: Surrey extortion cases, Eby wants more arrests (Jan 2026)](https://globalnews.ca/news/11615290/extortion-cases-surrey-2026)
- [Votes and Proceedings, October 25, 2023 (Bill 36)](https://lims.leg.bc.ca/pdms/ldp/42nd4th/votes/v231025.htm)
- [Surrey Police Service: transition timeline (July 2026)](https://www.surreypolice.ca/sites/default/files/media/documents/Policing%20Transition%20Timeline_july2026.pdf)
- [BC Ballot: Jagrup Brar voting record](https://bcballot.ca/mlas/jagrup-brar/)

**BC Conservatives** (basis: platform, confidence: medium)

- [Conservative Party of BC: Safe Streets for BC](https://conservativebc.ca/safe-streets-for-bc/)
- [Conservative Party of BC: Surrey candidates announcement (Sept 29, 2026)](https://conservativebc.ca/conservative-party-of-bc-announces-strong-surrey-candidates-for-serious-times/)
- [Conservative Party of BC: Garry Purewal candidate page](https://conservativebc.ca/candidate/garry-purewal/)
- [Conservative Party of BC: 2025 extortion statement](https://conservativebc.ca/extortion_shooting_in_surrey/)

**BC Greens** (no published position)

- [BC Ballot: BC Green commitments (no public safety item)](https://bcballot.ca/platforms/bc-green-party/)
- [BC Ballot: Tim Binnema, Surrey-Fleetwood](https://bcballot.ca/ridings/surrey-fleetwood/tim-binnema/)

**CentreBC** (basis: platform, confidence: medium)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 26-29)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [CentreBC: three-step anti-extortion plan (November 2025, not repeated in the platform)](https://www.centrebc.ca/news/news-release/centrebc-unveils-3-step-plan-to-crush-transnational-extortion-terrorizing-surrey/)
- [CentreBC: Paul Brar candidate page](https://centrebc.ca/candidates/paul-brar/)
- [CentreBC: leader biography](https://www.centrebc.ca/leader/)

**OneBC** (basis: platform, confidence: medium)

- [OneBC priorities](https://1bc.ca/priorities)
- [OneBC: Carolyn Hofbauer candidate page](https://1bc.ca/candidates/chofbauer)


</details>

<details>
<summary><b>How should the province handle Surrey's half-built hospital, overloaded emergency room and crowded schools?</b> (Regional: Surrey, <code>q_local_hospital_schools</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [Indo-Canadian Voice: Doerkson has no answer on Surrey hospital, Brar on progress (Oct 7, 2026)](https://voiceonline.com/doerkson-has-no-answer-on-surrey-hospital-more-than-halfway-built-bc-ndp/)
- [Global News: Surrey schools and the NDP's building record](https://globalnews.ca/news/11350841/surrey-schools-ndp-building)
- [Surrey Now-Leader: Eby promises more doctors in Surrey (Oct 9, 2026)](https://surreynowleader.com/2026/10/09/b-c-election-battleground-in-surrey-eby-promises-more-doctors-to-fast-track-intl-grads/)
- [CTV: new Surrey hospital cost and 2030 opening](https://guelph.ctvnews.ca/vancouver/article/new-surrey-hospital-will-cost-1b-more-than-planned-wont-open-until-2030)
- [Jagrup Brar campaign page (party-authored)](https://jagrupbrar.bcndp.ca)

**BC Conservatives** (basis: platform, confidence: low)

- [Indo-Canadian Voice: Doerkson on the Surrey hospital (Oct 7, 2026)](https://voiceonline.com/doerkson-has-no-answer-on-surrey-hospital-more-than-halfway-built-bc-ndp/)
- [Conservative Party of BC: Keep Emergency Rooms Open](https://conservativebc.ca/keep-emergency-rooms-open/)
- [Sitka Media: Conservative seniors plan](https://www.sitkamedia.ca/watch-bc-conservatives-unveil-plan-to-support-seniors/)
- [Conservative Party of BC: Garry Purewal candidate page](https://conservativebc.ca/candidate/garry-purewal/)

**BC Greens** (basis: platform, confidence: medium)

- [BC Ballot: BC Green health and education commitments](https://bcballot.ca/platforms/bc-green-party/)
- [BC Greens: Tim Binnema candidate page](https://bcgreens.ca/candidates/tim-binnema/)
- [BC Ballot: Tim Binnema, Surrey-Fleetwood](https://bcballot.ca/ridings/surrey-fleetwood/tim-binnema/)

**CentreBC** (basis: platform, confidence: medium)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 16-17, 21)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [CentreBC: Paul Brar candidate page](https://centrebc.ca/candidates/paul-brar/)

**OneBC** (basis: platform, confidence: medium)

- [OneBC priorities](https://1bc.ca/priorities)
- [OneBC: Carolyn Hofbauer candidate page](https://1bc.ca/candidates/chofbauer)


</details>

<details>
<summary><b>TransLink needs at least $112 million a year in new money from 2028. How should the province fund transit in Metro Vancouver?</b> (Regional: Metro Vancouver, <code>q_local_metro_translink</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [Daily Hive: Eby rules out TransLink vehicle levy (Oct 2, 2026)](https://dailyhive.com/vancouver/bc-ndp-david-eby-translink-vehicle-levy)
- [Sitka Media: TransLink calls for stable funding plan after NDP rules out levy (Oct 2, 2026)](https://www.sitkamedia.ca/translink-calls-for-stable-funding-plan-after-bc-ndp-says-vehicle-levy-road-pricing-off-the-table/)
- [Daily Hive: NDP fuel tax cut pledge (Oct 1, 2026)](https://dailyhive.com/vancouver/bc-gas-prices-david-eby-election-2026)

**BC Conservatives** (basis: platform, confidence: medium)

- [Conservative Party of BC: Eby must answer on secret vehicle tax plan (Oct 2, 2026)](https://conservativebc.ca/eby-must-answer-on-secret-vehicle-tax-plan/)
- [Conservative Party of BC: Delivering essential services and cutting waste at Metro Vancouver (Oct 5, 2026)](https://conservativebc.ca/conservative-platform-delivering-essential-services-and-cutting-waste-at-metro-vancouver/)
- [Conservative Party of BC: Support BC's seniors (Oct 9, 2026)](https://conservativebc.ca/support-bcs-seniors/)
- [CP24: campaigns enter second week, no new taxes pledge (Sept 28, 2026)](https://www.cp24.com/news/canada/2026/09/28/bc-election-campaigns-enter-second-week-with-candidate-policy-announcements/)

**BC Greens** (basis: platform, confidence: medium)

- [BC Greens: Transit and Transportation Policy Brief 2026 (PDF, Oct 9, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Transit-and-Transportation-Policy-Brief-2026.pdf)
- [BC Greens: funding for fast, frequent transit and passenger rail (Oct 9, 2026)](https://bcgreens.ca/bc-greens-commit-to-funding-for-fast-frequent-transit-pledge-to-fight-for-province-wide-passenger-rail/)
- [Daily Hive: reaction to Eby fuel tax promise (Oct 2, 2026)](https://dailyhive.com/vancouver/b-c-reacts-eby-promise-slash-gas-prices)

**CentreBC** (basis: platform, confidence: medium)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 10, 13)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (no published position)

- [OneBC priorities](https://1bc.ca/priorities)
- [BC Ballot: OneBC commitments (no transportation item)](https://bcballot.ca/platforms/onebc/)


</details>

<details>
<summary><b>A 2025 ruling recognized Cowichan title over Richmond land with private homes. How should owners be protected and claims settled?</b> (Regional: Metro Vancouver, <code>q_local_metro_title_homes</code>)</summary>

**BC NDP** (basis: record, confidence: medium)

- [The Narwhal: BC election 2026 and DRIPA (Oct 7, 2026)](https://thenarwhal.ca/bc-election-2026-dripa)
- [Angus Reid: BC, Musqueam and Cowichan, property rights (March 2026)](https://angusreid.org/bc-eby-musqueam-cowichan-property-rights-conservative-leadership/)

**BC Conservatives** (basis: both, confidence: medium)

- [Conservative Party of BC: First Nations and DRIPA (Oct 7, 2026)](https://conservativebc.ca/plan/first-nations-dripa/)
- [Lorne Doerkson on X: repeal DRIPA, protect property rights (Oct 7, 2026)](https://x.com/LDoerkson/status/2108048609283645690)
- [Votes and Proceedings, October 29, 2025 (Property Rights Protection Act)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251029.htm)

**BC Greens** (basis: platform, confidence: medium)

- [BC Greens: statement on the National Day for Truth and Reconciliation (Sept 30, 2026)](https://bcgreens.ca/statement-on-national-day-for-truth-and-reconciliation/)
- [BC Greens: Indigenous Rights Policy Brief 2026 (PDF)](https://bcgreens.ca/wp-content/uploads/2026/09/BC-Greens-Indigenous-Rights-Policy-Brief-2026.pdf)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 35-36)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (basis: platform, confidence: medium)

- [OneBC priorities](https://1bc.ca/priorities)
- [OneBC on X: property and the reconciliation industry (Sept 26, 2026)](https://x.com/One_BCHQ/status/2103913099086684163)
- [Votes and Proceedings, October 29, 2025 (Property Rights Protection Act)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251029.htm)


</details>

<details>
<summary><b>Sixteen Metro Vancouver mayors want the 2023 density laws undone. Keep the rules, add to them, or give councils back the say?</b> (Regional: Metro Vancouver, <code>q_local_metro_density</code>)</summary>

**BC NDP** (basis: record, confidence: high)

- [Daily Hive: Metro Vancouver mayors ask province to unwind housing laws (Dec 13, 2025)](https://dailyhive.com/vancouver/metro-vancouver-mayors-bc-housing-legislation-opposition-letter)
- [Votes and Proceedings, November 29, 2023 (Bills 44 and 46)](https://lims.leg.bc.ca/pdms/ldp/42nd4th/votes/v231129.htm)
- [BC NDP: turn more empty condos into homes (Sept 25, 2026)](https://www.bcndp.ca/releases/eby-turn-more-empty-condos-homes-people-can-afford)

**BC Conservatives** (basis: inferred, confidence: low)

- [Storeys: BC Conservatives' housing plan, 2024 election (Oct 1, 2024)](https://storeys.com/bc-conservatives-housing-plan-election-2024/)
- [Global News: Rustad housing policy (2024)](https://globalnews.ca/news/10779404/bc-election-conservative-rustad-housing-policy)
- [Conservative Party of BC: statement on the NDP housing tax plan (Sept 25, 2026)](https://conservativebc.ca/statement-from-interim-leader-lorne-doerkson-on-the-ndps-housing-tax-plan/)
- [Conservative Party of BC: Metro Vancouver plan (Oct 5, 2026)](https://conservativebc.ca/conservative-platform-delivering-essential-services-and-cutting-waste-at-metro-vancouver/)

**BC Greens** (basis: inferred, confidence: low)

- [Votes and Proceedings, November 29, 2023 (Bills 44 and 46)](https://lims.leg.bc.ca/pdms/ldp/42nd4th/votes/v231129.htm)
- [BC Greens: Our Plan](https://bcgreens.ca/our-plan/)
- [BC Greens: Rights for Renters Policy Brief 2026 (PDF, Sept 29, 2026)](https://bcgreens.ca/wp-content/uploads/2026/09/BC-Greens-Rights-for-Renters-Policy-Brief-2026.pdf)

**CentreBC** (basis: platform, confidence: medium)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 6, 10, 13)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (no published position)

- [OneBC priorities](https://1bc.ca/priorities)
- [BC Ballot: housing issue page (party commitments and votes)](https://bcballot.ca/platforms/issues/housing/)


</details>

<details>
<summary><b>The province proposed letting food plants use some lower-quality land in the Agricultural Land Reserve. What should happen?</b> (Regional: Fraser Valley, <code>q_local_fraser_valley_farmland</code>)</summary>

**BC NDP** (basis: both, confidence: medium)

- [BC Gov News: proposed changes to support food processing in the ALR (July 23, 2026)](https://news.gov.bc.ca/releases/2026AF0017-000863)
- [The Tyee: How the ALR's future is becoming an election issue (Oct 7, 2026)](https://thetyee.ca/News/2026/10/07/ALR-Future-Becoming-Election-Issue/)
- [BC Ballot: BC NDP commitments](https://bcballot.ca/platforms/bc-ndp/)

**BC Conservatives** (no published position)

- [The Tyee: How the ALR's future is becoming an election issue (Oct 7, 2026)](https://thetyee.ca/News/2026/10/07/ALR-Future-Becoming-Election-Issue/)
- [Conservative Party of BC: Our Plan (no agriculture item)](https://conservativebc.ca/plan/)

**BC Greens** (basis: platform, confidence: medium)

- [The Tyee: How the ALR's future is becoming an election issue (Oct 7, 2026)](https://thetyee.ca/News/2026/10/07/ALR-Future-Becoming-Election-Issue/)
- [BC Greens: plan to support local food production and farmers (Oct 2, 2026)](https://bcgreens.ca/launch-plan-to-support-local-food-production-and-farmers/)

**CentreBC** (basis: inferred, confidence: low)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, Economy and Affordability)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (no published position)

- [OneBC priorities](https://1bc.ca/priorities)
- [BC Ballot: OneBC commitments (no agriculture item)](https://bcballot.ca/platforms/onebc/)


</details>

<details>
<summary><b>Highway 1 widening is funded to Highway 11 in Abbotsford by 2031 and only planned to Chilliwack. Where should the next money go?</b> (Regional: Fraser Valley, <code>q_local_fraser_valley_highway1</code>)</summary>

**BC NDP** (basis: record, confidence: medium)

- [BC Gov: Fraser Valley Highway 1 program](https://www2.gov.bc.ca/gov/content/transportation-projects/fraser-valley-highway1)
- [BC Gov News: Highway 1 widening to Highway 11 (Aug 14, 2024)](https://news.gov.bc.ca/releases/2024MOTI0113-001306)
- [Fraser Valley Current: West Coast Express extension promise update (Mar 4, 2025)](https://fvcurrent.com/p/west-coast-extension-promise-update)
- [Daily Hive: Eby rules out TransLink vehicle levy and road pricing (Oct 2, 2026)](https://dailyhive.com/vancouver/bc-ndp-david-eby-translink-vehicle-levy)

**BC Conservatives** (basis: inferred, confidence: low)

- [Fraser Valley Today: Conservatives pledge six lanes through Chilliwack (Oct 3, 2024)](https://fraservalleytoday.ca/2024/10/03/b-c-conservatives-pledge-to-expand-highway-1-to-6-lanes-through-chilliwack/)
- [Conservative Party of BC: Our Plan (no highway item)](https://conservativebc.ca/plan/)
- [BC Ballot: Conservative commitments](https://bcballot.ca/platforms/conservative-party/)

**BC Greens** (basis: platform, confidence: medium)

- [Langley Advance Times: Greens release transportation plans (Oct 9, 2026)](https://langleyadvancetimes.com/2026/10/09/b-c-greens-release-transportation-plans-includes-free-transit-for-youth-seniors/)
- [BC Greens: Transit and Transportation Policy Brief 2026 (PDF)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Transit-and-Transportation-Policy-Brief-2026.pdf)

**CentreBC** (basis: platform, confidence: medium)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 10, 13)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (no published position)

- [OneBC priorities](https://1bc.ca/priorities)
- [BC Ballot: OneBC commitments (no transportation item)](https://bcballot.ca/platforms/onebc/)


</details>

<details>
<summary><b>Mission Memorial's emergency room closed overnight for 51 nights in a row this spring for lack of doctors. What should come first?</b> (Regional: Fraser Valley, <code>q_local_fraser_valley_er</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [Mission City Record: more overnight closures coming to Mission Memorial ER (Aug 6, 2026)](https://missioncityrecord.com/2026/08/06/more-overnight-closures-coming-to-mission-memorial-hospital-emergency-department/)
- [Langley Advance Times: Eby vows to fast-track international medical grads, more doctors for rural areas (Oct 9, 2026)](https://langleyadvancetimes.com/2026/10/09/b-c-election-eby-vows-to-fast-track-intl-medical-grads-bring-more-docs-to-rural-areas/)
- [BC NDP: more doctors and nurses, fast-tracking international graduates (Oct 9, 2026)](https://www.bcndp.ca/releases/ebys-plan-includes-more-doctors-and-nurses-fast-tracking-international-graduates)

**BC Conservatives** (basis: platform, confidence: medium)

- [Conservative Party of BC: Keep emergency rooms open (Oct 5, 2026)](https://conservativebc.ca/keep-emergency-rooms-open/)
- [Abbotsford News: Doerkson pledges $50M fund for ER closures (Oct 5, 2026)](https://abbynews.com/2026/10/05/lorne-doerkson-pledges-to-create-50m-fund-to-address-emergency-room-closures/)
- [Abbotsford News: Abbotsford-Mission by-election debate (Sept 14, 2026)](https://abbynews.com/2026/09/14/mla-hopefuls-spar-in-abbotsford-mission-byelection-debate/)

**BC Greens** (basis: platform, confidence: medium)

- [BC Greens: Healthcare Policy Brief 2026 (PDF, Oct 6, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Healthcare-Policy-Brief-2026.pdf)
- [BC Greens: Our Plan](https://bcgreens.ca/our-plan/)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, p 16)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [Abbotsford News: Abbotsford-Mission by-election debate (Sept 14, 2026)](https://abbynews.com/2026/09/14/mla-hopefuls-spar-in-abbotsford-mission-byelection-debate/)

**OneBC** (basis: platform, confidence: medium)

- [OneBC priorities](https://1bc.ca/priorities)
- [BC Ballot: OneBC commitments](https://bcballot.ca/platforms/onebc/)


</details>

<details>
<summary><b>BC Ferries has cancelled sailings, long waits, rising demand and a dispute over where ships are built. What should come first?</b> (Regional: Vancouver Island and the Coast, <code>q_local_island_coast_ferries</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [BC NDP: locals first with new ferry reservation pilot (Oct 10, 2026)](https://www.bcndp.ca/releases/bc-ndp-would-put-locals-first-new-ferry-reservation-pilot)
- [Victoria Buzz: what the major parties are promising for BC Ferries (Oct 11, 2026)](https://victoriabuzz.com/2026/10/heres-what-bcs-major-political-parties-are-promising-for-bc-ferries-ahead-of-the-election/)
- [Nanaimo News Bulletin: Greens release transportation plans, note on Chinese-built vessels (Oct 9, 2026)](https://nanaimobulletin.com/2026/10/09/b-c-greens-release-transportation-plans-includes-free-transit-for-youth-seniors/)

**BC Conservatives** (basis: platform, confidence: high)

- [Conservative Party of BC: Conservatives will fix BC Ferries (Oct 11, 2026)](https://conservativebc.ca/conservatives-will-fix-bc-ferries/)
- [Victoria Buzz: what the major parties are promising for BC Ferries (Oct 11, 2026)](https://victoriabuzz.com/2026/10/heres-what-bcs-major-political-parties-are-promising-for-bc-ferries-ahead-of-the-election/)

**BC Greens** (basis: platform, confidence: high)

- [BC Greens: funding for fast, frequent transit and province-wide passenger rail (Oct 9, 2026)](https://bcgreens.ca/bc-greens-commit-to-funding-for-fast-frequent-transit-pledge-to-fight-for-province-wide-passenger-rail/)
- [Parksville Qualicum Beach News: Lowan launches Greens' economic vision (Oct 7, 2026)](https://pqbnews.com/2026/10/07/lowan-launches-greens-economic-vision-for-b-c/)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, Economy and Affordability)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [Victoria Buzz: what the major parties are promising for BC Ferries (Oct 11, 2026)](https://victoriabuzz.com/2026/10/heres-what-bcs-major-political-parties-are-promising-for-bc-ferries-ahead-of-the-election/)

**OneBC** (no published position)

- [OneBC priorities](https://1bc.ca/priorities)
- [BC Ballot: OneBC commitments (no transportation item)](https://bcballot.ca/platforms/onebc/)


</details>

<details>
<summary><b>The Crofton pulp mill closed after the premier refused old-growth logs to supply it. What should be done with Island forests?</b> (Regional: Vancouver Island and the Coast, <code>q_local_island_coast_oldgrowth</code>)</summary>

**BC NDP** (basis: both, confidence: medium)

- [BC NDP: Eby's plan protects natural spaces, funds climate action (Oct 10, 2026)](https://www.bcndp.ca/releases/ebys-plan-protects-bcs-natural-spaces-funds-climate-action)
- [National Newswatch: Eby says no to harvesting old growth to extend life of pulp mill (Dec 3, 2025)](https://nationalnewswatch.com/2025/12/03/eby-says-no-to-harvesting-old-growth-to-extend-life-of-b-c-pulp-mill)
- [Tree Frog Creative: Minister Parmar outlines working forest vision (2026)](https://treefrogcreative.ca/minister-parmar-outlines-working-forest-vision-commits-to-structural-shift-as-sector-presses-for-fibre-flow/)
- [BC Gov: Working Forest Landscape Model](https://www2.gov.bc.ca/gov/content/industry/natural-resource-use/working-forest-landscape-model)

**BC Conservatives** (no published position)

- [Conservative Party of BC: Supercharge British Columbia's economy (Oct 7, 2026)](https://conservativebc.ca/supercharge-british-columbias-economy/)
- [Westk News: Conservative forestry critic on the 100 Mile House closure (Nov 7, 2025)](https://westknews.com/2025/11/07/conservative-forestry-critic-calls-closure-of-100-mile-west-fraser-mill-devastating/)
- [Armchair Mayor: Stamer op-ed on 45 million cubic metres (May 27, 2025)](https://armchairmayor.ca/2025/05/27/stamer-how-long-will-it-take-to-get-45-million-cubic-metres-of-viable-fibre/)

**BC Greens** (basis: platform, confidence: high)

- [BC Greens: plan to reform the forestry sector (Oct 4, 2026)](https://bcgreens.ca/announce-plan-to-reform-forestry-sector-protecting-forests-jobs-and-communities/)
- [Parksville Qualicum Beach News: Lowan launches Greens' economic vision (Oct 7, 2026)](https://pqbnews.com/2026/10/07/lowan-launches-greens-economic-vision-for-b-c/)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, Economy and Affordability)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (basis: platform, confidence: medium)

- [OneBC priorities](https://1bc.ca/priorities)
- [BC Ballot: OneBC commitments](https://bcballot.ca/platforms/onebc/)


</details>

<details>
<summary><b>Nanaimo's hospital tower and cardiac lab are only in planning, and a Campbell River care home was paused. What should come first?</b> (Regional: Vancouver Island and the Coast, <code>q_local_island_coast_seniors</code>)</summary>

**BC NDP** (basis: both, confidence: medium)

- [Times Colonist: NDP promises $90M to redevelop Oak Bay Lodge site, free shingles vaccines (Oct 6, 2026)](https://www.timescolonist.com/2026-bc-votes/bc-ndp-promises-90m-to-redevelop-oak-bay-lodge-site-free-shingles-vaccines-12859483)
- [Nanaimo News Bulletin: acute care tower and cardiac services advancing at Nanaimo hospital (Feb 24, 2026)](https://nanaimobulletin.com/2026/02/24/acute-care-tower-and-the-expansion-of-cardiac-services-advancing-at-nanaimo-hospital/)
- [Nanaimo NewsNOW: consultant sought to advance Nanaimo hospital tower, cath lab (July 28, 2026)](https://nanaimonewsnow.com/2026/07/28/consultant-sought-to-advance-nanaimo-hospital-patient-tower-cath-lab/)
- [Nanaimo News Bulletin: NDP promises faster health care with new diagnostic equipment (Oct 6, 2026)](https://nanaimobulletin.com/2026/10/06/b-c-ndp-promises-faster-health-care-with-new-diagnostic-equipment/)

**BC Conservatives** (basis: platform, confidence: medium)

- [Conservative Party of BC: build the long-term care beds the NDP shelved (Oct 9, 2026)](https://conservativebc.ca/conservatives-will-build-the-long-term-care-beds-the-ndp-shelved/)
- [Nanaimo News Bulletin: Doerkson pledges $50M fund for ER closures (Oct 5, 2026)](https://nanaimobulletin.com/2026/10/05/lorne-doerkson-pledges-to-create-50m-fund-to-address-emergency-room-closures/)
- [CHEK News: all Vancouver Island candidates for the 2026 election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)

**BC Greens** (basis: platform, confidence: medium)

- [BC Greens: Our Plan](https://bcgreens.ca/our-plan/)
- [BC Greens: Healthcare Policy Brief 2026 (PDF, Oct 6, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Healthcare-Policy-Brief-2026.pdf)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, Health Care)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (basis: inferred, confidence: low)

- [OneBC priorities](https://1bc.ca/priorities)
- [CBC: Dallas Brodie OneBC Q&A (Oct 3, 2026)](https://www.cbc.ca/news/canada/british-columbia/dallas-brodie-onebc-q-a-2026-election-9.7366117)


</details>

<details>
<summary><b>After the Bald Range fire near Summerland, where should the province put its main wildfire money and effort before next summer?</b> (Regional: Southern Interior, <code>q_local_interior_wildfire</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [BC NDP: new support for wildfire-impacted families, including the uninsured (Oct 2, 2026)](https://www.bcndp.ca/releases/bc-ndp-announces-new-support-wildfire-impacted-families-including-those-uninsured)
- [BC NDP: support for small businesses through the trade war (Oct 7, 2026)](https://www.bcndp.ca/releases/eby-support-small-businesses-through-trade-war)
- [UBCM: lack of funds drives changes to FireSmart program (Jan 2026)](https://www.ubcm.ca/about-ubcm/latest-news/lack-funds-drive-changes-firesmart-program)
- [BC Gov News: FireSmart funding, 2027 intake (release 2026FOR0046)](https://news.gov.bc.ca/releases/2026FOR0046-001061)

**BC Conservatives** (basis: platform, confidence: medium)

- [Conservative Party of BC: Fighting wildfires, protecting communities (Oct 2, 2026)](https://conservativebc.ca/fighting-wildfires-protecting-communities/)
- [AM 1150: Conservatives pledge $400M for water bombers (Oct 3, 2026)](https://www.am1150.ca/89964/news/elections/2026-bc-election/b-c-conservatives-pledge-400m-to-buy-water-bombers-in-wildfire-plan/)
- [Today in BC: Conservatives aim to increase wildfire protection (Oct 2, 2026)](https://todayinbc.com/2026/10/02/an-investment-b-c-has-to-make-conservatives-aim-to-increase-wildfire-protection/)
- [Global News: NDP and Conservative leaders campaign in the Okanagan (Oct 2, 2026)](https://globalnews.ca/news/12086166/bc-ndp-conservative-leaders-campaign-okanagan/)

**BC Greens** (basis: platform, confidence: medium)

- [BC Greens: Climate, LNG and Royalties Policy Brief 2026 (PDF, Oct 10, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Climate-LNG-and-Royalties-Policy-Brief-2026.pdf)
- [BC Greens: A New Economic Direction for British Columbia (PDF, Oct 7, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Economic-Vision.pdf)
- [BC Ballot: wildfire commitments by party](https://bcballot.ca/platforms/issues/wildfires/)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, Public Safety)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (no published position)

- [OneBC priorities](https://1bc.ca/priorities)
- [BC Ballot: wildfire commitments by party (no OneBC item)](https://bcballot.ca/platforms/issues/wildfires/)


</details>

<details>
<summary><b>Kelowna's council wants a regional involuntary care facility and its downtown consumption site closed. What should be done?</b> (Regional: Southern Interior, <code>q_local_interior_downtown</code>)</summary>

**BC NDP** (basis: both, confidence: medium)

- [Kelowna Capital News: Eby announces grocery price guard, addresses social disorder in Kelowna (Oct 2, 2026)](https://kelownacapnews.com/2026/10/02/eby-announces-b-c-grocery-price-guard-social-disorder-during-kelowna-visit/)
- [Kelowna Capital News: council pushes to close downtown supervised consumption site (Sept 1, 2026)](https://kelownacapnews.com/2026/09/01/kelowna-council-pushing-to-close-downtown-supervised-consumption-site/)
- [BC Ballot: drugs and addiction (record and commitments)](https://bcballot.ca/platforms/issues/drugs-and-addiction/)

**BC Conservatives** (basis: platform, confidence: medium)

- [Conservative Party of BC: Safe Streets for BC (Oct 6, 2026)](https://conservativebc.ca/safe-streets-for-bc/)
- [Global News: NDP and Conservative leaders campaign in the Okanagan (Oct 2, 2026)](https://globalnews.ca/news/12086166/bc-ndp-conservative-leaders-campaign-okanagan/)

**BC Greens** (basis: platform, confidence: medium)

- [BC Greens: Toxic Drugs Policy Brief 2026 (PDF, Oct 2, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Toxic-Drugs-Policy-Brief-2026-1.pdf)
- [BC Ballot: drugs and addiction commitments](https://bcballot.ca/platforms/issues/drugs-and-addiction/)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 15-20, 26-27)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (basis: platform, confidence: medium)

- [OneBC priorities](https://1bc.ca/priorities)
- [OneBC on X: street patrols and Riverview (Sept 29, 2026)](https://x.com/One_BCHQ/status/2105036887736058203)


</details>

<details>
<summary><b>Budget 2026 paused seven care home builds including Kelowna's, and a private 250-bed Vernon project was pulled. What now?</b> (Regional: Southern Interior, <code>q_local_interior_ltc</code>)</summary>

**BC NDP** (basis: both, confidence: medium)

- [Kelowna Capital News: Kelowna among seven long-term care projects delayed by budget (Feb 17, 2026)](https://kelownacapnews.com/2026/02/17/kelowna-among-7-scheduled-long-term-care-projects-delayed-by-b-c-budget/)
- [My South Okanagan Now: NDP plans to resume seven paused long-term care projects (Oct 5, 2026)](https://www.mysouthokanagannow.com/8300/news/elections/2026-bc-election/b-c-ndp-plans-to-resume-seven-paused-long-term-care-projects-if-re-elected/)

**BC Conservatives** (basis: platform, confidence: medium)

- [Conservative Party of BC: build the long-term care beds the NDP shelved (Oct 9, 2026)](https://conservativebc.ca/conservatives-will-build-the-long-term-care-beds-the-ndp-shelved/)

**BC Greens** (basis: platform, confidence: medium)

- [BC Greens: Healthcare Policy Brief 2026 (PDF, Oct 6, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Healthcare-Policy-Brief-2026.pdf)
- [BC Ballot: health care commitments by party](https://bcballot.ca/platforms/issues/health-care/)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, Health Care)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (basis: inferred, confidence: low)

- [OneBC priorities](https://1bc.ca/priorities)
- [BC Ballot: OneBC commitments](https://bcballot.ca/platforms/onebc/)


</details>

<details>
<summary><b>Northern mills, including Prince George's Northwood pulp mill, are closing over fibre supply. How should the harvest be set?</b> (Regional: North and Cariboo, <code>q_local_north_forestry</code>)</summary>

**BC NDP** (basis: both, confidence: medium)

- [BC Gov: Working Forest Landscape Model](https://www2.gov.bc.ca/gov/content/industry/natural-resource-use/working-forest-landscape-model)
- [BC NDP: Eby's plan protects natural spaces, funds climate action (Oct 10, 2026)](https://www.bcndp.ca/releases/ebys-plan-protects-bcs-natural-spaces-funds-climate-action)
- [Chilliwack Progress: BC piloting landscape-level, zone-based forestry (Aug 27, 2026)](https://theprogress.com/2026/08/27/b-c-piloting-landscape-level-forestry-zone-based-management/)
- [CKPG: Canfor announces permanent closure of Northwood pulp mill (July 14, 2026)](https://ckpgtoday.ca/2026/07/14/canfor-announces-permanent-closure-of-northwood-pulp-mill/)

**BC Conservatives** (no published position)

- [Conservative Party of BC: Supercharge British Columbia's economy (Oct 7, 2026)](https://conservativebc.ca/supercharge-british-columbias-economy/)
- [Conservative Party of BC: plan hub (Forestry for the Future heading, no text)](https://conservativebc.ca/plan/)
- [Williams Lake Tribune: Doerkson on the 100 Mile House mill closure (Nov 15, 2025)](https://wltribune.com/2025/11/15/doerkson-west-frasers-permanent-mill-closure-in-100-mile-house-shocking/)
- [Westk News: Conservative forestry critic on the 100 Mile House closure (Nov 7, 2025)](https://westknews.com/2025/11/07/conservative-forestry-critic-calls-closure-of-100-mile-west-fraser-mill-devastating/)

**BC Greens** (basis: platform, confidence: high)

- [BC Greens: Forestry Policy Brief 2026 (PDF, Oct 4, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Forestry-Policy-Brief-2026.pdf)
- [BC Greens: plan to reform the forestry sector (Oct 4, 2026)](https://bcgreens.ca/announce-plan-to-reform-forestry-sector-protecting-forests-jobs-and-communities/)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, Economy and Affordability)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (basis: platform, confidence: medium)

- [OneBC priorities](https://1bc.ca/priorities)
- [BC Ballot: OneBC commitments](https://bcballot.ca/platforms/onebc/)


</details>

<details>
<summary><b>Kitimat's gas export plant is doubling, and more plants, mines and a power line are proposed. What conditions should apply?</b> (Regional: North and Cariboo, <code>q_local_north_resources</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [BC NDP: Conservatives' LNG plan out of step with reality (Sept 28, 2026)](https://www.bcndp.ca/releases/bc-conservatives-lng-plan-out-step-reality)
- [BC NDP: double critical mineral exports, expand Port of Prince Rupert (Sept 28, 2026)](https://www.bcndp.ca/releases/eby-double-critical-mineral-exports-expand-port-prince-rupert)
- [BC NDP: Eby's plan protects natural spaces, funds climate action (Oct 10, 2026)](https://www.bcndp.ca/releases/ebys-plan-protects-bcs-natural-spaces-funds-climate-action)
- [BNN Bloomberg: LNG Canada to go ahead with Phase 2 (Sept 29, 2026)](https://www.bnnbloomberg.ca/business/company-news/2026/09/29/lng-canada-to-go-ahead-with-phase-2-expansion-project-in-kitimat-bc/)

**BC Conservatives** (basis: platform, confidence: high)

- [Conservative Party of BC: Make British Columbia an energy superpower (Sept 28, 2026)](https://conservativebc.ca/make-british-columbia-an-energy-superpower/)
- [Conservative Party of BC: BC Energy Superpower plan (PDF)](https://conservativebc.ca/wp-content/uploads/2026/09/BC-ENERGY-SUPERPOWER_5_compressed.pdf)
- [Conservative Party of BC: welcome LNG Canada Phase 2 (Sept 29, 2026)](https://conservativebc.ca/bc-conservatives-welcome-lng-canada-phase-2-we-will-treat-energy-as-an-urgent-mission/)

**BC Greens** (basis: platform, confidence: high)

- [BC Greens: Climate, LNG and Royalties Policy Brief 2026 (PDF, Oct 10, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Climate-LNG-and-Royalties-Policy-Brief-2026.pdf)
- [BC Greens: statement from Emily Lowan on LNG Canada Phase 2 (Sept 29, 2026)](https://bcgreens.ca/statement-from-emily-lowan-on-lng-canada-phase-2/)
- [BC Greens: A New Economic Direction for British Columbia (PDF, Oct 7, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Economic-Vision.pdf)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, Economy and Affordability)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (basis: platform, confidence: medium)

- [OneBC priorities](https://1bc.ca/priorities)
- [BC Ballot: OneBC commitments (Sept 26 post)](https://bcballot.ca/platforms/onebc/)


</details>

<details>
<summary><b>Emergency rooms in Fort St. James, Mackenzie, Hudson's Hope and 100 Mile House keep closing for lack of staff. What comes first?</b> (Regional: North and Cariboo, <code>q_local_north_er</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [CFJC Today: NDP talks health care, tuition discounts for rural work (Oct 9, 2026)](https://cfjctoday.com/2026/10/09/b-c-ndp-talks-health-care-on-the-campaign-promises-tuition-discounts-for-rural-work/)
- [The Northern View: Eby vows to fast-track international medical grads, bring more doctors to rural areas (Oct 9, 2026)](https://thenorthernview.com/2026/10/09/b-c-election-eby-vows-to-fast-track-intl-medical-grads-bring-more-docs-to-rural-areas/)
- [BC Gov: health capital projects (updated Sept 21, 2026)](https://www2.gov.bc.ca/gov/content/health/accessing-health-care/capital-projects)
- [Energeticcity: Northern Health clocks more than 100 hours of closures in March (Apr 10, 2026)](https://energeticcity.ca/2026/04/10/northern-health-clocks-in-more-than-100-hours-in-closures-in-march/)

**BC Conservatives** (basis: platform, confidence: medium)

- [Conservative Party of BC: Keep emergency rooms open (Oct 5, 2026)](https://conservativebc.ca/keep-emergency-rooms-open/)
- [100 Mile Free Press: Doerkson pledges $50M fund for ER closures (Oct 5, 2026)](https://100milefreepress.net/2026/10/05/lorne-doerkson-pledges-to-create-50m-fund-to-address-emergency-room-closures/)
- [CJDC TV: after 21 ER diversions in 56 days in Hudson's Hope, MLA calls for Northern Health to be dismantled (Apr 14, 2026)](https://www.cjdctv.com/news/article/after-21-er-diversions-in-56-days-in-hudsons-hope-mla-calls-for-northern-health-to-be-dismantled/)

**BC Greens** (basis: platform, confidence: medium)

- [BC Greens: community health centres in every riding, support for health workers (Oct 6, 2026)](https://bcgreens.ca/pledge-funding-for-community-health-centres-in-every-riding-support-for-healthcare-workers/)
- [BC Greens: Healthcare Policy Brief 2026 (PDF, Oct 6, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Healthcare-Policy-Brief-2026.pdf)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, Health Care)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (basis: platform, confidence: medium)

- [OneBC priorities](https://1bc.ca/priorities)
- [BC Ballot: OneBC commitments](https://bcballot.ca/platforms/onebc/)


</details>

### Parties: leaders, records and summaries

<details>
<summary>Sources for each party's summary and 2016 to 2026 record</summary>

**BC New Democratic Party**

- [BC NDP releases (party)](https://www.bcndp.ca/releases)
- [BC Budget 2026 and Fiscal Plan](https://www.bcbudget.gov.bc.ca/2026/pdf/2026_Budget_and_Fiscal_Plan.pdf)
- [BC Ballot tracker, BC NDP commitments](https://bcballot.ca/platforms/bc-ndp/)
- [Votes and Proceedings, May 28, 2025 (Bills 7, 14, 15)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v250528.htm)

**Conservative Party of British Columbia**

- [Conservative Party of BC plan hub](https://conservativebc.ca/plan/)
- [BC Ballot tracker, Conservative commitments](https://bcballot.ca/platforms/conservative-party/)
- [Votes and Proceedings, February 26, 2026 (Human Rights Code Repeal Act first reading)](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260226.htm)
- [CP24: Findlay resigns as BC Conservative leader](https://www.cp24.com/politics/2026/09/20/kerry-lynne-findlay-resigns-as-bc-conservative-leader/)
- [Global News: who are the BC party leaders (Doerkson interim, constitution bars interim leader from permanent post)](https://globalnews.ca/news/12068973/who-are-bc-party-leaders-2026-election/)

**BC Green Party**

- [BC Greens: Our Plan](https://bcgreens.ca/our-plan/)
- [BC Greens Fair Share Act release](https://bcgreens.ca/fair-share-act-would-unlock-22-2b-for-childcare-transit-and-housing/)
- [BC Greens Toxic Drugs Policy Brief 2026 (PDF)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Toxic-Drugs-Policy-Brief-2026-1.pdf)
- [CP24: Greens will not renew accord with NDP](https://www.cp24.com/news/canada/2026/02/09/bc-greens-wont-renew-accord-with-ndp-citing-stalled-undelivered-promises/)

**CentreBC**

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, Oct 10, 2026)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [CentreBC: platform landing page](https://www.centrebc.ca/platform/)
- [CentreBC news](https://www.centrebc.ca/news/)
- [CentreBC: Reconciliation, Certainty and Prosperity statement (Aug 13, 2026, superseded)](https://www.centrebc.ca/news/statement-reconciliation-certainty-and-prosperity/)
- [Surrey Now-Leader: Sturko promises manufacturing boost (Oct 9, 2026)](https://surreynowleader.com/2026/10/09/centrebc-leader-promisesmanufacturing-boost)

**OneBC**

- [OneBC priorities (party)](https://1bc.ca/priorities)
- [Wikipedia: OneBC (secondary)](https://en.wikipedia.org/wiki/OneBC_(political_party))
- [CTV: OneBC will not run against eight Conservative candidates](https://www.ctvnews.ca/vancouver/article/onebc-pledges-not-to-run-against-eight-principled-bc-conservative-candidates/)
- [Votes and Proceedings, October 29, 2025 (Property Rights Protection Act)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251029.htm)


</details>

### Background, polling, election facts and context

<details>
<summary>89 general sources</summary>

- [Elections BC: ways to vote](https://elections.bc.ca/voting/ways-to-vote/)
- [Elections BC: who can vote](https://elections.bc.ca/voting/who-can-vote/)
- [Elections BC: voter ID](https://elections.bc.ca/2026-provincial-election/voter-id/)
- [Elections BC: candidate nomination report (PDF)](https://www.elections.bc.ca/docs/fin/GE-2026-10-24-Candidate-Website-Report.PDF)
- [BC Budget 2026 and Fiscal Plan](https://www.bcbudget.gov.bc.ca/2026/pdf/2026_Budget_and_Fiscal_Plan.pdf)
- [BC Government: Budget 2026 tax changes](https://www2.gov.bc.ca/budgettaxchanges)
- [BC Government: First Quarterly Report 2026-27](https://news.gov.bc.ca/releases/2026FIN0031-001066)
- [Moody's rating action, March 2026](https://www2.gov.bc.ca/assets/gov/british-columbians-our-governments/government-finances/debt-management/moodys-ratings-march-2026.pdf)
- [BC Laws: Declaration on the Rights of Indigenous Peoples Act](https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/19044)
- [Blakes: Court of Appeal Gitxaala decision](https://www.blakes.com/insights/b-c-court-of-appeal-rules-previous-free-entry-mineral-tenure-regime-inconsistent-with-undrip/)
- [BLG: Aboriginal title litigation developments (June 2026)](https://www.blg.com/en/insights/2026/06/recent-developments-in-aboriginal-title-litigation)
- [The Narwhal: DRIPA explainer](https://thenarwhal.ca/bc-declaration-act-explainer/)
- [The Narwhal: DRIPA in the 2026 election](https://thenarwhal.ca/bc-election-2026-dripa/)
- [The Tyee: BC backs off DRIPA amendments](https://thetyee.ca/News/2026/04/14/BC-Backs-Off-DRIPA-Amendments/)
- [FNLC and Premier joint statement](https://www.fnlc.ca/premiers-first-nations-leadership-council-statement-about-dripa/)
- [Angus Reid: BC election polling and DRIPA opinion](https://angusreid.org/85168-2/)
- [Ipsos: top issues for British Columbians](https://www.ipsos.com/en-ca/top-issues-british-columbians)
- [Votes and Proceedings index (lims.leg.bc.ca)](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260305.htm)
- [Votes and Proceedings, November 26, 2019](https://lims.leg.bc.ca/pdms/ldp/41st4th/votes/v191126.htm)
- [Votes and Proceedings, November 22, 2018](https://lims.leg.bc.ca/pdms/ldp/41st3rd/votes/v181122.htm)
- [Votes and Proceedings, October 25, 2023](https://lims.leg.bc.ca/pdms/ldp/42nd4th/votes/v231025.htm)
- [Votes and Proceedings, November 29, 2023](https://lims.leg.bc.ca/pdms/ldp/42nd4th/votes/v231129.htm)
- [Votes and Proceedings, May 28, 2025](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v250528.htm)
- [Votes and Proceedings, October 29, 2025](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251029.htm)
- [Votes and Proceedings, December 2, 2025](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251202.htm)
- [Votes and Proceedings, February 19, 2026](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260219.htm)
- [Votes and Proceedings, February 26, 2026](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260226.htm)
- [CBC via Yahoo: where BC parties stand on SOGI 123](https://ca.news.yahoo.com/where-b-c-provincial-political-130000614.html)
- [SOGI 123 (ARC Foundation)](https://www.sogieducation.org/)
- [Castanet: province ends ARC Foundation funding](https://www.castanetkamloops.net/news/Kamloops/627143/SD73-schools-wont-feel-change-as-province-ends-funding-for-ARC-Foundation-superintendent)
- [National Newswatch / CP: decriminalization pilot ends](https://nationalnewswatch.com/2026/01/14/b-c-ending-its-3-year-drug-decriminalization-pilot-project)
- [The Free Press: 1,826 toxic drug deaths in 2025](https://thefreepress.ca/2026/02/20/1826-people-died-from-toxic-drugs-in-b-c-in-2025-a-21-decrease-from-2024/)
- [BC Government: May 2026 toxic drug deaths release](https://archive.news.gov.bc.ca/releases/news_releases_2024-2028/2026PSSG0042-000540.htm)
- [UBCM: decriminalization chronology](https://www.ubcm.ca/node/106160)
- [BCCSU: witnessed dosing](https://www.bccsu.ca/blog/news/b-c-to-require-most-drug-users-receiving-safe-supply-to-have-their-doses-witnessed/)
- [Global News: involuntary care provisions unconstitutional](https://globalnews.ca/news/12005744/sections-bc-involuntary-care-rules-found-unconstitutional/)
- [BC Greens Toxic Drugs Policy Brief 2026](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Toxic-Drugs-Policy-Brief-2026-1.pdf)
- [Surrey Police Service: extortion statistics](https://www.surreypolice.ca/extortions)
- [StatCan Daily: Crime Severity Index 2025](https://www150.statcan.gc.ca/n1/daily-quotidien/260722/cg-a003-eng.htm)
- [Conservative Party of BC: plan hub](https://conservativebc.ca/plan/)
- [Conservative Party of BC: Safe Streets for BC](https://conservativebc.ca/safe-streets-for-bc/)
- [Conservative Party of BC: $1,000 tax cut](https://conservativebc.ca/conservatives-will-cut-your-taxes-by-1000/)
- [Conservative Party of BC: BC Energy Superpower Plan](https://conservativebc.ca/make-british-columbia-an-energy-superpower/)
- [Conservative Party of BC: Insurance plan](https://conservativebc.ca/plan/insurance/)
- [Global News: Conservative plan to end no-fault (leaked letter)](https://globalnews.ca/news/12090331/bc-conservatives-plan-no-fault-insurance-repeal/)
- [Global News: 2024 Conservative platform](https://globalnews.ca/news/10812384/affordability-safety-scrapping-carbon-price-bc-conservatives-full-platform)
- [CP24: Findlay resigns](https://www.cp24.com/politics/2026/09/20/kerry-lynne-findlay-resigns-as-bc-conservative-leader/)
- [BC NDP releases](https://www.bcndp.ca/releases)
- [BC NDP: top-bracket tax proposal](https://www.bcndp.ca/releases/build-bc-strong-eby-will-ask-wealthy-pitch-bit-more)
- [BC NDP: speculation tax and Unsold Condo Tax](https://www.bcndp.ca/releases/eby-turn-more-empty-condos-homes-people-can-afford)
- [BC NDP: wait times and diagnostics](https://www.bcndp.ca/releases/getting-care-sooner-eby-will-cut-wait-times-add-new-diagnostic-equipment)
- [BC NDP: gas price plan](https://www.bcndp.ca/releases/ebys-plan-will-cut-gas-prices-30-cents-litre-crack-down-gouging)
- [BC NDP: ICBC rate freeze](https://www.bcndp.ca/releases/eby-freeze-car-insurance-rates-another-three-years)
- [Global News: BC pauses $1,000 rebate](https://globalnews.ca/news/11017886/bc-pauses-tax-rebate-donald-trump-tariffs/amp)
- [BC Greens: Our Plan](https://bcgreens.ca/our-plan/)
- [BC Greens: Fair Share Act](https://bcgreens.ca/fair-share-act-would-unlock-22-2b-for-childcare-transit-and-housing/)
- [BC Greens: Economic Vision (PDF)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Economic-Vision.pdf)
- [BC Greens: child care plan](https://bcgreens.ca/announce-plan-to-lift-the-freeze-on-10-a-day-daycare-with-universal-free-child-care-by-2031-alongside-new-candidate-for-victoria-swan-lake/)
- [CP24: Greens will not renew accord](https://www.cp24.com/news/canada/2026/02/09/bc-greens-wont-renew-accord-with-ndp-citing-stalled-undelivered-promises/)
- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, Oct 10, 2026)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [CentreBC: news](https://www.centrebc.ca/news/)
- [CentreBC: reconciliation statement](https://www.centrebc.ca/news/statement-reconciliation-certainty-and-prosperity/)
- [CentreBC: anti-extortion plan](https://www.centrebc.ca/news/news-release/centrebc-unveils-3-step-plan-to-crush-transnational-extortion-terrorizing-surrey/)
- [CentreBC: Budget 2026 response](https://www.centrebc.ca/news/budget-2026-managing-decline-is-not-leadership/)
- [CentreBC: Our Vision](https://www.centrebc.ca/vision/)
- [Surrey Now-Leader: Sturko manufacturing promise (Oct 9, 2026)](https://surreynowleader.com/2026/10/09/centrebc-leader-promisesmanufacturing-boost)
- [Penticton Western News: Sturko sole CentreBC incumbent](https://pentictonwesternnews.com/2026/09/22/surreys-elenore-sturko-is-the-sole-incumbent-mla-for-centrebc-ahead-of-election/)
- [OneBC priorities](https://1bc.ca/priorities)
- [Wikipedia: OneBC (secondary)](https://en.wikipedia.org/wiki/OneBC_(political_party))
- [Wikipedia: 2026 BC general election (secondary)](https://en.wikipedia.org/wiki/2026_British_Columbia_general_election)
- [BC Ballot: platform comparison](https://bcballot.ca/platforms/)
- [The Tyee: family doctor crisis](https://thetyee.ca/News/2026/05/31/BC-Family-Doctor-Crisis-Gets-Even-Worse/)
- [The Tyee: BC admits 2030 climate goal out of reach](https://thetyee.ca/News/2025/05/01/BC-Admits-Climate-Goals/)
- [CBC: consumer carbon tax ends](https://www.cbc.ca/lite/story/1.7493181)
- [Global News: $10-a-day program paused](https://globalnews.ca/news/11673463/10-a-day-daycare-program-paused/)
- [Global News: Surrey schools and the NDP record](https://globalnews.ca/news/11350841/surrey-schools-ndp-building)
- [CMHC Rental Market Report](https://www.cmhc-schl.gc.ca/professionals/housing-markets-data-and-research/market-reports/rental-market-reports-major-centres)
- [Global News: Metro Vancouver 2025 homeless count](https://globalnews.ca/news/11311816/metro-vancouver-2025-homeless-count)
- [Surrey-Langley SkyTrain status report (April 2026)](https://surreylangleyskytrain.gov.bc.ca/app/uploads/sites/938/2026/06/SLS_Monthly-Status-Report_April_2026.pdf)
- [Daily Hive: Eby rules out vehicle levy](https://dailyhive.com/vancouver/bc-ndp-david-eby-translink-vehicle-levy)
- [Indo-Canadian Voice: Doerkson on the Surrey hospital](https://voiceonline.com/doerkson-has-no-answer-on-surrey-hospital-more-than-halfway-built-bc-ndp/)
- [338Canada: Surrey-Fleetwood](https://338canada.com/bc/1070e.htm)
- [City of Surrey: Fleetwood neighbourhood profile](https://www.surrey.ca/sites/default/files/media/documents/Neighbourhood-Profile-Fleetwood.pdf)
- [BC Ballot: Jagrup Brar](https://bcballot.ca/mlas/jagrup-brar/)
- [BC NDP logos page](https://www.bcndp.ca/logos-photos)
- [Wikimedia Commons: Conservative Party of BC logo](https://upload.wikimedia.org/wikipedia/commons/b/b9/Conservative_Party_of_BC_Logo.png)
- [Wikimedia Commons: BC Greens logo](https://upload.wikimedia.org/wikipedia/commons/6/63/BCGreenslogo.svg)
- [CentreBC logo (party site)](https://www.centrebc.ca/wp-content/uploads/2025/07/CentreBC-logo2026.webp)
- [Wikimedia Commons: OneBC logo](https://upload.wikimedia.org/wikipedia/commons/1/18/OneBC_Party_Logo_%282025-present%29.svg)

</details>

### Ridings: 2024 results and candidates

Candidate lists come from Elections BC's official 2026 candidate list. Bios and 2024 results link to their sources.

<details>
<summary>Fraser Valley (10 ridings)</summary>

**Abbotsford South** (`ABS`)

- 2024 result: <Elections BC Statement of Votes 2024 (https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf), figures as reproduced by Wikipedia: https://en.wikipedia.org/wiki/Template:2024_British_Columbia_general_election/Abbotsford_South>
- Leah Ballantyne (BC NDP): [BC NDP candidate profiles (bcndp.ca team page)](https://www.bcndp.ca/team), [BC NDP release, Oct 3, 2026](https://www.bcndp.ca/releases/more-bc-ndp-candidates-ready-fight-their-communities)
- Bruce Banman (BC Conservatives): [BC Conservatives candidate page: Banman](https://conservativebc.ca/candidate/bruce-banman/), [Wikipedia: Bruce Banman](https://en.wikipedia.org/wiki/Bruce_Banman)
- Robin Roy (OneBC): [OneBC candidate page: Robin Roy](https://1bc.ca/candidates/rroy), [Elections BC candidate list, 2026 general election](https://elections.bc.ca/2026-provincial-election/candidate-list/)

**Abbotsford West** (`ABW`)

- 2024 result: <Elections BC Statement of Votes 2024 (https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf), figures as reproduced by Wikipedia: https://en.wikipedia.org/wiki/Template:2024_British_Columbia_general_election/Abbotsford_West>
- Gurpreet Chahal (CentreBC): [CentreBC candidate page: Gurpreet Singh Chahal](https://www.centrebc.ca/candidates/gurpreet-singh-chahal/), [Elections BC candidate list, 2026 general election](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Jules Côté (BC NDP): [BC NDP candidate profiles (bcndp.ca team page)](https://www.bcndp.ca/team), [UFV Cascade, 2025 federal campaign profile](https://ufvcascade.ca/jules-cote-for-ndp-mp/)
- Korky Neufeld (BC Conservatives): [BC Conservatives candidate page: Neufeld](https://conservativebc.ca/candidate/korky-neufeld/), [Wikipedia: Korky Neufeld](https://en.wikipedia.org/wiki/Korky_Neufeld)

**Abbotsford-Mission** (`ABM`)

- 2024 result: <Elections BC Statement of Votes 2024 (https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf), figures as reproduced by Wikipedia: https://en.wikipedia.org/wiki/Template:2024_British_Columbia_general_election/Abbotsford-Mission>
- Pam Alexis (BC NDP): [BC NDP candidate profiles (bcndp.ca team page)](https://www.bcndp.ca/team), [BC NDP release, Aug 29, 2026](https://www.bcndp.ca/releases/pam-alexis-run-bc-ndp-candidate-abbotsford-misson-election)
- Virender Dass (OneBC): [OneBC candidate page: Virender Dass](https://1bc.ca/candidates/vdass), [Elections BC candidate list, 2026 general election](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Lakhwinder Jhaj (CentreBC): [CentreBC candidate page: Lakhwinder Jhaj](https://www.centrebc.ca/candidates/lakhwinder-jhaj/), [Elections BC candidate list, 2026 general election](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Darryl Kropp (BC Conservatives): [BC Conservatives candidate page: Kropp](https://conservativebc.ca/candidate/darryl-kropp/), [Abbotsford News, Oct 5, 2026](https://abbynews.com/2026/10/05/19-provincial-election-candidates-finalized-for-5-abbotsford-ridings/)
- Jeff Monds (BC Libertarian): [Fraser Valley Today, Oct 4, 2026](https://fraservalleytoday.ca/2026/10/04/ndp-libertarians-onebc-field-candidates-for-langley-and-abbotsford-ridings/), [Elections BC candidate list, 2026 general election](https://elections.bc.ca/2026-provincial-election/candidate-list/)

**Chilliwack North** (`CHN`)

- 2024 result: <Elections BC Statement of Votes 2024 (https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf), figures as reproduced by Wikipedia: https://en.wikipedia.org/wiki/Template:2024_British_Columbia_general_election/Chilliwack_North>
- Dan Grice (CentreBC): [CentreBC candidate page: Dan Grice](https://www.centrebc.ca/candidates/dan-grice/), [Elections BC candidate list, 2026 general election](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Heather Maahs (BC Conservatives): [BC Conservatives candidate page: Maahs](https://conservativebc.ca/candidate/heather-maahs/), [Wikipedia: Heather Maahs](https://en.wikipedia.org/wiki/Heather_Maahs)
- Adila Shaukat (BC NDP): [BC NDP candidate profiles (bcndp.ca team page)](https://www.bcndp.ca/team), [Chilliwack Progress, Oct 5, 2026](https://theprogress.com/2026/10/05/adila-shaukat-to-run-as-bc-ndp-candidate-in-chilliwack-north/)

**Chilliwack-Cultus Lake** (`CHC`)

- 2024 result: <Elections BC Statement of Votes 2024 (https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf), figures as reproduced by Wikipedia: https://en.wikipedia.org/wiki/Template:2024_British_Columbia_general_election/Chilliwack-Cultus_Lake>
- Kelli Paddon (BC NDP): [BC NDP candidate profiles (bcndp.ca team page)](https://www.bcndp.ca/team), [Chilliwack Progress, Oct 5, 2026](https://theprogress.com/2026/10/05/adila-shaukat-to-run-as-bc-ndp-candidate-in-chilliwack-north/)
- A'aliya Warbus (BC Conservatives): [BC Conservatives candidate page: Warbus](https://conservativebc.ca/candidate/aaliya-warbus/), [Agassiz-Harrison Observer, Sept 23, 2026](https://agassizharrisonobserver.com/2026/09/23/incumbent-mla-aaliya-warbus-returns-to-conservatives/)

**Langley-Abbotsford** (`LLA`)

- 2024 result: <Elections BC Statement of Votes 2024 (https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf), figures as reproduced by Wikipedia: https://en.wikipedia.org/wiki/Template:2024_British_Columbia_general_election/Langley-Abbotsford>
- Harman Bhangu (BC Conservatives): [BC Conservatives candidate page: Bhangu](https://conservativebc.ca/candidate/harman-bhangu/), [Wikipedia: Harman Bhangu](https://en.wikipedia.org/wiki/Harman_Bhangu)
- Shelly Jan (OneBC): [Fraser Valley Today, Oct 4, 2026](https://fraservalleytoday.ca/2026/10/04/ndp-libertarians-onebc-field-candidates-for-langley-and-abbotsford-ridings/), [BC Ballot (aggregator of the Elections BC list): Shelly Jan](https://bcballot.ca/ridings/langley-abbotsford/shelly-jan/)
- Erin Osborne (BC NDP): [BC NDP candidate profiles (bcndp.ca team page)](https://www.bcndp.ca/team), [BC Ballot (aggregator of the Elections BC list): Erin Osborne](https://bcballot.ca/ridings/langley-abbotsford/erin-osborne/)
- Melissa Snazell (BC Greens): [BC Greens candidate page: Snazell](https://bcgreens.ca/candidates-2026/melissa-snazell/), [Elections BC candidate list, 2026 general election](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Alex Joehl (BC Libertarian): [Fraser Valley Today, Oct 4, 2026](https://fraservalleytoday.ca/2026/10/04/ndp-libertarians-onebc-field-candidates-for-langley-and-abbotsford-ridings/), [BC Ballot (aggregator of the Elections BC list): Alex Joehl](https://bcballot.ca/ridings/langley-abbotsford/alex-joehl/)

**Langley-Walnut Grove** (`LWG`)

- 2024 result: <Elections BC Statement of Votes 2024 (https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf), figures as reproduced by Wikipedia: https://en.wikipedia.org/wiki/Template:2024_British_Columbia_general_election/Langley-Walnut_Grove>
- Holly Isaac (BC NDP): [BC NDP candidate profiles (bcndp.ca team page)](https://www.bcndp.ca/team), [Aldergrove Star, Oct 4, 2026](https://aldergrovestar.com/2026/10/04/ndp-name-candidate-in-langley-walnut-grove/)
- Sam Meyer (BC Greens): [BC Greens 2026 candidates list](https://bcgreens.ca/candidates-2026/), [Elections BC candidate list, 2026 general election](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Kyle Stevenson (CentreBC): [CentreBC candidate page: Kyle Stevenson](https://www.centrebc.ca/candidates/kyle-stevenson/), [Elections BC candidate list, 2026 general election](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Misty Van Popta (BC Conservatives): [BC Conservatives candidate page: Van Popta](https://conservativebc.ca/candidate/misty-van-popta/), [Wikipedia: Misty Van Popta](https://en.wikipedia.org/wiki/Misty_Van_Popta)

**Langley-Willowbrook** (`LWI`)

- 2024 result: <Elections BC Statement of Votes 2024 (https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf), figures as reproduced by Wikipedia: https://en.wikipedia.org/wiki/Template:2024_British_Columbia_general_election/Langley-Willowbrook>
- Shubham Joshi (OneBC): [OneBC candidate page: Shubham Joshi](https://1bc.ca/candidates/sjoshi), [Elections BC candidate list, 2026 general election](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Andrew Mercier (BC NDP): [BC NDP candidate profiles (bcndp.ca team page)](https://www.bcndp.ca/team), [Langley Advance Times, Oct 5, 2026](https://langleyadvancetimes.com/2026/10/05/candidates-named-in-all-langley-ridings/)
- Anisha Sandhu (BC Greens): [BC Greens candidate page: Sandhu](https://bcgreens.ca/candidates-2026/anisha-sandhu/), [Aldergrove Star, Oct 8, 2026](https://aldergrovestar.com/2026/10/08/late-candidate-added-to-langley-willowbrook-ballot/)
- Jody Toor (BC Conservatives): [BC Conservatives candidate page: Toor](https://conservativebc.ca/candidate/jody-toor/), [Wikipedia: Jody Toor](https://en.wikipedia.org/wiki/Jody_Toor)

**Maple Ridge East** (`MAE`)

- 2024 result: <Elections BC Statement of Votes 2024 (https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf), figures as reproduced by Wikipedia: https://en.wikipedia.org/wiki/Template:2024_British_Columbia_general_election/Maple_Ridge_East>
- Hudson Campbell (BC NDP): [BC NDP candidate profiles (bcndp.ca team page)](https://www.bcndp.ca/team), [Maple Ridge News, Sept 29, 2026](https://mapleridgenews.com/2026/09/29/school-board-trustee-running-for-ndp-in-maple-ridge-east/)
- Daniel Kite (BC Greens): [BC Greens candidate page: Kite](https://bcgreens.ca/candidates-2026/daniel-kite/), [Elections BC candidate list, 2026 general election](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Lawrence Mok (BC Conservatives): [BC Conservatives candidate page: Mok](https://conservativebc.ca/candidate/lawrence-mok/), [Wikipedia: Lawrence Mok](https://en.wikipedia.org/wiki/Lawrence_Mok)
- Chris Hatchwell (Independent): [Elections BC candidate list, 2026 general election](https://elections.bc.ca/2026-provincial-election/candidate-list/), [BC Ballot (aggregator of the Elections BC list): Chris Hatchwell](https://bcballot.ca/ridings/maple-ridge-east/chris-hatchwell/)

**Maple Ridge-Pitt Meadows** (`MAP`)

- 2024 result: <Elections BC Statement of Votes 2024 (https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf), figures as reproduced by Wikipedia: https://en.wikipedia.org/wiki/Template:2024_British_Columbia_general_election/Maple_Ridge-Pitt_Meadows>
- Lisa Beare (BC NDP): [BC NDP candidate profiles (bcndp.ca team page)](https://www.bcndp.ca/team), [Maple Ridge News, Oct 5, 2026](https://mapleridgenews.com/2026/10/05/four-candidates-running-in-both-maple-ridge-ridings-in-oct-24-provincial-election/)
- Susan Einarsson (OneBC): [OneBC candidate page: Susan Einarsson](https://1bc.ca/candidates/seinarsson), [Elections BC candidate list, 2026 general election](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Doug Morneau (BC Conservatives): [BC Conservatives candidate page: Morneau](https://conservativebc.ca/candidate/doug-morneau/), [Elections BC candidate list, 2026 general election](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Jordan Simmons (CentreBC): [CentreBC candidate page: Jordan Simmons](https://www.centrebc.ca/candidates/jordan-simmons/), [Elections BC candidate list, 2026 general election](https://elections.bc.ca/2026-provincial-election/candidate-list/)


</details>

<details>
<summary>Southern Interior (15 ridings)</summary>

**Boundary-Similkameen** (`BDS`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf (names and party labels cross-checked on Wikipedia riding pages)>
- Keith Pomeroy (OneBC): [Similkameen Spotlight candidate profile](https://similkameenspotlight.com/2026/10/10/meet-boundary-similkameen-mla-candidate-keith-pomeroy/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Roly Russell (BC NDP): [Similkameen Spotlight candidate profile](https://similkameenspotlight.com/2026/10/09/meet-boundary-similkameen-mla-candidate-roly-russell), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Donegal Wilson (BC Conservatives): [Wikipedia: Donegal Wilson](https://en.wikipedia.org/wiki/Donegal_Wilson), [Similkameen Spotlight: who is running](https://similkameenspotlight.com/2026/10/03/b-c-election-2026-heres-whos-running-in-boundary-similkameen/)

**Columbia River-Revelstoke** (`CLR`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf (names and party labels cross-checked on Wikipedia riding pages)>
- Andrea Dunlop (BC NDP): [Cranbrook Townsman](https://cranbrooktownsman.com/2026/09/28/dunlop-running-for-bc-ndp-in-columbia-river-revelstoke/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Scott McInnis (BC Conservatives): [Wikipedia: Scott McInnis (Canadian politician)](https://en.wikipedia.org/wiki/Scott_McInnis_(Canadian_politician)), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Rana Nelson (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/rana-nelson/), [Revelstoke Review](https://revelstokereview.com/2026/10/09/rana-nelson-running-for-columbia-river-revelstoke-with-bc-greens/)

**Fraser-Nicola** (`FRN`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf (names and party labels cross-checked on Wikipedia riding pages)>
- Jason Leboe (BC NDP): [BC NDP release: six more candidates](https://www.bcndp.ca/releases/bc-ndp-announces-six-more-candidates-stand-british-columbians), [Agassiz-Harrison Observer](https://agassizharrisonobserver.com/2026/10/02/b-c-ndp-taps-jason-leboe-as-fraser-nicola-candidate/)
- Tony Luck (BC Conservatives): [Wikipedia: Tony Luck](https://en.wikipedia.org/wiki/Tony_Luck), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Patrick Michell (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/chief-patrick-michell/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)

**Kamloops Centre** (`KAC`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf (names and party labels cross-checked on Wikipedia riding pages)>
- Annelise Beach (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/annelise-beach/), [CFJC](https://cfjctoday.com/2026/10/07/beach-to-carry-green-party-banner-in-kamloops-centre/)
- Rocky McAfee (OneBC): [CFJC](https://cfjctoday.com/2026/10/09/tattoo-artist-mcafee-hopes-to-represent-onebc-in-kamloops-centre/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Peter Milobar (BC Conservatives): [Wikipedia: Peter Milobar](https://en.wikipedia.org/wiki/Peter_Milobar), [CFJC: Milobar rejoins BC Conservatives](https://cfjctoday.com/2026/09/22/kamloops-centre-mla-milobar-rejoins-bc-conservatives/)
- Mike Wisla (BC NDP): [BC NDP release: Penticton-Summerland and Kamloops candidates](https://www.bcndp.ca/releases/bc-ndp-announces-candidates-penticton-summerland-and-kamloops), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Thaelo Proctor (Independent): [CFJC](https://cfjctoday.com/2026/10/06/contractor-proctor-enters-kamloops-centre-mla-race-as-independent/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)

**Kamloops-North Thompson** (`KAN`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf (names and party labels cross-checked on Wikipedia riding pages)>
- Kory Clark (BC NDP): [BC NDP release: Penticton-Summerland and Kamloops candidates](https://www.bcndp.ca/releases/bc-ndp-announces-candidates-penticton-summerland-and-kamloops), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Deborah Friesen (OneBC): [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Ward Stamer (BC Conservatives): [Wikipedia: Ward Stamer](https://en.wikipedia.org/wiki/Ward_Stamer), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)

**Kelowna Centre** (`KEC`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf (names and party labels cross-checked on Wikipedia riding pages)>
- Bill Desrosiers (OneBC): [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Kristina Loewen (BC Conservatives): [Wikipedia: Kristina Loewen](https://en.wikipedia.org/wiki/Kristina_Loewen), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Loyal Wooldridge (BC NDP): [Castanet Kamloops](https://www.castanetkamloops.net/news/Kelowna/632584/Outgoing-Kelowna-city-councillor-Loyal-Wooldridge-running-for-MLA), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)

**Kelowna-Lake Country-Coldstream** (`KLC`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf (names and party labels cross-checked on Wikipedia riding pages)>
- Binny Boparai (BC NDP): [BC NDP release: more candidates](https://www.bcndp.ca/releases/more-bc-ndp-candidates-ready-fight-their-communities), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Carter Mochinski (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/carter-mochinski/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Pavneet Singh (BC Conservatives): [Conservative Party of BC candidate page](https://conservativebc.ca/candidate/pavneet-singh/), [Castanet Vernon: North Okanagan candidate lists](https://www.castanet.net/news/Vernon/633376/Candidate-lists-finalized-across-three-North-Okanagan-ridings-ahead-of-Oct-24-vote)
- Alexandra Wright (OneBC): [Kelowna Capital News](https://kelownacapnews.com/2026/10/01/former-controversial-conservative-selected-by-onebc-for-kelowna-lake-country-coldstream-riding/), [Castanet Vernon: North Okanagan candidate lists](https://www.castanet.net/news/Vernon/633376/Candidate-lists-finalized-across-three-North-Okanagan-ridings-ahead-of-Oct-24-vote)

**Kelowna-Mission** (`KLM`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf (names and party labels cross-checked on Wikipedia riding pages)>
- Gavin Dew (BC Conservatives): [Wikipedia: Gavin Dew](https://en.wikipedia.org/wiki/Gavin_Dew), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Saoirse MacKinnon (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/saoirse-mackinnon/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Abraham Nordine (OneBC): [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Miriam Rycroft (BC NDP): [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)

**Kootenay Central** (`KOC`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf (names and party labels cross-checked on Wikipedia riding pages)>
- Brittny Anderson (BC NDP): [Wikipedia: Brittny Anderson](https://en.wikipedia.org/wiki/Brittny_Anderson), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Nicole Charlwood (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/nicole-charlwood/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Hunter Corrigal (OneBC): [My Nelson Now](https://www.mynelsonnow.com/80656/news/elections/2026-bc-election/onebcs-hunter-corrigal-makes-tax-relief-key-focus-in-kootenay-central-race/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Gordon Skulnec (BC Conservatives): [Nelson Star](https://nelsonstar.com/2026/10/05/bc-conservative-candidate-for-kootenay-central-is-gordon-skulnec/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)

**Kootenay-Monashee** (`KOM`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf (names and party labels cross-checked on Wikipedia riding pages)>
- Stephen Hill (OneBC): [My Kootenay Now](https://www.mykootenaynow.com/77165/news/elections/2026-bc-election/stephen-hill-running-for-onebc-in-kootenay-monashee/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Connie Larochelle (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/connie-larochelle/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Warren Mirko (BC Conservatives): [My Kootenay Now](https://www.mykootenaynow.com/77147/news/elections/2026-bc-election/warren-mirko-running-for-bc-conservatives-in-kootenay-monashee/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Steve Morissette (BC NDP): [Wikipedia: Steve Morissette](https://en.wikipedia.org/wiki/Steve_Morissette), [Trail Times](https://trailtimes.ca/2026/09/28/kootenay-monashee-candidate-confident-in-ndp-direction/)

**Kootenay-Rockies** (`KOR`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf (names and party labels cross-checked on Wikipedia riding pages)>
- Norma Blissett (BC NDP): [Cranbrook Townsman](https://cranbrooktownsman.com/2026/09/29/blissett-running-for-bc-ndp-in-kootenay-rockies/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Pete Davis (BC Conservatives): [Conservative Party of BC candidate page](https://conservativebc.ca/candidate/pete-davis/), [Wikipedia: Pete Davis (politician)](https://en.wikipedia.org/wiki/Pete_Davis_(politician))
- Keenan Dennehy (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/keenan-dennehy/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Paul Heywood (CentreBC): [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- AJ Wolfe (OneBC): [OneBC candidate page](https://1bc.ca/candidates/awolfe), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)

**Penticton-Summerland** (`PES`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf (names and party labels cross-checked on Wikipedia riding pages)>
- Bradley Sean Bartsch (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/bradley-bartsch/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Warren Hamm (OneBC): [OneBC candidate page](https://1bc.ca/candidates/whamm), [Castanet Kamloops](https://www.castanetkamloops.net/news/Penticton/631470/Unoffocial-political-party-OneBC-eyes-Penticton-Summerland-seat-by-naming-former-Conservative-would-be-leader)
- Tina Lee (BC NDP): [BC NDP release: Penticton-Summerland and Kamloops candidates](https://www.bcndp.ca/releases/bc-ndp-announces-candidates-penticton-summerland-and-kamloops), [Summerland Review](https://summerlandreview.com/2026/10/01/tina-lee-to-take-second-shot-at-penticton-summerland-for-bc-ndp/)
- Tracy St Claire (BC Conservatives): [Conservative Party of BC candidate page](https://conservativebc.ca/candidate/tracy-st-claire/), [Castanet](https://www.castanet.net/news/Penticton/632836/Tracy-St-Claire-announced-as-Conservative-candidate-for-Penticton-Summerland-riding)

**Salmon Arm-Shuswap** (`SHU`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf (names and party labels cross-checked on Wikipedia riding pages)>
- Gloria Morgan (BC NDP): [BC NDP release: more candidates](https://www.bcndp.ca/releases/more-bc-ndp-candidates-ready-fight-their-communities), [Castanet: Salmon Arm-Shuswap candidates](https://www.castanet.net/news/Salmon-Arm/633350/Four-challengers-up-against-B-C-Conservative-incumbent-in-provincial-vote)
- Barbara Presch (OneBC): [Salmon Arm Observer](https://saobserver.net/2026/10/05/five-running-to-represent-salmon-arm-shuswap-riding/), [Castanet: Salmon Arm-Shuswap candidates](https://www.castanet.net/news/Salmon-Arm/633350/Four-challengers-up-against-B-C-Conservative-incumbent-in-provincial-vote)
- Denise Reimer (CentreBC): [Castanet: Salmon Arm-Shuswap candidates](https://www.castanet.net/news/Salmon-Arm/633350/Four-challengers-up-against-B-C-Conservative-incumbent-in-provincial-vote), [Castanet Vernon: North Okanagan candidate lists](https://www.castanet.net/news/Vernon/633376/Candidate-lists-finalized-across-three-North-Okanagan-ridings-ahead-of-Oct-24-vote)
- Jed Wiebe (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/jed-wiebe/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- David L Williams (BC Conservatives): [Wikipedia: David Williams (Canadian politician)](https://en.wikipedia.org/wiki/David_Williams_(Canadian_politician)), [Castanet Vernon: North Okanagan candidate lists](https://www.castanet.net/news/Vernon/633376/Candidate-lists-finalized-across-three-North-Okanagan-ridings-ahead-of-Oct-24-vote)

**Vernon-Lumby** (`VRL`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf (names and party labels cross-checked on Wikipedia riding pages)>
- Kevin Acton (BC Conservatives): [Vernon Morning Star](https://vernonmorningstar.com/2026/09/27/kevin-acton-announced-as-conservative-candidate-for-vernon-lumby/), [Castanet Vernon: North Okanagan candidate lists](https://www.castanet.net/news/Vernon/633376/Candidate-lists-finalized-across-three-North-Okanagan-ridings-ahead-of-Oct-24-vote)
- Chantel Gibbs (OneBC): [Vernon Morning Star](https://vernonmorningstar.com/2026/09/28/onebc-nominates-vernon-woman-for-b-c-vote/), [Castanet Vernon: North Okanagan candidate lists](https://www.castanet.net/news/Vernon/633376/Candidate-lists-finalized-across-three-North-Okanagan-ridings-ahead-of-Oct-24-vote)
- Harwinder Sandhu (BC NDP): [Wikipedia: Harwinder Sandhu](https://en.wikipedia.org/wiki/Harwinder_Sandhu), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Blair Visscher (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/blair-visscher/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)

**West Kelowna-Peachland** (`WKP`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf (names and party labels cross-checked on Wikipedia riding pages)>
- Adam Frank (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/adam-frank/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Macklin McCall (BC Conservatives): [Wikipedia: Macklin McCall](https://en.wikipedia.org/wiki/Macklin_McCall), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- George Morgan (BC NDP): [BC NDP release: six more candidates](https://www.bcndp.ca/releases/bc-ndp-announces-six-more-candidates-stand-british-columbians), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)


</details>

<details>
<summary>North and Cariboo (10 ridings)</summary>

**Bulkley Valley-Stikine** (`BLS`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; https://bcballot.ca/ridings/bulkley-valley-stikine/ ; Wikipedia 2024 riding result template>
- Frankie Abel (BC NDP): [BC NDP candidate page](https://frankieabel.bcndp.ca/), [Interior News](https://interior-news.com/2026/10/05/bc-ndp-selects-political-newcomer-as-bulkley-valley-stikine-candidate/)
- Sharon Hartwell (BC Conservatives): [Wikipedia: Sharon Hartwell](https://en.wikipedia.org/wiki/Sharon_Hartwell), [Interior News](https://interior-news.com/2026/10/05/bc-conservatives-hartwell-to-run-again-in-bulkley-valley-stikine/)
- Ed Ewald (Christian Heritage Party of BC): [Interior News](https://interior-news.com/2026/10/05/christian-heritage-partys-ed-ewald-steps-up-to-replace-rod-taylor/), [Elections BC candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)

**Cariboo-Chilcotin** (`CBC`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; https://bcballot.ca/ridings/cariboo-chilcotin/ ; Wikipedia 2024 riding result template>
- Kathryn Askew (BC NDP): [BC NDP candidate page](https://kathrynaskew.bcndp.ca/), [Williams Lake Tribune](https://wltribune.com/2026/10/01/retired-school-teacher-named-bc-ndp-candidate-for-cariboo-chilcoin/)
- Lorne Doerkson (BC Conservatives): [Wikipedia: Lorne Doerkson](https://en.wikipedia.org/wiki/Lorne_Doerkson), [Wikipedia: 2026 British Columbia general election](https://en.wikipedia.org/wiki/2026_British_Columbia_general_election)
- Douglas Gook (BC Greens): [VoteMate 2020 profile](https://votemate.org/c/4179), [Wikipedia: Nechako Lakes](https://en.wikipedia.org/wiki/Nechako_Lakes_(provincial_electoral_district))

**Nechako Lakes** (`NEC`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; https://bcballot.ca/ridings/nechako-lakes/ ; Wikipedia 2024 riding result template>
- Diane Black (BC Conservatives): [The Northern View](https://thenorthernview.com/2026/10/02/nechako-lakes-conservative-candidate-diane-black-is-ready-to-fight-for-the-north/), [BC Conservatives candidate page](https://conservativebc.ca/candidate/diane-black/)
- Jesse Gervais (BC NDP): [BC NDP candidate page](https://jessegervais.bcndp.ca/), [Omineca Express](https://ominecaexpress.com/2026/09/28/fraser-lake-official-jesse-gervais-named-bc-ndp-candidate-in-nechako-lakes/)
- Clint Lambert (Unaffiliated): [Caledonia Courier](https://caledoniacourier.com/2026/10/06/clint-lambert-enters-nechako-lakes-mla-race-as-a-blue-independent/), [Elections BC candidate report PDF (Oct 12, 2026)](https://www.elections.bc.ca/docs/fin/GE-2026-10-24-Candidate-Website-Report.PDF)

**North Coast-Haida Gwaii** (`NOH`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; https://bcballot.ca/ridings/north-coast-haida-gwaii/ ; Wikipedia 2024 riding result template>
- Tamara Davidson (BC NDP): [BC NDP candidate page](https://tamaradavidson.bcndp.ca/), [Wikipedia: Tamara Davidson](https://en.wikipedia.org/wiki/Tamara_Davidson)
- Rodney Proskiw (BC Conservatives): [BC Conservatives candidate page](https://conservativebc.ca/candidate/rodney-proskiw/), [Elections BC candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Francis Racy (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/francis-racy/), [Elections BC candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)

**Peace River North** (`PCN`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; https://bcballot.ca/ridings/peace-river-north/ ; Wikipedia 2024 riding result template>
- Curtis Whitford (BC Conservatives): [BC Conservatives candidate page](https://conservativebc.ca/candidate/curtis-whitford/), [Energeticcity candidates finalized](https://energeticcity.ca/2026/10/05/2026-provincial-election-candidates-finalized/)
- Jordan Kealy (Independent): [Wikipedia: Jordan Kealy](https://en.wikipedia.org/wiki/Jordan_Kealy), [Energeticcity: charged](https://energeticcity.ca/2026/06/04/independent-b-c-legislator-jordan-kealy-charged-with-sexual-assault/)

**Peace River South** (`PCS`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; https://bcballot.ca/ridings/peace-river-south/ ; Wikipedia 2024 riding result template>
- Marsha Rose Dufresne (BC NDP): [BC NDP candidate page](https://marshadufresne.bcndp.ca/), [BC NDP release, Oct 3, 2026](https://www.bcndp.ca/releases/more-bc-ndp-candidates-ready-fight-their-communities)
- Larry Neufeld (BC Conservatives): [Wikipedia: Larry Neufeld](https://en.wikipedia.org/wiki/Larry_Neufeld), [Energeticcity candidates finalized](https://energeticcity.ca/2026/10/05/2026-provincial-election-candidates-finalized/)
- Helen Scott (Unaffiliated): [Elections BC candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/), [Energeticcity candidates finalized](https://energeticcity.ca/2026/10/05/2026-provincial-election-candidates-finalized/)

**Prince George-Mackenzie** (`PRM`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; https://bcballot.ca/ridings/prince-george-mackenzie/ ; Wikipedia 2024 riding result template>
- Kiel Giddens (BC Conservatives): [Wikipedia: Kiel Giddens](https://en.wikipedia.org/wiki/Kiel_Giddens), [CKPG candidates announced](https://ckpgtoday.ca/2026/10/03/prince-george-area-candidates-announced-for-2026-provincial-election/)
- Ian McMahon (BC NDP): [BC NDP candidate page](https://ianmcmahon.bcndp.ca/), [Wikipedia: Results of the 2024 British Columbia general election by riding](https://en.wikipedia.org/wiki/Results_of_the_2024_British_Columbia_general_election_by_riding)
- Teri Young (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/teri-young/), [Elections BC candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)

**Prince George-North Cariboo** (`PRO`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; https://bcballot.ca/ridings/prince-george-north-cariboo/ ; Wikipedia 2024 riding result template>
- Denice Bardua (BC NDP): [BC NDP candidate page](https://denicebardua.bcndp.ca/), [Wikipedia: Results of the 2024 British Columbia general election by riding](https://en.wikipedia.org/wiki/Results_of_the_2024_British_Columbia_general_election_by_riding)
- Sheldon Clare (BC Conservatives): [Wikipedia: Sheldon Clare](https://en.wikipedia.org/wiki/Sheldon_Clare), [CKPG candidates announced](https://ckpgtoday.ca/2026/10/03/prince-george-area-candidates-announced-for-2026-provincial-election/)
- Randy Thompson (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/randy-thompson/), [Elections BC candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)

**Prince George-Valemount** (`PRV`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; https://bcballot.ca/ridings/prince-george-valemount/ ; Wikipedia 2024 riding result template>
- Rosalyn Bird (BC Conservatives): [Wikipedia: Rosalyn Bird](https://en.wikipedia.org/wiki/Rosalyn_Bird), [CKPG candidates announced](https://ckpgtoday.ca/2026/10/03/prince-george-area-candidates-announced-for-2026-provincial-election/)
- Carol Bourque (BC NDP): [BC NDP candidate page](https://carolbourque.bcndp.ca/), [Elections BC candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Jodie Capling (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/jodie-capling/), [Elections BC candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Mitchell Lukoni (OneBC): [OneBC candidate page](https://1bc.ca/candidates/mlukoni), [Elections BC candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)

**Skeena** (`SKE`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf (Skeena page: 6,243 / 5,419 / 406 / 126 votes)>
- Nick Gottlieb (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/nick-gottlieb/), [Elections BC candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Claire Rattée (BC Conservatives): [Wikipedia: Claire Ratt%C3%A9e](https://en.wikipedia.org/wiki/Claire_Ratt%C3%A9e), [Today in BC](https://todayinbc.com/2026/09/24/rattee-poised-to-seek-re-election-in-skeena-as-b-c-conservatives-regroup/)
- Larry Eugene Taylor (OneBC): [OneBC candidate page](https://1bc.ca/candidates/ltaylor), [Elections BC candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Sarah Zimmerman (BC NDP): [BC NDP candidate page](https://sarahzimmerman.bcndp.ca/), [Wikipedia: Skeena (provincial electoral district)](https://en.wikipedia.org/wiki/Skeena_(provincial_electoral_district))


</details>

<details>
<summary>Metro Vancouver (32 ridings)</summary>

**Burnaby Centre** (`BNC`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; cross-checked against https://bcballot.ca/ridings/burnaby-centre/>
- Joshua Domnich (BC Conservatives): [BC Conservatives candidate page](https://conservativebc.ca/candidate/joshua-domnich/), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)
- Vikas Gautam (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/vikas-gautam/), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)
- Anne Kang (BC NDP): [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/), [BC Ballot riding page](https://bcballot.ca/ridings/burnaby-centre/)
- Shila Taheri (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/shila-taheri/), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)

**Burnaby East** (`BNE`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; cross-checked against https://bcballot.ca/ridings/burnaby-east/>
- Rohini Reah Arora (BC NDP): [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/), [BC Ballot riding page](https://bcballot.ca/ridings/burnaby-east/)
- De Ding (OneBC): [BC Ballot candidate page](https://bcballot.ca/ridings/burnaby-east/de-ding/), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)
- Javad Shushtarian (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/javad-shushtarian/), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)
- Peter Si (BC Conservatives): [BC Conservatives candidate page](https://conservativebc.ca/candidate/peter-si/), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)

**Burnaby North** (`BNO`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; cross-checked against https://bcballot.ca/ridings/burnaby-north/>
- Simon Chandler (BC Conservatives): [BC Conservatives candidate page](https://conservativebc.ca/candidate/simon-chandler/), [Wikipedia, Burnaby East](https://en.wikipedia.org/wiki/Burnaby_East)
- Maddy Kennedy-Parrott (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/maddy-kennedy-parrott/), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)
- Janet Routledge (BC NDP): [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/), [BC Ballot riding page](https://bcballot.ca/ridings/burnaby-north/)
- Jenny Yamagata (OneBC): [Wikipedia, Candidates of the 2026 BC general election](https://en.wikipedia.org/wiki/Candidates_of_the_2026_British_Columbia_general_election), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)

**Burnaby South-Metrotown** (`BNS`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; cross-checked against https://bcballot.ca/ridings/burnaby-south-metrotown/>
- Paul Choi (BC NDP): [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/), [BC Ballot riding page](https://bcballot.ca/ridings/burnaby-south-metrotown/)
- Bryan Fockler (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/bryan-fockler/), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)
- Andrew Rose (OneBC): [OneBC candidate page](https://1bc.ca/candidates/arose), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)
- David Xie (BC Conservatives): [BC Conservatives candidate page](https://conservativebc.ca/candidate/david-xie/), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)

**Burnaby-New Westminster** (`BNN`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; cross-checked against https://bcballot.ca/ridings/burnaby-new-westminster/>
- Raj Chouhan (BC NDP): [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/), [BC Ballot riding page](https://bcballot.ca/ridings/burnaby-new-westminster/)
- Joe Latam (BC Conservatives): [BC Conservatives candidate page](https://conservativebc.ca/candidate/joe-latam/), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)

**Coquitlam-Burke Mountain** (`CQB`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; cross-checked against https://bcballot.ca/ridings/coquitlam-burke-mountain/>
- Kaden Mann (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/kaden-mann/), [BC Ballot riding page](https://bcballot.ca/ridings/coquitlam-burke-mountain/)
- Valerie Morrison (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/valerie-morrison/), [BC Ballot riding page](https://bcballot.ca/ridings/coquitlam-burke-mountain/)
- Ryan Peterson (BC Conservatives): [BC Conservatives candidate page](https://conservativebc.ca/candidate/ryan-peterson/), [BC Ballot riding page](https://bcballot.ca/ridings/coquitlam-burke-mountain/)
- Jodie Wickens (BC NDP): [Wikipedia, Jodie Wickens](https://en.wikipedia.org/wiki/Jodie_Wickens), [BC Ballot riding page](https://bcballot.ca/ridings/coquitlam-burke-mountain/)

**Coquitlam-Maillardville** (`CQM`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; cross-checked against https://bcballot.ca/ridings/coquitlam-maillardville/>
- Jennifer Blatherwick (BC NDP): [Wikipedia, Jennifer Blatherwick](https://en.wikipedia.org/wiki/Jennifer_Blatherwick), [BC Ballot riding page](https://bcballot.ca/ridings/coquitlam-maillardville/)
- Matt Liang (BC Conservatives): [BC Conservatives candidate page](https://conservativebc.ca/candidate/matthew-liang/), [BC Ballot riding page](https://bcballot.ca/ridings/coquitlam-maillardville/)
- Nicola Spurling (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/nicola-spurling/), [BC Ballot riding page](https://bcballot.ca/ridings/coquitlam-maillardville/)

**Delta North** (`DLN`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; cross-checked against https://bcballot.ca/ridings/delta-north/>
- Monica Mohan (BC Conservatives): [BC Conservatives candidate page](https://conservativebc.ca/candidate/monica-mohan/), [BC Ballot riding page](https://bcballot.ca/ridings/delta-north/)
- Kuldeep Rangi (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/kuldeep-rangi/), [BC Ballot riding page](https://bcballot.ca/ridings/delta-north/)
- Todd Schierling (BC NDP): [Elections BC 2026 candidate list (page)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [BC Ballot riding page](https://bcballot.ca/ridings/delta-north/)

**Delta South** (`DLS`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; cross-checked against https://bcballot.ca/ridings/delta-south/>
- Skadi Green (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/skadi-green/), [BC Ballot riding page](https://bcballot.ca/ridings/delta-south/)
- Jason McCormick (BC NDP): [Delta Optimist, NDP candidate announced for Delta South (2024; seen via search snippet only)](https://delta-optimist.com/local-news/ndp-candidate-announced-for-delta-south-9331350), [BC Ballot riding page](https://bcballot.ca/ridings/delta-south/)
- Jim McMurtry (OneBC): [OneBC candidate page](https://1bc.ca/candidates/jmcmurtry), [BC Ballot riding page](https://bcballot.ca/ridings/delta-south/)
- Ian Paton (BC Conservatives): [BC Conservatives candidate page](https://conservativebc.ca/candidate/ian-paton/), [Wikipedia, Ian Paton](https://en.wikipedia.org/wiki/Ian_Paton_(politician))

**New Westminster-Coquitlam** (`NMC`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; cross-checked against https://bcballot.ca/ridings/new-westminster-coquitlam/>
- Maureen Curran (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/maureen-curran/), [BC Ballot riding page](https://bcballot.ca/ridings/new-westminster-coquitlam/)
- Michele Lau (BC Conservatives): [BC Conservatives candidate page](https://conservativebc.ca/candidate/michele-lau/), [BC Ballot riding page](https://bcballot.ca/ridings/new-westminster-coquitlam/)
- Jennifer Whiteside (BC NDP): [Wikipedia, Jennifer Whiteside](https://en.wikipedia.org/wiki/Jennifer_Whiteside), [BC Ballot riding page](https://bcballot.ca/ridings/new-westminster-coquitlam/)
- Gerry Lenoski (Unaffiliated): [Elections BC 2026 candidate list (page)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [BC Ballot riding page](https://bcballot.ca/ridings/new-westminster-coquitlam/)

**North Vancouver-Lonsdale** (`NVL`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Joshua A Singer Johnson (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/joshua-a-singer-johnson/)
- Bowinn Ma (BC NDP): [Wikipedia: Bowinn Ma](https://en.wikipedia.org/wiki/Bowinn_Ma)
- Trevor Withers (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/trevor-withers/)

**North Vancouver-Seymour** (`NVS`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Lynne Block (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/lynne-block/), [North Shore News candidate roundup](https://www.nsnews.com/local-news/here-are-the-north-shore-candidates-running-in-bcs-snap-election-12858354)
- Susie Chant (BC NDP): [Wikipedia: Susie Chant](https://en.wikipedia.org/wiki/Susie_Chant)
- Lori Climenhaga (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/lori-climenhaga/)
- Ben Holt (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/ben-holt/)
- Frederick Thiele (OneBC): [VoteMate 2026 riding page](https://votemate.org/bc2026provincial/candidates/?riding=2165), [BC Ballot profile](https://bcballot.ca/ridings/north-vancouver-seymour/frederick-thiele/)

**Port Coquitlam** (`POC`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; cross-checked against https://bcballot.ca/ridings/port-coquitlam/>
- Keenan Adams (BC Conservatives): [BC Conservatives candidate page](https://conservativebc.ca/candidate/keenan-adams/), [BC Ballot riding page](https://bcballot.ca/ridings/port-coquitlam/)
- Mike Farnworth (BC NDP): [Wikipedia, Mike Farnworth](https://en.wikipedia.org/wiki/Mike_Farnworth), [BC Ballot riding page](https://bcballot.ca/ridings/port-coquitlam/)
- Stephanie Hendy (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/stephanie-hendy/), [BC Ballot riding page](https://bcballot.ca/ridings/port-coquitlam/)
- Lee-Ann Bates (Unaffiliated): [OneBC candidates page](https://1bc.ca/candidates), [BC Ballot riding page](https://bcballot.ca/ridings/port-coquitlam/)
- Lewis C. Dahlby (BC Libertarian): [BC Ballot riding page](https://bcballot.ca/ridings/port-coquitlam/), [Elections BC 2026 candidate list (page)](https://elections.bc.ca/2026-provincial-election/candidate-list/)

**Port Moody-Burquitlam** (`POM`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; cross-checked against https://bcballot.ca/ridings/port-moody-burquitlam/>
- Wei Chou (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/wei-chou/), [BC Ballot riding page](https://bcballot.ca/ridings/port-moody-burquitlam/)
- Rick Glumac (BC NDP): [Wikipedia, Rick Glumac](https://en.wikipedia.org/wiki/Rick_Glumac), [BC Ballot riding page](https://bcballot.ca/ridings/port-moody-burquitlam/)
- John McEwen (BC Conservatives): [BC Conservatives candidate page](https://conservativebc.ca/candidate/john-mcewen/), [BC Ballot riding page](https://bcballot.ca/ridings/port-moody-burquitlam/)
- Freddy Rawji (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/freddy-rawji/), [BC Ballot riding page](https://bcballot.ca/ridings/port-moody-burquitlam/)

**Richmond Centre** (`RCC`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; cross-checked against https://bcballot.ca/ridings/richmond-centre/>
- Calvin Dang (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/calvin-dang/), [BC Ballot riding page](https://bcballot.ca/ridings/richmond-centre/)
- Sacha Peter (BC Conservatives): [BC Conservatives candidate page](https://conservativebc.ca/candidate/sacha-peter/), [BC Ballot riding page](https://bcballot.ca/ridings/richmond-centre/)
- Henry Yao (BC NDP): [BC NDP nomination release (2024)](https://www.bcndp.ca/releases/bc-ndp-nominates-mla-and-community-advocate-henry-yao-richmond-centre-stand-you), [BC Ballot riding page](https://bcballot.ca/ridings/richmond-centre/)
- Lawrence Chen (CanWest Party): [BC Ballot riding page](https://bcballot.ca/ridings/richmond-centre/), [Elections BC 2026 candidate list (page)](https://elections.bc.ca/2026-provincial-election/candidate-list/)

**Richmond-Bridgeport** (`RCB`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; cross-checked against https://bcballot.ca/ridings/richmond-bridgeport/>
- Linda Li (BC NDP): [BC NDP release (2024)](https://www.bcndp.ca/releases/business-and-community-leader-linda-li-run-bc-ndp-richmond-bridgeport), [BC Ballot riding page](https://bcballot.ca/ridings/richmond-bridgeport/)
- Teresa Wat (BC Conservatives): [BC Conservatives candidate page](https://conservativebc.ca/candidate/teresa-wat/), [Wikipedia, Teresa Wat](https://en.wikipedia.org/wiki/Teresa_Wat)

**Richmond-Queensborough** (`RCQ`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; cross-checked against https://bcballot.ca/ridings/richmond-queensborough/>
- Luc Burns (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/luc-burns/), [BC Ballot riding page](https://bcballot.ca/ridings/richmond-queensborough/)
- Dhar Grewal (BC NDP): [Elections BC 2026 candidate list (page)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [BC Ballot riding page](https://bcballot.ca/ridings/richmond-queensborough/)
- Steve Kooner (BC Conservatives): [BC Conservatives candidate page](https://conservativebc.ca/candidate/steve-kooner/), [Wikipedia, Steve Kooner](https://en.wikipedia.org/wiki/Steve_Kooner)

**Richmond-Steveston** (`RCS`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; cross-checked against https://bcballot.ca/ridings/richmond-steveston/>
- Bruce Kong (BC NDP): [Elections BC 2026 candidate list (page)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [BC Ballot riding page](https://bcballot.ca/ridings/richmond-steveston/)
- Barry Wosk (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/barry-wosk/), [BC Ballot riding page](https://bcballot.ca/ridings/richmond-steveston/)
- Gordon Zhang (BC Conservatives): [BC Conservatives candidate page](https://conservativebc.ca/candidate/gordon-zhang/), [BC Ballot riding page](https://bcballot.ca/ridings/richmond-steveston/)
- Robert Evans (Independent): [Elections BC 2026 candidate list (page)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [BC Ballot riding page](https://bcballot.ca/ridings/richmond-steveston/)
- Keenan Yang (CanWest Party): [Elections BC 2026 candidate list (page)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [BC Ballot riding page](https://bcballot.ca/ridings/richmond-steveston/)

**Vancouver-Fraserview** (`VFV`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Francoise Raunet (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/francoise-raunet/)
- Deep Sandhu (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/deep-sandhu/)
- Aman Singh (BC NDP): [Wikipedia: Aman Singh](https://en.wikipedia.org/wiki/Aman_Singh)

**Vancouver-Hastings** (`VHA`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Christian Bosio (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/christian-bosio/)
- Kyra Philbert (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/kyra-philbert/)
- Niki Sharma (BC NDP): [Wikipedia: Niki Sharma](https://en.wikipedia.org/wiki/Niki_Sharma)
- Phyllis Tang (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/phyllis-tang/)
- Kimball Cariou (Communist Party of BC): [BC Ballot profile](https://bcballot.ca/ridings/vancouver-hastings/kimball-cariou/), [Wikipedia: Communist Party of British Columbia](https://en.wikipedia.org/wiki/Communist_Party_of_British_Columbia)
- Phil Webb (BC Libertarian): [BC Ballot profile](https://bcballot.ca/ridings/vancouver-hastings/phil-webb/)

**Vancouver-Kensington** (`VKE`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Mable Elmore (BC NDP): [Wikipedia: Mable Elmore](https://en.wikipedia.org/wiki/Mable_Elmore)
- Adam Hawk (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/adam-hawk/), [Elections BC Statement of Votes 2024](https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf)
- Aron Lageri (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/aron-lageri/), [Elections BC Statement of Votes 2024](https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf)

**Vancouver-Langara** (`VLA`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- John Atoyebi (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/john-atoyebi/)
- Alan Beesley (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/alan-beesley/)
- Sunita Dhir (BC NDP): [Wikipedia: Sunita Dhir](https://en.wikipedia.org/wiki/Sunita_Dhir)
- Jaime Stein (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/jaime-stein/)

**Vancouver-Little Mountain** (`VLM`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Christine Boyle (BC NDP): [Wikipedia: Christine Boyle](https://en.wikipedia.org/wiki/Christine_Boyle)
- Sarah MacLeod (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/sarah-macleod/)
- Alex Muir (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/alex-muir/)

**Vancouver-Point Grey** (`VNP`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Michael Davis (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/michael-davis/)
- David Eby (BC NDP): [Wikipedia: David Eby](https://en.wikipedia.org/wiki/David_Eby)
- Alex McMillan (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/alex-mcmillan/)
- Beatrice Sharpe (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/beatrice-sharpe/)

**Vancouver-Quilchena** (`VNQ`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Carson Binda (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/carson-binda/)
- Dallas Brodie (OneBC): [Wikipedia: Dallas Brodie](https://en.wikipedia.org/wiki/Dallas_Brodie)
- Douglas Courtemanche (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/douglas-courtemanche/)
- Petra Kuret (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/petra-kuret/)
- Callista Ryan (BC NDP): [BC NDP release (2024 nomination)](https://bcndp.ca/releases/youth-advocate-callista-ryan-run-bc-ndp-vancouver-quilchena)

**Vancouver-Renfrew** (`VNR`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Adrian Dix (BC NDP): [Wikipedia: Adrian Dix](https://en.wikipedia.org/wiki/Adrian_Dix)
- Rebecca Haber (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/rebecca-haber/)
- Tom Ikonomou (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/tom-ikonomou/)
- Lisa Prescott (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/lisa-prescott/)

**Vancouver-South Granville** (`VNS`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Maria J Cruz (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/maria-cruz/)
- Lara Honrado (BC NDP): [BC NDP release, more candidates (2026)](https://www.bcndp.ca/releases/more-bc-ndp-candidates-ready-fight-their-communities)
- Lisa Phillips (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/lisa-phillips/)
- Colin Smith (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/colin-smith/)
- Salvatore Vetro (OneBC): [BC Ballot profile](https://bcballot.ca/ridings/vancouver-south-granville/salvatore-vetro/)

**Vancouver-Strathcona** (`VNT`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Amanda Burrows (BC NDP): [Daily Hive](https://dailyhive.com/vancouver/amanda-burrows-bc-ndp)
- Jordan Zheng McIntosh (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/jordan-mcintosh/)
- Tanya Webking (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/tanya-webking/)
- Robert Crooks (Communist Party of BC): [Wikipedia: Communist Party of British Columbia](https://en.wikipedia.org/wiki/Communist_Party_of_British_Columbia), [Elections BC Statement of Votes 2024](https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf)

**Vancouver-West End** (`VNW`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Spencer Chandra Herbert (BC NDP): [Wikipedia: Spencer Chandra Herbert](https://en.wikipedia.org/wiki/Spencer_Chandra_Herbert)
- Scott MacDonald (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/donald-scott-macdonald/)
- Dion Weisner (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/dion-weisner/)

**Vancouver-Yaletown** (`VNY`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Sam Chandola (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/sam-chandola/), [Elections BC Statement of Votes 2024](https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf)
- Margareta Dovgal (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/margareta-dovgal/)
- Priyan Samarakoone (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/priyan-samarakoone/)
- Terry Yung (BC NDP): [Wikipedia: Terry Yung](https://en.wikipedia.org/wiki/Terry_Yung)

**West Vancouver-Capilano** (`WVC`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Honieh Barzegari (BC NDP): [BC NDP release, more candidates (2026)](https://www.bcndp.ca/releases/more-bc-ndp-candidates-ready-fight-their-communities)
- Naomi Chocyk (OneBC): [BC Ballot profile](https://bcballot.ca/ridings/west-vancouver-capilano/naomi-chocyk/)
- Caroline Elliott (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/caroline-elliott/), [CTV News](https://www.ctvnews.ca/vancouver/article/former-bc-conservative-leadership-candidate-caroline-elliott-will-run-in-election/)
- Arwa Shurab (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/arwa-shurab/)

**West Vancouver-Sea to Sky** (`WVS`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Ayla Dumais (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/ayla-dumais/)
- Michelle Livaja (BC NDP): [Pique Newsmagazine](https://www.piquenewsmagazine.com/local-news/four-candidates-announced-in-west-vancouver-sea-to-sky-provincial-race-12848838)
- Jeremy Valeriote (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/jeremy-valeriote-2/)
- Dan Wood (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/dan-wood/)


</details>

<details>
<summary>Vancouver Island and the Coast (16 ridings)</summary>

**Courtenay-Comox** (`CRC`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Will Cole-Hamilton (BC NDP): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Jason Cook (CentreBC): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Brennan Day (BC Conservatives): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Jay Van Oostdam (BC Greens): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)

**Cowichan Valley** (`CWV`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Bert Chen (BC Conservatives): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Justin Douglas (BC Greens): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Debra Toporowski (BC NDP): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- James Chumsa (Communist Party of BC): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)

**Esquimalt-Colwood** (`ESC`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Sidney Coles (BC Greens): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Dave Johnston (BC Conservatives): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Darlene Rotchford (BC NDP): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Sid Tobias (CentreBC): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)

**Juan de Fuca-Malahat** (`JFM`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- David Evans (BC Greens): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Shane Friesen (OneBC): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Mike Hicks (BC Conservatives): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Dana Lajeunesse (BC NDP): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Jeff Brown (Christian Heritage Party of BC): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)

**Ladysmith-Oceanside** (`LAO`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Stephanie Higginson (BC NDP): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Kris McNichol (BC Conservatives): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Charlene Smylie (BC Greens): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)

**Langford-Highlands** (`LFH`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Sean Flynn (CentreBC): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Christopher Moon (BC Greens): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Ravi Parmar (BC NDP): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Cindy Scott (BC Conservatives): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Christian McCay (Christian Heritage Party of BC): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Alex Thurlborn (Independent): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)

**Mid Island-Pacific Rim** (`MPR`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Joshua Dahling (BC Conservatives): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Gracie MacDonald (BC Greens): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Josie Osborne (BC NDP): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)

**Nanaimo-Gabriola Island** (`NAI`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Mark MacDonald (BC Conservatives): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Sheila Malcolmson (BC NDP): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Anna Mary McKenzie (BC Greens): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)

**Nanaimo-Lantzville** (`NAL`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- George Anderson (BC NDP): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Kelsey Pringle (BC Conservatives): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Sharleen Weatherley (BC Greens): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Pepper Saltman (Communist Party of BC): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)

**North Island** (`NOI`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Anna Kindy (BC Conservatives): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Sara Lopez (BC NDP): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Benjamin Olsson (BC Greens): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Richard Lambert (Independent): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)

**Oak Bay-Gordon Head** (`OBG`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Andrew Appleton (BC Greens): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Diana Gibson (BC NDP): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Stan Sipos (BC Conservatives): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Andrew Weaver (CentreBC): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)

**Powell River-Sunshine Coast** (`POR`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- John Henderson (BC Conservatives): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [Powell River Peak: Powell River-Sunshine Coast will see three candidates run for MLA](https://www.prpeak.com/2026-bc-votes/powell-river-sunshine-coast-will-see-three-candidates-run-for-mla-12869651)
- Griffin Leonard Lea (BC Greens): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [Powell River Peak: Powell River-Sunshine Coast will see three candidates run for MLA](https://www.prpeak.com/2026-bc-votes/powell-river-sunshine-coast-will-see-three-candidates-run-for-mla-12869651)
- Randene Neill (BC NDP): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [Powell River Peak: Powell River-Sunshine Coast will see three candidates run for MLA](https://www.prpeak.com/2026-bc-votes/powell-river-sunshine-coast-will-see-three-candidates-run-for-mla-12869651)

**Saanich North and the Islands** (`SAN`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Kala Bryson (BC NDP): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Emily Lowan (BC Greens): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Richard Smith (CentreBC): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Ryan Windsor (BC Conservatives): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)

**Saanich South** (`SAS`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Lisa Lapointe (BC Greens): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Cathie Ounsted (BC Conservatives): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Richard Zussman (BC NDP): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)

**Victoria-Beacon Hill** (`VTB`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Joachim Agou (BC Conservatives): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Grace Lore (BC NDP): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Rajinder S. Sahota (BC Greens): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)

**Victoria-Swan Lake** (`VTS`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Carolyn Howe (BC Greens): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Nina Krieger (BC NDP): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Tim Taylor (BC Conservatives): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)


</details>

<details>
<summary>Surrey (10 ridings)</summary>

**Surrey City Centre** (`SRC`)

- 2024 result: <https://bcelectionguide.ca/ridings/surrey-city-centre/ (citing Elections BC Statement of Votes, https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf)>
- Amna Shah (BC NDP): [Amna Shah campaign page](https://amnashah.bcndp.ca), [Surrey Now-Leader: final list of 47 candidates](https://surreynowleader.com/2026/10/04/see-the-final-list-of-47-candidates-in-10-surrey-ridings-for-b-c-election/)
- Raman Sharma (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/raman-sharma/), [Elections BC 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Zeeshan Wahla (BC Conservatives): [Conservative candidate page](https://conservativebc.ca/candidate/zeeshan-wahla/), [Surrey Now-Leader: who's running in Surrey ridings](https://surreynowleader.com/2026/09/28/b-c-votes-whos-running-in-surrey-ridings-oct-24-and-what-happened-last-election/)
- Oliver Wildfong (OneBC): [Elections BC 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)

**Surrey North** (`SUN`)

- 2024 result: <https://bcelectionguide.ca/ridings/surrey-north/ (citing Elections BC Statement of Votes, https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf)>
- Parm Bhandol (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/bhandol-parm/), [Elections BC 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Mandeep Singh Dhaliwal (BC Conservatives): [Conservative candidate page](https://conservativebc.ca/candidate/mandeep-dhaliwal/), [Surrey Now-Leader: who's running in Surrey ridings](https://surreynowleader.com/2026/09/28/b-c-votes-whos-running-in-surrey-ridings-oct-24-and-what-happened-last-election/)
- Yudhbir Gill (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/yudhbir-gill/), [Elections BC 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Tanya Gupta (OneBC): [Surrey Now-Leader: meet your Surrey North candidates](https://surreynowleader.com/2026/10/09/b-c-votes-meet-your-surrey-north-candidates/), [Surrey Now-Leader: who's running in Surrey ridings](https://surreynowleader.com/2026/09/28/b-c-votes-whos-running-in-surrey-ridings-oct-24-and-what-happened-last-election/)
- Sahib Thind (BC NDP): [Sahib Thind campaign page](https://sahibthind.bcndp.ca), [Elections BC 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Jag Bhandari (Unaffiliated): [Elections BC 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)

**Surrey South** (`SUS`)

- 2024 result: <https://bcelectionguide.ca/ridings/surrey-south/ (citing Elections BC Statement of Votes, https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf)>
- Megan Knight (BC Conservatives): [Conservative candidate page](https://conservativebc.ca/candidate/megan-knight/), [Daily Hive: Megan Knight to run in Surrey South](https://dailyhive.com/vancouver/megan-knight-white-rock-surrey-south-civic-provincial-election-conservatives)
- Bill McConnell (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/bill-mcconnell/), [Elections BC 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Elenore Sturko (CentreBC): [Wikipedia: Elenore Sturko](https://en.wikipedia.org/wiki/Elenore_Sturko), [CentreBC candidates page](https://centrebc.ca/candidates)
- Parik Tahlan (BC NDP): [Parik Tahlan campaign page](https://pariktahlan.bcndp.ca/), [Elections BC 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Denis R Hurtubise (Unaffiliated): [Elections BC 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)

**Surrey-Cloverdale** (`SRD`)

- 2024 result: <https://bcelectionguide.ca/ridings/surrey-cloverdale/ (citing Elections BC Statement of Votes, https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf)>
- Nicholas Cartmell (BC Conservatives): [Conservative candidate page](https://conservativebc.ca/candidate/nicholas-cartmell/), [Surrey Now-Leader: meet the candidates in Surrey-Cloverdale](https://surreynowleader.com/2026/10/08/bc-votes-meet-the-candidates-in-surrey-cloverdale/)
- Sargy Chima (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/sargy-chima/), [Elections BC 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Stephen Dooley (BC NDP): [Stephen Dooley campaign page](https://stephendooley.bcndp.ca/), [Surrey Now-Leader: meet the candidates in Surrey-Cloverdale](https://surreynowleader.com/2026/10/08/bc-votes-meet-the-candidates-in-surrey-cloverdale/)
- Travis Marchenski (OneBC): [Surrey Now-Leader: meet the candidates in Surrey-Cloverdale](https://surreynowleader.com/2026/10/08/bc-votes-meet-the-candidates-in-surrey-cloverdale/), [Elections BC 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Pat McCutcheon (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/patrick-mccutcheon/), [BC Election Guide: Surrey-Cloverdale](https://bcelectionguide.ca/ridings/surrey-cloverdale/)

**Surrey-Fleetwood** (`SRF`)

- 2024 result: <https://bcelectionguide.ca/ridings/surrey-fleetwood/ (citing Elections BC Statement of Votes, https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf)>
- Tim Binnema (BC Greens): [BC Greens: Tim Binnema candidate page](https://bcgreens.ca/candidates/tim-binnema/), [BC Ballot: Tim Binnema, Surrey-Fleetwood](https://bcballot.ca/ridings/surrey-fleetwood/tim-binnema/)
- Jagrup Brar (BC NDP): [BC Ballot: Jagrup Brar](https://bcballot.ca/mlas/jagrup-brar/), [Wikipedia: Jagrup Brar (secondary)](https://en.wikipedia.org/wiki/Jagrup_Brar), [Votes and Proceedings, May 28, 2025](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v250528.htm), [BC Government: Eskay Creek approval](https://news.gov.bc.ca/releases/2026MCM0008-000078), [Jagrup Brar campaign page (party-authored)](https://jagrupbrar.bcndp.ca)
- Paul Brar (CentreBC): [CentreBC: Paul Brar candidate page](https://centrebc.ca/candidates/paul-brar/), [Surrey Now-Leader: who is running in Surrey ridings (Sept 28, 2026)](https://surreynowleader.com/2026/09/28/b-c-votes-whos-running-in-surrey-ridings-oct-24-and-what-happened-last-election/), [BC Ballot: Paul Brar, Surrey-Fleetwood](https://bcballot.ca/ridings/surrey-fleetwood/paul-brar/)
- Carolyn Hofbauer (OneBC): [OneBC: Carolyn Hofbauer candidate page](https://1bc.ca/candidates/chofbauer), [BC Ballot: Carolyn Hofbauer, Surrey-Fleetwood](https://bcballot.ca/ridings/surrey-fleetwood/carolyn-hofbauer/)
- Garry Purewal (BC Conservatives): [Conservative Party of BC: Garry Purewal candidate page](https://conservativebc.ca/candidate/garry-purewal/), [BC Ballot: Garry Purewal, Surrey-Fleetwood](https://bcballot.ca/ridings/surrey-fleetwood/garry-purewal/), [Conservative Party of BC: Surrey candidates (Sept 29, 2026)](https://conservativebc.ca/conservative-party-of-bc-announces-strong-surrey-candidates-for-serious-times/)

**Surrey-Guildford** (`SRG`)

- 2024 result: <https://bcelectionguide.ca/ridings/surrey-guildford/ (citing Elections BC Statement of Votes, https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf)>
- Garry Begg (BC NDP): [Garry Begg campaign page](https://garrybegg.bcndp.ca), [Surrey Now-Leader: final list of 47 candidates](https://surreynowleader.com/2026/10/04/see-the-final-list-of-47-candidates-in-10-surrey-ridings-for-b-c-election/)
- Jodi Murphy (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/jodi-murphy/), [Elections BC 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Garry Thind (BC Conservatives): [Conservative candidate page](https://conservativebc.ca/candidate/garry-thind/), [Surrey Now-Leader: who's running in Surrey ridings](https://surreynowleader.com/2026/09/28/b-c-votes-whos-running-in-surrey-ridings-oct-24-and-what-happened-last-election/)
- James Yaroshuk (Unaffiliated): [Elections BC 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)

**Surrey-Newton** (`SRN`)

- 2024 result: <https://bcelectionguide.ca/ridings/surrey-newton/ (citing Elections BC Statement of Votes, https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf)>
- Harj Dhaliwal (BC Conservatives): [Conservative candidate page](https://conservativebc.ca/candidate/harj-dhaliwal/), [Elections BC 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Harman Preet Singh (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/harman-preet-singh/), [Elections BC 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Jessie Sunner (BC NDP): [Jessie Sunner campaign page](https://jessiesunner.bcndp.ca), [Surrey Now-Leader: who's running in Surrey ridings](https://surreynowleader.com/2026/09/28/b-c-votes-whos-running-in-surrey-ridings-oct-24-and-what-happened-last-election/)

**Surrey-Panorama** (`SUP`)

- 2024 result: <https://bcelectionguide.ca/ridings/surrey-panorama/ (citing Elections BC Statement of Votes, https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf)>
- Manav Manro (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/manav-manro/), [Elections BC 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Nolen Scott (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/nolen-scott/), [Elections BC 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Jinny Sims (BC NDP): [Jinny Sims campaign page](https://jinnysims.bcndp.ca), [Surrey Now-Leader: who's running in Surrey ridings](https://surreynowleader.com/2026/09/28/b-c-votes-whos-running-in-surrey-ridings-oct-24-and-what-happened-last-election/)
- Bryan Tepper (BC Conservatives): [Conservative candidate page](https://conservativebc.ca/candidate/bryan-tepper/), [Surrey Now-Leader: who's running in Surrey ridings](https://surreynowleader.com/2026/09/28/b-c-votes-whos-running-in-surrey-ridings-oct-24-and-what-happened-last-election/)

**Surrey-Serpentine River** (`SUR`)

- 2024 result: <https://bcelectionguide.ca/ridings/surrey-serpentine-river/ (citing Elections BC Statement of Votes, https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf)>
- Judy Higginbotham (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/judy-higginbotham/), [Elections BC 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Todd Holowchak (OneBC): [Elections BC 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Sikander Kang (BC NDP): [Sikander Kang campaign page](https://sikanderkang.bcndp.ca), [Surrey Now-Leader: who's running in Surrey ridings](https://surreynowleader.com/2026/09/28/b-c-votes-whos-running-in-surrey-ridings-oct-24-and-what-happened-last-election/)
- Jessy Sahota (BC Conservatives): [Conservative candidate page](https://conservativebc.ca/candidate/jessy-sahota/), [Surrey Now-Leader: who's running in Surrey ridings](https://surreynowleader.com/2026/09/28/b-c-votes-whos-running-in-surrey-ridings-oct-24-and-what-happened-last-election/)
- Errol Povah (Freedom Party of BC): [VoteMate 2024 profile](https://votemate.org/bc2024/candidates/9213), [Elections BC 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)

**Surrey-White Rock** (`SWR`)

- 2024 result: <https://bcelectionguide.ca/ridings/surrey-white-rock/ (citing Elections BC Statement of Votes, https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf)>
- Trevor Halford (BC Conservatives): [Conservative candidate page](https://conservativebc.ca/candidate/trevor-halford/), [Wikipedia: Trevor Halford](https://en.wikipedia.org/wiki/Trevor_Halford)
- Amanda James (OneBC): [Elections BC 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/), [Elections BC 2026 candidate list (CSV)](https://elections.bc.ca/2026election/2026-provincial-general-election-candidates.csv)
- Christine Kinnie (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/christine-kinnie/), [Elections BC 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Waqas Rana (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/waqas-rana/), [Elections BC 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- Darryl Walker (BC NDP): [Darryl Walker campaign page](https://darrylwalker.bcndp.ca/), [Surrey Now-Leader: new candidates announced for Surrey-White Rock](https://surreynowleader.com/2026/10/02/new-election-candidates-announced-for-surrey-white-rock/)
- Kevin Diakiw (Independent): [Surrey Now-Leader: new candidates announced for Surrey-White Rock](https://surreynowleader.com/2026/10/02/new-election-candidates-announced-for-surrey-white-rock/), [Elections BC 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)


</details>

### Surrey local context and how to vote

<details>
<summary>Local context and Elections BC voting information</summary>

- [BC Electoral Boundaries Commission final report (2023)](https://votebymail.elections.bc.ca/docs/rpt/BCEBC-Final-Report-April-3-2023.pdf)
- [Elections BC: 2026 candidate nomination report (PDF)](https://www.elections.bc.ca/docs/fin/GE-2026-10-24-Candidate-Website-Report.PDF)
- [Wikipedia: Surrey-Fleetwood results (citing Elections BC)](https://en.wikipedia.org/wiki/Surrey-Fleetwood)
- [Stephen Taylor: 2024 Surrey-Fleetwood result](https://www.stephentaylor.ca/data/political/canada/provincial/election/bc/2024/325/)
- [338Canada: Surrey-Fleetwood projection](https://338canada.com/bc/1070e.htm)
- [PoliWave: Surrey-Fleetwood model](https://www.poliwave.com/ca/bc/ridings/surrey-fleetwood)
- [City of Surrey: Fleetwood neighbourhood profile](https://www.surrey.ca/sites/default/files/media/documents/Neighbourhood-Profile-Fleetwood.pdf)
- [Surrey Now-Leader: final list of 47 Surrey candidates (Oct 4, 2026)](https://surreynowleader.com/2026/10/04/see-the-final-list-of-47-candidates-in-10-surrey-ridings-for-b-c-election/)
- [Wikipedia: 2026 BC general election poll table (secondary)](https://en.wikipedia.org/wiki/2026_British_Columbia_general_election)
- [SWRBOT: Surrey and White Rock provincial candidates forum (Oct 15, 2026)](https://swrbot.com/events/surrey-and-white-rock-provincial-candidates-forum/)
- [Elections BC: ways to vote](https://elections.bc.ca/voting/ways-to-vote/)
- [Elections BC: who can vote](https://elections.bc.ca/voting/who-can-vote/)
- [Elections BC: voter ID](https://elections.bc.ca/2026-provincial-election/voter-id/)
- [Elections BC home](https://elections.bc.ca/)
- [City of Surrey: 2026 municipal election](https://www.surrey.ca/2026-municipal-election/voters)

</details>

### Geography and data files

- Riding boundaries (2023 redistribution, used for the 2024 and 2026 elections) and postal code lookup: [Open North, Represent API](https://represent.opennorth.ca/api/), boundary set `british-columbia-electoral-districts-2023-redistribution`. Boundaries originate from Elections BC.
- Official candidate list: [Elections BC, 2026 provincial election candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/), copied into `geo/ebc/candidates_min.json` on October 12, 2026.
- Postal code points for the backup lookup: [GeoNames postal code data for Canada](https://download.geonames.org/export/zip/), CC BY 4.0, credit [GeoNames](https://www.geonames.org/). 122,424 BC postal codes, fetched October 12, 2026.
- Fonts: Archivo and Atkinson Hyperlegible (Next and Mono) from [Google Fonts](https://fonts.google.com/), SIL Open Font License, served from this site. PDF export: [jsPDF](https://github.com/parallax/jsPDF) 2.5.1, MIT.
- How the lookup data is built: [`geo/SOURCES.txt`](geo/SOURCES.txt) and `build_geo.py`.

### Research notes in this repository

The working notes the positions and candidate bios were written from, with their own inline citations.

<details>
<summary>27 files</summary>

- [`research/BC 2026 election platforms.md`](research/BC%202026%20election%20platforms.md)
- [`research/notes/centrebc_platform_2026-10-10.md`](research/notes/centrebc_platform_2026-10-10.md)
- [`research/notes/election_landscape.md`](research/notes/election_landscape.md)
- [`research/notes/gap_centrebc_platform.md`](research/notes/gap_centrebc_platform.md)
- [`research/notes/gap_conservative_housing_climate_fiscal.md`](research/notes/gap_conservative_housing_climate_fiscal.md)
- [`research/notes/gap_fleetwood_candidates.md`](research/notes/gap_fleetwood_candidates.md)
- [`research/notes/gap_ndp_forward_positions.md`](research/notes/gap_ndp_forward_positions.md)
- [`research/notes/issues_dripa_sogi_drugs_safety.md`](research/notes/issues_dripa_sogi_drugs_safety.md)
- [`research/notes/issues_health_climate_education_other.md`](research/notes/issues_health_climate_education_other.md)
- [`research/notes/issues_housing_affordability_inequality_economy.md`](research/notes/issues_housing_affordability_inequality_economy.md)
- [`research/notes/legislative_voting_record.md`](research/notes/legislative_voting_record.md)
- [`research/notes/party_bc_conservative.md`](research/notes/party_bc_conservative.md)
- [`research/notes/party_bc_green_and_minor.md`](research/notes/party_bc_green_and_minor.md)
- [`research/notes/party_bc_ndp.md`](research/notes/party_bc_ndp.md)
- [`research/notes/riding_surrey_fleetwood.md`](research/notes/riding_surrey_fleetwood.md)
- [`geo/research/candidates_burnaby_richmond_tricities.json`](geo/research/candidates_burnaby_richmond_tricities.json)
- [`geo/research/candidates_fraser_valley.json`](geo/research/candidates_fraser_valley.json)
- [`geo/research/candidates_interior.json`](geo/research/candidates_interior.json)
- [`geo/research/candidates_island_coast.json`](geo/research/candidates_island_coast.json)
- [`geo/research/candidates_north.json`](geo/research/candidates_north.json)
- [`geo/research/candidates_surrey.json`](geo/research/candidates_surrey.json)
- [`geo/research/candidates_vancouver_northshore.json`](geo/research/candidates_vancouver_northshore.json)
- [`geo/research/local_issues_fraser_valley.md`](geo/research/local_issues_fraser_valley.md)
- [`geo/research/local_issues_interior.md`](geo/research/local_issues_interior.md)
- [`geo/research/local_issues_island_coast.md`](geo/research/local_issues_island_coast.md)
- [`geo/research/local_issues_metro.md`](geo/research/local_issues_metro.md)
- [`geo/research/local_issues_north.md`](geo/research/local_issues_north.md)

</details>

<!-- SOURCES:END -->

## Licence

- Code: [MIT](LICENSE).
- Questions, position summaries, scores, rationales and research notes written for this project: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Credit "BC Vote Helper 2026".
- Party names and logos belong to the parties and identify them.
- Third-party data keeps its own terms: candidate lists and boundaries from Elections BC, the riding lookup from Open North's Represent, postal code points from GeoNames (CC BY 4.0), fonts under the SIL Open Font License, and jsPDF under MIT. See the geography part of the sources.
