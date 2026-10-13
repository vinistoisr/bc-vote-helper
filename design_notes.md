# BC Vote Helper 2026: design notes

Spec: `quiz_spec.json` (built by `python -I build_spec.py` from `spec_parts/`; audited by `python -I audit_scoring.py`). Data as of 2026-10-09. Research basis: a platform research report and notes compiled on 2026-10-09 from the sources cited in the spec. Revision 2 (2026-10-09, after four independent audits; see section 7).

These notes describe version 1 (Surrey-Fleetwood only, 16 questions). Version 2 (2026-10-12) kept the 13 province-wide questions and their scores, rewrote the wording in full sentences, relabelled reading levels by experience, and added all 93 ridings, a postal code lookup and 3 regional questions for each of six regions (`spec_parts/16` to `20`), still 16 questions per voter.

## 1. What the bank contains

16 questions: 13 provincial, 3 Surrey-Fleetwood. 72 answer options. Five parties scored (NDP, Conservative, Green, CentreBC, OneBC). Five minor parties listed, not scored. Every prompt, context and option exists at five reading levels; party positions at levels 1, 3 and 5 (the UI shows level 1 at level 2 and level 5 at level 4). Scores are fixed per option and do not change with the level.

| # | id | issue | options | why it is in |
|---|---|---|---|---|
| 1 | q_cost_of_living | cost of living | 5 | Top issue for 56% of voters (Ipsos). Parties differ by instrument: deep rate cuts, a higher basic personal amount, price rules, higher incomes at the bottom, producer costs. |
| 2 | q_taxes_deficit | taxes, wealth, deficit | 5 | Record deficit in dollar terms plus four downgrades; all five parties have a distinct, published answer. Covers the "wealth inequality" item (options d and e) and the fiscal split in one place. |
| 3 | q_housing | housing | 5 | Third-ranked issue. Method split: deregulation, demand-side taxes plus mandates, non-market build plus vacancy control, outcomes test, Step Code and rent-control ban. |
| 4 | q_health | health care | 5 | Second-ranked issue. All parties say "public"; the split is delivery (public-only, mixed, private tier) and funding. |
| 5 | q_dripa | DRIPA | 5 | The sharpest either-or in the campaign; genuine five-way split (repeal and void UNDRIP, repeal, amend, keep plus treaty framework, strengthen). |
| 6 | q_sogi | SOGI 123 | 4 | Second culture-war divider. Four positions exist in the record (repeal plus parental-rights law, repeal, keep protections and let districts choose, expand); the NDP and CentreBC share the third. |
| 7 | q_drugs | toxic drugs | 4 | Life-and-death issue with a converged centre: the NDP ended decriminalization, so it sits one step from the Conservatives and the Greens stand alone. CentreBC has no party policy and is not scored. |
| 8 | q_public_safety | policing | 4 | Mid-ranked issue; the Conservatives have the most specific plan; CentreBC's problem-specific enforcement model and OneBC's repeat-offender focus are distinct. The Greens have no plan and are not scored. |
| 9 | q_economy_tariffs | economy and tariffs | 5 | The election's stated reason. LNG is shared by four parties; the split is procurement rules versus deregulation versus manufacturing versus transition. |
| 10 | q_climate_energy | climate and energy | 5 | Consumer carbon tax is gone, so the live splits are industrial pricing, targets and the pipeline. |
| 11 | q_education_childcare | education and child care | 5 | The $10-a-day freeze is a real NDP reversal; Green and CentreBC positions differ from it; OneBC (testing, strike ban, parental rights) and the Conservatives (letter grades, exams, basics) each have a home. |
| 12 | q_icbc | ICBC | 3 | Concrete, costly for Surrey families, clean NDP versus Conservative split with a 2021 record behind it. Greens and CentreBC have no position and are not scored. |
| 13 | q_democracy_power | government power | 5 | Brief asked for democracy and government conduct. Scores the NDP's record of using power, the Conservative permitting law, CentreBC's costing and oversight pitch, the Green PR pledge and OneBC's 2025 voting-rules stance. Weakest evidence base; flagged. |
| 14 | q_local_skytrain | Surrey transit | 3 | Three stations in or beside the riding; TransLink's 2028 gap. CentreBC and OneBC have no position and are not scored. |
| 15 | q_local_extortion | Surrey safety | 4 | 133 cases and 49 shootings in 2025; only CentreBC has a Surrey-specific plan; SPS transition context. Greens not scored. |
| 16 | q_local_hospital_schools | Surrey growth | 5 | Cloverdale hospital, Surrey Memorial ER, portables. Applies the health and education splits to the two biggest local capital files. |

