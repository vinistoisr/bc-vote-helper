const REPO_ROOT = require("path").resolve(__dirname, "..");
const SP = process.env.TEST_TMP || require("path").join(__dirname, ".tmp");
for (const d of ["", "/shots", "/smoke_v2", "/smoke_v2/shots"]) require("fs").mkdirSync(SP + d, { recursive: true });
const { chromium } = require("playwright-core");
(async () => {
  const b = await chromium.launch(); const p = await b.newPage(); const bad = [];
  p.on("console", (m) => { if (m.type() === "error") bad.push(m.text()); });
  p.on("request", (r) => { if (!r.url().startsWith(process.argv[2] || "http://127.0.0.1:8799")) bad.push("3rd party: " + r.url()); });
  await p.goto(process.argv[2] || "http://127.0.0.1:8799/", { waitUntil: "networkidle" });
  const f = await p.evaluate(async () => { await document.fonts.ready; return ["Archivo", "Atkinson Hyperlegible Next", "Atkinson Hyperlegible Mono"].map((n) => n + ":" + document.fonts.check("16px '" + n + "'")); });
  const pdf = await p.evaluate(() => !!(window.jspdf && window.jspdf.jsPDF));
  console.log(JSON.stringify({ f, pdf, bad }));
  await b.close();
})();
