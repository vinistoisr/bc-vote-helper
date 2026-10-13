const REPO_ROOT = require("path").resolve(__dirname, "..");
const SP = process.env.TEST_TMP || require("path").join(__dirname, ".tmp");
for (const d of ["", "/shots", "/smoke_v2", "/smoke_v2/shots"]) require("fs").mkdirSync(SP + d, { recursive: true });
const fs = require("fs");
const { chromium } = require("playwright-core");
const SHOTS = SP + "/shots";
const html = fs.readFileSync(REPO_ROOT + "/site/public/admin/index.html", "utf8");
const valid = JSON.parse(fs.readFileSync(REPO_ROOT + "/site/src/spec_valid.json", "utf8"));
let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
const subs = [], people = []; const cities = [["Surrey","BC"],["Vancouver","BC"],["Burnaby","BC"],["Calgary","AB"],["Saanich","BC"]];
for (let s = 0; s < 30; s++) {
  const sid = s.toString(16).padStart(32, "0"); const count = 1 + Math.floor(rnd() * 3); const c = cities[Math.floor(rnd() * cities.length)];
  const created = new Date(Date.now() - rnd() * 6 * 86400000).toISOString();
  const riding = [null, "SRF", "SRF", "SUP", "VNP"][s % 5];
  subs.push({ sid, created_at: created, updated_at: created, count, country: "CA", region: c[1] === "BC" ? "British Columbia" : "Alberta", region_code: c[1], city: c[0], data_as_of: "2026-10-10", riding });
  for (let i = 0; i < count; i++) {
    const answers = {}; let answered = 0;
    for (const [q, opts] of Object.entries(valid.questions)) { const r = rnd(); const ch = r < 0.1 ? "skip" : opts[Math.floor(rnd() * opts.length)]; answers[q] = { c: ch, w: ["low","medium","high"][Math.floor(rnd()*3)] }; if (ch !== "skip") answered++; }
    people.push({ sid, idx: i, level: 1 + Math.floor(rnd() * 5), answered, answers });
  }
}
(async () => {
  const b = await chromium.launch();
  const ok = (n, c, d) => console.log((c ? "PASS " : "FAIL ") + n + (d ? "  | " + d : ""));
  for (const [w, scheme] of [[1280, "light"], [390, "dark"]]) {
    const p = await b.newPage({ viewport: { width: w, height: 900 }, colorScheme: scheme });
    const errs = []; p.on("pageerror", e => errs.push(String(e))); p.on("console", m => { if (m.type() === "error") errs.push(m.text()); });
    let deleted = null;
    await p.route("**/admin/", r => r.fulfill({ contentType: "text/html", body: html }));
    await p.route("**/api/admin/data", r => r.fulfill({ contentType: "application/json", body: JSON.stringify({ generated_at: new Date().toISOString(), submissions: subs, people }) }));
    await p.route("**/api/admin/delete", r => { deleted = JSON.parse(r.request().postData()); r.fulfill({ contentType: "application/json", body: '{"ok":true}' }); });
    await p.route("**/geo/eds.json", r => r.fulfill({ contentType: "application/json", body: fs.readFileSync(REPO_ROOT + "/site/public/geo/eds.json", "utf8") }));
    await p.route("**/geo/basemap.json", r => r.fulfill({ contentType: "application/json", body: fs.readFileSync(REPO_ROOT + "/site/public/geo/basemap.json", "utf8") }));
    await p.goto("http://127.0.0.1:8799/admin/");
    await p.waitForSelector(".kpi");
    ok(w + " kpi people", (await p.textContent(".kpi b")) === String(people.length), await p.textContent(".kpi b"));
    ok(w + " all spec questions listed (" + Object.keys(valid.questions).length + ")", (await p.locator(".q").count()) === Object.keys(valid.questions).length);
    // Map: every riding drawn, the ridings with responses coloured, the rest marked as no data
    await p.waitForSelector("#map-g path");
    ok(w + " map draws 93 ridings", (await p.locator("#map-g path").count()) === 93);
    const withRiding = new Set(subs.filter((s) => s.riding).map((s) => s.riding)).size;
    ok(w + " map colours the " + withRiding + " ridings with responses", (await p.locator("#map-g path:not(.nodata)").count()) === withRiding, String(await p.locator("#map-g path:not(.nodata)").count()));
    ok(w + " map draws land, lakes, rivers and names", (await p.locator("#map-svg .land").count()) === 1 && (await p.locator("#map-svg .lakes").count()) === 1 && (await p.locator("#map-labels text").count()) > 100);
    // Questions collapse to one line each and open on demand
    ok(w + " questions start closed", (await p.$$eval("details.q", (ds) => ds.filter((d) => !d.open).length)) === Object.keys(valid.questions).length);
    await p.selectOption("#f-who", "kids");
    const kids = people.filter(x => x.level <= 2).length;
    ok(w + " kids filter", (await p.textContent(".kpi b")) === String(kids));
    await p.selectOption("#f-who", "all");
    // V2: riding and region filters
    const bySid = {}; subs.forEach((s) => (bySid[s.sid] = s));
    const cnt = (f) => String(people.filter((x) => f(bySid[x.sid])).length);
    ok(w + " by-riding table has Not given row", /Not given/.test(await p.textContent("body")) && (await p.locator("table >> text=Surrey-Fleetwood").count()) > 0);
    ok(w + " no candidate panel without a riding", /Pick one riding/.test(await p.textContent("body")));
    await p.selectOption("#f-riding", "SRF");
    ok(w + " riding filter SRF people", (await p.textContent(".kpi b")) === cnt((s) => s.riding === "SRF"), await p.textContent(".kpi b"));
    ok(w + " region follows riding", (await p.inputValue("#f-region")) === "surrey");
    const candRows = await p.$$eval(".card", (cs) => { const c = cs.find((x) => /Surrey-Fleetwood candidate match/.test(x.textContent)); return c ? c.querySelectorAll(".bar-row").length : -1; });
    ok(w + " SRF candidate match panel (5 candidates)", candRows === 5, String(candRows));
    ok(w + " SRF shows 16 questions", (await p.locator(".q").count()) === 16);
    await p.selectOption("#f-riding", "VNP");
    ok(w + " VNP: 16 questions, candidate panel", (await p.locator(".q").count()) === 16 && /Vancouver-Point Grey candidate match/.test(await p.textContent("body")), String(await p.locator(".q").count()));
    await p.selectOption("#f-riding", "none");
    ok(w + " Not given filter", (await p.textContent(".kpi b")) === cnt((s) => !s.riding));
    await p.selectOption("#f-riding", "all");
    await p.selectOption("#f-region", "metro");
    ok(w + " region metro filter", (await p.textContent(".kpi b")) === cnt((s) => s.riding === "VNP"));
    await p.selectOption("#f-region", "all");
    await p.locator(".del").first().check(); await p.click("#del-btn"); await p.click("#del-btn");
    await p.waitForTimeout(300);
    ok(w + " delete posts sid", deleted && deleted.sids.length === 1, JSON.stringify(deleted));
    const sw = await p.evaluate(() => document.documentElement.scrollWidth);
    ok(w + " no h-scroll", sw <= w, String(sw));
    await p.evaluate(() => window.scrollTo(0, 0)); await p.screenshot({ path: "" + SP + "/shots/admin_" + w + ".png", fullPage: false }); await p.evaluate(() => document.querySelectorAll(".q")[4].scrollIntoView()); await p.screenshot({ path: "" + SP + "/shots/admin_q_" + w + ".png" });
    ok(w + " no errors", errs.length === 0, errs.join(" ; "));
    await p.close();
  }
  await b.close();
})();