## 2. Judgment calls

**Record over rhetoric.** Where a party's actions contradict its words, the score follows the action and the level-3 and level-5 position text says so. Concrete cases: NDP scored on the child care freeze, not the 2018 promise; on the end of decriminalization, not the 2023 launch; on the enacted 5.60% bottom rate and indexation freeze, which now appear inside its own fiscal option at every level; on its defunding of SOGI 123 (1, not 2, on "expand"); on its use of fast-track and override powers (democracy question, option a, phrased as its supporters would). Conservatives scored on 2026 text, not 2024 planks that were dropped (rent rebate, Bill 44 repeal, private clinics, two-term balance), but their 2024 and 2025 positions on industrial carbon pricing and SOGI materials pull their scores on the adjacent options (3 rather than 0). First-reading votes on private members' bills are described in party records but never scored, for every party alike.

**Merging taxes and the deficit.** One five-option question gives each party exactly one home and keeps the bank at 16.

**Splitting the right.** The Conservatives and OneBC were near-identical on cost of living and education. Each question now has a separate home for each (basic personal amount versus 25% rate cuts; letter grades and exams versus standardized testing, a strike ban and a Parental Bill of Rights). Cross-scores between parties on the same side of a question are kept within one point of each other unless the rationale documents why not (`build_spec.py` warns on the rest).

**Giving CentreBC a real home.** CentreBC has thin, prior-leader positions. Each question where it has said something has an option written as its concrete stated position (outcomes test with no new taxes or mandates until shown, price tag and annual report on every promise, treaty framework, pipeline conditions, enforcement cells, long-term care first). Valence phrases ("decide using science", "instead of announcements", "real supply over slogans") were removed because almost anyone agrees with them. Where it has said nothing (drugs, ICBC, transit) it is not scored.

**No published position means not scored.** `party_positions[P].no_position = true` marks a cell where the party has no published 2026 position (seven cells: CentreBC on drugs, ICBC and transit; Greens on public safety, ICBC and Surrey extortion; OneBC on transit). The stored scores are placeholders (2), and the question leaves that party's numerator and denominator, so denominators differ by party. The per-issue view shows "No published position". One cell is scored by inference from an adjacent stated policy and labelled `basis: inferred` (OneBC on climate, from its Step Code repeal, pipeline and deregulation items). Earlier drafts imputed moderate scores for all of these; the audits showed that pulled users toward parties on issues they never addressed.

**Kids' levels.** Level 1 uses one analogy per question (classroom, family budget, a law about deciding together with First Nations, lessons about families). Level-1 option meaning is identical to level 5; only the words change. Both sides of each question get their own reason in the kids' text (for example, involuntary care "so they can get better"; the industrial carbon price as a "climate fee", not "smoke"). No numbers at level 1 (`build_spec.py` warns on digits). Sentences at level 1 run to 24 words at most; most are shorter.

**Local scoring.** Candidates inherit party scores, with the three local questions double-weighted (`local.formula`). No incumbent adjustment: Jagrup Brar voted with his caucus in all 105 recorded divisions and no challenger has a published position. Candidate biographies live only in `local.candidates`, not inside issue positions.

**Option ordering.** The stored order runs along a spectrum (deregulate to intervene, repeal to strengthen) so the rationale can refer to letters. The front end must shuffle the display order per respondent and record the order shown (`meta.display_rules.option_order`). The audit's unshuffled worst cases show why: with 40% first-option clicks OneBC wins 46% of random voters; with 40% middle-option clicks the NDP wins 40%.

**Results rules** (`meta.display_rules`): "I'm not sure" counts as a skip; first and second place within 3 points is shown as close (the page compares the whole-number percentages it displays, so a displayed gap of 3 or less is always labelled close); the results page lists the three questions that drove the top party's lead; the family score shows an adults-only mean beside the all-members mean.

