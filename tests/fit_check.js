// Fit checks: quiz screens fit one laptop/desktop screen without scrolling. Run: node fit_check.js [--quick]
const REPO_ROOT = require("path").resolve(__dirname, "..");
const SP = process.env.TEST_TMP || require("path").join(__dirname, ".tmp");
for (const d of ["", "/shots", "/smoke_v2", "/smoke_v2/shots"]) require("fs").mkdirSync(SP + d, { recursive: true });
const { chromium } = require("playwright-core");
const fs = require("fs");
const ROOT = REPO_ROOT + "";
const SHOTS = SP + "/shots";
const EXE = process.env.CHROMIUM_PATH || undefined;
const body = fs.readFileSync(ROOT + "/index.html", "utf8");
const wrap = (b) => '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>' + b + "</body></html>";
const PAGE = SP + "/page_fit.html";
fs.writeFileSync(PAGE, wrap(body));

// Stress copy: the three questions due to gain a 6th option get one (a copy of their longest option) if they do not have it yet
const m = body.match(/(<script type="application\/json" id="bcvh-spec">)([\s\S]*?)(<\/script>)/);
const spec = JSON.parse(m[2]);
let stressed = [];
for (const q of spec.questions) {
  if (!["q_drugs", "q_icbc", "q_local_skytrain"].includes(q.id)) continue;
  while (q.options.length < 6) {
    const longest = q.options.slice().sort((a, b) => (b.text["4"] || "").length - (a.text["4"] || "").length)[0];
    const id = "abcdefgh"[q.options.length];
    q.options.push(Object.assign(JSON.parse(JSON.stringify(longest)), { id }));
    stressed.push(q.id + ":" + id);
  }
}
const safe = JSON.stringify(spec).replace(/</g, "\\u003c").replace(/>/g, "\\u003e").replace(/&/g, "\\u0026");
const PAGE6 = SP + "/page_fit6.html";
fs.writeFileSync(PAGE6, wrap(body.replace(m[0], m[1] + safe + m[3])));

const VIEWS = process.env.ONLY ? [[1263, 667]] : [[1263, 667], [1366, 657], [1440, 790], [1920, 960], [1024, 620]];
const NAMES = ["Alexandra", "Sam", "Kim", "Jo"];
let pass = 0, fail = 0;
const misses = [];
function check(n, ok, d) { ok ? pass++ : fail++; if (!ok || process.env.VERBOSE) console.log((ok ? "PASS " : "FAIL ") + n + (d !== undefined ? "  | " + String(d).slice(0, 300) : "")); }

async function measure(p) {
  return p.evaluate(() => {
    const ih = innerHeight;
    const r = (e) => (e ? e.getBoundingClientRect() : null);
    const opts = document.querySelectorAll(".tg-opt, .opt");
    const lastOpt = r(opts[opts.length - 1]);
    const persons = document.querySelectorAll(".tg-person");
    const lastP = r(persons[persons.length - 1]);
    const next = r(document.getElementById("next-btn"));
    const imp = r(document.querySelector(".solo .imp"));
    const sh = document.documentElement.scrollHeight;
    const inside = (b) => !b || (b.top >= -0.5 && b.bottom <= ih + 0.5);
    const card = r(document.querySelector('.tg-people'));
    const contained = !card || Array.from(document.querySelectorAll('.tg-person, .tg-r')).every((e) => { const x = e.getBoundingClientRect(); return x.left >= card.left - 0.5 && x.right <= card.right + 0.5; });
    return { sh, ih, over: Math.max(0, Math.round(sh - ih)), ok: contained && sh <= ih + 1 && inside(lastOpt) && inside(next) && inside(lastP) && inside(imp), sw: document.scrollingElement.scrollWidth, iw: innerWidth };
  });
}

