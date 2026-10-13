// V2 riding checks. Needs `npx wrangler dev --port 8799` running in bc-vote-helper-v2/site.
// Run: node riding_check.js [baseUrl]
const REPO_ROOT = require("path").resolve(__dirname, "..");
const SP = process.env.TEST_TMP || require("path").join(__dirname, ".tmp");
for (const d of ["", "/shots", "/smoke_v2", "/smoke_v2/shots"]) require("fs").mkdirSync(SP + d, { recursive: true });
const { chromium } = require("playwright-core");
const fs = require("fs");
const BASE = process.argv[2] || "http://127.0.0.1:8799/";
const ROOT = REPO_ROOT + "";
const SHOTS = SP + "/shots";
const EXE = process.env.CHROMIUM_PATH || undefined;
let pass = 0, fail = 0;
function check(n, ok, d) { ok ? pass++ : fail++; console.log((ok ? "PASS " : "FAIL ") + n + (d !== undefined ? "  | " + String(d).slice(0, 260) : "")); }
const state = (p) => p.evaluate(() => BCVH.getState());
const noH = (p) => p.evaluate(() => document.scrollingElement.scrollWidth <= innerWidth);

function watch(p, errs) {
  p.on("pageerror", (e) => errs.push("pageerror " + e.message));
  p.on("console", (m) => { if (m.type() === "error") errs.push("console " + m.text()); });
}
async function fresh(p) {
  await p.goto(BASE, { waitUntil: "load" });
  await p.evaluate(() => { try { localStorage.clear(); } catch (e) {} });
  await p.reload({ waitUntil: "load" });
  await p.waitForSelector("#setup-title");
}
async function pickFromList(p, code) {
  if (await p.$("#riding-change")) await p.click("#riding-change");
  await p.selectOption("#riding-select", code);
  await p.waitForSelector("#riding-change");
}
/** Answer everything one at a time; person k picks option (q + k) so people differ. Returns the question counts seen. */
async function finishSolo(p) {
  const seen = new Set();
  for (let guard = 0; guard < 200; guard++) {
    if (await p.$("#res-title")) break;
    if (await p.$("#handoff-go")) { await p.click("#handoff-go"); continue; }
    await p.waitForSelector("#q-title");
    const qc = (await p.textContent(".qcount")).trim();
    seen.add(qc.replace(/Question \d+ of /, ""));
    const n = Number((qc.match(/Question (\d+)/) || [])[1] || 1);
    const ids = await p.$$eval('input[name="choice"]', (xs) => xs.map((x) => x.id).filter((i) => !/skip$/.test(i)));
    const cur = (await state(p)).cur;
    await p.click(`label[for="${ids[(n + cur) % ids.length]}"]`);
    await p.click("#next-btn");
  }
  await p.waitForSelector("#res-title");
  return [...seen];
}
async function finishTogether(p, count) {
  const seen = new Set();
  for (let guard = 0; guard < 60; guard++) {
    if (await p.$("#res-title")) break;
    await p.waitForSelector("section.tg #q-title");
    seen.add((await p.textContent(".tg-head .who")).replace(/Question \d+ of /, "").trim());
    const order = await p.$$eval(".tg-opt", (xs) => xs.map((x) => x.id.replace("tg-opt-", "")));
    for (let i = 0; i < count; i++) await p.click(`label[for="tg-c-${i}-${order[(i * 2) % order.length]}"]`);
    await p.click("#next-btn");
  }
  await p.waitForSelector("#res-title");
  return [...seen];
}
async function resultsFacts(p) {
  return p.evaluate(() => ({
    eyebrow: document.querySelector(".res-head .eyebrow").textContent,
    localCards: document.querySelectorAll(".hl-card.hl-local").length,
    cands: document.querySelectorAll("#riding .cand:not(.cand-other)").length,
    issues: document.querySelectorAll("#breakdown details.issue").length,
    breakdownEyebrow: document.querySelector("#breakdown .eyebrow").textContent,
    ridingTitle: (document.getElementById("riding-title") || {}).textContent,
    localTags: Array.from(document.querySelectorAll("#breakdown .sum-title .tag")).map((t) => t.textContent),
    text: document.getElementById("app").innerText,
  }));
}