## 3. Left out, and why

- **Immigration and population.** No 2026 provincial commitment from any party except OneBC's slogan; levels are federal. Not scorable.
- **Forestry and old growth as a standalone.** Folded into economy (options d and e) and climate; only Greens and OneBC have forestry items.
- **Wildfire.** Real but low salience in Surrey-Fleetwood and not divisive in direction.
- **Seniors care as a standalone.** Folded into health (options b and e) and the local growth question.
- **Post-secondary and international students.** No party platform found.
- **Pronouns, parental notification, trans athletes, gender-affirming care.** No 2026 party position from anyone; scoring them would be guesswork. The SOGI explainer says so; the October 2025 private member's bill appears in OneBC's record only.
- **Cowichan title and private property as its own question.** Rests on section 35, not DRIPA; folded into DRIPA context.
- **A prevention-first public safety option.** Removed in revision 2: no party has published it, and it existed only to house an inferred Green score.
- **A second provincial health question.** Suggested by one audit; rejected because the bank is at the brief's size cap and the local hospital question already covers ER access.
- **Minor parties.** No platform documents; listed in `other_parties_note`.
- **Leader-personality questions.** Deliberately none; leadership turnover appears in party records, not in scoring.

## 4. Known weaknesses

1. **Platforms were incomplete on October 9.** CentreBC's platform was due October 10; the Greens' full platform and possible NDP and Conservative costings were pending. Re-run the research and rescore before advance voting opens October 16. Highest-risk cells: every CentreBC position (six of its scored cells are low confidence), Conservative housing, climate and Surrey items, the NDP's DRIPA amendment text.
2. **Single-reviewer scoring, four reviewers' findings applied.** Scores were assigned by one reviewer and revised against four independent audits (section 7). A blind second scorer with different priors has not re-scored every cell.
3. **Random-voter structure.** Under uniform random answering the Conservatives win 27% and the Greens 15% (section 5). The gap is structural, not a data error: the Conservatives have a near-twin on the ballot (OneBC gives their measures 2 or 3 as a step on its own path), and the Greens stand alone at one end of economy, climate and drugs. The respondent-side mitigations (not sure, tie display, drivers panel, method text) are in `meta.display_rules`; the party scores were left as the evidence reads.
4. **CentreBC's ideal voter now lands closer to the NDP (48) than to the Conservatives (42).** That follows from its stated positions (keep DRIPA, keep anti-discrimination law, child care as infrastructure, pipeline only with the tanker ban) and from not scoring it where it has said nothing. The October 10 platform may move it.
5. **Democracy question.** The thinnest evidence. Scoring the NDP at 4 on "use strong powers" is a record-based reading its supporters may dislike; the wording is theirs ("get things done"). OneBC's voting-rules stance is a 2025 release not repeated in 2026 (low confidence). Users can rate it low importance.
6. **Length for young children.** Sixteen questions is at the top of the brief. For levels 1 and 2 a front end could default the three local questions and q_democracy_power to optional.
7. **Option length at levels 4 and 5.** Some five-option questions carry 30 to 50 words per option. Check on phone widths.
8. **Local questions mirror party positions.** Unavoidable given the evidence; stated plainly in `local.scoring_method`. Watch the October 15 SWRBOT forum for divergent candidate statements.
9. **Polls and projection.** 338Canada's toss-up call is a model, not a riding poll, and provincial polls span ten points. The front end should not imply a winner.
10. **Level consistency is checked by hand.** `build_spec.py` blocks party names and reviewer caveats in option text and warns on digits at level 1, but there is no automated check that each level carries the same policy elements; a synonym list would be unreliable because level-1 vocabulary differs by design. Re-read all five levels of any option you edit.

## 5. Ideal-voter answer sets and audit results

Produced by `build_spec.py` and `audit_scoring.py` (revision 2). A party's ideal voter skips the questions where that party has no published position ("-").

