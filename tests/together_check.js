// Together mode checks for BC Vote Helper 2026. Run: node together_check.js
const REPO_ROOT = require("path").resolve(__dirname, "..");
const SP = process.env.TEST_TMP || require("path").join(__dirname, ".tmp");
for (const d of ["", "/shots", "/smoke_v2", "/smoke_v2/shots"]) require("fs").mkdirSync(SP + d, { recursive: true });
const { chromium } = require("playwright-core");
const fs = require("fs");
const ROOT = REPO_ROOT + "";
const SHOTS = SP + "/shots";
const EXE = process.env.CHROMIUM_PATH || undefined;
const body = fs.readFileSync(ROOT + "/index.html", "utf8");
const PAGE = SP + "/page_tg.html";
fs.writeFileSync(PAGE, '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>' + body + "</body></html>");
const URL = "file:///" + PAGE;
const SITE_URL = "file:///" + ROOT + "/site/public/index.html";
let pass = 0, fail = 0;
function check(n, ok, d) { ok ? pass++ : fail++; console.log((ok ? "PASS " : "FAIL ") + n + (d !== undefined ? "  | " + String(d).slice(0, 300) : "")); }
const noHScroll = (p) => p.evaluate(() => [document.scrollingElement.scrollWidth, innerWidth]);

async function setRange(p, sel, v) {
  await p.$eval(sel, (r, v) => { r.value = String(v); r.dispatchEvent(new Event("input", { bubbles: true })); r.dispatchEvent(new Event("change", { bubbles: true })); }, v);
}
async function state(p) { return p.evaluate(() => BCVH.getState()); }

