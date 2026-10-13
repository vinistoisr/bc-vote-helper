const REPO_ROOT = require("path").resolve(__dirname, "..");
const SP = process.env.TEST_TMP || require("path").join(__dirname, ".tmp");
for (const d of ["", "/shots", "/smoke_v2", "/smoke_v2/shots"]) require("fs").mkdirSync(SP + d, { recursive: true });
const { chromium } = require("playwright-core");
const BASE = process.argv[2] || "http://127.0.0.1:8799/";
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 390, height: 860 } });
  const errs = []; p.on("pageerror", e => errs.push(String(e))); p.on("console", m => { if (m.type() === "error") errs.push(m.text()); });
  const posts = [], bodies = []; p.on("response", r => { if (r.url().includes("/api/response")) { posts.push(r.status()); bodies.push(r.request().postData() || ""); } });
  const ok = (n, c, d) => console.log((c ? "PASS " : "FAIL ") + n + (d ? "  | " + d : ""));
  await p.goto(BASE);
  ok("share checkbox shown", await p.isVisible("#share-chk"));
  await p.selectOption("#riding-select", "SRF");
  await p.click('label[for="count-2"]');
  await p.click("#start-btn");
  for (let person = 0; person < 2; person++) {
    for (let i = 0; i < 16; i++) { await p.click(".opt >> nth=" + ((i + person) % 3)); await p.click("#next-btn"); }
    if (person === 0) await p.click("#handoff-go");
  }
  await p.waitForSelector("#res-title");
  await p.waitForTimeout(1500);
  ok("posted once, 200", posts.length === 1 && posts[0] === 200, JSON.stringify(posts));
  ok("post carries riding SRF, no postal code", bodies[0] && JSON.parse(bodies[0]).riding === "SRF" && !/V3S/i.test(bodies[0]), (bodies[0] || "").slice(0, 120));
  ok("pdf button visible", await p.isVisible("#pdf-btn"));
  const [dl] = await Promise.all([p.waitForEvent("download", { timeout: 15000 }).catch(() => null), p.click("#pdf-btn")]);
  ok("pdf downloads", !!dl, dl ? dl.suggestedFilename() : "");
  await p.reload(); await p.waitForTimeout(1500);
  ok("no repost on reload", posts.length === 1, JSON.stringify(posts));
  const sw = await p.evaluate(() => document.documentElement.scrollWidth);
  ok("no horizontal scroll", sw <= 390, String(sw));
  ok("no errors", errs.length === 0, errs.join(" ; "));
  await b.close();
})();
