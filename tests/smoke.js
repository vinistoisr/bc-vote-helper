const REPO_ROOT = require("path").resolve(__dirname, "..");
const SP = process.env.TEST_TMP || require("path").join(__dirname, ".tmp");
for (const d of ["", "/shots", "/smoke_v2", "/smoke_v2/shots"]) require("fs").mkdirSync(SP + d, { recursive: true });
const { chromium } = require("playwright-core");
const fs = require("fs"), path = require("path");
const ROOT = REPO_ROOT + "";
const OUTD = SP + "/smoke_v2";
const EXE = process.env.CHROMIUM_PATH || undefined;
const body = fs.readFileSync(ROOT + "/index.html", "utf8");
// emulate the Artifact skeleton wrap
const page_html = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>' + body + "</body></html>";
const PAGE = OUTD + "/page.html"; fs.writeFileSync(PAGE, page_html);
const URL = "file:///" + PAGE;
let pass = 0, fail = 0;
function check(n, ok, d) { ok ? pass++ : fail++; console.log((ok ? "PASS " : "FAIL ") + n + (d !== undefined ? "  | " + String(d).slice(0, 250) : "")); }

async function run(browser, width, height, dark) {
  const tag = `${width} ${dark ? "dark" : "light"}`;
  const ctx = await browser.newContext({ viewport: { width, height }, colorScheme: dark ? "dark" : "light" });
  const page = await ctx.newPage();
  const errs = [];
  page.on("pageerror", (e) => errs.push("pageerror " + e.message));
  page.on("console", (m) => { if (m.type() === "error") errs.push("console " + m.text()); });
  page.on("requestfailed", (r) => errs.push("reqfail " + r.url().slice(0, 90)));
  await page.goto(URL, { waitUntil: "networkidle" });
  await page.evaluate(() => { try { localStorage.clear(); } catch (e) {} });
  await page.reload({ waitUntil: "networkidle" });
  const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
  console.log("NOTE body bg " + tag + ": " + bg);
  await page.selectOption("#riding-select", "SRF");
  await page.click('label[for="count-2"]');
  await page.fill("#name-0", "Alex");
  await page.fill("#name-1", "Sam");
  await page.click("#start-btn");
  for (let p = 0; p < 2; p++) {
    if (p === 1) { await page.waitForSelector("#handoff-title"); await page.click("#handoff-go"); }
    for (let k = 0; k < 16; k++) {
      await page.waitForSelector("#q-title");
      const ids = await page.$$eval('input[name="choice"]', (xs) => xs.map((x) => x.id).filter((i) => !/skip$/.test(i)));
      const pick = p === 0 ? ids[0] : ids[(k * 3 + 1) % ids.length];
      await page.click(`label[for="${pick}"]`);
      if (k === 2) { const sw = await page.evaluate(() => [document.scrollingElement.scrollWidth, innerWidth]); check("no h-scroll quiz " + tag, sw[0] <= sw[1], sw); }
      await page.click("#next-btn");
    }
  }
  await page.waitForSelector("#res-title"); await page.waitForTimeout(400);
  const title = (await page.textContent("#res-title")).trim();
  console.log("NOTE title " + tag + ": " + title);
  const hl = await page.$$eval(".hl-card", (cs) => cs.map((c) => ({ local: c.classList.contains("hl-local"), img: !!(c.querySelector("img") && c.querySelector("img").naturalWidth > 0), name: (c.querySelector(".hl-name") || {}).textContent, pct: (c.querySelector(".hl-pct") || {}).textContent })));
  const party = hl.filter((h) => !h.local), cand = hl.filter((h) => h.local);
  check("headline party card: logo + name + % " + tag, party.length > 0 && party.every((h) => h.img && h.name && /\d+\s*%/.test(h.pct)), JSON.stringify(party));
  check("local candidate headline card " + tag, cand.length > 0 && cand.every((h) => h.img && h.name && /%/.test(h.pct)), JSON.stringify(cand));
  const issues = await page.$$eval("#breakdown .issues > details, #breakdown .issues > *", (x) => x.length);
  check("per-issue breakdown present (16) " + tag, issues >= 16, issues);
  const candCount = await page.$$eval(".cand", (x) => x.length);
  check("local candidate list rendered " + tag, candCount > 0, candCount);
  for (const st of ["folded", "all open"]) {
    if (st === "all open") await page.$$eval("details", (ds) => ds.forEach((d) => (d.open = true)));
    await page.waitForTimeout(100);
    const sw = await page.evaluate(() => [document.scrollingElement.scrollWidth, innerWidth]);
    check(`no h-scroll results ${st} ` + tag, sw[0] <= sw[1], sw);
  }
  const txt = await page.evaluate(() => document.body.innerText);
  check("no em dash in rendered text " + tag, !/\u2014/.test(txt));
  await page.$$eval("details", (ds) => ds.forEach((d) => (d.open = false)));
  await page.evaluate(() => scrollTo(0, 0));
  await page.screenshot({ path: `${OUTD}/res-${width}-${dark ? "dark" : "light"}.png` });
  const r = await page.evaluate(async () => {
    const b = BCVH.buildResultsPdf(BCVH.getState()); const u = new Uint8Array(await b.arrayBuffer());
    let s = ""; for (let i = 0; i < u.length; i += 0x8000) s += String.fromCharCode.apply(null, u.subarray(i, i + 0x8000));
    return { type: b.type, size: b.size, head: s.slice(0, 8), tail: s.slice(-8).trim(), b64: btoa(s) };
  });
  fs.writeFileSync(`${OUTD}/smoke-${width}.pdf`, Buffer.from(r.b64, "base64"));
  check("PDF valid " + tag, r.type === "application/pdf" && r.head.startsWith("%PDF-") && /%%EOF/.test(r.tail) && r.size > 5000, `${r.type} ${r.size}B ${r.head} ...${r.tail}`);
  check("no console/page errors " + tag, errs.length === 0, errs.join(" || "));
  await ctx.close();
}
(async () => {
  const browser = await chromium.launch({ executablePath: EXE, headless: true });
  await run(browser, 390, 844, true);
  await run(browser, 1280, 900, false);
  await browser.close();
  console.log(`${pass}/${pass + fail} passed`); process.exit(fail ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(2); });