async function main(browser) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, colorScheme: "dark" });
  const p = await ctx.newPage();
  const errs = [];
  p.on("pageerror", (e) => errs.push("pageerror " + e.message));
  p.on("console", (m) => { if (m.type() === "error") errs.push("console " + m.text()); });
  await p.goto(URL, { waitUntil: "networkidle" });
  await p.evaluate(() => { try { localStorage.clear(); } catch (e) {} });
  await p.reload({ waitUntil: "networkidle" });

  // 1. Toggle only with 2+ people
  await p.selectOption("#riding-select", "SRF");
  check("toggle hidden with 1 person", (await p.$("#mode-together")) === null);
  await p.click('label[for="count-2"]');
  check("toggle shown with 2 people", await p.isVisible('label[for="mode-together"]') && await p.isVisible('label[for="mode-solo"]'));
  check("default mode is one at a time", await p.isChecked("#mode-solo"));
  await p.click('label[for="count-3"]');
  check("toggle shown with 3 people", await p.isVisible('label[for="mode-together"]'));
  await p.click('label[for="mode-together"]');
  check("mode saved as together", (await state(p)).mode === "together");
  check("start button says together", /together/i.test(await p.textContent("#start-btn")), await p.textContent("#start-btn"));
  await p.fill("#name-0", "Alex");
  await p.fill("#name-1", "Sam");
  await p.fill("#name-2", "Kim");
  await setRange(p, "#level-0", 4);
  await setRange(p, "#level-1", 3);
  await setRange(p, "#level-2", 2);
  let sw = await noHScroll(p);
  check("no h-scroll setup 390", sw[0] <= sw[1], sw);
  await p.click("#start-btn");
  await p.waitForSelector("section.tg #q-title");
  let st = await state(p);
  check("phase together, default level = lowest (2)", st.phase === "together" && st.groupLevel === 2 && (await p.inputValue("#tg-level")) === "2", JSON.stringify({ ph: st.phase, gl: st.groupLevel }));
  check("focus on question heading", await p.evaluate(() => document.activeElement && document.activeElement.id === "q-title"));
  check("header shows Question 1 of 16", /Question 1 of 16/.test(await p.textContent(".tg-head")));
  check("one row per person (3)", (await p.$$(".tg-person")).length === 3);
  check("person names shown", (await p.textContent("#tg-name-0")).includes("Alex") && (await p.textContent("#tg-name-2")).includes("Kim"));

  // Letters follow person 1's order for everyone
  const q1 = await p.evaluate(() => { const s = BCVH.getState(); return { id: BCVH.spec.questions[0].id, order: s.people[0].order[BCVH.spec.questions[0].id] }; });
  const domOrder = await p.$$eval(".tg-opt", (xs) => xs.map((x) => x.id.replace("tg-opt-", "")));
  check("options in shared order (person 1)", JSON.stringify(domOrder) === JSON.stringify(q1.order), domOrder + " vs " + q1.order);
  const rowOrders = await p.$$eval(".tg-pick", (fs) => fs.map((f) => Array.from(f.querySelectorAll("input")).map((i) => i.value).filter((v) => v !== "skip").join(",")));
  check("each row uses the same letter order", rowOrders.every((r) => r === q1.order.join(",")), rowOrders.join(" | "));

  // 2. Level slider rewords live
  const before = await p.textContent("#q-title");
  const opt0before = await p.textContent("#tg-txt-" + q1.order[0]);
  await p.$eval("#tg-level", (r) => { r.value = "5"; r.dispatchEvent(new Event("input", { bubbles: true })); });
  const after = await p.textContent("#q-title");
  const exp5 = await p.evaluate(() => BCVH.pick(BCVH.spec.questions[0].prompt, 5));
  const opt0after = await p.textContent("#tg-txt-" + q1.order[0]);
  check("slider changes prompt live", before !== after && after === exp5, JSON.stringify([before, after]));
  check("slider changes option text live", opt0before !== opt0after);
  check("level label updates", /Expert/.test(await p.textContent("#tg-level-now")));
  check("slider level saved", (await state(p)).groupLevel === 5);
  sw = await noHScroll(p);
  check("no h-scroll at level 5, 390", sw[0] <= sw[1], sw);
  await p.$eval("#tg-level", (r) => { r.value = "1"; r.dispatchEvent(new Event("input", { bubbles: true })); });
  check("simple wording at level 1 (Not sure / A lot)", (await p.textContent(".tg-skip-l")) === "Not sure" && /A lot/.test(await p.textContent(".tg-imp")));
  await p.$eval("#tg-level", (r) => { r.value = "3"; r.dispatchEvent(new Event("input", { bubbles: true })); });

  // 3. Three people answer different options and importances on 4 questions
  const plan = [ // [optionIndex or "skip", importance] per person, per question
    [[0, "high"], [1, "low"], [2, "medium"]],
    [[1, "medium"], [1, "high"], ["skip", "medium"]],
    [[2, "low"], [0, "medium"], [3, "high"]],
    [[0, "high"], [2, "high"], [1, "low"]],
  ];
  for (let k = 0; k < plan.length; k++) {
    await p.waitForSelector("#q-title");
    const order = await p.$$eval(".tg-opt", (xs) => xs.map((x) => x.id.replace("tg-opt-", "")));
    for (let i = 0; i < 3; i++) {
      const [oi, imp] = plan[k][i];
      const val = oi === "skip" ? "skip" : order[oi];
      await p.click(`label[for="tg-c-${i}-${val}"]`);
      await p.click(`label[for="tg-i-${i}-${imp}"]`);
    }
    if (k === 0) {
      const chips = await p.$$eval(".tg-who", (ws) => ws.map((w) => w.textContent));
      check("who-picked chips under options", chips[0].includes("Alex") && chips[1].includes("Sam") && chips[2].includes("Kim"), chips.join(" | "));
      sw = await noHScroll(p);
      check("no h-scroll together 390 with picks", sw[0] <= sw[1], sw);
      await p.click("#tg-bg summary");
      sw = await noHScroll(p);
      check("no h-scroll with background open", sw[0] <= sw[1], sw);
      await p.evaluate(() => scrollTo(0, 0));
      await p.screenshot({ path: SHOTS + "/together-390.png", fullPage: true });
      // keyboard: arrow key moves Sam's pick to the next letter
      await p.focus(`#tg-c-1-${order[1]}`);
      await p.keyboard.press("ArrowRight");
      const sAns = (await state(p)).people[1].answers[await p.evaluate(() => BCVH.spec.questions[0].id)];
      check("arrow key changes pick (radio group)", sAns && sAns.choice === order[2], JSON.stringify(sAns));
      await p.click(`label[for="tg-c-1-${order[1]}"]`);
    }
    if (k === 1) {
      // back and forward keep answers
      await p.click("#back-btn");
      await p.waitForSelector("#q-title");
      check("back goes to Question 1", /Question 1 of 16/.test(await p.textContent(".tg-head")));
      const o1 = await p.$$eval(".tg-opt", (xs) => xs.map((x) => x.id.replace("tg-opt-", "")));
      check("back keeps picks", await p.isChecked(`#tg-c-0-${o1[0]}`) && await p.isChecked(`#tg-c-2-${o1[2]}`) && await p.isChecked("#tg-i-0-high") && await p.isChecked("#tg-i-1-low"));
      await p.click("#next-btn");
      await p.waitForSelector("#q-title");
      check("next returns to Question 2 with picks", /Question 2 of 16/.test(await p.textContent(".tg-head")) && await p.isChecked("#tg-c-2-skip"));
    }
    if (k === 2) {
      // reload mid-question
      await p.reload({ waitUntil: "networkidle" });
      await p.waitForSelector("section.tg #q-title");
      const o3 = await p.$$eval(".tg-opt", (xs) => xs.map((x) => x.id.replace("tg-opt-", "")));
      check("reload restores question and picks", /Question 3 of 16/.test(await p.textContent(".tg-head")) && await p.isChecked(`#tg-c-0-${o3[2]}`) && await p.isChecked(`#tg-c-2-${o3[3]}`) && await p.isChecked("#tg-i-2-high"));
      check("reload restores level", (await p.inputValue("#tg-level")) === "3");
    }
    await p.click("#next-btn");
  }
  // 4. Rest: Alex answers a few more, nobody else (unanswered = skip)
  for (let k = 4; k < 16; k++) {
    await p.waitForSelector("#q-title");
    check(`header Question ${k + 1}`, (await p.textContent(".tg-head")).includes(`Question ${k + 1} of 16`)) || 0;
    if (k < 8) { const order = await p.$$eval(".tg-opt", (xs) => xs.map((x) => x.id.replace("tg-opt-", ""))); await p.click(`label[for="tg-c-0-${order[k % order.length]}"]`); await p.click(`label[for="tg-c-1-${order[(k + 1) % order.length]}"]`); }
    if (k === 15) check("last Next says See results", (await p.textContent("#next-btn")).trim() === "See results");
    if (k === 15) {
      await p.setViewportSize({ width: 1280, height: 900 });
      await p.evaluate(() => scrollTo(0, 0));
      await p.screenshot({ path: SHOTS + "/together-1280.png", fullPage: true });
      sw = await noHScroll(p);
      check("no h-scroll together 1280", sw[0] <= sw[1], sw);
      await p.setViewportSize({ width: 390, height: 844 });
    }
    await p.click("#next-btn");
  }
  await p.waitForSelector("#res-title");
  st = await state(p);
  check("results phase, everyone done, finishedAt set", st.phase === "results" && st.people.slice(0, 3).every((x) => x.done) && !!st.finishedAt);
  const allAnswered = st.people.slice(0, 3).every((x) => Object.keys(x.answers).length === 16);
  check("every person has 16 answers (unanswered = skip)", allAnswered);
  const skipCount = st.people[2].answers ? Object.values(st.people[2].answers).filter((a) => a.choice === "skip").length : -1;
  check("Kim's unanswered recorded as skip", skipCount === 13, skipCount);
  const orderOk = st.people.slice(0, 3).every((x) => Object.keys(x.answers).every((qid) => JSON.stringify(x.answers[qid].order) === JSON.stringify(st.people[0].order[qid])));
  check("a.order = shared display order for all", orderOk);
  check("importance recorded per person", st.people[0].answers[q1.id].importance === "high" && st.people[1].answers[q1.id].importance === "low" && st.people[2].answers[q1.id].importance === "medium");
  // per-person differences shown
  const pc = await p.$$eval(".pcard", (cs) => cs.map((c) => c.textContent));
  check("3 per-person result cards", pc.length === 3 && pc[0].includes("Alex") && pc[2].includes("Kim"), pc.length);
  const cmp = await p.evaluate(() => {
    const s = BCVH.getState();
    const R = BCVH.computeResults(s);
    const mp = R.members.map((m) => JSON.stringify(m.parties));
    // Same answers, solo mode: family scores must match
    const solo = JSON.parse(JSON.stringify(s)); solo.mode = "solo";
    const R2 = BCVH.computeResults(solo);
    const fam = BCVH.familyScores(s.people.slice(0, s.count).map((p) => ({ answers: p.answers, level: p.level })));
    const ind = s.people.slice(0, s.count).map((p) => BCVH.scoreParties(p.answers));
    return { differ: new Set(mp).size > 1, same: JSON.stringify(R.fam) === JSON.stringify(R2.fam) && JSON.stringify(R.rankedP) === JSON.stringify(R2.rankedP), famMatch: JSON.stringify(fam.all) === JSON.stringify(R.fam.all), indMatch: JSON.stringify(ind) === JSON.stringify(R.members.map((m) => m.parties)), split: R.agreeCounts };
  });
  check("per-person scores differ", cmp.differ);
  check("family scores same as solo mode", cmp.same);
  check("family average = BCVH.familyScores", cmp.famMatch);
  check("person scores = BCVH.scoreParties", cmp.indMatch);
  check("disagreement table present", (await p.$$("#agreement table tr")).length >= 17, JSON.stringify(cmp.split));
  const methodTxt = await p.evaluate(() => { const m = document.getElementById("method"); return m ? m.textContent : ""; });
  check("method text fits together mode", /one random order for the group/.test(methodTxt) || /mixed-up order,/.test(methodTxt));
  sw = await noHScroll(p);
  check("no h-scroll results 390", sw[0] <= sw[1], sw);
  const txt = await p.evaluate(() => document.body.innerText);
  check("no em dash on results", !/\u2014/.test(txt));

  // 5. Redo (no-answers view) goes back to Together
  await p.evaluate(() => { const s = BCVH.getState(); for (let i = 0; i < 3; i++) Object.keys(s.people[i].answers).forEach((q) => (s.people[i].answers[q].choice = "skip")); BCVH.setState(s); });
  await p.waitForSelector("#redo-btn");
  await p.click("#redo-btn");
  await p.waitForSelector("section.tg #q-title");
  check("redo returns to Together", (await state(p)).phase === "together" && /Question 1 of 16/.test(await p.textContent(".tg-head")));

  // 6. Back on Q1 goes to setup; toggle remembered
  await p.click("#back-btn");
  await p.waitForSelector("#setup-title");
  check("back on Q1 -> setup, together still selected", await p.isChecked("#mode-together"));
  await p.click("#start-btn");
  await p.waitForSelector("section.tg");

  // 7. Reset from Together screen
  check("reset chip visible in Together", await p.isVisible("#mast-reset"));
  await p.click("#mast-reset");
  await p.click("#reset-yes");
  await p.waitForSelector("#setup-title");
  const ls = await p.evaluate(() => localStorage.getItem("bcvh2026:v1"));
  st = await state(p);
  check("reset -> setup, mode solo, cleared", ls === null && st.mode === "solo" && st.count === 1 && (await p.$("#mode-together")) === null);

  // 8. Count back to 1 forces solo
  await p.click('label[for="count-2"]');
  await p.click('label[for="mode-together"]');
  await p.click('label[for="count-1"]');
  check("toggle hidden again at 1 person", (await p.$("#mode-together")) === null);
  await p.click("#start-btn");
  await p.waitForSelector("#q-title");
  check("1 person starts solo quiz", (await state(p)).phase === "quiz" && (await p.$("section.tg")) === null);

  // 9. Sanitize: stale together phase with 1 person falls back to setup
  const ok = await p.evaluate(() => { const s = BCVH.getState(); s.phase = "together"; s.count = 1; s.mode = "together"; BCVH.setState(s); return BCVH.getState().phase; });
  check("sanitize: together with 1 person -> setup", ok === "setup", ok);

  check("no console/page errors (artifact page)", errs.length === 0, errs.join(" || "));
  await ctx.close();
}

