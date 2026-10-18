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

### How sources are chosen

Every source is sorted into one of three tiers. [`audit_sources.py`](audit_sources.py) holds the lists and runs before each build.

- **Tier 1, primary:** the party's or candidate's own website, platform and news releases; BC government and budget pages; the Legislature (Hansard, votes, bills); Elections BC; BC Laws; Statistics Canada; poll firms' own releases for poll numbers.
- **Tier 2, news:** established outlets with editors and a corrections policy, such as CBC, CTV, Global, The Canadian Press (including copies on other sites), the Vancouver Sun, Times Colonist, The Tyee, The Narwhal, BIV and BC community papers.
- **Tier 3, extra reading only:** Wikipedia, election aggregator sites, opinion columns and blogs, advocacy groups, partisan outlets and social media posts. These may be listed next to a better source, but never as the only support for a party position, a candidate bio or a voting rule.

The build fails if any party position, party profile or candidate bio has no Tier 1 or Tier 2 source, if a voting rule cites anything other than Elections BC, or if a source comes from a site not yet sorted into a tier. `python -I audit_sources.py --links` also checks every link and lists dead ones.

### Keeping it current

Parties are still announcing promises. Party news pages and the Elections BC candidate list are checked several times a day until voting day. A new announcement changes a position only after it is confirmed on the party's own site or in a Tier 2 outlet. Every change is a commit in this repository, and the date at the top of the quiz shows when the positions were last checked.