async function siteRun(browser) {
  const ctx = await browser.newContext({ viewport: { width: 1263, height: 667 }, geolocation: { latitude: 49.2606, longitude: -123.246 }, permissions: ["geolocation"] });
  const p = await ctx.newPage();
  const errs = []; watch(p, errs);
  const lookups = []; p.on("request", (r) => { if (r.url().includes("/api/riding")) lookups.push(r.url()); });
  await fresh(p);

  // Setup copy and picker
  check("picker shown above the people", await p.evaluate(() => { const a = document.getElementById("riding-pick"), b = document.querySelector(".people"); return !!a && !!b && (a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING) > 0; }));
  check("no riding: lede says 13 questions", /Answer 13 short questions/.test(await p.textContent("#setup-lede")), await p.textContent("#setup-lede"));
  check("share text mentions riding", /answers, reading level, your riding and rough location \(city\)/.test(await p.textContent(".share-opt")));
  check("no age wording on setup", !/\bAges?\b|Little kids|Adults|teens?\b/i.test(await p.textContent("#app")));
  check("experience shown beside level", (await p.textContent("#lvl-exp-0")) === "Follow the news a bit");
  check("93 ridings in the list, grouped by 6 regions", (await p.$$eval("#riding-select option[value]:not([value=''])", (o) => o.length)) === 93 && (await p.$$eval("#riding-select optgroup", (g) => g.length)) === 6);
  await p.screenshot({ path: SHOTS + "/setup-1263x667.png", fullPage: true });

  // Postal code validation (no network for these)
  await p.fill("#pc-input", "M5V 3L9"); await p.click("#pc-find");
  check("outside BC message", /outside BC/.test(await p.textContent("#riding-status")), await p.textContent("#riding-status"));
  await p.fill("#pc-input", "12345"); await p.click("#pc-find");
  check("bad format message", /does not look like a postal code/.test(await p.textContent("#riding-status")));
  check("no lookup for invalid codes", lookups.length === 0, lookups.join(" "));

  // Real lookup through the worker and Represent
  await p.fill("#pc-input", "v3s 1a1");
  await p.press("#pc-input", "Enter");
  await p.waitForSelector("#riding-change", { timeout: 20000 });
  check("V3S 1A1 resolves to Surrey-Panorama", (await p.textContent("#riding-name")) === "Surrey-Panorama", await p.textContent("#riding-name"));
  check("lookup went to /api/riding only", lookups.length === 1 && /\/api\/riding\?pc=V3S1A1$/.test(lookups[0]), lookups.join(" "));
  check("masthead chip shows riding", (await p.textContent("#mast-riding")) === "Surrey-Panorama" && !(await p.$eval("#mast-riding", (e) => e.hidden)));
  const supN = await p.evaluate(() => BCVH.spec.ridings.filter((r) => r.code === "SUP")[0].candidates.length);
  const supMeta = await p.textContent("#riding-meta");
  check("Surrey-Panorama: candidate count from spec, 3 local questions", (supN ? new RegExp("^Surrey\\. " + supN + " candidates?") : /Candidate list not loaded yet/).test(supMeta) && /3 local questions/.test(supMeta), supMeta);
  check("lede now 16 questions", /Answer 16 short questions/.test(await p.textContent("#setup-lede")));
  const ls = await p.evaluate(() => localStorage.getItem("bcvh2026:v1") || "");
  check("postal code not in localStorage", !/V3S|v3s|1A1/i.test(ls) && /"riding":"SUP"/.test(ls));
  await p.reload({ waitUntil: "load" });
  check("riding kept through reload", (await p.textContent("#riding-name")) === "Surrey-Panorama");

  // Use my location (site only): Point Grey coordinates
  await p.click("#riding-change");
  check("Use my location offered on the site", await p.isVisible("#geo-btn"));
  await p.click("#geo-btn");
  await p.waitForSelector("#riding-change", { timeout: 20000 });
  check("location resolves to Vancouver-Point Grey", (await p.textContent("#riding-name")) === "Vancouver-Point Grey", await p.textContent("#riding-name"));
  check("location sent rounded to 3 decimals", /lat=49\.261&lon=-123\.246$/.test(lookups[lookups.length - 1]), lookups[lookups.length - 1]);
  // Local location lookup through the real Worker (no Represent call)
  const pg = await p.evaluate(() => fetch("/api/riding?lat=53.917&lon=-122.749").then((r) => r.json()));
  check("API: Prince George point -> PRV (local shapes)", pg.code === "PRV", JSON.stringify(pg));
  const van = await p.evaluate(() => fetch("/api/riding?lat=49.283&lon=-123.120").then((r) => r.json()));
  check("API: downtown Vancouver point -> a Vancouver riding", /^VN/.test(van.code), JSON.stringify(van));
  // Busy lookup service: the Worker offers a short pick list for the postal code area
  await p.route("**/api/riding?pc=V0B9Z9", (r) => r.fulfill({ contentType: "application/json", body: JSON.stringify({ approximate: true, choices: [{ code: "KOC", name: "Kootenay Central" }, { code: "CLR", name: "Columbia River-Revelstoke" }, { code: "KOR", name: "Kootenay-Rockies" }] }) }));
  await p.click("#riding-change");
  await p.fill("#pc-input", "V0B 9Z9");
  await p.click("#pc-find");
  await p.waitForSelector("#riding-choices [data-riding]", { timeout: 10000 });
  check("fallback: short pick list of 3 ridings", (await p.$$eval("#riding-choices [data-riding]", (b) => b.map((x) => x.textContent))).join("|") === "Kootenay Central|Columbia River-Revelstoke|Kootenay-Rockies");
  check("fallback: plain status asks to pick", /Pick yours/.test(await p.textContent("#riding-status")) && !/—/.test(await p.textContent("#riding-status")), await p.textContent("#riding-status"));
  check("fallback: postal code not saved", !/V0B|9Z9/.test(await p.evaluate(() => JSON.stringify(localStorage))));
  await p.click('#riding-choices [data-riding="CLR"]');
  await p.waitForSelector("#riding-change");
  check("fallback: picking one sets the riding", (await p.textContent("#riding-name")) === "Columbia River-Revelstoke" && (await state(p)).riding === "CLR");
  await p.unroute("**/api/riding?pc=V0B9Z9");

  // Surrey-Fleetwood from the list, 1 person
  await pickFromList(p, "SRF");
  check("Surrey-Fleetwood picked from list", (await p.textContent("#riding-name")) === "Surrey-Fleetwood" && /5 candidates/.test(await p.textContent("#riding-meta")));
  await p.click("#start-btn");
  await p.waitForSelector("#q-title");
  // local tag on a local question shows the region name
  const tag = await p.evaluate(() => { const s = BCVH.getState(); s.qi = 13; BCVH.setState(s); return (document.querySelector(".qcard .tag") || {}).textContent; });
  check("local question tag shows region (Surrey)", tag === "Surrey", tag);
  await p.evaluate(() => { const s = BCVH.getState(); s.qi = 0; BCVH.setState(s); });
  let seen = await finishSolo(p);
  check("1 person solo: 16 questions", seen.length === 1 && seen[0] === "16", seen.join(","));
  let R = await resultsFacts(p);
  check("1 person: results riding Surrey-Fleetwood", /^Surrey-Fleetwood/.test(R.eyebrow) && R.ridingTitle === "Surrey-Fleetwood", R.eyebrow);
  check("1 person: candidate headline + 5 candidates", R.localCards >= 1 && R.cands === 5, JSON.stringify({ l: R.localCards, c: R.cands }));
  check("1 person: All 16 questions in breakdown", R.issues === 16 && /All 16 questions/.test(R.breakdownEyebrow), R.issues + " " + R.breakdownEyebrow);
  check("1 person: local tags say Surrey", R.localTags.length === 3 && R.localTags.every((t) => t === "Surrey"), R.localTags.join(","));
  // Page wording only: "kids" can appear in question text (school policy), which is not a reading-level label
  const ageHit = R.text.match(/.{0,50}(\bAges? \d|Little kids|For kids|\bAdults\b|team's|\bteams\b).{0,30}/i);
  check("no age wording on results", !ageHit, ageHit && ageHit[0]);
  const txt = await p.evaluate(() => BCVH.resultsText());
  check("text summary names Surrey-Fleetwood and closest candidate", /^Surrey-Fleetwood \|/m.test(txt) && /Surrey-Fleetwood: (closest candidate|close result)/.test(txt), txt.split("\n").slice(0, 6).join(" / "));
  await p.evaluate(() => scrollTo(0, 0));
  await p.screenshot({ path: SHOTS + "/results-srf-1263x667.png" });
  check("no h-scroll results 1263", await noH(p));

  // 2 people, one at a time
  await p.click("#tb-reset"); await p.click("#reset-yes"); await p.waitForSelector("#setup-title");
  check("reset clears riding", (await state(p)).riding === null && !!(await p.$("#riding-select")));
  await pickFromList(p, "SRF");
  await p.click('label[for="count-2"]');
  await p.fill("#name-0", "Alex"); await p.fill("#name-1", "Sam");
  await p.click("#start-btn");
  seen = await finishSolo(p);
  check("2 people solo: 16 questions", seen.length === 1 && seen[0] === "16", seen.join(","));
  R = await resultsFacts(p);
  check("2 people solo: Surrey-Fleetwood candidates", R.localCards >= 1 && R.cands === 5 && R.issues === 16, JSON.stringify({ l: R.localCards, c: R.cands, i: R.issues }));
  check("2 people solo: family columns say L3-5, not Adults", /L3-5/.test(R.text) && !/Adults/.test(R.text));

  // 2 people, together
  await p.click("#tb-reset"); await p.click("#reset-yes"); await p.waitForSelector("#setup-title");
  await pickFromList(p, "SRF");
  await p.click('label[for="count-2"]');
  await p.click('label[for="mode-together"]');
  await p.click("#start-btn");
  await p.waitForSelector("section.tg");
  check("Together slider shows experience", /Follow the news a bit/.test(await p.textContent("#tg-level-now")), await p.textContent("#tg-level-now"));
  seen = await finishTogether(p, 2);
  check("2 people together: 16 questions", seen.length === 1 && seen[0] === "16", seen.join(","));
  R = await resultsFacts(p);
  check("2 people together: Surrey-Fleetwood candidates", R.localCards >= 1 && R.cands === 5 && R.issues === 16, JSON.stringify({ l: R.localCards, c: R.cands, i: R.issues }));

  // Switch to a riding with no local questions yet: Vancouver-Point Grey (keep answers)
  const before = await p.evaluate(() => BCVH.getState());
  await p.evaluate(() => { const s = BCVH.getState(); s.phase = "setup"; BCVH.setState(s); });
  await pickFromList(p, "VNP");
  check("VNP: Metro local questions", !/No local questions yet/.test(await p.textContent("#riding-meta")) && /Answer 16 short questions/.test(await p.textContent("#setup-lede")), await p.textContent("#riding-meta"));
  const kept = await p.evaluate(() => BCVH.getState());
  check("Surrey answers kept in state after switching", Object.keys(kept.people[0].answers).filter((k) => /^q_local_/.test(k)).length === 3);
  const scoreSame = await p.evaluate((b) => {
    const a = BCVH.getState().people[0].answers;
    const stripped = {}; Object.keys(a).forEach((k) => { if (!/^q_local_/.test(k)) stripped[k] = a[k]; });
    return JSON.stringify(BCVH.scoreParties(a)) === JSON.stringify(BCVH.scoreParties(stripped));
  });
  check("other region's answers do not count", scoreSame);
  await p.evaluate(() => { const s = BCVH.getState(); s.phase = "results"; BCVH.setState(s); });
  await p.waitForSelector("#res-title");
  R = await resultsFacts(p);
  check("VNP results: 16 questions", R.issues === 16 && /All 16 questions/.test(R.breakdownEyebrow), R.issues);
  const vnpN = await p.evaluate(() => BCVH.spec.ridings.filter((r) => r.code === "VNP")[0].candidates.length);
  check("VNP results: its own candidates (" + vnpN + "), headline when scored", R.cands === vnpN && (vnpN ? R.localCards >= 1 : /Candidate list not loaded yet/.test(R.text)), JSON.stringify({ c: R.cands, l: R.localCards }));
  check("VNP results: local weighting note mentions counted double", /counted double/.test(R.text) || !vnpN, (R.text.match(/Candidates[^.]*\./) || [""])[0]);
  const own = await p.evaluate(() => [".res-head", ".hl-grid", "#ranked", "#riding", ".jump"].map((s) => (document.querySelector(s) || {}).textContent || "").join(" "));
  check("VNP results: no Surrey-Fleetwood in page-owned sections", !/Fleetwood/.test(own));
  // A riding with unscored candidates lists them under the scored ones
  const withOthers = await p.evaluate(() => { const r = BCVH.spec.ridings.filter((x) => x.others && x.others.length)[0]; return r ? { code: r.code, n: r.others.length, name: r.others[0].name } : null; });
  if (withOthers) {
    await p.evaluate((c) => { const s = BCVH.getState(); s.riding = c; BCVH.setState(s); }, withOthers.code);
    const oth = await p.evaluate(() => ({ n: document.querySelectorAll("#riding .cand-other").length, head: /Also running, not scored/.test(document.getElementById("riding").textContent) }));
    check("others listed, not scored (" + withOthers.code + ")", oth.n === withOthers.n && oth.head, JSON.stringify(oth));
    const t2 = await p.evaluate(() => BCVH.resultsText());
    check("others in text summary", t2.indexOf("Also running, not scored: " + withOthers.name) >= 0);
    await p.evaluate(() => { const s = BCVH.getState(); s.riding = "VNP"; BCVH.setState(s); });
  }
  check("VNP results: riding name Vancouver-Point Grey", /^Vancouver-Point Grey/.test(R.eyebrow) && R.ridingTitle === "Vancouver-Point Grey");
  const pdf = await p.evaluate(async () => { const b = BCVH.buildResultsPdf(BCVH.getState()); return { type: b.type, size: b.size }; });
  check("VNP PDF builds", pdf.type === "application/pdf" && pdf.size > 5000, JSON.stringify(pdf));
  check("no console errors (site)", errs.length === 0, errs.join(" || "));
  await ctx.close();
}

async function noRidingAndPhone(browser) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, colorScheme: "dark" });
  const p = await ctx.newPage();
  const errs = []; watch(p, errs);
  await fresh(p);
  check("390 no h-scroll setup (picker open)", await noH(p));
  await p.screenshot({ path: SHOTS + "/setup-390x844.png", fullPage: true });
  // Skip: parties only
  await p.click("#riding-skip");
  check("skip shows Parties only", (await p.textContent("#riding-name")) === "Parties only" && (await state(p)).ridingSkip === true);
  await p.click("#start-btn");
  const seen = await finishSolo(p);
  check("no riding: 13 questions", seen.length === 1 && seen[0] === "13", seen.join(","));
  let R = await resultsFacts(p);
  check("no riding: results say pick your riding", /Pick your riding to see your local candidates/.test(R.text) && R.localCards === 0 && /^All of BC/.test(R.eyebrow), R.eyebrow);
  check("390 no h-scroll results (no riding)", await noH(p));
  const txt = await p.evaluate(() => BCVH.resultsText());
  check("no riding: text summary", /Pick your riding to see your local candidates/.test(txt));
  const pdf = await p.evaluate(async () => { const b = BCVH.buildResultsPdf(BCVH.getState()); return b.size; });
  check("no riding: PDF builds", pdf > 5000, pdf);
  // Pick your riding from results goes back to setup with picker open, then on to the local questions
  await p.click("#pick-riding-hl");
  await p.waitForSelector("#riding-select");
  await p.selectOption("#riding-select", "SRF");
  await p.click("#start-btn");
  await p.waitForSelector("#q-title");
  check("new local questions reopen the quiz at the first unanswered (Q14)", /Question 14 of 16/.test(await p.textContent(".qcount")), await p.textContent(".qcount"));
  await finishSolo(p);
  R = await resultsFacts(p);
  check("390 SRF results after adding riding", R.cands === 5 && R.issues === 16);
  await p.evaluate(() => scrollTo(0, 0));
  await p.screenshot({ path: SHOTS + "/results-srf-390x844.png" });
  await p.screenshot({ path: SHOTS + "/results-srf-390x844-full.png", fullPage: true });
  check("390 no h-scroll results (SRF, folds open)", await p.evaluate(() => { document.querySelectorAll("details").forEach((d) => (d.open = true)); return document.scrollingElement.scrollWidth <= innerWidth; }));
  // VNP at phone width
  await p.evaluate(() => { const s = BCVH.getState(); s.riding = "VNP"; BCVH.setState(s); });
  await p.evaluate(() => scrollTo(0, 0));
  await p.screenshot({ path: SHOTS + "/results-vnp-390x844.png" });
  check("no console errors (phone)", errs.length === 0, errs.join(" || "));
  await ctx.close();

  // 1263 results for VNP and setup with a riding chosen
  const c2 = await browser.newContext({ viewport: { width: 1263, height: 667 } });
  const p2 = await c2.newPage();
  const e2 = []; watch(p2, e2);
  await fresh(p2);
  await pickFromList(p2, "VNP");
  await p2.screenshot({ path: SHOTS + "/setup-riding-1263x667.png", fullPage: true });
  await p2.click("#start-btn");
  await finishSolo(p2);
  await p2.evaluate(() => scrollTo(0, 0));
  await p2.screenshot({ path: SHOTS + "/results-vnp-1263x667.png" });
  await p2.screenshot({ path: SHOTS + "/results-vnp-1263x667-full.png", fullPage: true });
  check("no console errors (1263 VNP)", e2.length === 0, e2.join(" || "));
  await c2.close();
}