// Website build: answers sent exactly once when Together finishes
async function siteRun(browser) {
  if (!fs.existsSync(ROOT + "/site/public/index.html")) { console.log("NOTE site build missing, skipped"); return; }
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const p = await ctx.newPage();
  const errs = [];
  p.on("pageerror", (e) => errs.push("pageerror " + e.message));
  await ctx.addInitScript(() => {
    window.__posts = 0;
    window.fetch = function (u, o) { if (String(u).indexOf("/api/response") >= 0) window.__posts++; return Promise.resolve(new Response("{}", { status: 200 })); };
  });
  await p.goto(SITE_URL, { waitUntil: "load" });
  await p.evaluate(() => { try { localStorage.clear(); } catch (e) {} });
  await p.reload({ waitUntil: "load" });
  await p.selectOption("#riding-select", "SRF");
  await p.click('label[for="count-2"]');
  await p.click('label[for="mode-together"]');
  await p.click("#start-btn");
  for (let k = 0; k < 16; k++) {
    await p.waitForSelector("section.tg #q-title");
    const order = await p.$$eval(".tg-opt", (xs) => xs.map((x) => x.id.replace("tg-opt-", "")));
    await p.click(`label[for="tg-c-0-${order[0]}"]`);
    await p.click(`label[for="tg-c-1-${order[order.length - 1]}"]`);
    await p.click("#next-btn");
  }
  await p.waitForSelector("#res-title");
  await p.waitForTimeout(300);
  check("site: submitResponses fired once on finish", (await p.evaluate(() => window.__posts)) === 1, await p.evaluate(() => window.__posts));
  await p.reload({ waitUntil: "load" });
  await p.waitForSelector("#res-title");
  await p.waitForTimeout(300);
  check("site: no re-send on reload of results", (await p.evaluate(() => window.__posts)) === 0);
  check("site: no page errors", errs.filter((e) => !/fonts|cdnjs/.test(e)).length === 0, errs.join(" || "));
  await ctx.close();
}

(async () => {
  if (!fs.existsSync(SHOTS)) fs.mkdirSync(SHOTS);
  const browser = await chromium.launch({ executablePath: EXE, headless: true });
  await main(browser);
  await siteRun(browser);
  await browser.close();
  console.log(`${pass}/${pass + fail} passed`);
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(2); });