| question | NDP | Conservative | Green | CentreBC | OneBC |
|---|---|---|---|---|---|
| q_cost_of_living | c | b | d | e | a |
| q_taxes_deficit | d | b | e | c | a |
| q_housing | b | a | c | d | e |
| q_health | a | b | d | e | c |
| q_dripa | c | b | e | d | a |
| q_sogi | c | b | d | c | a |
| q_drugs | c | b | d | - | a |
| q_public_safety | c | a | - | b | d |
| q_economy_tariffs | b | a | d | c | e |
| q_climate_energy | c | b | d | e | a |
| q_education_childcare | c | b | e | d | a |
| q_icbc | c | b | - | - | a |
| q_democracy_power | a | b | d | c | e |
| q_local_skytrain | a | b | c | - | - |
| q_local_extortion | c | b | - | a | d |
| q_local_hospital_schools | a | b | c | d | e |

Alignment for each ideal voter (all questions medium importance, provincial formula; best achievable is 100 for every party):

| ideal voter | NDP | Conservative | Green | CentreBC | OneBC | winner | margin |
|---|---|---|---|---|---|---|---|
| NDP | 100.0 | 23.4 | 40.4 | 46.2 | 3.3 | NDP | 53.8 |
| Conservative | 25.0 | 100.0 | 0.0 | 40.4 | 68.3 | Conservative | 31.7 |
| Green | 30.8 | 0.0 | 100.0 | 27.3 | 0.0 | Green | 69.2 |
| CentreBC | 48.1 | 42.3 | 38.6 | 100.0 | 21.2 | CentreBC | 51.9 |
| OneBC | 0.0 | 53.3 | 0.0 | 11.5 | 100.0 | OneBC | 46.7 |

The local formula produces the same winners. With high importance on each party's three most distinctive questions the margins are 55.4, 30.9, 73.4, 54.7 and 51.4.

Random voters (20,000, uniform options and importance): mean alignment NDP 41.1, Conservative 46.4, Green 36.8, CentreBC 45.0, OneBC 41.8; wins NDP 16.5%, Conservative 27.3%, Green 14.8%, CentreBC 23.1%, OneBC 18.3%. No party is outside the 8 to 35% band; 30% skipping and the local formula move these by under 3 points. 50/50 split voters: NDP-Conservative 51.7/48.3, NDP-Green 55/45, Conservative-OneBC 24.6/75.4 (was 13.6/86.4 before revision 2), NDP-CentreBC 66/34. Closest pair: Conservative-OneBC (ideal margins 31.7 and 46.7, up from 20.3 and 39.1). 28.8% of random voters have a first-to-second gap under 3 points, which is why ties are shown.

## 6. Refresh checklist before October 16

- CentreBC platform (October 10): rescore every CentreBC cell; remove `no_position` flags where it now has a position (drugs, ICBC, transit); update confidence.
- Green full platform: check safety, ICBC, transit; remove `no_position` flags if positions appear.
- Conservative releases: housing, Surrey items (hospital, SkyTrain, SPS), industrial carbon price, costing.
- NDP: any DRIPA amendment text, child care, education, Surrey Police Service.
- October 14 debate and October 15 SWRBOT forum: candidate statements that depart from party lines.
- Elections BC: confirm the 2024 margin (751 by the figures that reconcile with the vote total) and any candidate withdrawals.
- Re-run `python -I build_spec.py` (fails on missing levels, bad scores, em dashes, party or plan names and reviewer caveats in option text, no_position cells without placeholder scores, scored cells without a 4, or a party that cannot win) and `python -I audit_scoring.py` (schema, ideal voters, random-voter skew, pair splits).

## 7. Revision log (2026-10-09)

Four independent audits (neutrality N1-N25, facts F1-F15, language L1-L22, scoring S1-S6). Every finding was arbitrated; "accepted" means applied to `quiz_spec.json` (via `spec_parts/`), `build_spec.py` or `audit_scoring.py`.

### Neutrality audit