// V2: each question is shown under a riding whose region asks it (provincial: Surrey-Fleetwood)
const PLACE = `function place(s, k) {
  const q = BCVH.spec.allQuestions[k];
  let riding = "SRF";
  if (q.scope !== "provincial") {
    const reg = BCVH.spec.regions.filter((r) => (r.local_qids || []).indexOf(q.id) >= 0)[0];
    const rd = reg ? BCVH.spec.ridings.filter((r) => r.region === reg.id)[0] : null;
    riding = rd ? rd.code : null;
  }
  s.riding = riding;
  s.qi = BCVH.questionsFor(riding).indexOf(q.id);
  return q;
}`;
async function askable(p) {
  return p.evaluate(() => BCVH.spec.allQuestions.map((q, k) => (q.scope === "provincial" || BCVH.spec.regions.some((r) => (r.local_qids || []).indexOf(q.id) >= 0) ? k : -1)).filter((k) => k >= 0));
}
async function setTogether(p, k, L, n) {
  await p.evaluate(([k, L, n, NAMES, PLACE]) => {
    const place = new Function("return " + PLACE)();
    const s = BCVH.getState();
    s.count = n; s.mode = "together"; s.phase = "together"; s.groupLevel = L;
    const q = place(s, k);
    const ord = s.people[0].order[q.id];
    for (let i = 0; i < 4; i++) {
      s.people[i].name = NAMES[i];
      // everyone picks a different answer, so every name chip shows
      s.people[i].answers[q.id] = { choice: ord[i % ord.length], importance: ["low", "medium", "high", "medium"][i], order: ord.slice() };
    }
    BCVH.setState(s);
  }, [k, L, n, NAMES, PLACE]);
}
async function setSolo(p, k, L) {
  await p.evaluate(([k, L, PLACE]) => {
    const place = new Function("return " + PLACE)();
    const s = BCVH.getState();
    s.count = 2; s.mode = "solo"; s.phase = "quiz"; s.cur = 0;
    s.people[0].name = "Alexandra"; s.people[0].level = L;
    const q = place(s, k);
    s.people[0].answers[q.id] = { choice: s.people[0].order[q.id][0], importance: "high", order: s.people[0].order[q.id].slice() };
    BCVH.setState(s);
  }, [k, L, PLACE]);
}

async function desktop(browser, url, tag, quick) {
  const report = [];
  for (const [w, h] of VIEWS) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h } });
    const p = await ctx.newPage();
    const errs = [];
    p.on("pageerror", (e) => errs.push(e.message));
    p.on("console", (mm) => { if (mm.type() === "error") errs.push(mm.text()); });
    await p.goto(url, { waitUntil: "networkidle" });
    await p.evaluate(() => { try { localStorage.clear(); } catch (e) {} });
    await p.reload({ waitUntil: "networkidle" });
    const ks = await askable(p), nq = ks.length;
    let tgBad = [], soloBad = [], worst = 0, l5 = 0, bgOpen = 0;
    for (const L of [1, 2, 3, 4]) {
      for (const k of ks) {
        await setTogether(p, k, L, 4);
        let r = await measure(p);
        if (!r.ok) { tgBad.push(`q${k + 1}/L${L} +${r.over}px`); worst = Math.max(worst, r.over); }
        await setSolo(p, k, L);
        r = await measure(p);
        if (!r.ok) { soloBad.push(`q${k + 1}/L${L} +${r.over}px`); worst = Math.max(worst, r.over); }
      }
    }
    // Not required to fit: level 5 and open Background. Report the overflow.
    for (const k of ks) {
      await setTogether(p, k, 5, 4); l5 = Math.max(l5, (await measure(p)).over);
      await setTogether(p, k, 3, 4); if (await p.$("#tg-bg")) { await p.click("#tg-bg summary"); bgOpen = Math.max(bgOpen, (await measure(p)).over); await p.click("#tg-bg summary"); }
    }
    check(`${tag} ${w}x${h} Together, 4 people, L1-4, all ${nq} questions fit`, tgBad.length === 0, tgBad.join(", "));
    check(`${tag} ${w}x${h} one at a time, L1-4, all ${nq} questions fit`, soloBad.length === 0, soloBad.join(", "));
    const hs = await measure(p);
    check(`${tag} ${w}x${h} no horizontal scroll`, hs.sw <= hs.iw, hs.sw + " > " + hs.iw);
    check(`${tag} ${w}x${h} no console errors`, errs.length === 0, errs.join(" | "));
    console.log(`NOTE ${tag} ${w}x${h}: level 5 worst overflow ${l5}px; Background open (L3) worst overflow ${bgOpen}px`);
    misses.push(...tgBad.map((x) => `${tag} ${w}x${h} together ${x}`), ...soloBad.map((x) => `${tag} ${w}x${h} solo ${x}`));
    if (tag === "spec" && w === 1263) {
      await setTogether(p, 0, 3, 4);
      await p.screenshot({ path: SHOTS + "/fit-together-1263x667.png" });
      await setSolo(p, 0, 3);
      await p.screenshot({ path: SHOTS + "/fit-solo-1263x667.png" });
    }
    await ctx.close();
  }
}