The question design, the judgment calls and the audit history are in [`design_notes.md`](design_notes.md). [`audit_scoring.py`](audit_scoring.py) checks schema completeness, an ideal-voter test (each party's own answers must put it first by a clear margin), random-voter bias, how well each question separates the parties, how distinct each pair of parties is, the local formula, and how far the low-confidence and inferred scores move results.

## Languages

The site is available in English, Punjabi (ਪੰਜਾਬੀ), Simplified Chinese (简体中文), Traditional Chinese (繁體中文), Tagalog, French (Français), Russian (Русский), Korean (한국어) and Persian (فارسی, shown right to left). Pick a language from the menu at the top of the page, or add `?lang=` to the address (for example `votebc.vinceroyer.ca/?lang=pa`). On a first visit the site uses your browser's language if it is one of these.

How the translations were made:

- An AI assistant (Anthropic's Claude) translated the questions, answer options, party positions, candidate bios and page text at all five reading levels, following a written brief ([`i18n/BRIEF.txt`](i18n/BRIEF.txt)) and a glossary for each language. Names of people, ridings and places stay in English, as they appear on the ballot.
- A script ([`i18n_check.py`](i18n_check.py)) checks every string: the numbers must have the same values as the English, placeholders must match, the text must be in the right script, and nothing may be left out.
- A second AI model (OpenAI's Codex) then compared every translated string with the English and flagged changed meaning, wrong numbers and wording that treats a party differently from the English. Those fixes were applied ([`i18n_review.py`](i18n_review.py)).
- No native speaker has reviewed the translations yet. The English version is the reference, and every other language says so at the top of the page. Corrections from fluent readers are welcome as GitHub issues.

Scores do not depend on the language: each answer option has the same score in every language. Each translated string stores a fingerprint of the English it was made from. When the English changes, that string shows in English until it is translated again.

## Authorship and AI use

Vincent Royer built this as a side project, first for his own family, then opened it to the public. It has no affiliation with any party, candidate, Elections BC or media outlet, and no one paid for it.

The research, the position summaries, the 0 to 4 scores and the code were produced with an AI assistant (Anthropic's Claude), working from the sources listed below. Separate AI review passes checked the scores against the sources, the wording for loaded language, and the scoring for bias. Automated browser tests check the site. Vincent reviewed the questions, the wording and the results. He did not re-read all 600+ sources himself, which is why every score has a source and a written rationale here for anyone to check.

Data as of October 12, 2026. Parties are still announcing promises, and the televised leaders' debate is on October 14. Positions will be rechecked after the debate, and every change will show in this repository's history.

## Privacy

- No accounts, names, email addresses or tracking cookies. Cloudflare Web Analytics counts visits without cookies. Fonts and scripts are served from this site, so no other company sees your visit. Your progress is saved in your own browser, so a reload keeps your answers.
- Your postal code is used to find your riding and then discarded. The server looks it up with Open North's Represent service, which receives the postal code from the server and never sees your IP address. When Represent is busy or slow, the server answers from its own postal code table instead. The postal code is never stored or logged; request logging is off on the server for this reason. Only the riding code is kept.
- With the "share my answers anonymously" box ticked, the site stores your answers, reading level, riding, page language, and the city and province Cloudflare reports for the connection. No IP address is stored. The IP is used only as a counter key for rate limits.
- Shared answers feed anonymous totals on a private dashboard that only the site owner can open (behind Cloudflare Access).
- All shared answers are deleted automatically on November 23, 2026, 30 days after the election. The cutoff is `DELETE_AFTER` in the Worker config, and a daily scheduled job in [`site/src/worker.js`](site/src/worker.js) runs the delete.
- The quiz is open to visitors connecting from Canada. Search engine and AI crawlers may read the pages from anywhere so the site can show up in search; they cannot reach the answer or riding lookup endpoints. The plain riding and About pages (`/ridings/`, `/about/`, built by `build_seo.py`) are open to everyone.

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
| `build_page.py` | Puts the spec into the template and writes the site to `site/public/`, with one translation file per language in `site/public/i18n/` |
| `i18n/` | Translations: `ui.en.json` (page text in English), `<lang>.spec.json` and `<lang>.ui.json` (translations, each tied to a fingerprint of its English source), a glossary per language, and the translation brief |
| `i18n_strings.py`, `i18n_check.py`, `i18n_review.py`, `i18n_merge.py` | Extract the text to translate, check translations, run the second-model review, merge translations into the files the build reads |
| `site/src/worker.js` | Cloudflare Worker: serves the page, riding lookup, anonymous answer storage, private dashboard API |
| `site/admin_template.html` | Private results dashboard |
| `audit_scoring.py`, `sim_random_voters.py`, `check_local_lengths.py` | Bias and quality checks |
| `audit_sources.py` | Source tier check and link check |
| `gen_sources.py` | Writes the source list below from `quiz_spec.json` |
| `tests/` | Browser tests (Playwright) |
| `make_og.py` | Draws the link-preview image |
| `build_geo.py`, `fetch_fonts.py` | Build the riding lookup files and download the self-hosted fonts |

### Build

```
python -I merge_ridings.py      # only if candidate data changed
python -I build_spec.py         # spec_parts/ -> quiz_spec.json, with validation
python -I audit_scoring.py      # bias checks
python -I audit_sources.py      # source tiers (add --links to check every link)
python -I i18n_strings.py extract   # list the English text to translate
python -I i18n_strings.py status    # per language: translated, out of date, missing
python -I build_page.py         # writes site/public/
python -I gen_sources.py        # refreshes the source list in this README
```

### Deploy

To run your own copy on Cloudflare: copy `site/wrangler.example.toml` to `site/wrangler.toml`, fill in your D1 database id, domain and Cloudflare Access values, run `site/schema.sql` on the database, then run `npx wrangler deploy` from `site/`. A database created before the languages were added also needs `site/migrate_i18n.sql`.

## Sources

Every link the tool uses, generated from `quiz_spec.json` by `gen_sources.py`. Click a section to expand it.

<!-- SOURCES:START -->
**725 unique links.**

### Party positions, question by question

For each question: the sources behind each party's position. The written reason for every score is in `scoring_rationale` in `quiz_spec.json`.

<details>
<summary><b>Which approach should the province take on the cost of living?</b> (Province-wide, <code>q_cost_of_living</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [BC NDP: gas price plan (Oct 1, 2026)](https://www.bcndp.ca/releases/ebys-plan-will-cut-gas-prices-30-cents-litre-crack-down-gouging)
- [BC NDP: ICBC rate freeze to 2030 (Oct 8, 2026)](https://www.bcndp.ca/releases/eby-freeze-car-insurance-rates-another-three-years)
- [Global News: BC pauses $1,000 rebate (Feb 2025)](https://globalnews.ca/news/11017886/bc-pauses-tax-rebate-donald-trump-tariffs/amp)
- [BC Government: Budget 2026 tax changes (5.60% rate, indexation pause)](https://www2.gov.bc.ca/budgettaxchanges)
- [Canadian Press via BOE Report: cost of the fuel tax cut (Oct 1, 2026)](https://boereport.com/2026/10/01/b-c-s-eby-promises-relief-at-gas-pumps-while-conservative-doerkson-praises-pipeline/amp/)
- [Daily Hive: Eby grocery price guard on milk, eggs, cheese, butter and poultry (Oct 2, 2026)](https://dailyhive.com/vancouver/david-eby-grocery-prices-bc)

**BC Conservatives** (basis: platform, confidence: high)

- [Conservative Party of BC: $1,000 tax cut (Oct 8, 2026)](https://conservativebc.ca/conservatives-will-cut-your-taxes-by-1000/)
- [Conservative Party of BC: no new taxes pledge](https://conservativebc.ca/conservative-party-of-bc-pledges-no-new-taxes-on-british-columbians/)
- [Daily Hive: tax cut benefit shape and funding](https://dailyhive.com/vancouver/bc-conservatives-election-annual-income-tax-cut-promise)
- [Abbotsford News (Black Press): temporary PST cut on Canadian alcohol (Sept 29, 2026)](https://abbynews.com/2026/09/29/doerkson-promises-to-cut-pst-on-canadian-alcohol/)
- [Surrey Now-Leader (Black Press): three-year PST break on business machinery and software (Oct 7, 2026)](https://surreynowleader.com/2026/10/07/doerkson-promises-in-surrey-pst-break-for-3-years-for-business-investment/)
- [Canadian Press via Medicine Hat News: Conservative $1,000 tax cut and NDP cost claim (Oct 8, 2026)](https://medicinehatnews.com/news/national-news/2026/10/08/b-c-campaign-trail-conservatives-promise-1000-tax-cut-by-boosting-exemption-level/)
- [Canadian Press via Narcity: economist Ross Hickey on the cost of the tax cuts (Oct 9, 2026)](https://www.narcity.com/tax-talk-a-theme-in-b-c-s-election-campaign)
- [Votes and Proceedings, April 1, 2026 (Bill 2, Budget Measures Implementation Act, 2026, third reading)](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260401.htm)
- [Conservative Party of BC: reverse the Property Tax Deferment Program changes (Oct 9, 2026)](https://conservativebc.ca/conservatives-will-stop-the-ndp-from-taxing-seniors-out-of-their-homes/)
- [Daily Hive: Conservatives promise to reverse property tax deferral changes (Oct 9, 2026)](https://dailyhive.com/vancouver/bc-conservatives-property-tax-deferment-program-promise)

**BC Greens** (basis: platform, confidence: high)

- [BC Greens: Our Plan](https://bcgreens.ca/our-plan/)
- [Global News: Green free transit pledge (Oct 9, 2026)](https://globalnews.ca/news/12097726/bc-leaders-campaign-trail-health-care-supporting-seniors-october-9)
- [BC Greens: plan to end legislated poverty (Oct 6, 2026)](https://bcgreens.ca/announce-plan-to-end-legislated-poverty-and-address-low-assistance-rates/)
- [BC Greens: transit funding and phased free transit (Oct 9, 2026)](https://bcgreens.ca/bc-greens-commit-to-funding-for-fast-frequent-transit-pledge-to-fight-for-province-wide-passenger-rail/)
- [BC Greens: Economic Vision (PDF, Oct 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Economic-Vision.pdf)
- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 6-7, 12-13)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [CentreBC: platform landing page](https://www.centrebc.ca/platform/)

**OneBC** (basis: platform, confidence: high)

- [OneBC priorities](https://1bc.ca/priorities)


</details>

<details>
<summary><b>BC expects to spend about $13.8 billion more than it takes in this year. What should it do?</b> (Province-wide, <code>q_taxes_deficit</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [BC NDP: top-bracket tax proposal (Oct 4, 2026)](https://www.bcndp.ca/releases/build-bc-strong-eby-will-ask-wealthy-pitch-bit-more)
- [BC Budget 2026 and Fiscal Plan](https://www.bcbudget.gov.bc.ca/2026/pdf/2026_Budget_and_Fiscal_Plan.pdf)
- [Moody's rating action, March 2026](https://www2.gov.bc.ca/assets/gov/british-columbians-our-governments/government-finances/debt-management/moodys-ratings-march-2026.pdf)
- [National Newswatch: Eby defends budget after downgrade](https://nationalnewswatch.com/2026/03/19/premier-eby-defends-budget-after-credit-drop-but-opposition-says-b-c-is-going-broke)
- [Fitch rating report: BC downgraded to AA- (2026)](https://www2.gov.bc.ca/assets/gov/british-columbians-our-governments/government-finances/debt-management/fitch-rating-report.pdf)
- [Morningstar DBRS rating report: BC downgraded to AA (April 9, 2026)](https://www2.gov.bc.ca/assets/gov/british-columbians-our-governments/government-finances/debt-management/dbrs-rating-report.pdf)
- [BC Government: First Quarterly Report, deficit forecast $13.8 billion (Sept 14, 2026)](https://news.gov.bc.ca/releases/2026FIN0031-001066)

**BC Conservatives** (basis: both, confidence: medium)

- [Conservative Party of BC: $1,000 tax cut](https://conservativebc.ca/conservatives-will-cut-your-taxes-by-1000/)
- [Canadian Press via Medicine Hat News: tax cut and NDP cost claim (Oct 8, 2026)](https://medicinehatnews.com/news/national-news/2026/10/08/b-c-campaign-trail-conservatives-promise-1000-tax-cut-by-boosting-exemption-level/)
- [Canadian Press via Narcity: economist Ross Hickey on the cost of the tax cuts (Oct 9, 2026)](https://www.narcity.com/tax-talk-a-theme-in-b-c-s-election-campaign)
- [Votes and Proceedings, April 1, 2026 (Bill 2, Budget Measures Implementation Act, 2026, third reading)](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260401.htm)
- [Votes and Proceedings, May 29, 2025 (Supply Act, 2025-2026, third reading)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v250529.htm)
- [Conservative Party of BC: no new taxes pledge (Sept 27, 2026)](https://conservativebc.ca/conservative-party-of-bc-pledges-no-new-taxes-on-british-columbians/)

**BC Greens** (basis: both, confidence: high)

- [BC Greens: Fair Share Act](https://bcgreens.ca/fair-share-act-would-unlock-22-2b-for-childcare-transit-and-housing/)
- [Daily Hive: Green wealth tax details and critiques](https://dailyhive.com/vancouver/bc-greens-wealth-tax-fair-share-act)
- [BC Greens: Fair Share Act FAQ (Oct 11, 2026)](https://bcgreens.ca/the-fair-share-act-faq/)
- [BC Greens: Fair Share Act policy brief (PDF, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Fair-Share-Act-Policy-Brief-2026.pdf)
- [BC Greens: Economic Vision (PDF, Oct 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Economic-Vision.pdf)
- [Votes and Proceedings, March 9, 2026 (Bill 2 second reading)](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260309.htm)
- [Votes and Proceedings, April 1, 2026 (Bill 2, Budget Measures Implementation Act, 2026, third reading)](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260401.htm)
- [Votes and Proceedings, May 29, 2025 (Supply Act, 2025-2026, third reading)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v250529.htm)
- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 4, 11-13, 37)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [CentreBC: 'A Blueprint for Bankruptcy' (February 2026 budget response)](https://www.centrebc.ca/news/budget-2026-a-blueprint-for-bankruptcy/)

**OneBC** (basis: platform, confidence: high)

- [OneBC priorities](https://1bc.ca/priorities)


</details>

<details>
<summary><b>Which approach should the province take on housing costs?</b> (Province-wide, <code>q_housing</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [BC NDP: speculation tax increase and Unsold Condo Tax (Sept 25, 2026)](https://www.bcndp.ca/releases/eby-turn-more-empty-condos-homes-people-can-afford)
- [Votes and Proceedings, November 29, 2023 (Bills 44 and 46)](https://lims.leg.bc.ca/pdms/ldp/42nd4th/votes/v231129.htm)
- [Votes and Proceedings, November 22, 2018 (Bill 45 spec tax)](https://lims.leg.bc.ca/pdms/ldp/41st3rd/votes/v181122.htm)
- [CMHC Rental Market Report (Vancouver vacancy)](https://www.cmhc-schl.gc.ca/professionals/housing-markets-data-and-research/market-reports/rental-market-reports-major-centres)
- [Global News: Metro Vancouver 2025 homeless count](https://globalnews.ca/news/11311816/metro-vancouver-2025-homeless-count)
- [The Tyee: Budget 2026 cancels the 2025 Community Housing Fund call (July 7, 2026)](https://thetyee.ca/News/2026/07/07/BC-Affordable-Homes-Budget-Cuts/)

**BC Conservatives** (basis: both, confidence: medium)

- [Conservative Party of BC: statement on the NDP housing tax plan](https://conservativebc.ca/statement-from-interim-leader-lorne-doerkson-on-the-ndps-housing-tax-plan/)
- [Daily Hive: Conservative Metro Vancouver rollback](https://dailyhive.com/vancouver/bc-conservatives-metro-vancouver-regional-district-reform-platform-promise)
- [Conservative Party of BC: no new taxes pledge (Sept 27, 2026)](https://conservativebc.ca/conservative-party-of-bc-pledges-no-new-taxes-on-british-columbians/)
- [Votes and Proceedings, November 30, 2023 (Bill 47 third reading, unanimous)](https://lims.leg.bc.ca/pdms/ldp/42nd4th/votes/v231130.htm)

**BC Greens** (basis: both, confidence: high)

- [BC Greens: renters plan (Sept 29, 2026)](https://bcgreens.ca/announce-plan-to-support-renters-unveil-two-new-candidates-for-south-island/)
- [Daily Hive: Green vacancy control](https://dailyhive.com/vancouver/bc-greens-vacancy-control-rentals)
- [BC Greens: Our Plan](https://bcgreens.ca/our-plan/)
- [BC Greens: Rights for Renters policy brief (PDF, Sept 2026)](https://bcgreens.ca/wp-content/uploads/2026/09/BC-Greens-Rights-for-Renters-Policy-Brief-2026.pdf)
- [BC Greens: Economic Vision (PDF, Oct 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Economic-Vision.pdf)
- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 7, 12-13, 27)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [CentreBC: platform landing page](https://www.centrebc.ca/platform/)

**OneBC** (basis: platform, confidence: high)

- [OneBC priorities](https://1bc.ca/priorities)


</details>

<details>
<summary><b>Which approach should the province take on access to family doctors, emergency rooms and surgeries?</b> (Province-wide, <code>q_health</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [BC NDP: wait times and diagnostics (Oct 6, 2026)](https://www.bcndp.ca/releases/getting-care-sooner-eby-will-cut-wait-times-add-new-diagnostic-equipment)
- [Global News: leaders on health care and seniors (Oct 9, 2026)](https://globalnews.ca/news/12097726/bc-leaders-campaign-trail-health-care-supporting-seniors-october-9)
- [The Tyee: family doctor crisis figures (May 31, 2026)](https://thetyee.ca/News/2026/05/31/BC-Family-Doctor-Crisis-Gets-Even-Worse/)
- [BCNU: nurse-patient ratios progress (2026)](https://www.bcnu.org/news-and-events/news/2026/minimum-nurse-patient-ratios-focus-bc-nurses-conference)
- [BC NDP: seniors health care plan (Oct 5, 2026)](https://www.bcndp.ca/releases/bc-ndp-seniors-healthcare-plan-free-vaccines-home-care-long-term-care-david-eby)
- [Canadian Press via CFJC Today: NDP 20 clinics and 1,000 training seats (Oct 9, 2026)](https://cfjctoday.com/?p=1128165)
- [BC NDP: Public Health Care Guarantee and agency nurse phase-out (Oct 12, 2026)](https://www.bcndp.ca/releases/eby-will-protect-public-health-care-us-style-privatization)

**BC Conservatives** (basis: both, confidence: medium)

- [Conservative Party of BC: Keep Emergency Rooms Open (Oct 5, 2026)](https://conservativebc.ca/keep-emergency-rooms-open/)
- [Sitka Media: Conservative seniors plan (Oct 9, 2026)](https://www.sitkamedia.ca/watch-bc-conservatives-unveil-plan-to-support-seniors/)
- [Global News 2024: Conservative hybrid health plan (not repeated in 2026)](https://globalnews.ca/news/10631278/bc-conservatives-hybrid-health-care-system)
- [Conservative Party of BC: response on health care (Oct 12, 2026)](https://conservativebc.ca/conservative-party-of-bc-responds-to-the-ndps-tired-health-care-fearmongering/)
- [Votes and Proceedings, December 2, 2025 (Bill 32 third reading)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251202.htm)

**BC Greens** (basis: platform, confidence: high)

- [BC Greens: Our Plan](https://bcgreens.ca/our-plan/)
- [CP24: Greens cite undelivered health commitments](https://www.cp24.com/news/canada/2026/02/09/bc-greens-wont-renew-accord-with-ndp-citing-stalled-undelivered-promises/)
- [BC Greens: community health centres in every riding (Oct 6, 2026)](https://bcgreens.ca/pledge-funding-for-community-health-centres-in-every-riding-support-for-healthcare-workers/)
- [BC Greens: Healthcare policy brief (PDF, Oct 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Healthcare-Policy-Brief-2026.pdf)
- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 14-19)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [CentreBC: 'Healthcare crisis was never a surprise' (June 2026)](https://www.centrebc.ca/news/opinion-healthcare-crisis-was-never-a-surprise/)

**OneBC** (basis: platform, confidence: high)

- [OneBC priorities](https://1bc.ca/priorities)


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
- [Global News: no DRIPA legislation this session (Apr 19, 2026)](https://globalnews.ca/news/11807996/bc-dripa-suspension-legislation/)
- [National Newswatch / CP: First Nations want Bills 14 and 15 killed (May 15, 2025)](https://nationalnewswatch.com/2025/05/15/first-nations-in-b-c-want-new-democrats-to-kill-fast-track-bills)
- [Votes and Proceedings, May 28, 2025 (Bills 14 and 15, third reading)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v250528.htm)

**BC Conservatives** (basis: both, confidence: high)

- [Conservative Party of BC: Repeal DRIPA plan page](https://conservativebc.ca/plan/first-nations-dripa/)
- [The Tyee: Rustad on his 2019 DRIPA vote (Feb 10, 2026)](https://thetyee.ca/News/2026/02/10/First-Nations-Would-Not-Exist-Without-Canada-Rustad/)
- [The Narwhal: DRIPA explainer (repeal would not end duty to consult)](https://thenarwhal.ca/bc-declaration-act-explainer/)
- [Votes and Proceedings, November 19, 2025 (DRIPA Statute Repeal Act, first reading lost 43-48)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251119.htm)
- [Votes and Proceedings, April 22, 2026 (DRIPA Repeal Act, first reading lost 44-47)](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260422.htm)
- [Votes and Proceedings, November 26, 2019 (Bill 41, 82-0)](https://lims.leg.bc.ca/pdms/ldp/41st4th/votes/v191126.htm)
- [CHEK News: Rustad pledges to repeal DRIPA (Jun 9, 2024)](https://www.cheknews.ca/bc-conservatives-want-to-repeal-the-provinces-commitment-to-undrip-1208019/)

**BC Greens** (basis: both, confidence: high)

- [BC Greens: statement on National Day for Truth and Reconciliation (Sep 30, 2026)](https://bcgreens.ca/statement-on-national-day-for-truth-and-reconciliation/)
- [BC Greens: Indigenous Rights Policy Brief 2026 (PDF)](https://bcgreens.ca/wp-content/uploads/2026/09/BC-Greens-Indigenous-Rights-Policy-Brief-2026.pdf)
- [CP24: Lowan on weakening Indigenous rights (Feb 9, 2026)](https://www.cp24.com/news/canada/2026/02/09/bc-greens-wont-renew-accord-with-ndp-citing-stalled-undelivered-promises/)
- [BC Greens: Our Plan](https://bcgreens.ca/our-plan/)
- [Votes and Proceedings, May 28, 2025 (Bills 14 and 15, third reading)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v250528.htm)
- [Votes and Proceedings, April 22, 2026 (DRIPA Repeal Act, first reading lost 44-47)](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260422.htm)
- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 8-9, 32, 35-36)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [CentreBC: Reconciliation, Certainty and Prosperity (Aug 13, 2026, superseded)](https://www.centrebc.ca/news/statement-reconciliation-certainty-and-prosperity/)
- [Votes and Proceedings, November 19, 2025 (DRIPA Statute Repeal Act, first reading lost 43-48)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251119.htm)
- [Votes and Proceedings, April 22, 2026 (DRIPA Repeal Act, first reading lost 44-47)](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260422.htm)

**OneBC** (basis: both, confidence: high)

- [OneBC priorities](https://1bc.ca/priorities)
- [Votes and Proceedings, October 29, 2025 (Property Rights Protection Act, 40-48)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251029.htm)
- [Votes and Proceedings, October 23, 2025 (Land Acknowledgement Prohibition Act, 5-85)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251023.htm)
- [Votes and Proceedings, November 19, 2025 (DRIPA Statute Repeal Act, first reading lost 43-48)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251119.htm)
- [Votes and Proceedings, April 22, 2026 (DRIPA Repeal Act, first reading lost 44-47)](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260422.htm)
- [CKPG Today / CP: Brodie launches OneBC, 'defund the reconciliation industry' (Jun 12, 2025)](https://ckpgtoday.ca/2025/06/12/b-c-independent-mlas-start-new-party-to-combat-the-globalist-assault/)
- [National Newswatch / CP: Rustad ejects Brodie over residential school comments (Mar 7, 2025)](https://nationalnewswatch.com/2025/03/07/bc-conservatives-leader-rustad-ejects-dallas-brodie-over-residential-school-comments)


</details>

<details>
<summary><b>Should the province repeal, step back from, keep or expand SOGI 123, optional school materials on sexual orientation and gender identity?</b> (Province-wide, <code>q_sogi</code>)</summary>

**BC NDP** (basis: both, confidence: medium)

- [CBC via Yahoo: where BC parties stand on SOGI 123 (Sept 28, 2026)](https://ca.news.yahoo.com/where-b-c-provincial-political-130000614.html)
- [Castanet: province ends ARC Foundation funding](https://www.castanetkamloops.net/news/Kamloops/627143/SD73-schools-wont-feel-change-as-province-ends-funding-for-ARC-Foundation-superintendent)
- [Votes and Proceedings, February 26, 2026](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260226.htm)
- [BC Government: access zones in place around schools (May 31, 2024)](https://news.gov.bc.ca/releases/2024ECC0028-000850)

**BC Conservatives** (basis: both, confidence: high)

- [Conservative Party of BC: Safe Schools plan](https://conservativebc.ca/plan/safe-schools/)
- [CBC via Yahoo: where BC parties stand on SOGI 123 (Doerkson on 'arithmetic and reading')](https://ca.news.yahoo.com/where-b-c-provincial-political-130000614.html)
- [Global News: 2024 Conservative platform (SOGI pledges)](https://globalnews.ca/news/10812384/affordability-safety-scrapping-carbon-price-bc-conservatives-full-platform)
- [Rocky Mountain Goat: Conservatives on the Human Rights Code Repeal Act first reading](https://therockymountaingoat.com/2026/03/bird-conservatives-vote-to-give-first-reading-to-human-rights-code-repeal-act/)
- [Votes and Proceedings, February 19, 2026](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260219.htm)
- [Maple Ridge News: Conservatives on letting bills pass first reading (Mar 5, 2026)](https://mapleridgenews.com/2026/03/05/b-c-ndp-allow-armstrong-bill-on-closing-all-consumption-sites-to-pass-1st-reading/)

**BC Greens** (basis: both, confidence: high)

- [CBC via Yahoo: parties on SOGI 123](https://ca.news.yahoo.com/where-b-c-provincial-political-130000614.html)
- [BC Greens: plan to close the inclusive education funding gap (Oct 8, 2026)](https://bcgreens.ca/pledge-to-close-the-inclusive-education-funding-gap-so-every-student-gets-the-support-they-need/)
- [BC Greens: Education Policy Brief 2026 (PDF)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Education-Policy-Brief-2026.pdf)
- [Votes and Proceedings, October 8, 2025 (Protecting Minors from Gender Transition Act, 40-48)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251008.htm)
- [Votes and Proceedings, February 19, 2026 (Gender Ideology and Child Protection Act, 38-49)](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260219.htm)
- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)

**CentreBC** (basis: both, confidence: medium)

- [CBC via Yahoo: parties on SOGI 123](https://ca.news.yahoo.com/where-b-c-provincial-political-130000614.html)
- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 20-24; no SOGI item)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [Penticton Western News: Sturko on why she cannot return to the Conservatives](https://pentictonwesternnews.com/2026/09/22/surreys-elenore-sturko-is-the-sole-incumbent-mla-for-centrebc-ahead-of-election/)

**OneBC** (basis: both, confidence: high)

- [OneBC priorities](https://1bc.ca/priorities)
- [CTV: puberty blocker bill defeated](https://www.ctvnews.ca/vancouver/article/bc-bill-that-would-have-stopped-doctors-from-providing-puberty-blockers-defeated/)
- [CTV: OneBC stands aside for eight Conservatives](https://www.ctvnews.ca/vancouver/article/onebc-pledges-not-to-run-against-eight-principled-bc-conservative-candidates/)
- [Votes and Proceedings, October 8, 2025 (Protecting Minors from Gender Transition Act, 40-48)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251008.htm)
- [Votes and Proceedings, February 19, 2026 (Gender Ideology and Child Protection Act, 38-49)](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260219.htm)
- [CP24 / CP: Armstrong left OneBC in December 2025 (Oct 4, 2026)](https://www.cp24.com/news/canada/2026/10/04/bc-legislator-who-sought-to-repeal-the-human-rights-code-wont-seek-re-election/)


</details>

<details>
<summary><b>BC's toxic drug emergency is ten years old. What approach should the province take now?</b> (Province-wide, <code>q_drugs</code>)</summary>

**BC NDP** (basis: record, confidence: high)

- [National Newswatch / CP: BC ending decriminalization pilot (Jan 14, 2026)](https://nationalnewswatch.com/2026/01/14/b-c-ending-its-3-year-drug-decriminalization-pilot-project)
- [BCCSU: witnessed dosing required for safer supply](https://www.bccsu.ca/blog/news/b-c-to-require-most-drug-users-receiving-safe-supply-to-have-their-doses-witnessed/)
- [Global News: involuntary care provisions found unconstitutional (Jul 31, 2026)](https://globalnews.ca/news/12005744/sections-bc-involuntary-care-rules-found-unconstitutional/)
- [Kelowna Capital News: Eby on involuntary care and supervised sites (Oct 2, 2026)](https://kelownacapnews.com/2026/10/02/eby-announces-b-c-grocery-price-guard-social-disorder-during-kelowna-visit/)
- [CKPG: Prince George involuntary care facility, first 24 beds by December 2027 (Jul 10, 2026)](https://ckpgtoday.ca/2026/07/10/premier-announces-location-of-prince-george-involuntary-care-facility/)
- [BC Government: two facilities to add 132 involuntary care beds (Jul 10, 2026)](https://news.gov.bc.ca/releases/2026HLTH0029-000808)
- [Global News: Eby, 'not returning to decriminalized public drug use' (Jan 6, 2026)](https://globalnews.ca/news/11601344/bc-decriminalized-public-drug-use-premier)
- [The Tyee: witnessed dosing and safer supply enrolment (Feb 21, 2025)](https://thetyee.ca/News/2025/02/21/BC-Restricts-Safer-Supply-Pharmacy-Crackdown/)

**BC Conservatives** (basis: both, confidence: high)

- [Conservative Party of BC: Safe Streets for BC](https://conservativebc.ca/safe-streets-for-bc/)
- [CBC 2024: Conservatives vow to shut consumption sites (not repeated in 2026)](https://amp.cbc.ca/lite/story/1.7331415)
- [Langley Advance Times: Conservative plan on police and drug use in hospitals](https://langleyadvancetimes.com/2026/10/06/b-c-conservatives-plan-to-hire-more-police-stop-illegal-drug-use-in-hospitals-shelters/)
- [Votes and Proceedings, December 2, 2025 (Bill 32, third reading 45-41)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251202.htm)

**BC Greens** (basis: platform, confidence: high)

- [BC Greens Toxic Drugs Policy Brief 2026 (PDF)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Toxic-Drugs-Policy-Brief-2026-1.pdf)
- [BC Greens: toxic drugs policy release with Lisa Lapointe](https://bcgreens.ca/announce-toxic-drugs-policy-alongside-former-chief-coroner-and-candidate-for-saanich-south-lisa-lapointe/)
- [Votes and Proceedings, March 5, 2026 (Drug Recovery and Community Safety Act, first reading 84-2)](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260305.htm)
- [Maple Ridge News: only Greens oppose first reading of consumption site bill (Mar 5, 2026)](https://mapleridgenews.com/2026/03/05/b-c-ndp-allow-armstrong-bill-on-closing-all-consumption-sites-to-pass-1st-reading/)
- [Votes and Proceedings, December 2, 2025 (Bill 32, third reading 45-41)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251202.htm)
- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 18-19, 25-27)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (basis: platform, confidence: high)

- [OneBC priorities](https://1bc.ca/priorities)


</details>

<details>
<summary><b>Which approach should the province take on crime and public safety?</b> (Province-wide, <code>q_public_safety</code>)</summary>

**BC NDP** (basis: both, confidence: medium)

- [BC NDP: gangs, guns and extortion plan (Oct 14, 2026)](https://www.bcndp.ca/releases/eby-targets-gangs-guns-and-extortion)
- [BC NDP: Jewish community security and extremism summit (Oct 5, 2026)](https://www.bcndp.ca/releases/bc-ndp-commits-jewish-community-security-investment-and-summit-confront-organized-hate)
- [Kelowna Capital News: Eby on repeat property offenders (Oct 2, 2026)](https://kelownacapnews.com/2026/10/02/eby-announces-b-c-grocery-price-guard-social-disorder-during-kelowna-visit/)
- [BC Government: Crime Severity Index release (Jul 22, 2026)](https://archive.news.gov.bc.ca/releases/news_releases_2024-2028/2026PSSG0064-000862.htm)
- [Votes and Proceedings, October 25, 2023 (Bill 36)](https://lims.leg.bc.ca/pdms/ldp/42nd4th/votes/v231025.htm)
- [Justice Canada: Eby and federal bail reform (Oct 2025)](https://www.canada.ca/en/department-justice/news/2025/10/minister-fraser-premier-eby-and-attorney-general-sharma-underscore-collaboration-behind-canadas-new-bail-and-sentencing-reforms.html)
- [BC Budget 2025 Backgrounder 5: Making communities stronger, safer](https://www.bcbudget.gov.bc.ca/2025/accessibility/2025_Backgrounder_5.htm)
- [CKPG Today / CP: enforcement teams in 12 communities for repeat violent offenders (Apr 12, 2023)](https://ckpgtoday.ca/2023/04/12/b-c-creates-enforcement-teams-in-12-communities-to-tackle-repeat-violent-offenders/)
- [Energeticcity / CP: law forcing Surrey to go with municipal police (Oct 16, 2023)](https://energeticcity.ca/2023/10/16/b-c-to-bring-in-law-forcing-surrey-to-go-with-municipal-police-force/)
- [City of Surrey: province and Surrey reach police transition agreement (Jul 10, 2024)](https://www.surrey.ca/news-events/news/province-surrey-reach-agreement-police-transition)

**BC Conservatives** (basis: platform, confidence: high)

- [Conservative Party of BC: Safe Streets for BC](https://conservativebc.ca/safe-streets-for-bc/)
- [Conservative Party of BC: crack down on gangs and violent offenders (Oct 13, 2026)](https://conservativebc.ca/conservatives-will-crack-down-on-gangs-and-lock-up-violent-offenders/)
- [Langley Advance Times: Conservative plan to hire more police (Oct 6, 2026)](https://langleyadvancetimes.com/2026/10/06/b-c-conservatives-plan-to-hire-more-police-stop-illegal-drug-use-in-hospitals-shelters/)
- [Fraser Institute: violent crime index commentary](https://www.fraserinstitute.org/commentary/crime-stats-belie-bc-governments-safer-province-claims)
- [Votes and Proceedings, October 25, 2023 (Bill 36, 56-27)](https://lims.leg.bc.ca/pdms/ldp/42nd4th/votes/v231025.htm)

**BC Greens** (basis: platform, confidence: high)

- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)
- [BC Greens Toxic Drugs Policy Brief 2026 (PDF)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Toxic-Drugs-Policy-Brief-2026-1.pdf)
- [Votes and Proceedings, March 5, 2026 (Drug Recovery and Community Safety Act, first reading 84-2)](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260305.htm)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 26-29)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [CentreBC: three-step anti-extortion plan (November 2025, not repeated in the platform)](https://www.centrebc.ca/news/news-release/centrebc-unveils-3-step-plan-to-crush-transnational-extortion-terrorizing-surrey/)
- [CentreBC: leader biography](https://www.centrebc.ca/leader/)
- [Votes and Proceedings, October 25, 2023 (Bill 36, 56-27)](https://lims.leg.bc.ca/pdms/ldp/42nd4th/votes/v231025.htm)

**OneBC** (basis: platform, confidence: medium)

- [OneBC priorities](https://1bc.ca/priorities)


</details>

<details>
<summary><b>With American tariffs and slow growth, what should BC's plan for the economy be?</b> (Province-wide, <code>q_economy_tariffs</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [BC Government: First Quarterly Report 2026-27 (Sept 14, 2026)](https://news.gov.bc.ca/releases/2026FIN0031-001066)
- [BC Government: Look West strategy, delivering major projects faster](https://www2.gov.bc.ca/gov/content/employment-business/look-west-strategy/delivering-major-projects-faster)
- [Votes and Proceedings, May 28, 2025 (Bills 7, 14, 15)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v250528.htm)
- [CTV / CP: LNG Canada Phase 2 and the campaign](https://www.ctvnews.ca/vancouver/article/ebys-election-campaign-gets-lift-from-lng-canada-announcement/)
- [BC NDP: Small Business Tariff & Wildfire Relief Fund and Youth Hiring Tax Credit (Oct 7, 2026)](https://www.bcndp.ca/releases/eby-support-small-businesses-through-trade-war)
- [BC NDP: Built-in-BC and Canada buying rules (Sept 24, 2026)](https://www.bcndp.ca/releases/eby-pledges-new-built-bc-and-canada-buying-rules)
- [BC NDP: double critical mineral exports, concurrent permits (Sept 28, 2026)](https://www.bcndp.ca/releases/eby-double-critical-mineral-exports-expand-port-prince-rupert)
- [BC Government: Ksi Lisims LNG environmental assessment certificate (Sept 15, 2025)](https://news.gov.bc.ca/releases/2025ENV0032-000878)
- [CP24 / Canadian Press: $1.46B in gas revenue forecast errors (Sept 1, 2026)](https://www.cp24.com/news/canada/2026/09/01/bc-confirms-146b-in-gas-revenue-forecast-errors/)

**BC Conservatives** (basis: both, confidence: high)

- [Conservative Party of BC: BC Energy Superpower Plan](https://conservativebc.ca/make-british-columbia-an-energy-superpower/)
- [Conservative Party of BC: Supercharge BC's economy](https://conservativebc.ca/supercharge-british-columbias-economy/)
- [Votes and Proceedings, May 28, 2025 (Conservative nay on Bills 7, 14 and 15)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v250528.htm)
- [Conservative Party of BC: welcome LNG Canada Phase 2 (Sept 29, 2026)](https://conservativebc.ca/bc-conservatives-welcome-lng-canada-phase-2-we-will-treat-energy-as-an-urgent-mission/)
- [Conservative Party of BC: First Job Tax Credit (Oct 10, 2026)](https://conservativebc.ca/conservatives-will-give-young-british-columbians-a-reason-to-stay/)
- [BOE Report / Canadian Press: Doerkson welcomes Pacific Link pipeline (Oct 1, 2026)](https://boereport.com/2026/10/01/b-c-s-eby-promises-relief-at-gas-pumps-while-conservative-doerkson-praises-pipeline/)
- [CFJC Today / Canadian Press: Eby walks back tariff bill; Conservatives call it undemocratic (Mar 28, 2025)](https://cfjctoday.com/2025/03/28/b-c-premier-david-eby-walking-back-tariff-bill-after-anxiety-from-stakeholders/)

**BC Greens** (basis: platform, confidence: high)

- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)
- [BC Greens: Economic Vision (PDF)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Economic-Vision.pdf)
- [BC Greens: Our Plan](https://bcgreens.ca/our-plan/)
- [BC Greens: support renewables, not Bill 14 as drafted](https://bcgreens.ca/bc-greens-support-renewable-energy-not-bill-14-as-currently-drafted/)
- [BC Greens: Forestry Policy Brief (Oct 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Forestry-Policy-Brief-2026.pdf)
- [BC Greens: Climate, LNG and Royalties Policy Brief (Oct 10, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Climate-LNG-and-Royalties-Policy-Brief-2026.pdf)
- [Votes and Proceedings, May 28, 2025 (Bills 7, 14, 15)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v250528.htm)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 8-10, 13, 36-37)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [Surrey Now-Leader: Sturko promises manufacturing boost (Oct 9, 2026)](https://surreynowleader.com/2026/10/09/centrebc-leader-promisesmanufacturing-boost)
- [CentreBC: pipeline conditions (Jul 7, 2026)](https://www.centrebc.ca/news/ottawa-and-bc-just-moved-toward-centrebc-pipeline-conditions/)

**OneBC** (basis: platform, confidence: medium)

- [OneBC priorities](https://1bc.ca/priorities)


</details>

<details>
<summary><b>What direction should BC take on climate change and energy?</b> (Province-wide, <code>q_climate_energy</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [The Tyee: BC admits 2030 climate goal out of reach (May 2025)](https://thetyee.ca/News/2025/05/01/BC-Admits-Climate-Goals/)
- [CBC: BC ends consumer carbon tax (April 2025)](https://www.cbc.ca/lite/story/1.7493181)
- [National Newswatch: BC to redraw EV mandate, scrapping the 100% by 2035 goal (Nov 2025)](https://nationalnewswatch.com/2025/11/18/b-c-to-redraw-ev-sales-mandate-scrapping-goal-of-100-per-cent-by-2035)
- [BC NDP: LNG capacity figures (Sept 28, 2026)](https://www.bcndp.ca/releases/bc-conservatives-lng-plan-out-step-reality)
- [CTV: Eby open to pipeline if tanker ban remains (2025)](https://www.ctvnews.ca/politics/article/bc-premier-open-to-new-pipeline-if-tanker-ban-remains-in-place/)
- [BC Government: B.C. eliminates carbon tax, output-based pricing stays (Mar 31, 2025)](https://news.gov.bc.ca/releases/2025FIN0014-000280)
- [BOE Report / Canadian Press: Eby promises temporary 10-cent fuel tax cut (Oct 1, 2026)](https://boereport.com/2026/10/01/b-c-s-eby-promises-relief-at-gas-pumps-while-conservative-doerkson-praises-pipeline/)
- [BC Government: 2035 ZEV sales target cut from 100% to 75% (Apr 1, 2026)](https://news.gov.bc.ca/releases/2026ECS0009-000355)
- [BC NDP: Build BC Strong plan page (climate and costing items, Oct 2026)](https://www.bcndp.ca/plan)

**BC Conservatives** (basis: both, confidence: medium)

- [Conservative Party of BC: BC Energy Superpower Plan](https://conservativebc.ca/make-british-columbia-an-energy-superpower/)
- [Conservative Party of BC: welcome LNG Canada Phase 2](https://conservativebc.ca/bc-conservatives-welcome-lng-canada-phase-2-we-will-treat-energy-as-an-urgent-mission/)
- [Conservative Party of BC: Supercharge BC's economy (permitting, environmental standards)](https://conservativebc.ca/supercharge-british-columbias-economy/)
- [BOE Report / Canadian Press: Doerkson welcomes Pacific Link pipeline (Oct 1, 2026)](https://boereport.com/2026/10/01/b-c-s-eby-promises-relief-at-gas-pumps-while-conservative-doerkson-praises-pipeline/)
- [CFJC Today / Canadian Press: Rustad on the 'punishing' industrial carbon tax (Mar 31, 2025)](https://cfjctoday.com/2025/03/31/b-c-government-tables-bill-to-end-consumer-carbon-tax/)
- [CBC: 2024 platforms compared (Conservatives would end the carbon tax and low carbon fuel standard)](https://newsinteractives.cbc.ca/features/2024/british-columbia-party-platforms/)

**BC Greens** (basis: both, confidence: high)

- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)
- [BC Greens: Our Plan](https://bcgreens.ca/our-plan/)
- [BC Greens: Economic Vision (PDF)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Economic-Vision.pdf)
- [BC Greens: Climate, LNG and Royalties Policy Brief (Oct 10, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Climate-LNG-and-Royalties-Policy-Brief-2026.pdf)
- [BC Greens: new royalty framework and Pacific Link opposition (Oct 10, 2026)](https://bcgreens.ca/new-royalty-framework-accountability-for-fossil-fuel-corporations-getting-b-c-back-on-track-on-climate-proposed-by-bc-greens/)
- [National Newswatch / Canadian Press: Botterell lone vote against carbon tax bill at first reading (Mar 31, 2025)](https://nationalnewswatch.com/2025/03/31/b-c-legislature-back-in-session-government-tables-bill-to-end-consumer-carbon-tax)
- [Votes and Proceedings, May 28, 2025 (Bills 14, 15)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v250528.htm)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 8, 11, 30-33, 39)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [CentreBC: Ottawa and BC moved toward CentreBC pipeline conditions (Jul 2026)](https://www.centrebc.ca/news/ottawa-and-bc-just-moved-toward-centrebc-pipeline-conditions/)

**OneBC** (basis: inferred, confidence: low)

- [OneBC priorities](https://1bc.ca/priorities)


</details>

<details>
<summary><b>What should the province's priorities be for child care and for schools from kindergarten to Grade 12?</b> (Province-wide, <code>q_education_childcare</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [Global News: $10-a-day program paused (Feb 2026)](https://globalnews.ca/news/11673463/10-a-day-daycare-program-paused/)
- [Global News: Surrey schools and the NDP's building record](https://globalnews.ca/news/11350841/surrey-schools-ndp-building)
- [BC Government: more than 16,000 $10-a-day spaces (Mar 24, 2025)](https://news.gov.bc.ca/releases/2025ECC0015-000242)
- [BC Budget 2026: Budget and Fiscal Plan (child care $330 million, school capital)](https://www.bcbudget.gov.bc.ca/2026/pdf/2026_Budget_and_Fiscal_Plan.pdf)
- [BC NDP: more affordable child care for BC families (Oct 17, 2026)](https://www.bcndp.ca/releases/bc-ndp-deliver-more-affordable-child-care-bc-families)

**BC Conservatives** (basis: both, confidence: low)

- [Conservative Party of BC: Safe Schools plan](https://conservativebc.ca/plan/safe-schools/)
- [Global News: 2024 Conservative education plan (letter grades Grades 4-9, exams Grades 10 and 12) (Oct 14, 2024)](https://globalnews.ca/news/10810503/bc-election-conservative-education)

**BC Greens** (basis: platform, confidence: high)

- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)
- [BC Greens: lift the freeze on $10-a-day, universal free child care by 2031](https://bcgreens.ca/announce-plan-to-lift-the-freeze-on-10-a-day-daycare-with-universal-free-child-care-by-2031-alongside-new-candidate-for-victoria-swan-lake/)
- [BC Greens: Childcare Policy Brief (Sept 2026)](https://bcgreens.ca/wp-content/uploads/2026/09/BC-Greens-Childcare-Policy-Brief-2026.pdf)
- [BC Greens: Education Policy Brief (Oct 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Education-Policy-Brief-2026.pdf)
- [BC Greens: close the inclusive education funding gap (Oct 8, 2026)](https://bcgreens.ca/pledge-to-close-the-inclusive-education-funding-gap-so-every-student-gets-the-support-they-need/)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 6, 20-24, 40-41)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [CentreBC: AI strategy vacuum (Jun 2026)](https://www.centrebc.ca/news/ai-strategy-vacuum/)

**OneBC** (basis: platform, confidence: high)

- [OneBC priorities](https://1bc.ca/priorities)


</details>

<details>
<summary><b>Should BC keep no-fault car insurance, bring back lawsuits for serious injuries, or open insurance to competition?</b> (Province-wide, <code>q_icbc</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [BC NDP: ICBC rate freeze to 2030 (Oct 8, 2026)](https://www.bcndp.ca/releases/eby-freeze-car-insurance-rates-another-three-years)
- [BC Government: ICBC rate freeze to spring 2027, $496 average saving, $2.7B rebates (Oct 28, 2025)](https://news.gov.bc.ca/releases/2025AG0063-001064)
- [ICBC 2025/26 Service Plan (about $5 billion in pre-2021 claims still to settle)](https://bcbudget.gov.bc.ca/2025/sp/pdf/agency/icbc.pdf)

**BC Conservatives** (basis: platform, confidence: medium)

- [Global News: Conservative plan to end no-fault (leaked letter)](https://globalnews.ca/news/12090331/bc-conservatives-plan-no-fault-insurance-repeal/)
- [CP24: leaked letter details (Oct 6, 2026)](https://www.cp24.com/news/canada/2026/10/06/bc-conservatives-plan-to-end-no-fault-insurance-leaked-letter-shows/)
- [Conservative Party of BC: Insurance plan page](https://conservativebc.ca/plan/insurance/)
- [Daily Hive: Conservative ICBC letter, minor-injury limits and private competition (Oct 6, 2026)](https://dailyhive.com/vancouver/bc-conservatives-icbc-no-fault-insurance-system-changes-platform)

**BC Greens** (basis: platform, confidence: medium)

- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)

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
- [BC Government: 2017 donation ban release](https://news.gov.bc.ca/releases/2017PREM0084-001592)
- [BC Government: Order in Council 321/2025, Bill 14 regulation adds all wind and solar projects (June 27, 2025)](https://www.alc.gov.bc.ca/assets/alc/assets/legislation-and-regulation/the-act-and-regulation/oic_321_2025_bill_14_regulation.pdf)
- [Global News: Angus Reid, two-thirds say the election is 'too soon' (Sept 25, 2026)](https://globalnews.ca/news/12073073/bc-conservatives-ahead-ndp-snap-election-poll/)
- [Daily Hive: Leger, 57% disapprove of the early election (Sept 2026)](https://dailyhive.com/vancouver/bc-election-ndp-conservatives-survey-september-2026-leger)
- [The Tyee: north coast line exempted from environmental assessment and BCUC review (Sept 4, 2026)](https://thetyee.ca/News/2026/09/04/Old-Growth-Chopping-Block-North-Coast-Transmission-Line/)
- [Votes and Proceedings, Nov 29, 2023 (time allocation on Bill 44)](https://lims.leg.bc.ca/pdms/ldp/42nd4th/votes/v231129.htm)
- [Votes and Proceedings, May 28, 2025 (Bills 7, 14, 15)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v250528.htm)

**BC Conservatives** (basis: both, confidence: medium)

- [Conservative Party of BC: Supercharge BC's economy (permitting act, red tape law)](https://conservativebc.ca/supercharge-british-columbias-economy/)
- [Votes and Proceedings, May 28, 2025](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v250528.htm)
- [Daily Hive: Metro Vancouver rollback](https://dailyhive.com/vancouver/bc-conservatives-metro-vancouver-regional-district-reform-platform-promise)
- [CFJC Today / Canadian Press: Rustad and the party on Bill 7 (Mar 28, 2025)](https://cfjctoday.com/2025/03/28/b-c-premier-david-eby-walking-back-tariff-bill-after-anxiety-from-stakeholders/)
- [Global News: 2024 Conservative platform (voter approval for new taxes)](https://globalnews.ca/news/10812384/affordability-safety-scrapping-carbon-price-bc-conservatives-full-platform)

**BC Greens** (basis: both, confidence: high)

- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)
- [BC Greens: Our Plan (proportional representation)](https://bcgreens.ca/our-plan/)
- [CBC: 2018 electoral reform referendum results](https://www.cbc.ca/news/canada/british-columbia/electoral-reform-referendum-results-1.4954538)
- [Castanet: Greens will not back vague infrastructure bill](https://www.castanetkamloops.net/news/BC/549318/B-C-Greens-wont-back-governments-vague-infrastructure-bill)
- [Votes and Proceedings, May 28, 2025 (Bills 7, 14, 15)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v250528.htm)
- [National Newswatch / Canadian Press: Greens won't renew accord with NDP (Feb 9, 2026)](https://nationalnewswatch.com/2026/02/09/bc-greens-wont-renew-accord-with-ndp-citing-stalled-or-undelivered-commitments)

**CentreBC** (basis: platform, confidence: medium)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 34-37, 39-41)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [Penticton Western News: Sturko on the snap election](https://pentictonwesternnews.com/2026/09/22/surreys-elenore-sturko-is-the-sole-incumbent-mla-for-centrebc-ahead-of-election/)

**OneBC** (basis: platform, confidence: low)

- [Global News: Brodie pledges to end mail-in and early voting (June 12, 2025)](https://globalnews.ca/news/11238390/dallas-brodie-onebc/)
- [OneBC priorities](https://1bc.ca/priorities)


</details>

<details>
<summary><b>How should the province finish the SkyTrain line and fund TransLink, the regional transit agency, after 2028?</b> (Regional: Surrey, <code>q_local_skytrain</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [Surrey-Langley SkyTrain monthly status report (April 2026)](https://surreylangleyskytrain.gov.bc.ca/app/uploads/sites/938/2026/06/SLS_Monthly-Status-Report_April_2026.pdf)
- [Daily Hive: Eby rules out TransLink vehicle levy (Oct 2, 2026)](https://dailyhive.com/vancouver/bc-ndp-david-eby-translink-vehicle-levy)
- [Jagrup Brar campaign page (party-authored)](https://jagrupbrar.bcndp.ca)
- [BC Gov News: all eight Surrey-Langley SkyTrain stations under construction (May 8, 2026)](https://news.gov.bc.ca/releases/2026TT0022-000515)
- [Global News: TransLink gets $479 million in surplus money (March 15, 2023)](https://globalnews.ca/news/9553930/translink-funding-bc-government)
- [BC NDP: getting around Surrey more easily and affordably (Oct 15, 2026)](https://www.bcndp.ca/releases/eby-will-help-people-surrey-get-around-more-easily-affordably)

**BC Conservatives** (basis: both, confidence: low)

- [Global News: Surrey-Langley SkyTrain cost rises to $6B, Rustad on getting it done affordably (Aug 2024)](https://globalnews.ca/news/10701039/surrey-langley-skytrain-cost)
- [Daily Hive: Metro Vancouver rollback](https://dailyhive.com/vancouver/bc-conservatives-metro-vancouver-regional-district-reform-platform-promise)
- [Global News: Rustad calls the $6 billion line a debacle (Aug 2024)](https://globalnews.ca/news/10702469/surrey-langley-skytrain-delay-cost-reaction/amp)
- [Conservative Party of BC: Eby must answer on secret vehicle tax plan (Oct 2, 2026)](https://conservativebc.ca/eby-must-answer-on-secret-vehicle-tax-plan/)
- [CP24: Doerkson pledges no new or higher taxes (Sept 28, 2026)](https://www.cp24.com/news/canada/2026/09/28/bc-election-campaigns-enter-second-week-with-candidate-policy-announcements/)

**BC Greens** (basis: platform, confidence: medium)

- [Global News: Green free transit pledge (Oct 9, 2026)](https://globalnews.ca/news/12097726/bc-leaders-campaign-trail-health-care-supporting-seniors-october-9)
- [BC Greens: Our Plan](https://bcgreens.ca/our-plan/)
- [BC Greens: Tim Binnema candidate page](https://bcgreens.ca/candidates/tim-binnema/)
- [BC Greens: funding for fast, frequent transit and passenger rail (Oct 9, 2026)](https://bcgreens.ca/bc-greens-commit-to-funding-for-fast-frequent-transit-pledge-to-fight-for-province-wide-passenger-rail/)
- [BC Greens: Transit and Transportation Policy Brief 2026 (PDF, Oct 9, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Transit-and-Transportation-Policy-Brief-2026.pdf)
- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)

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

- [BC NDP: gangs, guns and extortion plan (Oct 14, 2026)](https://www.bcndp.ca/releases/eby-targets-gangs-guns-and-extortion)
- [Surrey Police Service: extortion statistics](https://www.surreypolice.ca/extortions)
- [Global News: Surrey extortion cases, Eby wants more arrests (Jan 2026)](https://globalnews.ca/news/11615290/extortion-cases-surrey-2026)
- [Votes and Proceedings, October 25, 2023 (Bill 36)](https://lims.leg.bc.ca/pdms/ldp/42nd4th/votes/v231025.htm)
- [Surrey Police Service: transition timeline (July 2026)](https://www.surreypolice.ca/sites/default/files/media/documents/Policing%20Transition%20Timeline_july2026.pdf)
- [BC Ballot: Jagrup Brar voting record](https://bcballot.ca/mlas/jagrup-brar/)
- [BC Gov News: five new members appointed to the Surrey Police Board (March 23, 2026)](https://news.gov.bc.ca/releases/2026PSSG0023-000299)
- [Peace Arch News: five new Surrey police board appointees; vacancies by mayor and minister agreement (March 24, 2026)](https://peacearchnews.com/2026/03/24/five-new-surrey-police-board-appointees-named/)
- [BC Gov News: trilateral summit, $1 million for extortion victims shared with Ottawa (Nov 28, 2025)](https://news.gov.bc.ca/stories/trilateral-summit-brings-leaders-together-to-combat-extortion-and-organized-crime)

**BC Conservatives** (basis: platform, confidence: medium)

- [Conservative Party of BC: crack down on gangs and violent offenders (Oct 13, 2026)](https://conservativebc.ca/conservatives-will-crack-down-on-gangs-and-lock-up-violent-offenders/)
- [Conservative Party of BC: Safe Streets for BC](https://conservativebc.ca/safe-streets-for-bc/)
- [Conservative Party of BC: Surrey candidates announcement (Sept 29, 2026)](https://conservativebc.ca/conservative-party-of-bc-announces-strong-surrey-candidates-for-serious-times/)
- [Conservative Party of BC: Garry Purewal candidate page](https://conservativebc.ca/candidate/garry-purewal/)

**BC Greens** (no published position)

- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)
- [BC Greens: Tim Binnema candidate page](https://bcgreens.ca/candidates/tim-binnema/)

**CentreBC** (basis: platform, confidence: medium)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 26-29)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [CentreBC: three-step anti-extortion plan (November 2025, not repeated in the platform)](https://www.centrebc.ca/news/news-release/centrebc-unveils-3-step-plan-to-crush-transnational-extortion-terrorizing-surrey/)
- [CentreBC: Paul Brar candidate page](https://centrebc.ca/candidates/paul-brar/)
- [CentreBC: leader biography](https://www.centrebc.ca/leader/)
- [Votes and Proceedings, October 25, 2023 (Bill 36)](https://lims.leg.bc.ca/pdms/ldp/42nd4th/votes/v231025.htm)

**OneBC** (basis: platform, confidence: medium)

- [OneBC priorities](https://1bc.ca/priorities)
- [OneBC: Carolyn Hofbauer candidate page](https://1bc.ca/candidates/chofbauer)


</details>

<details>
<summary><b>How should the province handle Surrey's new hospital under construction, its busy emergency room and its crowded schools?</b> (Regional: Surrey, <code>q_local_hospital_schools</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [Indo-Canadian Voice: Doerkson has no answer on Surrey hospital, Brar on progress (Oct 7, 2026)](https://voiceonline.com/doerkson-has-no-answer-on-surrey-hospital-more-than-halfway-built-bc-ndp/)
- [Global News: Surrey schools and the NDP's building record](https://globalnews.ca/news/11350841/surrey-schools-ndp-building)
- [Surrey Now-Leader: Eby promises more doctors in Surrey (Oct 9, 2026)](https://surreynowleader.com/2026/10/09/b-c-election-battleground-in-surrey-eby-promises-more-doctors-to-fast-track-intl-grads/)
- [CTV: new Surrey hospital cost and 2030 opening](https://guelph.ctvnews.ca/vancouver/article/new-surrey-hospital-will-cost-1b-more-than-planned-wont-open-until-2030)
- [Jagrup Brar campaign page (party-authored)](https://jagrupbrar.bcndp.ca)
- [Fraser Health: second Surrey hospital breaks ground, $2.88 billion, open 2030 (Sept 12, 2023)](https://www.fraserhealth.ca/news/2023/Sep/second-hospital-new-cancer-centre-breaks-ground-in-surrey)
- [CFJC Today (Canadian Press): Eby promises 20 clinics and 1,000 training seats (Oct 9, 2026)](https://cfjctoday.com/?p=1128165)
- [Daily Hive: NDP promises eight MRI machines and 10 CT scanners (Oct 6, 2026)](https://dailyhive.com/vancouver/bc-ndp-surgery-medical-wait-times)
- [BC Gov News: 60 mental health beds with involuntary capacity in Surrey (Sept 4, 2026)](https://news.gov.bc.ca/releases/2026HLTH0034-001028)
- [CBC: Horgan promises to rid Surrey schools of portables within four years (Aug 31, 2016)](https://www.cbc.ca/lite/story/1.3742047)
- [CBC: B.C. school portables survey, Surrey has 361 (Sept 16, 2023)](https://www.cbc.ca/lite/story/1.6967543)
- [BC NDP: Doerkson hiding plans on Massey and health care (Oct 15, 2026)](https://www.bcndp.ca/releases/doerkson-hiding-his-plans-cancel-massey-replacement-cut-healthcare)

**BC Conservatives** (basis: platform, confidence: medium)

- [Indo-Canadian Voice: Doerkson on the Surrey hospital (Oct 7, 2026)](https://voiceonline.com/doerkson-has-no-answer-on-surrey-hospital-more-than-halfway-built-bc-ndp/)
- [Conservative Party of BC: Keep Emergency Rooms Open](https://conservativebc.ca/keep-emergency-rooms-open/)
- [Sitka Media: Conservative seniors plan](https://www.sitkamedia.ca/watch-bc-conservatives-unveil-plan-to-support-seniors/)
- [Conservative Party of BC: Garry Purewal candidate page](https://conservativebc.ca/candidate/garry-purewal/)
- [Conservative Party of BC: response on health care (Oct 12, 2026)](https://conservativebc.ca/conservative-party-of-bc-responds-to-the-ndps-tired-health-care-fearmongering/)
- [Conservative Party of BC: new Massey bridge and new hospital in Surrey (Oct 15, 2026)](https://conservativebc.ca/conservatives-will-build-a-new-massey-bridge-and-new-hospital-in-surrey/)

**BC Greens** (basis: platform, confidence: medium)

- [BC Greens: Tim Binnema candidate page](https://bcgreens.ca/candidates/tim-binnema/)
- [BC Greens: Community Health Centres in every riding (Oct 6, 2026)](https://bcgreens.ca/pledge-funding-for-community-health-centres-in-every-riding-support-for-healthcare-workers/)
- [BC Greens: close the inclusive education funding gap (Oct 8, 2026)](https://bcgreens.ca/pledge-to-close-the-inclusive-education-funding-gap-so-every-student-gets-the-support-they-need/)
- [BC Greens: child care plan with an early childhood educator wage grid](https://bcgreens.ca/announce-plan-to-lift-the-freeze-on-10-a-day-daycare-with-universal-free-child-care-by-2031-alongside-new-candidate-for-victoria-swan-lake/)
- [BC Greens: Our Plan (Fair Share Act for public schools)](https://bcgreens.ca/our-plan/)
- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)

**CentreBC** (basis: platform, confidence: medium)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 17-19, 21, 24)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [CentreBC: Paul Brar candidate page](https://centrebc.ca/candidates/paul-brar/)

**OneBC** (basis: platform, confidence: medium)

- [OneBC priorities](https://1bc.ca/priorities)
- [OneBC: Carolyn Hofbauer candidate page](https://1bc.ca/candidates/chofbauer)


</details>

<details>
<summary><b>TransLink says it needs at least $112 million a year in new money from 2028. What should the province do about transit in Metro Vancouver?</b> (Regional: Metro Vancouver, <code>q_local_metro_translink</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [Daily Hive: Eby rules out TransLink vehicle levy (Oct 2, 2026)](https://dailyhive.com/vancouver/bc-ndp-david-eby-translink-vehicle-levy)
- [Sitka Media: TransLink calls for stable funding plan after NDP rules out levy (Oct 2, 2026)](https://www.sitkamedia.ca/translink-calls-for-stable-funding-plan-after-bc-ndp-says-vehicle-levy-road-pricing-off-the-table/)
- [Daily Hive: NDP fuel tax cut pledge (Oct 1, 2026)](https://dailyhive.com/vancouver/bc-gas-prices-david-eby-election-2026)
- [Global News: TransLink gets $479 million in surplus money (March 15, 2023)](https://globalnews.ca/news/9553930/translink-funding-bc-government)
- [BC NDP: Eby will expand transit (Oct 14, 2026)](https://www.bcndp.ca/releases/eby-expand-transit-get-people-where-they-need-go-faster)
- [BC NDP: getting around Surrey more easily and affordably (Oct 15, 2026)](https://www.bcndp.ca/releases/eby-will-help-people-surrey-get-around-more-easily-affordably)

**BC Conservatives** (basis: platform, confidence: medium)

- [Conservative Party of BC: Eby must answer on secret vehicle tax plan (Oct 2, 2026)](https://conservativebc.ca/eby-must-answer-on-secret-vehicle-tax-plan/)
- [Conservative Party of BC: Delivering essential services and cutting waste at Metro Vancouver (Oct 5, 2026)](https://conservativebc.ca/conservative-platform-delivering-essential-services-and-cutting-waste-at-metro-vancouver/)
- [Conservative Party of BC: Support BC's seniors (Oct 9, 2026)](https://conservativebc.ca/support-bcs-seniors/)
- [CP24: campaigns enter second week, no new taxes pledge (Sept 28, 2026)](https://www.cp24.com/news/canada/2026/09/28/bc-election-campaigns-enter-second-week-with-candidate-policy-announcements/)

**BC Greens** (basis: platform, confidence: medium)

- [BC Greens: Transit and Transportation Policy Brief 2026 (PDF, Oct 9, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Transit-and-Transportation-Policy-Brief-2026.pdf)
- [BC Greens: funding for fast, frequent transit and passenger rail (Oct 9, 2026)](https://bcgreens.ca/bc-greens-commit-to-funding-for-fast-frequent-transit-pledge-to-fight-for-province-wide-passenger-rail/)
- [Daily Hive: reaction to Eby fuel tax promise (Oct 2, 2026)](https://dailyhive.com/vancouver/b-c-reacts-eby-promise-slash-gas-prices)
- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)

**CentreBC** (basis: platform, confidence: medium)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 11, 13)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (no published position)

- [OneBC priorities](https://1bc.ca/priorities)


</details>

<details>
<summary><b>A 2025 ruling recognized Cowichan title over Richmond land with private homes. How should the province handle homeowners and title claims?</b> (Regional: Metro Vancouver, <code>q_local_metro_title_homes</code>)</summary>

**BC NDP** (basis: record, confidence: medium)

- [The Narwhal: BC election 2026 and DRIPA (Oct 7, 2026)](https://thenarwhal.ca/bc-election-2026-dripa)
- [Angus Reid: BC, Musqueam and Cowichan, property rights (March 2026)](https://angusreid.org/bc-eby-musqueam-cowichan-property-rights-conservative-leadership/)

**BC Conservatives** (basis: both, confidence: medium)

- [Conservative Party of BC: Repeal DRIPA, Promote Economic Reconciliation (Oct 7, 2026)](https://conservativebc.ca/plan/first-nations-dripa/)
- [Lorne Doerkson on X: repeal DRIPA, protect property rights (Oct 7, 2026)](https://x.com/LDoerkson/status/2108048609283645690)
- [Votes and Proceedings, October 29, 2025 (Property Rights Protection Act)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251029.htm)

**BC Greens** (basis: platform, confidence: medium)

- [BC Greens: statement on the National Day for Truth and Reconciliation (Sept 30, 2026)](https://bcgreens.ca/statement-on-national-day-for-truth-and-reconciliation/)
- [BC Greens: Indigenous Rights Policy Brief 2026 (PDF)](https://bcgreens.ca/wp-content/uploads/2026/09/BC-Greens-Indigenous-Rights-Policy-Brief-2026.pdf)
- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 35-36)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (basis: platform, confidence: medium)

- [OneBC priorities](https://1bc.ca/priorities)
- [OneBC on X: repeal DRIPA, defund the reconciliation industry (Sept 26, 2026)](https://x.com/One_BCHQ/status/2103913099086684163)
- [Votes and Proceedings, October 29, 2025 (Property Rights Protection Act)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251029.htm)


</details>

<details>
<summary><b>Sixteen Metro Vancouver mayors want the 2023 density laws undone. Keep the rules, add to them, or give councils back the say?</b> (Regional: Metro Vancouver, <code>q_local_metro_density</code>)</summary>

**BC NDP** (basis: record, confidence: high)

- [Daily Hive: Metro Vancouver mayors ask province to unwind housing laws (Dec 13, 2025)](https://dailyhive.com/vancouver/metro-vancouver-mayors-bc-housing-legislation-opposition-letter)
- [Votes and Proceedings, November 29, 2023 (Bills 44 and 46)](https://lims.leg.bc.ca/pdms/ldp/42nd4th/votes/v231129.htm)
- [BC NDP: turn more empty condos into homes (Sept 25, 2026)](https://www.bcndp.ca/releases/eby-turn-more-empty-condos-homes-people-can-afford)

**BC Conservatives** (basis: inferred, confidence: low)

- [Global News: Conservative housing plan would scrap density rules (Sept 27, 2024)](https://globalnews.ca/news/10779404/bc-election-conservative-rustad-housing-policy)
- [Conservative Party of BC: statement on the NDP housing tax plan (Sept 25, 2026)](https://conservativebc.ca/statement-from-interim-leader-lorne-doerkson-on-the-ndps-housing-tax-plan/)
- [Conservative Party of BC: Metro Vancouver plan (Oct 5, 2026)](https://conservativebc.ca/conservative-platform-delivering-essential-services-and-cutting-waste-at-metro-vancouver/)

**BC Greens** (basis: both, confidence: medium)

- [Votes and Proceedings, November 29, 2023 (Bills 44 and 46)](https://lims.leg.bc.ca/pdms/ldp/42nd4th/votes/v231129.htm)
- [BC Greens: Our Plan](https://bcgreens.ca/our-plan/)
- [BC Greens: Rights for Renters Policy Brief 2026 (PDF, Sept 29, 2026)](https://bcgreens.ca/wp-content/uploads/2026/09/BC-Greens-Rights-for-Renters-Policy-Brief-2026.pdf)
- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)

**CentreBC** (basis: platform, confidence: medium)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 7, 11, 13)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (no published position)

- [OneBC priorities](https://1bc.ca/priorities)
- [BC Ballot: housing issue page (party commitments and votes)](https://bcballot.ca/platforms/issues/housing/)


</details>

<details>
<summary><b>The province proposed letting food plants use some lower-quality land in the Agricultural Land Reserve. What should happen?</b> (Regional: Fraser Valley, <code>q_local_fraser_valley_farmland</code>)</summary>

**BC NDP** (basis: both, confidence: medium)

- [BC Gov News: proposed changes to support food processing in the ALR (July 23, 2026)](https://news.gov.bc.ca/releases/2026AF0017-000863)
- [The Tyee: How the ALR's future is becoming an election issue (Oct 7, 2026)](https://thetyee.ca/News/2026/10/07/ALR-Future-Becoming-Election-Issue/)
- [Daily Hive: Eby grocery plan, price guard and Lower Mainland food terminal (Oct 2, 2026)](https://dailyhive.com/vancouver/david-eby-grocery-prices-bc)

**BC Conservatives** (no published position)

- [The Tyee: How the ALR's future is becoming an election issue (Oct 7, 2026)](https://thetyee.ca/News/2026/10/07/ALR-Future-Becoming-Election-Issue/)
- [Conservative Party of BC: Our Plan (no agriculture item)](https://conservativebc.ca/plan/)

**BC Greens** (basis: platform, confidence: medium)

- [The Tyee: How the ALR's future is becoming an election issue (Oct 7, 2026)](https://thetyee.ca/News/2026/10/07/ALR-Future-Becoming-Election-Issue/)
- [BC Greens: plan to support local food production and farmers (Oct 2, 2026)](https://bcgreens.ca/launch-plan-to-support-local-food-production-and-farmers/)
- [BC Greens: Agriculture and Food Policy Brief 2026 (PDF, Oct 2, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Agriculture-and-Food-Policy-Brief-2026.pdf)
- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)

**CentreBC** (basis: inferred, confidence: low)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, Economy and Affordability)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (no published position)

- [OneBC priorities](https://1bc.ca/priorities)


</details>

<details>
<summary><b>Highway 1 widening is funded to Highway 11 in Abbotsford by 2031 and only planned to Chilliwack. Where should the next money go?</b> (Regional: Fraser Valley, <code>q_local_fraser_valley_highway1</code>)</summary>

**BC NDP** (basis: record, confidence: medium)

- [BC Gov: Fraser Valley Highway 1 program](https://www2.gov.bc.ca/gov/content/transportation-projects/fraser-valley-highway1)
- [BC Gov News: Highway 1 widening to Highway 11 (Aug 14, 2024)](https://news.gov.bc.ca/releases/2024MOTI0113-001306)
- [Fraser Valley Current: West Coast Express extension promise update (Mar 4, 2025)](https://fvcurrent.com/p/west-coast-extension-promise-update)
- [Daily Hive: Eby rules out TransLink vehicle levy (Oct 2, 2026)](https://dailyhive.com/vancouver/bc-ndp-david-eby-translink-vehicle-levy)
- [BC NDP: Rustad candidate supports mobility tax; no mobility pricing under Eby (Oct 13, 2024)](https://www.bcndp.ca/releases/john-rustads-hand-picked-candidate-supports-mobility-tax)
- [Canadian Press via BOE Report: Eby promises relief at gas pumps, 10 cents a litre (Oct 1, 2026)](https://boereport.com/2026/10/01/b-c-s-eby-promises-relief-at-gas-pumps-while-conservative-doerkson-praises-pipeline/amp/)

**BC Conservatives** (basis: inferred, confidence: low)

- [Fraser Valley Today: Conservatives pledge six lanes through Chilliwack (Oct 3, 2024)](https://fraservalleytoday.ca/2024/10/03/b-c-conservatives-pledge-to-expand-highway-1-to-6-lanes-through-chilliwack/)
- [Conservative Party of BC: Our Plan (no highway item)](https://conservativebc.ca/plan/)

**BC Greens** (basis: platform, confidence: medium)

- [Langley Advance Times: Greens release transportation plans (Oct 9, 2026)](https://langleyadvancetimes.com/2026/10/09/b-c-greens-release-transportation-plans-includes-free-transit-for-youth-seniors/)
- [BC Greens: Transit and Transportation Policy Brief 2026 (PDF)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Transit-and-Transportation-Policy-Brief-2026.pdf)
- [BC Greens: funding for fast, frequent transit and province-wide passenger rail (Oct 9, 2026)](https://bcgreens.ca/bc-greens-commit-to-funding-for-fast-frequent-transit-pledge-to-fight-for-province-wide-passenger-rail/)
- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)

**CentreBC** (basis: platform, confidence: medium)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 11, 13)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (no published position)

- [OneBC priorities](https://1bc.ca/priorities)


</details>

<details>
<summary><b>Mission Memorial's emergency room cut overnight hours for 51 nights in a row earlier this year for lack of doctors. What should come first?</b> (Regional: Fraser Valley, <code>q_local_fraser_valley_er</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [Mission City Record: more overnight closures coming to Mission Memorial ER (Aug 6, 2026)](https://missioncityrecord.com/2026/08/06/more-overnight-closures-coming-to-mission-memorial-hospital-emergency-department/)
- [Langley Advance Times: Eby vows to fast-track international medical grads, more doctors for rural areas (Oct 9, 2026)](https://langleyadvancetimes.com/2026/10/09/b-c-election-eby-vows-to-fast-track-intl-medical-grads-bring-more-docs-to-rural-areas/)
- [BC NDP: more doctors and nurses, fast-tracking international graduates (Oct 9, 2026)](https://www.bcndp.ca/releases/ebys-plan-includes-more-doctors-and-nurses-fast-tracking-international-graduates)
- [Nanaimo News Bulletin: NDP promises faster health care with new diagnostic equipment (Oct 6, 2026)](https://nanaimobulletin.com/2026/10/06/b-c-ndp-promises-faster-health-care-with-new-diagnostic-equipment/)

**BC Conservatives** (basis: platform, confidence: medium)

- [Conservative Party of BC: Keep emergency rooms open (Oct 5, 2026)](https://conservativebc.ca/keep-emergency-rooms-open/)
- [Abbotsford News: Doerkson pledges $50M fund for ER closures (Oct 5, 2026)](https://abbynews.com/2026/10/05/lorne-doerkson-pledges-to-create-50m-fund-to-address-emergency-room-closures/)
- [Abbotsford News: Abbotsford-Mission by-election debate (Sept 14, 2026)](https://abbynews.com/2026/09/14/mla-hopefuls-spar-in-abbotsford-mission-byelection-debate/)

**BC Greens** (basis: platform, confidence: medium)

- [BC Greens: Healthcare Policy Brief 2026 (PDF, Oct 6, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Healthcare-Policy-Brief-2026.pdf)
- [BC Greens: Our Plan](https://bcgreens.ca/our-plan/)
- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 16-17)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [Abbotsford News: Abbotsford-Mission by-election debate (Sept 14, 2026)](https://abbynews.com/2026/09/14/mla-hopefuls-spar-in-abbotsford-mission-byelection-debate/)

**OneBC** (basis: platform, confidence: medium)

- [OneBC priorities](https://1bc.ca/priorities)
- [OneBC on X: reinstate nurses with back pay (Oct 11, 2026)](https://x.com/One_BCHQ/status/2109406941118079436)
- [OneBC on YouTube: OneBC will bring nurses back to work (Oct 11, 2026)](https://www.youtube.com/watch?v=WQk8R4dwmsI)
- [OneBC on X: Our Plan graphic (Oct 5, 2026)](https://x.com/One_BCHQ/status/2107175484186624143)


</details>

<details>
<summary><b>BC Ferries has cancelled sailings, long waits, rising demand and a dispute over where ships are built. What should come first?</b> (Regional: Vancouver Island and the Coast, <code>q_local_island_coast_ferries</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [BC NDP: locals first with new ferry reservation pilot (Oct 10, 2026)](https://www.bcndp.ca/releases/bc-ndp-would-put-locals-first-new-ferry-reservation-pilot)
- [Victoria Buzz: what the major parties are promising for BC Ferries (Oct 11, 2026)](https://victoriabuzz.com/2026/10/heres-what-bcs-major-political-parties-are-promising-for-bc-ferries-ahead-of-the-election/)
- [Nanaimo News Bulletin: Greens release transportation plans, note on Chinese-built vessels (Oct 9, 2026)](https://nanaimobulletin.com/2026/10/09/b-c-greens-release-transportation-plans-includes-free-transit-for-youth-seniors/)
- [Victoria News: Eby pledges future ferries to be built locally (Sept 18, 2026)](https://vicnews.com/2026/09/18/eby-suspends-planned-b-c-pst-expansion-pledges-future-ferries-to-be-built-locally/)

**BC Conservatives** (basis: platform, confidence: high)

- [Conservative Party of BC: Conservatives will fix BC Ferries (Oct 11, 2026)](https://conservativebc.ca/conservatives-will-fix-bc-ferries/)
- [Victoria Buzz: what the major parties are promising for BC Ferries (Oct 11, 2026)](https://victoriabuzz.com/2026/10/heres-what-bcs-major-political-parties-are-promising-for-bc-ferries-ahead-of-the-election/)

**BC Greens** (basis: platform, confidence: high)

- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)
- [BC Greens: funding for fast, frequent transit and province-wide passenger rail (Oct 9, 2026)](https://bcgreens.ca/bc-greens-commit-to-funding-for-fast-frequent-transit-pledge-to-fight-for-province-wide-passenger-rail/)
- [BC Greens: Transit and Transportation Policy Brief 2026 (PDF, Oct 9, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Transit-and-Transportation-Policy-Brief-2026.pdf)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, Economy and Affordability)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)
- [Victoria Buzz: what the major parties are promising for BC Ferries (Oct 11, 2026)](https://victoriabuzz.com/2026/10/heres-what-bcs-major-political-parties-are-promising-for-bc-ferries-ahead-of-the-election/)

**OneBC** (no published position)

- [OneBC priorities](https://1bc.ca/priorities)
- [CHEK News: all Vancouver Island candidates for the 2026 election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)


</details>

<details>
<summary><b>The Crofton pulp mill has closed, and old-growth logging is still argued over on the Island. What should be done with Island forests?</b> (Regional: Vancouver Island and the Coast, <code>q_local_island_coast_oldgrowth</code>)</summary>

**BC NDP** (basis: both, confidence: medium)

- [BC NDP: Eby's plan protects natural spaces, funds climate action (Oct 10, 2026)](https://www.bcndp.ca/releases/ebys-plan-protects-bcs-natural-spaces-funds-climate-action)
- [National Newswatch: Eby says no to harvesting old growth to extend life of pulp mill (Dec 3, 2025)](https://nationalnewswatch.com/2025/12/03/eby-says-no-to-harvesting-old-growth-to-extend-life-of-b-c-pulp-mill)
- [Tree Frog Creative: Minister Parmar outlines working forest vision (2026)](https://treefrogcreative.ca/minister-parmar-outlines-working-forest-vision-commits-to-structural-shift-as-sector-presses-for-fibre-flow/)
- [BC Gov: Working Forest Landscape Model](https://www2.gov.bc.ca/gov/content/industry/natural-resource-use/working-forest-landscape-model)
- [Canadian Press via Castanet: Campbell River area first to test new forest management model (Sept 15, 2026)](https://castanet.net/edition/news-story-631385-3-.htm)

**BC Conservatives** (no published position)

- [Conservative Party of BC: Supercharge British Columbia's economy (Oct 7, 2026)](https://conservativebc.ca/supercharge-british-columbias-economy/)
- [Westk News: Conservative forestry critic on the 100 Mile House closure (Nov 7, 2025)](https://westknews.com/2025/11/07/conservative-forestry-critic-calls-closure-of-100-mile-west-fraser-mill-devastating/)

**BC Greens** (basis: platform, confidence: high)

- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)
- [BC Greens: plan to reform the forestry sector (Oct 4, 2026)](https://bcgreens.ca/announce-plan-to-reform-forestry-sector-protecting-forests-jobs-and-communities/)
- [Parksville Qualicum Beach News: Lowan launches Greens' economic vision (Oct 7, 2026)](https://pqbnews.com/2026/10/07/lowan-launches-greens-economic-vision-for-b-c/)
- [BC Greens: Forestry Policy Brief 2026 (PDF, Oct 4, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Forestry-Policy-Brief-2026.pdf)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, Economy and Affordability)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (basis: platform, confidence: medium)

- [OneBC priorities](https://1bc.ca/priorities)
- [OneBC on X: Our Plan graphic (Oct 5, 2026)](https://x.com/One_BCHQ/status/2107175484186624143)


</details>

<details>
<summary><b>Nanaimo's hospital tower and cardiac lab are funded for planning, not construction, and a Campbell River care home was paused. What should come first?</b> (Regional: Vancouver Island and the Coast, <code>q_local_island_coast_seniors</code>)</summary>

**BC NDP** (basis: both, confidence: medium)

- [Times Colonist: NDP promises $90M to redevelop Oak Bay Lodge site, free shingles vaccines (Oct 6, 2026)](https://www.timescolonist.com/2026-bc-votes/bc-ndp-promises-90m-to-redevelop-oak-bay-lodge-site-free-shingles-vaccines-12859483)
- [Nanaimo News Bulletin: acute care tower and cardiac services advancing at Nanaimo hospital (Feb 24, 2026)](https://nanaimobulletin.com/2026/02/24/acute-care-tower-and-the-expansion-of-cardiac-services-advancing-at-nanaimo-hospital/)
- [Nanaimo NewsNOW: consultant sought to advance Nanaimo hospital tower, cath lab (July 28, 2026)](https://nanaimonewsnow.com/2026/07/28/consultant-sought-to-advance-nanaimo-hospital-patient-tower-cath-lab/)
- [Nanaimo News Bulletin: NDP promises faster health care with new diagnostic equipment (Oct 6, 2026)](https://nanaimobulletin.com/2026/10/06/b-c-ndp-promises-faster-health-care-with-new-diagnostic-equipment/)
- [My Cariboo Now: NDP plans to resume seven paused long-term care projects (Oct 5, 2026)](https://mycariboonow.com/316576/news/elections/2026-bc-election/b-c-ndp-plans-to-resume-seven-paused-long-term-care-projects-if-re-elected)
- [Victoria News: NDP commits $90M to redevelop former Oak Bay Lodge site (Oct 5, 2026)](https://vicnews.com/2026/10/05/bc-ndp-commits-90m-to-redevelop-former-oak-bay-lodge-site/)
- [The Tyee: BC halts construction on seven long-term care facilities (Feb 20, 2026)](https://thetyee.ca/News/2026/02/20/BC-Halts-Construction-Seven-Long-Term-Care-Facilities/)

**BC Conservatives** (basis: platform, confidence: medium)

- [Conservative Party of BC: build the long-term care beds the NDP shelved (Oct 9, 2026)](https://conservativebc.ca/conservatives-will-build-the-long-term-care-beds-the-ndp-shelved/)
- [Nanaimo News Bulletin: Doerkson pledges $50M fund for ER closures (Oct 5, 2026)](https://nanaimobulletin.com/2026/10/05/lorne-doerkson-pledges-to-create-50m-fund-to-address-emergency-room-closures/)
- [CHEK News: all Vancouver Island candidates for the 2026 election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)

**BC Greens** (basis: platform, confidence: high)

- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)
- [BC Greens: Our Plan](https://bcgreens.ca/our-plan/)
- [BC Greens: Healthcare Policy Brief 2026 (PDF, Oct 6, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Healthcare-Policy-Brief-2026.pdf)
- [BC Greens: plan to support seniors (Oct 4, 2026)](https://bcgreens.ca/announce-plan-to-support-seniors/)
- [BC Greens: Supporting Seniors Policy Brief 2026 (PDF, Oct 4, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Supporting-Seniors-Policy-Brief-2026.pdf)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, Health Care, pp 16-18)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (basis: inferred, confidence: low)

- [OneBC priorities](https://1bc.ca/priorities)
- [CBC: Dallas Brodie OneBC Q&A (Oct 3, 2026)](https://www.cbc.ca/news/canada/british-columbia/dallas-brodie-onebc-q-a-2026-election-9.7366117)
- [OneBC on X: reinstate nurses with back pay (Oct 11, 2026)](https://x.com/One_BCHQ/status/2109406941118079436)
- [OneBC on YouTube: OneBC will bring nurses back to work (Oct 11, 2026)](https://www.youtube.com/watch?v=WQk8R4dwmsI)


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
- [CFJC Today (Canadian Press): Doerkson promises to buy firefighting water bombers (Oct 2, 2026)](https://cfjctoday.com/2026/10/02/b-c-conservative-interim-leader-doerkson-promises-to-buy-firefighting-water-bombers/)

**BC Greens** (basis: platform, confidence: high)

- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)
- [BC Greens: Climate, LNG and Royalties Policy Brief 2026 (PDF, Oct 10, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Climate-LNG-and-Royalties-Policy-Brief-2026.pdf)
- [BC Greens: A New Economic Direction for British Columbia (PDF, Oct 7, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Economic-Vision.pdf)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, Public Safety)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (no published position)

- [OneBC priorities](https://1bc.ca/priorities)
- [OneBC on X: Our Plan summary (Oct 5, 2026)](https://x.com/One_BCHQ/status/2107175484186624143)


</details>

<details>
<summary><b>Kelowna's council wants a regional involuntary care facility and its downtown consumption site closed. What should be done?</b> (Regional: Southern Interior, <code>q_local_interior_downtown</code>)</summary>

**BC NDP** (basis: both, confidence: medium)

- [Kelowna Capital News: Eby announces grocery price guard, addresses social disorder in Kelowna (Oct 2, 2026)](https://kelownacapnews.com/2026/10/02/eby-announces-b-c-grocery-price-guard-social-disorder-during-kelowna-visit/)
- [Kelowna Capital News: council pushes to close downtown supervised consumption site (Sept 1, 2026)](https://kelownacapnews.com/2026/09/01/kelowna-council-pushing-to-close-downtown-supervised-consumption-site/)
- [BCCDC: decriminalization in BC (exemption expired January 31, 2026)](https://www.bccdc.ca/health-info/prevention-public-health/decriminalization-in-bc)

**BC Conservatives** (basis: platform, confidence: medium)

- [Conservative Party of BC: Safe Streets for BC (Oct 6, 2026)](https://conservativebc.ca/safe-streets-for-bc/)
- [Global News: NDP and Conservative leaders campaign in the Okanagan (Oct 2, 2026)](https://globalnews.ca/news/12086166/bc-ndp-conservative-leaders-campaign-okanagan/)

**BC Greens** (basis: platform, confidence: high)

- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)
- [BC Greens: Toxic Drugs Policy Brief 2026 (PDF, Oct 2, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Toxic-Drugs-Policy-Brief-2026-1.pdf)
- [BC Greens: toxic drugs policy announced with Lisa Lapointe (Oct 2, 2026)](https://bcgreens.ca/announce-toxic-drugs-policy-alongside-former-chief-coroner-and-candidate-for-saanich-south-lisa-lapointe/)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, pp 15-20, 26-27)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (basis: platform, confidence: medium)

- [OneBC priorities](https://1bc.ca/priorities)
- [OneBC on X: drugs and addiction, including reopening Riverview (Sept 29, 2026)](https://x.com/One_BCHQ/status/2105036887736058203)
- [OneBC on X: Our Plan summary, including street patrols and no charge downgrades (Oct 5, 2026)](https://x.com/One_BCHQ/status/2107175484186624143)


</details>

<details>
<summary><b>Budget 2026 paused seven care home builds including Kelowna's, and a private 250-bed Vernon project was pulled. What now?</b> (Regional: Southern Interior, <code>q_local_interior_ltc</code>)</summary>

**BC NDP** (basis: both, confidence: medium)

- [Kelowna Capital News: Kelowna among seven long-term care projects delayed by budget (Feb 17, 2026)](https://kelownacapnews.com/2026/02/17/kelowna-among-7-scheduled-long-term-care-projects-delayed-by-b-c-budget/)
- [My South Okanagan Now: NDP plans to resume seven paused long-term care projects (Oct 5, 2026)](https://www.mysouthokanagannow.com/8300/news/elections/2026-bc-election/b-c-ndp-plans-to-resume-seven-paused-long-term-care-projects-if-re-elected/)
- [BC NDP: seniors health care plan, seven long-term care projects resumed (Oct 5, 2026)](https://www.bcndp.ca/releases/bc-ndp-seniors-healthcare-plan-free-vaccines-home-care-long-term-care-david-eby)
- [BC NDP: $90 million to redevelop the former Oak Bay Lodge site (Oct 5, 2026)](https://www.bcndp.ca/releases/bc-ndp-commits-90-million-redevelop-former-oak-bay-lodge-site-deliver-new-health-and)
- [The Tyee: BC halts construction of seven long-term care facilities (Feb 20, 2026)](https://thetyee.ca/News/2026/02/20/BC-Halts-Construction-Seven-Long-Term-Care-Facilities/)

**BC Conservatives** (basis: platform, confidence: medium)

- [Conservative Party of BC: build the long-term care beds the NDP shelved (Oct 9, 2026)](https://conservativebc.ca/conservatives-will-build-the-long-term-care-beds-the-ndp-shelved/)
- [Conservative Party of BC: Keep emergency rooms open, health spending kept (Oct 5, 2026)](https://conservativebc.ca/keep-emergency-rooms-open/)

**BC Greens** (basis: platform, confidence: high)

- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)
- [BC Greens: Healthcare Policy Brief 2026 (PDF, Oct 6, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Healthcare-Policy-Brief-2026.pdf)
- [BC Greens: plan to support seniors (Oct 4, 2026)](https://bcgreens.ca/announce-plan-to-support-seniors/)
- [BC Greens: Supporting Seniors Policy Brief 2026 (PDF, Oct 4, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Supporting-Seniors-Policy-Brief-2026.pdf)
- [BC Greens: Our Plan](https://bcgreens.ca/our-plan)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, Health Care)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (basis: inferred, confidence: low)

- [OneBC priorities](https://1bc.ca/priorities)
- [OneBC on X: reinstate nurses with back pay (Oct 11, 2026)](https://x.com/One_BCHQ/status/2109406941118079436)


</details>

<details>
<summary><b>Northern mills, including Prince George's Northwood pulp mill, are closing, and companies cite fibre supply. How should the harvest be set?</b> (Regional: North and Cariboo, <code>q_local_north_forestry</code>)</summary>

**BC NDP** (basis: both, confidence: medium)

- [BC Gov: Working Forest Landscape Model](https://www2.gov.bc.ca/gov/content/industry/natural-resource-use/working-forest-landscape-model)
- [BC NDP: Eby's plan protects natural spaces, funds climate action (Oct 10, 2026)](https://www.bcndp.ca/releases/ebys-plan-protects-bcs-natural-spaces-funds-climate-action)
- [Chilliwack Progress: BC piloting landscape-level, zone-based forestry (Aug 27, 2026)](https://theprogress.com/2026/08/27/b-c-piloting-landscape-level-forestry-zone-based-management/)
- [CKPG: Canfor announces permanent closure of Northwood pulp mill (July 14, 2026)](https://ckpgtoday.ca/2026/07/14/canfor-announces-permanent-closure-of-northwood-pulp-mill/)
- [BC Gov News: Campbell River first candidate area for the Working Forest Landscape Model (Sept 15, 2026)](https://news.gov.bc.ca/releases/2026FOR0034-001069)
- [BC NDP: Eby outlines next steps for forestry (Oct 14, 2026)](https://www.bcndp.ca/releases/eby-outlines-next-steps-forestry)

**BC Conservatives** (no published position)

- [Conservative Party of BC: Supercharge British Columbia's economy (Oct 7, 2026)](https://conservativebc.ca/supercharge-british-columbias-economy/)
- [Conservative Party of BC: plan hub (Forestry for the Future heading, no text)](https://conservativebc.ca/plan/)
- [Williams Lake Tribune: Doerkson on the 100 Mile House mill closure (Nov 15, 2025)](https://wltribune.com/2025/11/15/doerkson-west-frasers-permanent-mill-closure-in-100-mile-house-shocking/)
- [Westk News: Conservative forestry critic on the 100 Mile House closure (Nov 7, 2025)](https://westknews.com/2025/11/07/conservative-forestry-critic-calls-closure-of-100-mile-west-fraser-mill-devastating/)

**BC Greens** (basis: platform, confidence: high)

- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)
- [BC Greens: Forestry Policy Brief 2026 (PDF, Oct 4, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Forestry-Policy-Brief-2026.pdf)
- [BC Greens: plan to reform the forestry sector (Oct 4, 2026)](https://bcgreens.ca/announce-plan-to-reform-forestry-sector-protecting-forests-jobs-and-communities/)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, Economy and Affordability)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (basis: platform, confidence: medium)

- [OneBC priorities](https://1bc.ca/priorities)
- [OneBC on X: Our Plan summary (Oct 5, 2026)](https://x.com/One_BCHQ/status/2107175484186624143)


</details>

<details>
<summary><b>Kitimat's gas export plant is doubling, and more plants, mines and a power line are proposed. How should the province decide on them?</b> (Regional: North and Cariboo, <code>q_local_north_resources</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [BC NDP: Conservatives' LNG plan out of step with reality (Sept 28, 2026)](https://www.bcndp.ca/releases/bc-conservatives-lng-plan-out-step-reality)
- [BC NDP: double critical mineral exports, expand Port of Prince Rupert (Sept 28, 2026)](https://www.bcndp.ca/releases/eby-double-critical-mineral-exports-expand-port-prince-rupert)
- [BC NDP: Eby's plan protects natural spaces, funds climate action (Oct 10, 2026)](https://www.bcndp.ca/releases/ebys-plan-protects-bcs-natural-spaces-funds-climate-action)
- [BNN Bloomberg: LNG Canada to go ahead with Phase 2 (Sept 29, 2026)](https://www.bnnbloomberg.ca/business/company-news/2026/09/29/lng-canada-to-go-ahead-with-phase-2-expansion-project-in-kitimat-bc/)
- [BC NDP: new Built in BC and Canada buying rules, Canadian steel for the North Coast line (Sept 24, 2026)](https://www.bcndp.ca/releases/eby-pledges-new-built-bc-and-canada-buying-rules)

**BC Conservatives** (basis: platform, confidence: high)

- [Conservative Party of BC: Make British Columbia an energy superpower (Sept 28, 2026)](https://conservativebc.ca/make-british-columbia-an-energy-superpower/)
- [Conservative Party of BC: BC Energy Superpower plan (PDF)](https://conservativebc.ca/wp-content/uploads/2026/09/BC-ENERGY-SUPERPOWER_5_compressed.pdf)
- [Conservative Party of BC: welcome LNG Canada Phase 2 (Sept 29, 2026)](https://conservativebc.ca/bc-conservatives-welcome-lng-canada-phase-2-we-will-treat-energy-as-an-urgent-mission/)
- [Conservative Party of BC: Supercharge British Columbia's economy, 120 Day Permitting Act over $250 million (Oct 7, 2026)](https://conservativebc.ca/supercharge-british-columbias-economy/)

**BC Greens** (basis: platform, confidence: high)

- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)
- [BC Greens: Climate, LNG and Royalties Policy Brief 2026 (PDF, Oct 10, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Climate-LNG-and-Royalties-Policy-Brief-2026.pdf)
- [BC Greens: statement from Emily Lowan on LNG Canada Phase 2 (Sept 29, 2026)](https://bcgreens.ca/statement-from-emily-lowan-on-lng-canada-phase-2/)
- [BC Greens: A New Economic Direction for British Columbia (PDF, Oct 7, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Economic-Vision.pdf)
- [BC Greens: Healthcare Policy Brief 2026 (PDF, Oct 6, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Healthcare-Policy-Brief-2026.pdf)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, Economy and Affordability)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (basis: platform, confidence: medium)

- [OneBC priorities](https://1bc.ca/priorities)
- [OneBC on X: major projects without veto consultations (Sept 26, 2026)](https://x.com/One_BCHQ/status/2103913099086684163)
- [OneBC on X: Our Plan summary (Oct 5, 2026)](https://x.com/One_BCHQ/status/2107175484186624143)


</details>

<details>
<summary><b>Emergency rooms in Fort St. James, Chetwynd, Hudson's Hope and 100 Mile House keep closing for lack of staff. What comes first?</b> (Regional: North and Cariboo, <code>q_local_north_er</code>)</summary>

**BC NDP** (basis: both, confidence: high)

- [CFJC Today: NDP talks health care, tuition discounts for rural work (Oct 9, 2026)](https://cfjctoday.com/2026/10/09/b-c-ndp-talks-health-care-on-the-campaign-promises-tuition-discounts-for-rural-work/)
- [The Northern View: Eby vows to fast-track international medical grads, bring more doctors to rural areas (Oct 9, 2026)](https://thenorthernview.com/2026/10/09/b-c-election-eby-vows-to-fast-track-intl-medical-grads-bring-more-docs-to-rural-areas/)
- [BC Gov: health capital projects (updated Sept 21, 2026)](https://www2.gov.bc.ca/gov/content/health/accessing-health-care/capital-projects)
- [Energeticcity: Northern Health clocks more than 100 hours of closures in March (Apr 10, 2026)](https://energeticcity.ca/2026/04/10/northern-health-clocks-in-more-than-100-hours-in-closures-in-march/)
- [BC NDP: more doctors and nurses, fast-tracking international graduates (Oct 9, 2026)](https://www.bcndp.ca/releases/ebys-plan-includes-more-doctors-and-nurses-fast-tracking-international-graduates)
- [BC NDP: getting care sooner, new diagnostic equipment (Oct 6, 2026)](https://www.bcndp.ca/releases/getting-care-sooner-eby-will-cut-wait-times-add-new-diagnostic-equipment)
- [BC NDP: protect public health care from US-style privatization, phase out agency nurses (Oct 12, 2026)](https://www.bcndp.ca/releases/eby-will-protect-public-health-care-us-style-privatization)

**BC Conservatives** (basis: platform, confidence: medium)

- [Conservative Party of BC: Keep emergency rooms open (Oct 5, 2026)](https://conservativebc.ca/keep-emergency-rooms-open/)
- [100 Mile Free Press: Doerkson pledges $50M fund for ER closures (Oct 5, 2026)](https://100milefreepress.net/2026/10/05/lorne-doerkson-pledges-to-create-50m-fund-to-address-emergency-room-closures/)
- [CJDC TV: after 21 ER diversions in 56 days in Hudson's Hope, MLA calls for Northern Health to be dismantled (Apr 14, 2026)](https://www.cjdctv.com/news/article/after-21-er-diversions-in-56-days-in-hudsons-hope-mla-calls-for-northern-health-to-be-dismantled/)

**BC Greens** (basis: platform, confidence: high)

- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)
- [BC Greens: community health centres in every riding, support for health workers (Oct 6, 2026)](https://bcgreens.ca/pledge-funding-for-community-health-centres-in-every-riding-support-for-healthcare-workers/)
- [BC Greens: Healthcare Policy Brief 2026 (PDF, Oct 6, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Healthcare-Policy-Brief-2026.pdf)
- [BC Greens: Our Plan](https://bcgreens.ca/our-plan)
- [BC Greens: Supporting Seniors Policy Brief 2026 (PDF, Oct 4, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BC-Greens-Supporting-Seniors-Policy-Brief-2026.pdf)

**CentreBC** (basis: platform, confidence: high)

- [CentreBC: A Balanced Plan for British Columbia, 2026 Platform (PDF, Health Care)](https://www.centrebc.ca/wp-content/uploads/2026/10/CentreBC-2026-Platform-Web.pdf)

**OneBC** (basis: platform, confidence: medium)

- [OneBC priorities](https://1bc.ca/priorities)
- [OneBC on X: reinstate nurses with back pay (Oct 11, 2026)](https://x.com/One_BCHQ/status/2109406941118079436)
- [OneBC on X: Our Plan summary (Oct 5, 2026)](https://x.com/One_BCHQ/status/2107175484186624143)


</details>

### Parties: leaders, records and summaries

<details>
<summary>Sources for each party's summary and 2016 to 2026 record</summary>

**BC New Democratic Party**

- [BC NDP releases (party)](https://www.bcndp.ca/releases)
- [BC Budget 2026 and Fiscal Plan](https://www.bcbudget.gov.bc.ca/2026/pdf/2026_Budget_and_Fiscal_Plan.pdf)
- [Votes and Proceedings, May 28, 2025 (Bills 7, 14, 15)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v250528.htm)
- [BC NDP: 20 team-based primary care clinics (Oct 9, 2026)](https://www.bcndp.ca/releases/ebys-plan-includes-more-doctors-and-nurses-fast-tracking-international-graduates)
- [Daily Hive: Eby grocery price guard on staples (Oct 2, 2026)](https://dailyhive.com/vancouver/david-eby-grocery-prices-bc)
- [Morningstar DBRS rating report, downgrade April 9, 2026 (gov.bc.ca copy)](https://www2.gov.bc.ca/assets/gov/british-columbians-our-governments/government-finances/debt-management/dbrs-rating-report.pdf)
- [Fitch rating report, downgrade to AA- (April 24, 2026, gov.bc.ca copy)](https://www2.gov.bc.ca/assets/gov/british-columbians-our-governments/government-finances/debt-management/fitch-rating-report.pdf)
- [BC NDP: costing for Eby's plan (Oct 14, 2026)](https://www.bcndp.ca/releases/bc-ndp-releases-costing-ebys-plan-build-bc-strong)
- [BC NDP: Build BC Strong plan page (climate and costing items, Oct 2026)](https://www.bcndp.ca/plan)
- [Victoria News (Black Press): NDP releases costed platform (Oct 14, 2026)](https://vicnews.com/2026/10/14/ndp-release-costed-platform-with-added-spending-new-taxes-on-wealthy/)

**Conservative Party of British Columbia**

- [Conservative Party of BC plan hub](https://conservativebc.ca/plan/)
- [Votes and Proceedings, November 19, 2025 (DRIPA Statute Repeal Act first reading, 43-48)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251119.htm)
- [Votes and Proceedings, April 22, 2026 (DRIPA Repeal Act first reading, 44-47)](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260422.htm)
- [Votes and Proceedings, February 26, 2026 (Human Rights Code Repeal Act first reading)](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260226.htm)
- [CP24: Findlay resigns as BC Conservative leader](https://www.cp24.com/politics/2026/09/20/kerry-lynne-findlay-resigns-as-bc-conservative-leader/)
- [Global News: who are the BC party leaders (Doerkson interim, constitution bars interim leader from permanent post)](https://globalnews.ca/news/12068973/who-are-bc-party-leaders-2026-election/)
- [CFJC / Canadian Press: John Rustad resigns as leader (Dec 4, 2025)](https://cfjctoday.com/2025/12/04/john-rustad-resigns-as-leader-of-the-b-c-conservatives/)
- [Castanet / Canadian Press: five return to Conservative caucus, party standings (Sept 21, 2026)](https://www.castanetkamloops.net/news/BC/631916/Five-return-to-B-C-Conservative-caucus-as-early-election-looms)
- [Energeticcity (Canadian Press): voting begins without Conservative costed platform (Oct 16, 2026)](https://energeticcity.ca/2026/10/16/b-c-begins-voting-without-conservatives-costed-platform-doerkson-calls-it-imminent/)

**BC Green Party**

- [BC Greens: 2026 platform (Oct 13, 2026)](https://bcgreens.ca/wp-content/uploads/2026/10/BCG_Platform.pdf)
- [BC Greens: lift the $10-a-day freeze, universal free child care by 2031 (Sept 28, 2026)](https://bcgreens.ca/announce-plan-to-lift-the-freeze-on-10-a-day-daycare-with-universal-free-child-care-by-2031-alongside-new-candidate-for-victoria-swan-lake/)
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
- [Votes and Proceedings, April 22, 2026 (DRIPA Repeal Act first reading, 44-47)](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260422.htm)
- [Narcity / Canadian Press: Eby calls election; seven CentreBC MLAs rejoin Conservatives (Sept 22, 2026)](https://www.narcity.com/b-c-s-eby-calls-provincial-election-for-oct-24)

**OneBC**

- [OneBC priorities (party)](https://1bc.ca/priorities)
- [National Newswatch / Canadian Press: Brodie reinstated as OneBC leader (Dec 21, 2025)](https://nationalnewswatch.com/2025/12/22/dallas-brodie-reinstated-as-leader-of-onebc-party-after-abrupt-removal-this-month)
- [Narcity / Canadian Press: OneBC fails to gain party status before the vote (Sept 24, 2026)](https://www.narcity.com/onebc-overwhelmed-with-candidate-applications)
- [CTV: OneBC will not run against eight Conservative candidates](https://www.ctvnews.ca/vancouver/article/onebc-pledges-not-to-run-against-eight-principled-bc-conservative-candidates/)
- [Votes and Proceedings, October 29, 2025 (Property Rights Protection Act)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251029.htm)
- [Votes and Proceedings, October 8, 2025 (Protecting Minors from Gender Transition Act, 48-40)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251008.htm)
- [Votes and Proceedings, October 23, 2025 (Land Acknowledgement Prohibition Act, 85-5)](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251023.htm)
- [Votes and Proceedings, April 22, 2026 (DRIPA Repeal Act first reading, 44-47)](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260422.htm)


</details>

### Background, polling, election facts and context

<details>
<summary>97 general sources</summary>

- [Elections BC: ways to vote](https://elections.bc.ca/voting/ways-to-vote/)
- [Elections BC: who can vote](https://elections.bc.ca/voting/who-can-vote/)
- [Elections BC: voter ID](https://elections.bc.ca/2026-provincial-election/voter-id/)
- [Elections BC: vote by mail](https://elections.bc.ca/voting/ways-to-vote/vote-by-mail/)
- [Elections BC: 2026 provincial election](https://elections.bc.ca/2026-provincial-election/)
- [Elections BC: 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)
- [Elections BC: registered political parties (PDF)](https://elections.bc.ca/docs/fin/Registered-Political-Parties-Information.pdf)
- [Elections BC: Statement of Votes, 2024 (PDF)](https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf)
- [CFJC / Canadian Press: leaders' debate date set (Oct 6, 2026)](https://cfjctoday.com/2026/10/06/b-c-campaign-trail-date-for-leaders-debate-is-set/)
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
- [Angus Reid: BC election polling and DRIPA opinion](https://angusreid.org/ballot-backlash-bc-conservatives-open-8-point-lead-after-snap-election-call-but-electorate-far-from-locked-in/)
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
- [National Newswatch / Canadian Press: Brodie reinstated as OneBC leader (Dec 21, 2025)](https://nationalnewswatch.com/2025/12/22/dallas-brodie-reinstated-as-leader-of-onebc-party-after-abrupt-removal-this-month)
- [Narcity / Canadian Press: OneBC fails to gain party status before the vote (Sept 24, 2026)](https://www.narcity.com/onebc-overwhelmed-with-candidate-applications)
- [Castanet / Canadian Press: five return to Conservative caucus (Sept 21, 2026)](https://www.castanetkamloops.net/news/BC/631916/Five-return-to-B-C-Conservative-caucus-as-early-election-looms)
- [Votes and Proceedings, November 19, 2025](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251119.htm)
- [Votes and Proceedings, April 22, 2026](https://lims.leg.bc.ca/pdms/ldp/43rd2nd/votes/v260422.htm)
- [Votes and Proceedings, October 23, 2025](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v251023.htm)
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
- Pete Davis (BC Conservatives): [Conservative Party of BC candidate page](https://conservativebc.ca/candidate/pete-davis/), [Elections BC: Statement of Votes, 2024 (PDF)](https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf)
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
- Lorne Doerkson (BC Conservatives): [Conservative Party of BC: Lorne Doerkson](https://conservativebc.ca/mla/lorne-doerkson/), [Elections BC: Statement of Votes, 2020 (PDF)](https://elections.bc.ca/docs/rpt/statement-of-votes-2020-provincial-general-election.pdf)
- Douglas Gook (BC Greens): [BC Greens: 2026 candidates](https://bcgreens.ca/candidates-2026/), [Elections BC: Statement of Votes, 2024 (PDF)](https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf)

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
- Anne Kang (BC NDP): [BC Government: Minister Anne Kang biography](https://news.gov.bc.ca/ministries/tourism-arts-culture-and-sport/biography), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)
- Shila Taheri (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/shila-taheri/), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)

**Burnaby East** (`BNE`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; cross-checked against https://bcballot.ca/ridings/burnaby-east/>
- Rohini Reah Arora (BC NDP): [BC NDP: our eighteen newest MLAs (party)](https://www.bcndp.ca/latest/our-eighteen-newest-mlas-standing-strong-bc-you-every-day), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)
- De Ding (OneBC): [Elections BC: 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/), [OneBC: candidates](https://1bc.ca/candidates)
- Javad Shushtarian (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/javad-shushtarian/), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)
- Peter Si (BC Conservatives): [BC Conservatives candidate page](https://conservativebc.ca/candidate/peter-si/), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)

**Burnaby North** (`BNO`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; cross-checked against https://bcballot.ca/ridings/burnaby-north/>
- Simon Chandler (BC Conservatives): [BC Conservatives candidate page](https://conservativebc.ca/candidate/simon-chandler/), [Wikipedia, Burnaby East](https://en.wikipedia.org/wiki/Burnaby_East)
- Maddy Kennedy-Parrott (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/maddy-kennedy-parrott/), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)
- Janet Routledge (BC NDP): [Janet Routledge campaign page (party)](https://janetroutledge.bcndp.ca), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)
- Jenny Yamagata (OneBC): [Elections BC: 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/), [OneBC: candidates](https://1bc.ca/candidates)

**Burnaby South-Metrotown** (`BNS`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; cross-checked against https://bcballot.ca/ridings/burnaby-south-metrotown/>
- Paul Choi (BC NDP): [BC Government: Parliamentary Secretary for Trade (Paul Choi)](https://www2.gov.bc.ca/gov/content/governments/organizational-structure/cabinet/cabinet-ministers/parliamentary-secretary-for-asia-pacific-trade), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)
- Bryan Fockler (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/bryan-fockler/), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)
- Andrew Rose (OneBC): [OneBC candidate page](https://1bc.ca/candidates/arose), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)
- David Xie (BC Conservatives): [BC Conservatives candidate page](https://conservativebc.ca/candidate/david-xie/), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)

**Burnaby-New Westminster** (`BNN`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; cross-checked against https://bcballot.ca/ridings/burnaby-new-westminster/>
- Raj Chouhan (BC NDP): [Global News: Raj Chouhan becomes first South Asian Speaker (Dec 7, 2020)](https://globalnews.ca/news/7506336/mla-raj-chouhan-becomes-b-c-s-first-south-asian-speaker-of-the-house/), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)
- Joe Latam (BC Conservatives): [BC Conservatives candidate page](https://conservativebc.ca/candidate/joe-latam/), [Burnaby Board of Trade](https://www.bbot.ca/2026/10/09/election-candidates-copy/)
- Greg DePaco (BC Green on the ballot; withdrew Oct 9): [Elections BC: candidate withdrawn, Burnaby-New Westminster (Oct 10, 2026)](https://elections.bc.ca/news/2026-provincial-general-election-candidates-update-3/)

**Coquitlam-Burke Mountain** (`CQB`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; cross-checked against https://bcballot.ca/ridings/coquitlam-burke-mountain/>
- Kaden Mann (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/kaden-mann/), [BC Ballot riding page](https://bcballot.ca/ridings/coquitlam-burke-mountain/)
- Valerie Morrison (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/valerie-morrison/), [BC Ballot riding page](https://bcballot.ca/ridings/coquitlam-burke-mountain/)
- Ryan Peterson (BC Conservatives): [BC Conservatives candidate page](https://conservativebc.ca/candidate/ryan-peterson/), [BC Ballot riding page](https://bcballot.ca/ridings/coquitlam-burke-mountain/)
- Jodie Wickens (BC NDP): [BC Government: Minister Jodie Wickens biography](https://news.gov.bc.ca/ministries/children-and-family-development/biography)

**Coquitlam-Maillardville** (`CQM`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; cross-checked against https://bcballot.ca/ridings/coquitlam-maillardville/>
- Jennifer Blatherwick (BC NDP): [BC Government: Parliamentary Secretary for Gender Equity (Jennifer Blatherwick)](https://www2.gov.bc.ca/gov/content/governments/organizational-structure/cabinet/cabinet-ministers/parliamentary-secretary-gender-equity), [BC NDP: our eighteen newest MLAs (party)](https://www.bcndp.ca/latest/our-eighteen-newest-mlas-standing-strong-bc-you-every-day)
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
- Jennifer Whiteside (BC NDP): [BC Government: Minister Jennifer Whiteside biography](https://news.gov.bc.ca/ministries/labour/biography)
- Gerry Lenoski (Unaffiliated on the ballot; withdrew Oct 13): [Elections BC: 2026 candidates update, two withdrawals (Oct 14, 2026)](https://elections.bc.ca/news/2026-provincial-general-election-candidates/), [Elections BC 2026 candidate list (page)](https://elections.bc.ca/2026-provincial-election/candidate-list/)

**North Vancouver-Lonsdale** (`NVL`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Joshua A Singer Johnson (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/joshua-a-singer-johnson/)
- Bowinn Ma (BC NDP): [BC Government: Minister Bowinn Ma biography](https://news.gov.bc.ca/ministries/infrastructure/biography)
- Trevor Withers (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/trevor-withers/)

**North Vancouver-Seymour** (`NVS`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Lynne Block (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/lynne-block/), [North Shore News candidate roundup](https://www.nsnews.com/local-news/here-are-the-north-shore-candidates-running-in-bcs-snap-election-12858354)
- Susie Chant (BC NDP): [BC Government: Parliamentary Secretary for Seniors' Services and Long-Term Care (Susie Chant)](https://www2.gov.bc.ca/gov/content/governments/organizational-structure/cabinet/cabinet-ministers/parliamentary-secretary-seniors-services-long-term-care)
- Lori Climenhaga (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/lori-climenhaga/)
- Ben Holt (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/ben-holt/)
- Frederick Thiele (OneBC on the ballot; withdrew Oct 13): [Elections BC: 2026 candidates update, two withdrawals (Oct 14, 2026)](https://elections.bc.ca/news/2026-provincial-general-election-candidates/), [OneBC: Fred Thiele candidate page](https://1bc.ca/candidates/fthiele)

**Port Coquitlam** (`POC`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; cross-checked against https://bcballot.ca/ridings/port-coquitlam/>
- Keenan Adams (BC Conservatives): [BC Conservatives candidate page](https://conservativebc.ca/candidate/keenan-adams/), [BC Ballot riding page](https://bcballot.ca/ridings/port-coquitlam/)
- Mike Farnworth (BC NDP): [BC Government: Minister Mike Farnworth biography](https://news.gov.bc.ca/ministries/transportation-and-transit/biography)
- Stephanie Hendy (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/stephanie-hendy/), [BC Ballot riding page](https://bcballot.ca/ridings/port-coquitlam/)
- Lee-Ann Bates (Unaffiliated): [OneBC candidates page](https://1bc.ca/candidates), [BC Ballot riding page](https://bcballot.ca/ridings/port-coquitlam/)
- Lewis C. Dahlby (BC Libertarian): [BC Ballot riding page](https://bcballot.ca/ridings/port-coquitlam/), [Elections BC 2026 candidate list (page)](https://elections.bc.ca/2026-provincial-election/candidate-list/)

**Port Moody-Burquitlam** (`POM`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf ; cross-checked against https://bcballot.ca/ridings/port-moody-burquitlam/>
- Wei Chou (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/wei-chou/), [BC Ballot riding page](https://bcballot.ca/ridings/port-moody-burquitlam/)
- Rick Glumac (BC NDP): [BC Government: Minister of State Rick Glumac biography](https://news.gov.bc.ca/ministries/ai-and-new-technologies/biography)
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
- Aman Singh (BC NDP): [Castanet / Canadian Press: Aman Singh to run in Vancouver-Fraserview (Sept 28, 2026)](https://www.castanetkamloops.net/edition/news-story-632623-3-.htm), [Elections BC: Statement of Votes, 2020 (PDF)](https://elections.bc.ca/docs/rpt/statement-of-votes-2020-provincial-general-election.pdf)

**Vancouver-Hastings** (`VHA`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Christian Bosio (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/christian-bosio/)
- Kyra Philbert (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/kyra-philbert/)
- Niki Sharma (BC NDP): [BC Government: Attorney General Niki Sharma biography](https://news.gov.bc.ca/ministries/attorney-general/biography)
- Phyllis Tang (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/phyllis-tang/)
- Kimball Cariou (Communist Party of BC): [Elections BC: Statement of Votes, 2024 (PDF)](https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf), [Elections BC: Statement of Votes, 2020 (PDF)](https://elections.bc.ca/docs/rpt/statement-of-votes-2020-provincial-general-election.pdf)
- Phil Webb (BC Libertarian): [Elections BC: 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/)

**Vancouver-Kensington** (`VKE`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Mable Elmore (BC NDP): [Legislative Assembly of BC: Mable Elmore](https://www.leg.bc.ca/node/138)
- Adam Hawk (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/adam-hawk/), [Elections BC Statement of Votes 2024](https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf)
- Aron Lageri (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/aron-lageri/), [Elections BC Statement of Votes 2024](https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf)

**Vancouver-Langara** (`VLA`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- John Atoyebi (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/john-atoyebi/)
- Alan Beesley (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/alan-beesley/)
- Sunita Dhir (BC NDP): [BC Government: Parliamentary Secretary for International Credentials (Sunita Dhir)](https://www2.gov.bc.ca/gov/content/governments/organizational-structure/cabinet/cabinet-ministers/parliamentary-secretary-for-international-credentials)
- Jaime Stein (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/jaime-stein/)

**Vancouver-Little Mountain** (`VLM`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Christine Boyle (BC NDP): [BC Government: Minister Christine Boyle biography](https://news.gov.bc.ca/ministries/housing-and-municipal-affairs/biography)
- Sarah MacLeod (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/sarah-macleod/)
- Alex Muir (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/alex-muir/)

**Vancouver-Point Grey** (`VNP`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Michael Davis (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/michael-davis/)
- David Eby (BC NDP): [BC Government: Premier David Eby biography](https://news.gov.bc.ca/ministries/office-of-the-premier/biography), [Daily Hive: Eby sworn in as premier (Nov 18, 2022)](https://dailyhive.com/vancouver/david-eby-sworn-in)
- Alex McMillan (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/alex-mcmillan/)
- Beatrice Sharpe (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/beatrice-sharpe/)

**Vancouver-Quilchena** (`VNQ`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Carson Binda (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/carson-binda/)
- Dallas Brodie (OneBC): [CBC: Brodie removed from Conservative caucus (Mar 7, 2025)](https://www.cbc.ca/1.7478162), [National Newswatch / Canadian Press: Brodie reinstated as OneBC leader (Dec 21, 2025)](https://nationalnewswatch.com/2025/12/22/dallas-brodie-reinstated-as-leader-of-onebc-party-after-abrupt-removal-this-month)
- Douglas Courtemanche (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/douglas-courtemanche/)
- Petra Kuret (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/petra-kuret/)
- Callista Ryan (BC NDP): [BC NDP release (2024 nomination)](https://bcndp.ca/releases/youth-advocate-callista-ryan-run-bc-ndp-vancouver-quilchena)

**Vancouver-Renfrew** (`VNR`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Adrian Dix (BC NDP): [BC Government: Minister Adrian Dix biography](https://news.gov.bc.ca/ministries/energy-and-climate-solutions/biography)
- Rebecca Haber (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/rebecca-haber/)
- Tom Ikonomou (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/tom-ikonomou/)
- Lisa Prescott (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/lisa-prescott/)

**Vancouver-South Granville** (`VNS`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Maria J Cruz (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/maria-cruz/)
- Lara Honrado (BC NDP): [BC NDP release, more candidates (2026)](https://www.bcndp.ca/releases/more-bc-ndp-candidates-ready-fight-their-communities)
- Lisa Phillips (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/lisa-phillips/)
- Colin Smith (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/colin-smith/)
- Salvatore Vetro (OneBC): [OneBC: Salvatore Vetro candidate page](https://1bc.ca/candidates/svetro), [Elections BC: Statement of Votes, 2020 (PDF)](https://elections.bc.ca/docs/rpt/statement-of-votes-2020-provincial-general-election.pdf)

**Vancouver-Strathcona** (`VNT`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Amanda Burrows (BC NDP): [Daily Hive](https://dailyhive.com/vancouver/amanda-burrows-bc-ndp)
- Tanya Webking (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/tanya-webking/)
- Robert Crooks (Communist Party of BC): [Wikipedia: Communist Party of British Columbia](https://en.wikipedia.org/wiki/Communist_Party_of_British_Columbia), [Elections BC Statement of Votes 2024](https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf)
- Jordan Zheng McIntosh (Conservative on the ballot; dropped by the party Oct 15): [insauga (Canadian Press): Conservatives drop Vancouver-Strathcona candidate (Oct 15, 2026)](https://www.insauga.com/b-c-conservatives-dump-candidate-accused-of-hitler-remarks/), [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/jordan-mcintosh/)

**Vancouver-West End** (`VNW`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Spencer Chandra Herbert (BC NDP): [BC Government: Minister Spencer Chandra Herbert biography](https://news.gov.bc.ca/ministries/indigenous-relations-and-reconciliation/biography)
- Scott MacDonald (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/donald-scott-macdonald/)
- Dion Weisner (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/dion-weisner/)

**Vancouver-Yaletown** (`VNY`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Sam Chandola (CentreBC): [CentreBC candidate page](https://www.centrebc.ca/candidates/sam-chandola/), [Elections BC Statement of Votes 2024](https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf)
- Margareta Dovgal (BC Conservatives): [Conservative Party of BC candidate page](https://www.conservativebc.ca/candidate/margareta-dovgal/)
- Priyan Samarakoone (BC Greens): [BC Greens candidate page](https://bcgreens.ca/candidates-2026/priyan-samarakoone/)
- Terry Yung (BC NDP): [BC Government: Minister of State Terry Yung biography](https://news.gov.bc.ca/ministries/community-safety-and-integrated-services/biography), [BC NDP: our eighteen newest MLAs (party)](https://www.bcndp.ca/latest/our-eighteen-newest-mlas-standing-strong-bc-you-every-day)
- Timothy Webster (On the ballot; withdrew Oct 8): [Elections BC: candidate withdrawn, Vancouver-Yaletown (Oct 2026)](https://elections.bc.ca/news/2026-provincial-general-election-candidates-update/)

**West Vancouver-Capilano** (`WVC`)

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Honieh Barzegari (BC NDP): [BC NDP release, more candidates (2026)](https://www.bcndp.ca/releases/more-bc-ndp-candidates-ready-fight-their-communities)
- Naomi Chocyk (OneBC): [Elections BC: 2026 candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/), [OneBC: candidates](https://1bc.ca/candidates)
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
- Grace Lore (BC NDP): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Rajinder S. Sahota (BC Greens): [Elections BC candidate list (2026)](https://elections.bc.ca/2026-provincial-election/candidate-list/), [CHEK News: All Vancouver Island candidates for the 2026 B.C. election](https://cheknews.ca/all-vancouver-island-candidates-for-the-2026-b-c-election-1351308/)
- Joachim Agou (Conservative on the ballot; dropped by the party Oct 8): [Times Colonist: turfed Conservative candidate to run as independent (Oct 9, 2026)](https://www.timescolonist.com/2026-bc-votes/turfed-bc-conservative-candidate-to-run-as-independent-in-victoria-beacon-hill-12881081), [CBC: Conservatives drop Victoria-Beacon Hill candidate Joachim Agou (Oct 8, 2026)](https://www.cbc.ca/news/canada/british-columbia/b-c-conservatives-drop-candidate-for-victoria-beacon-hill-after-offensive-social-media-posts-9.7374798)

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

- 2024 result: <https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf>
- Tim Binnema (BC Greens): [BC Greens: Tim Binnema candidate page](https://bcgreens.ca/candidates/tim-binnema/), [Elections BC: Statement of Votes, 2024 Provincial General Election (PDF)](https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf)
- Jagrup Brar (BC NDP): [BC Government: Minister of Mining and Critical Minerals biography](https://news.gov.bc.ca/ministries/mining-and-critical-minerals/biography), [Jagrup Brar campaign page (party-authored)](https://jagrupbrar.bcndp.ca), [Votes and Proceedings, May 28, 2025](https://lims.leg.bc.ca/pdms/ldp/43rd1st/votes/v250528.htm), [BC Government: Eskay Creek approval](https://news.gov.bc.ca/releases/2026MCM0008-000078)
- Paul Brar (CentreBC): [CentreBC: Paul Brar candidate page](https://centrebc.ca/candidates/paul-brar/), [Surrey Now-Leader: who is running in Surrey ridings (Sept 28, 2026)](https://surreynowleader.com/2026/09/28/b-c-votes-whos-running-in-surrey-ridings-oct-24-and-what-happened-last-election/)
- Carolyn Hofbauer (OneBC): [OneBC: Carolyn Hofbauer candidate page](https://1bc.ca/candidates/chofbauer)
- Garry Purewal (BC Conservatives): [Conservative Party of BC: Garry Purewal candidate page](https://conservativebc.ca/candidate/garry-purewal/), [Conservative Party of BC: Surrey candidates (Sept 29, 2026)](https://conservativebc.ca/conservative-party-of-bc-announces-strong-surrey-candidates-for-serious-times/)

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
- [Elections BC: Statement of Votes, 2024 Provincial General Election (PDF)](https://elections.bc.ca/docs/rpt/statement-of-votes-2024-provincial-election.pdf)
- [Elections BC: Statement of Votes, 2020 Provincial General Election (PDF)](https://elections.bc.ca/docs/rpt/statement-of-votes-2020-provincial-general-election.pdf)
- [Wikipedia: Surrey-Fleetwood results, 2013 and 2017 (secondary)](https://en.wikipedia.org/wiki/Surrey-Fleetwood)
- [Stephen Taylor: 2024 Surrey-Fleetwood result](https://www.stephentaylor.ca/data/political/canada/provincial/election/bc/2024/325/)
- [338Canada: Surrey-Fleetwood projection](https://338canada.com/bc/1070e.htm)
- [PoliWave: Surrey-Fleetwood model](https://www.poliwave.com/ca/bc/ridings/surrey-fleetwood)
- [City of Surrey: Fleetwood neighbourhood profile](https://www.surrey.ca/sites/default/files/media/documents/Neighbourhood-Profile-Fleetwood.pdf)
- [Surrey Now-Leader: final list of 47 Surrey candidates (Oct 4, 2026)](https://surreynowleader.com/2026/10/04/see-the-final-list-of-47-candidates-in-10-surrey-ridings-for-b-c-election/)
- [Wikipedia: 2026 BC general election poll table (secondary)](https://en.wikipedia.org/wiki/2026_British_Columbia_general_election)
- [SWRBOT: Surrey and White Rock provincial candidates forum (Oct 15, 2026)](https://swrbot.com/events/surrey-and-white-rock-provincial-candidates-forum/)
- [Elections BC: ways to vote](https://elections.bc.ca/voting/ways-to-vote/)
- [Elections BC: vote by mail](https://elections.bc.ca/voting/ways-to-vote/vote-by-mail/)
- [Elections BC: 2026 provincial election key dates](https://elections.bc.ca/2026-provincial-election/)
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