// claude.ai artifact mode: window.claude present, Represent is called directly
async function artifactRun(browser) {
  let body = fs.readFileSync(ROOT + "/index.html", "utf8");
  // Test copy only: Vancouver-Point Grey with no candidate list, as before research arrives
  const m = body.match(/(<script type="application\/json" id="bcvh-spec">)([\s\S]*?)(<\/script>)/);
  const spec = JSON.parse(m[2]);
  spec.ridings.forEach((r) => { if (r.code === "VNP") { r.candidates = []; r.others = []; r.list_status = "pending"; } });
  body = body.replace(m[0], () => m[1] + JSON.stringify(spec).replace(/</g, "\\u003c").replace(/>/g, "\\u003e").replace(/&/g, "\\u0026") + m[3]);
  const PAGE = SP + "/page_riding.html";
  fs.writeFileSync(PAGE, '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>' + body + "</body></html>");
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
  await ctx.addInitScript(() => { window.claude = { use: function () { return Promise.resolve(null); } }; });
  const p = await ctx.newPage();
  const errs = []; watch(p, errs);
  const reqs = []; p.on("request", (r) => { if (/represent|api\/riding/.test(r.url())) reqs.push(r.url()); });
  await p.goto("file:///" + PAGE, { waitUntil: "load" });
  await p.evaluate(() => { try { localStorage.clear(); } catch (e) {} });
  await p.reload({ waitUntil: "load" });
  check("artifact: no Use my location button", (await p.$("#geo-btn")) === null);
  await p.fill("#pc-input", "V3S 1A1");
  await p.click("#pc-find");
  await p.waitForSelector("#riding-change", { timeout: 20000 });
  check("artifact: Represent called directly, resolves Surrey-Panorama", (await p.textContent("#riding-name")) === "Surrey-Panorama" && reqs.length === 1 && reqs[0].startsWith("https://represent.opennorth.ca/postcodes/V3S1A1/"), reqs.join(" "));
  // Failure falls back to the list
  await p.route("https://represent.opennorth.ca/**", (r) => r.abort());
  await p.click("#riding-change");
  await p.fill("#pc-input", "V6T 1Z4");
  await p.click("#pc-find");
  await p.waitForFunction(() => /Pick it from the list/.test((document.getElementById("riding-status") || {}).textContent || ""), null, { timeout: 15000 });
  check("artifact: lookup failure points to the list", await p.evaluate(() => document.activeElement && document.activeElement.id === "riding-select"));
  // Empty candidate list: "not loaded yet" on setup and results, 13 questions
  await p.selectOption("#riding-select", "VNP");
  await p.waitForSelector("#riding-change");
  check("empty list: setup says Candidate list not loaded yet", /Candidate list not loaded yet/.test(await p.textContent("#riding-meta")), await p.textContent("#riding-meta"));
  await p.click("#start-btn");
  const seenA = await finishSolo(p);
  check("empty list: 16 questions", seenA.length === 1 && seenA[0] === "16", seenA.join(","));
  const RA = await resultsFacts(p);
  check("empty list: results say not loaded yet, no candidate headline", /Candidate list not loaded yet/.test(RA.text) && RA.localCards === 0 && RA.cands === 0 && RA.issues === 16);
  await p.evaluate(() => scrollTo(0, 0));
  await p.screenshot({ path: SHOTS + "/results-notloaded-390x844.png" });
  check("empty list: 390 no h-scroll", await noH(p));
  const real = errs.filter((e) => !/ERR_FAILED|Failed to load resource|Failed to fetch/.test(e));
  check("artifact: no page errors", real.length === 0, real.join(" || "));
  await ctx.close();
}

(async () => {
  if (!fs.existsSync(SHOTS)) fs.mkdirSync(SHOTS, { recursive: true });
  const browser = await chromium.launch({ executablePath: EXE, headless: true });
  await siteRun(browser);
  await noRidingAndPhone(browser);
  await artifactRun(browser);
  await browser.close();
  console.log(`${pass}/${pass + fail} passed`);
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(2); });