async function phone(browser) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, colorScheme: "dark" });
  const p = await ctx.newPage();
  const errs = [];
  p.on("pageerror", (e) => errs.push(e.message));
  await p.goto("file:///" + PAGE, { waitUntil: "networkidle" });
  await p.evaluate(() => { try { localStorage.clear(); } catch (e) {} });
  await p.reload({ waitUntil: "networkidle" });
  const ks = await askable(p);
  let hBad = [], nBad = [];
  for (const L of [1, 3, 5]) {
    for (const k of ks) {
      for (const mode of ["together", "solo"]) {
        if (mode === "together") await setTogether(p, k, L, 4); else await setSolo(p, k, L);
        const r = await p.evaluate(() => {
          const out = [];
          for (const y of [0, (document.documentElement.scrollHeight - innerHeight) / 2, document.documentElement.scrollHeight]) {
            scrollTo(0, y);
            const b = document.getElementById("next-btn").getBoundingClientRect();
            out.push(b.top >= 0 && b.bottom <= innerHeight + 0.5);
          }
          scrollTo(0, 0);
          return { sw: document.scrollingElement.scrollWidth, iw: innerWidth, vis: out.every(Boolean) };
        });
        if (r.sw > r.iw) hBad.push(`${mode} q${k + 1}/L${L}`);
        if (!r.vis) nBad.push(`${mode} q${k + 1}/L${L}`);
      }
    }
  }
  check("390x844 no horizontal scroll (both modes, L1/3/5, all questions)", hBad.length === 0, hBad.join(", "));
  check("390x844 Next visible at top, middle and bottom (sticky bar)", nBad.length === 0, nBad.join(", "));
  // a real click flow still works with the sticky bar on top of the content
  await setTogether(p, 0, 3, 4);
  await p.click('label[for^="tg-c-3-"] >> nth=2');
  await p.click("#next-btn");
  check("390 sticky Next advances", /Question 2 of 16/.test(await p.textContent(".tg-head")));
  await setTogether(p, 0, 3, 4);
  await p.evaluate(() => scrollTo(0, 0));
  await p.screenshot({ path: SHOTS + "/fit-together-390.png" });
  check("390 no page errors", errs.length === 0, errs.join(" | "));
  await ctx.close();
}

(async () => {
  const browser = await chromium.launch({ executablePath: EXE, headless: true });
  await desktop(browser, "file:///" + PAGE, "spec");
  if (stressed.length) console.log("NOTE 6-option stress copy adds: " + stressed.join(", "));
  if (!process.env.ONLY) { await desktop(browser, "file:///" + PAGE6, "6-opt"); await phone(browser); }
  await browser.close();
  if (misses.length) console.log("MISSES:\n  " + misses.join("\n  "));
  console.log(`${pass}/${pass + fail} passed`);
  process.exit(fail ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(2); });