- **N1 CentreBC valence options and hedge scores.** Accepted. Rewrote CentreBC's homes in housing (outcomes test, no new taxes or rules until shown), climate (pipeline conditions only), health (paperwork, home care, long-term care), democracy (price tag on every promise, annual report, legislature vote before big powers), Surrey growth (scorecards, seniors first, AI literacy); deleted "instead of announcements", "Decide using science", "real supply over slogans", "every grant tracked on a public scorecard". CentreBC on drugs is now not scored (see N16) rather than 3 on one option; the leader's record stays in the explainer. CentreBC democracy confidence set to low; taxes left medium with a "no costing published" note. Rejected the suggested housing text "keep the speculation tax and the four-homes-per-lot law as they are": CentreBC has no position on either, so that would invent one.
- **N2 Fixed option order.** Accepted as a display rule (`meta.display_rules.option_order`: shuffle per respondent and family member, record the order shown, alternate direction in print). Stored order unchanged because every rationale refers to letters. The audit now reports the unshuffled worst cases (OneBC 45.6% under first-option bias, NDP 40.2% under middle-option bias) to show why the shuffle is mandatory.
- **N3 Prompts built from the NDP's record.** Accepted. Prompts at levels 3 to 5 neutralized in cost of living, taxes, health, SOGI, economy, education, democracy, Surrey extortion, Surrey growth and DRIPA (level 4); the record facts moved to context, balanced with other parties' records.
- **N4 DRIPA kids' framing.** Accepted in full: "law" not "promise", "First Nations governments" not "those families' councils", new label and context, "legal force" not "teeth".
- **N5 SOGI label, prompt, c/d duplicate, Conservative contradiction.** Accepted. Label and prompt rewritten with both sides' reasons; c and d merged into one keep-protections, districts-choose option (NDP 4, CentreBC 4, Green 2, Conservative 1, OneBC 0); first-reading votes removed from the level-5 prompt and context.
- **N6 Climate kids' wording, party names, OneBC inference.** Accepted: "climate fee on big companies" and "pollution that warms the planet" replace "smoke"; option e is the concrete pipeline conditions; party-naming clause deleted; OneBC marked `basis: inferred`, confidence low.
- **N7 Economy kids' verbs and NDP on option a.** Accepted, including NDP 1 to 2 on resource-led growth (LNG expansion, fast-track bills and faster permitting are its record); scorecard and costing clauses deleted from option c.
- **N8 Democracy analogy, option a record items, churn notes.** Accepted: class-leader prompt; option a without "early elections" or "snap dissolution"; leadership-churn sentences removed from the Conservative and OneBC issue positions (they remain in party records, and CentreBC's now does too per N17); NDP 1 to 2 on costed plans.
- **N9 ICBC kids' prompt and inferred Greens/CentreBC.** Accepted: balanced prompt with both sides' cost; Greens and CentreBC not scored.
- **N10 Taxes wording at levels 1 and 2.** Accepted: balanced contexts, even verbs, borrowing restored in d at level 1, the enacted Budget 2026 measures added to d at all five levels (not only 4 and 5, to keep the level rule), evaluative clauses removed from a, b and e.
- **N11 Drugs framing.** Accepted: prompt 2 and context 1 give both sides their reason; "so they can get better" added; context 4 names supporters of involuntary care as well as the critic; Conservative position carries the Charter ruling note.
- **N12 Health asides.** Accepted (c at level 3 in supporters' terms; d level 1; CentreBC e without digs).
- **N13 Same option, different meaning across levels.** Accepted: every listed element was deleted from levels 4 and 5 (SOGI testing and transition bill, bubble zones, SOGI repeal and Parental Bill of Rights in education and Surrey growth, pipeline in economy a, early elections, "roll back decriminalization", extortion clause) or added at every level (taxes d; teacher strike ban is now its own option at all levels). The suggested per-option keyword check was rejected: level-1 vocabulary differs by design, so a synonym list would be unreliable. `build_spec.py` instead blocks party, leader and plan names and reviewer caveats in option text.
- **N14 Double counting.** Accepted: public safety option b is the problem-specific enforcement model without the Surrey specifics (which stay in the local question); the prevention-only option was dropped; SOGI and extortion content removed from education and Surrey growth.
- **N15 Conservative-OneBC cross-score asymmetry.** Accepted with a symmetry warning in `build_spec.py`. Cells changed: health b OneBC 3 to 2, democracy b OneBC 3 to 2, Surrey growth b OneBC 3 to 2, public safety a OneBC 3 to 2 (instead of raising the Conservatives on e, which the evidence does not support), taxes a Conservative 1 to 2, DRIPA a Conservative 3 to 2. The 50/50 split moved from 86/14 to 75/25. The residual lean is evidence-based: OneBC endorses each Conservative measure as a step on its own path, while the Conservatives have not endorsed OneBC's further steps.
- **N16 Directional scores for parties with no position.** Accepted in the preferred form: seven cells excluded from the party's numerator and denominator, "No published position" in the per-issue view, placeholder scores of 2. OneBC on climate kept as an inference from adjacent stated policy and labelled.
- **N17 Uneven record notes.** Accepted: CentreBC record now carries the Milobar and seven-MLA return and Sturko's 2024 Conservative platform; CentreBC child care carries the uncosted-universal note; Weaver removed from position, context and rationale; Green housing carries the Bills 44 and 46 votes, cost of living the unpublished revenue method, record the budget second and third reading votes.
- **N18 Party summaries.** Accepted: level-1 one-liners rewritten for all five; level-3 critiques added for Greens, OneBC and CentreBC; Conservative record gains its own-light items; first-reading votes stay in the party record and the SOGI position only.
- **N19 Party, leader and plan names in option text.** Accepted; all eleven removed and `build_spec.py` fails on any recurrence.
- **N20 Trade-offs at levels 1 and 2 in the Surrey growth question.** Partly accepted: stated funding added where the party stated it (Conservative "without raising taxes", Green wealth tax). Rejected "no promise yet about the new hospital" and "with no new public building promised" inside options: those are gap caveats, which N25 and L8 remove from option text.
- **N21 Context editorializing.** Accepted: "most detailed plan" removed; public safety and cost of living contexts carry both sides' facts (violent crime up a third since 2017 and no NDP numeric police pledge; Conservative cut uncosted and nothing for non-taxpayers; Green revenue method unpublished).
- **N22 Frightening kids' wording.** Accepted (extortion prompts 1 and 2, drugs prompt 2).
- **N23 Character and biography notes.** Accepted: Brodie's removal from caucus worded neutrally and kept at level 5 and in `leader_note` only; candidate bios kept in `local.candidates` and removed from issue positions at every level; "forced" replaced with "required by law" everywhere.
- **N24 Weighting.** Accepted for the adults-only family mean, the "what drove your match" panel and tie display (`meta.display_rules`). Rejected a second provincial health question (bank at the size cap; the Surrey growth question covers ER access) and a non-medium default importance (the user sets it; the method text now says a centrist match follows from partial agreement with everyone).
- **N25 Auditor's critique inside options.** Accepted for every listed clause; `build_spec.py` fails on "uncosted", "unaddressed", "unpublished", "unquantified", "unspecified", "platform due" and similar tokens in option text.

### Facts audit

- **F1 Non-neutral scores for parties with no stated position.** Accepted (same implementation as N16); SkyTrain option b is now Conservative-only and CentreBC and OneBC are not scored there.
- **F2 OneBC on climate option a.** Partly accepted: party-naming clause deleted, confidence low, basis inferred. Score kept at 4 because the Step Code repeal (a CleanBC building measure) and the pipeline are stated items; lowering to 3 would leave OneBC with no home on the question, and marking it no-position would discard a stated energy policy.
- **F3 Conservatives 3 on DRIPA option a.** Accepted: 2, with the first-reading rule stated in the rationale and applied the same way in the SOGI question.
- **F4 DRIPA option c level 5 and CentreBC 3 on it.** Accepted: amendment described by target not section number, Narwhal piece cited; CentreBC 2.
- **F5 2024 margin 753.** Accepted: 751, with the Stephen Taylor figure noted.
- **F6 Doerkson interim-leader source.** Accepted: Global News explainer added to Conservative sources.
- **F7 SOGI quote attribution.** Accepted: the plan page is quoted only for "safe place for our kids" and "lightning rod for division" (as the notes record), "arithmetic and reading" is attributed to CBC with the URL added, "has to be repealed" is no longer presented as a page quote, and the DRIPA plan page date is given as October 7 with the September 23 first pledge.
- **F8 Fuel tax cost $250M to $280M.** Accepted: "about $250M per the Premier as reported", BOE Report cited, duration removed.
- **F9 Bill 32 context.** Accepted.
- **F10 NDP 2 on "no stealth taxes".** Accepted: 1.
- **F11 OneBC voting rules from 2025.** Accepted: low confidence, "not repeated in 2026" in the position text.
- **F12 Seat counts and OneBC status.** Accepted: labelled secondary; the status conflict is stated rather than resolved.
- **F13 CentreBC author and date notes.** Accepted: Loke and Kirkpatrick named on the extortion plan, Bernier already named on DRIPA; re-score after October 10 remains on the checklist.
- **F14 "Largest ever".** Accepted: "in dollar terms", moved out of the prompt.
- **F15 North Coast Transmission Line $3.5B.** Accepted: funding commitment, line about $6B.

### Language audit

- **L1 Taxes d omits borrowing at level 1.** Accepted (and c level 1 as suggested).
- **L2 Economy b omits gas at level 1.** Accepted.
- **L3 Housing d level 1 contradicts higher levels.** Accepted; this version was used in preference to N1's.
- **L4 SOGI a level 5 adds the transition bill.** Accepted.
- **L5 SOGI c and d indistinguishable at level 1.** Superseded by the merge (N5): the policy difference the proposed texts describe is not in the record.
- **L6 Surrey growth a level 1 "richest".** Accepted.
- **L7 Cost of living d levels 1 and 2 omit the tax elements.** Accepted.
- **L8 Reviewer caveats and names at levels 4 and 5.** Accepted for every listed clause (build check added).
- **L9 Extortion prompt 2 shootings.** Accepted.
- **L10 SOGI label and prompt.** Accepted (label from this audit; prompt merged with N5).
- **L11 Taxes "hope".** Accepted, including the a and e rewrites.
- **L12 Level-1 sentence length.** Accepted for every sentence of 25 words or more (split into shorter sentences); the 15-word target is not met everywhere, the longest remaining sentence is 24 words.
- **L13 Democracy prompt and option d.** Accepted.
- **L14 "Toughest", "hardest", "most detailed", "best way", "clear street disorder".** Accepted.
- **L15 Numbers at level 1.** Accepted; `build_spec.py` warns on digits at level 1 and number words were replaced where the audit listed them.
- **L16 "Province" at level 1.** Accepted.
- **L17 Health d level 1.** Accepted.
- **L18 DRIPA a level 1 and d level 4.** Accepted.
- **L19 Drugs prompt 2.** Accepted (merged with N11).
- **L20 Level 3/4 additions.** Accepted: extortion clause, vaccines and Mental Health Act powers removed; climate a level 1 gains "drop the goals".
- **L21 Jargon at levels 2 and 3.** Accepted.
- **L22 Tone imbalances.** Accepted.

### Scoring audit

- **S1 Surrey extortion drives Green skew.** Accepted, form (b): Greens not scored there.
- **S2 Eight structural-ceiling cells.** Accepted: seven cells are now `no_position`; the Conservative education ceiling was fixed by splitting option a into separate OneBC and Conservative homes. Every party's ceiling is now 100% over its scored questions.
- **S3 CentreBC's centrist advantage.** Accepted on the respondent side (not-sure counts as skip, ties under 3 points shown as close, method text). Party scores left as the evidence reads; CentreBC's random win rate is now 23.1% (was 26.0%).
- **S4 Conservative-OneBC near-identical.** Accepted: cost of living and education options split; ideal margins now 31.7 and 46.7 (were 20.3 and 39.1).
- **S5 NDP-CentreBC on SOGI.** Rejected as written: the proposed c/d distinction is tonal, not policy, so the options were merged (N5). The pair remains separated by cost of living, taxes and housing (3-point gaps).
- **S6 Party positions only at levels 1, 3 and 5.** Accepted: mapping documented (`display_rules.party_positions_levels`: 2 shows 1, 4 shows 5).

### Script changes

- `build_spec.py`: understands `no_position` (placeholder 2s, per-party denominators, ideal voters skip), accepts `basis: inferred` (must be low confidence), fails on party, leader or plan names and on reviewer caveats in option text, fails on a scored party without a 4, warns on cross-score asymmetry over one point, on digits at level 1 and on a party with several 4s.
- `audit_scoring.py`: same `no_position` rules in the schema check, ideal-voter test (now also checks the local formula) and random-voter simulations; adds unshuffled primacy and middle-option bias runs, 50/50 split-voter rates for every pair, and an OVERALL PASS/FAIL line.
