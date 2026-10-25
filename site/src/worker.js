/*
 * BC Vote Helper 2026 - votebc.vinceroyer.ca
 *
 * - Serves the quiz (static assets) to visitors in Canada; search and AI crawlers may read pages from anywhere.
 * - /ridings/ and /about/: plain-HTML pages for search engines (build_seo.py), open to everyone.
 * - POST /api/response stores anonymous answers in D1 (no names, no IP), with the page language.
 * - /i18n/<lang>.json: translation bundles, fetched by the page when a reader picks a language.
 * - GET /api/riding?pc= finds the BC riding through Represent (Open North),
 *   cached 30 days, with a local postal code table as the fallback when
 *   Represent is busy. ?lat=&lon= is answered locally from the riding shapes.
 *   The postal code is not logged or stored.
 * - /admin and /api/admin/* sit behind Cloudflare Access; the Worker also
 *   verifies the Access JWT itself, so the admin side fails closed.
 */
import VALID from "./spec_valid.json";
import NAMES from "./riding_names.json";
import META_I18N from "./meta_i18n.json";

const IMPORTANCE = new Set(["low", "medium", "high"]);
/* Page languages (template.html LANGS); anything else is rejected */
const LANGS = new Set(["en", "pa", "zh-Hans", "zh-Hant", "tl", "fr", "ru", "ko", "fa"]);
const MAX_BODY = 24 * 1024;
/* Traffic source categories, worked out in the browser from where the visitor landed from. Never a raw hostname. */
const SOURCES = new Set(["reddit", "facebook", "instagram", "x", "search", "classroom", "linkedin", "bluesky", "github", "email", "direct", "other"]);
function cleanSource(v) { return typeof v === "string" && SOURCES.has(v) ? v : null; }
const RIDING_RE = /^[A-Z]{3}$/;
const POSTAL_RE = /^[A-Z]\d[A-Z]\d[A-Z]\d$/;
const REPRESENT = "https://represent.opennorth.ca";
const BC_SET = "british-columbia-electoral-districts-2023-redistribution";
const LOOKUP_TTL = 30 * 86400;
const UPSTREAM_TIMEOUT_MS = 4000;
const BREAKER_TTL = 60;
const NOT_FOUND_TTL = 3600;
const NEAR_EDGE_M = 300;
const OFFSHORE_M = 2000;
/* Generous box around BC; the riding shapes decide the exact riding */
const BC_BOX = { south: 48.2, north: 60.0, west: -139.1, east: -114.0 };

const SECURITY_HEADERS = {
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  /* geolocation=(self): the "Use my location" riding lookup on the page */
  "Permissions-Policy": "camera=(), microphone=(), geolocation=(self), interest-cohort=()",
  "X-Frame-Options": "DENY",
};
const PAGE_CSP =
  "default-src 'self'; script-src 'self' 'unsafe-inline' https://static.cloudflareinsights.com; " +
  "style-src 'self' 'unsafe-inline'; font-src 'self'; " +
  "img-src 'self' data: blob:; connect-src 'self' https://cloudflareinsights.com; frame-ancestors 'none'; base-uri 'none'; form-action 'self'";

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    const isAdmin = path === "/admin" || path.startsWith("/admin/") || path.startsWith("/api/admin/");

    try {
      if (isAdmin) {
        const who = await verifyAccess(request, env);
        if (!who) return text("Forbidden", 403);
        if (path.startsWith("/api/admin/")) return await adminApi(request, env, path);
        return withHeaders(await env.ASSETS.fetch(request), { "Cache-Control": "no-store", "Content-Security-Policy": PAGE_CSP });
      }

      /* Link-preview image and icon are public everywhere, so shared links show a card */
      if ((path === "/og.png" || path === "/favicon.ico") && (request.method === "GET" || request.method === "HEAD")) {
        return withHeaders(await env.ASSETS.fetch(request), { "Cache-Control": "public, max-age=86400" });
      }

      /* BC Election Act s.233.1(2): no new survey results on voting day before polls close */
      if (isResults(path) && Date.now() < RESULTS_AT) {
        return text("Results are posted after polls close at 8 PM Pacific on October 24, 2026.", 404, { "Cache-Control": "no-store" });
      }

      /* Live totals for the results page since polls closed: open to everyone, totals only, cached 5 minutes */
      if (path === "/api/live" && Date.now() >= RESULTS_AT) {
        if (request.method !== "GET") return text("Method not allowed", 405, { Allow: "GET" });
        return await liveTotals(request, env, ctx);
      }

      if (!countryAllowed(request, env) && !openOutsideCanada(request, path)) {
        if (isPreviewBot(request) && !path.startsWith("/api/") && (request.method === "GET" || request.method === "HEAD")) {
          return await previewStub(request, env);
        }
        return await geoBlocked(request, env);
      }

      if (path === "/api/response") {
        if (request.method !== "POST") return text("Method not allowed", 405, { Allow: "POST" });
        return await saveResponse(request, env);
      }
      if (path === "/api/complete") {
        if (request.method !== "POST") return text("Method not allowed", 405, { Allow: "POST" });
        return await saveCompletion(request, env);
      }
      if (path === "/api/riding") {
        if (request.method !== "GET") return text("Method not allowed", 405, { Allow: "GET" });
        return await ridingLookup(request, env, ctx);
      }
      if (path.startsWith("/api/")) return text("Not found", 404);

      if (request.method !== "GET" && request.method !== "HEAD") return text("Method not allowed", 405);
      const res = await env.ASSETS.fetch(request);
      /* Translation bundles change with each deploy; the page asks for them with ?v=<content hash> */
      if (path.startsWith("/i18n/") && res.ok) return withHeaders(res, { "Cache-Control": "public, max-age=300" });
      const type = res.headers.get("Content-Type") || "";
      if (!type.includes("text/html")) return withHeaders(res, {});
      return withHeaders(localizeHead(res, url), { "Content-Security-Policy": PAGE_CSP, "Cache-Control": "public, max-age=300" });
    } catch (err) {
      console.error("unhandled", err && err.stack ? err.stack : err);
      return text("Something went wrong", 500);
    }
  },

  /* Data retention: once DELETE_AFTER has passed, a daily cron deletes every stored answer. */
  async scheduled(event, env, ctx) {
    ctx.waitUntil(purgeAfterCutoff(env, event.scheduledTime));
  },
};

async function purgeAfterCutoff(env, now) {
  const cutoff = Date.parse(env.DELETE_AFTER || "");
  if (!Number.isFinite(cutoff) || now < cutoff) return { purged: false };
  const [p, s] = await env.DB.batch([env.DB.prepare("DELETE FROM people"), env.DB.prepare("DELETE FROM submissions")]);
  console.log("retention purge", (p.meta && p.meta.changes) || 0, "people,", (s.meta && s.meta.changes) || 0, "sessions");
  return { purged: true };
}

/* ------------------------------------------------------------------ */
/* Geo restriction                                                     */
/* ------------------------------------------------------------------ */
function countryAllowed(request, env) {
  const allowed = String(env.ALLOWED_COUNTRIES || "CA").split(",").map((s) => s.trim().toUpperCase()).filter(Boolean);
  const country = request.cf && request.cf.country ? String(request.cf.country).toUpperCase() : "";
  return allowed.includes(country);
}

/*
 * Search engines and AI assistants crawl from outside Canada. They may read pages (never the API), so the site can
 * appear in search results; the quiz still cannot save answers from outside Canada. The plain-HTML riding and About
 * pages and the crawler files are open to everyone: they hold only public election facts.
 */
const SEARCH_BOTS = /googlebot|google-inspectiontool|googleother|storebot-google|adsbot-google|bingbot|bingpreview|msnbot|adidxbot|duckduckbot|duckassistbot|yandex(bot)?|baiduspider|applebot|gptbot|oai-searchbot|chatgpt-user|claudebot|claude-user|claude-searchbot|anthropic-ai|perplexitybot|perplexity-user|amazonbot|bravebot|ccbot|meta-externalagent|meta-externalfetcher|mistralai-user|youbot|kagibot|cohere-ai|petalbot|seznambot|naverbot|yeti\//i;
const OPEN_FILES = new Set(["/robots.txt", "/sitemap.xml", "/llms.txt", "/7c1e4b9a2f6d48e3a05b9c8d1e2f3a47.txt"]);
function openOutsideCanada(request, path) {
  if (request.method !== "GET" && request.method !== "HEAD") return false;
  if (path.startsWith("/api/")) return false;
  if (OPEN_FILES.has(path) || path === "/about" || path.startsWith("/about/") || path === "/ridings" || path.startsWith("/ridings/") || path.startsWith("/fonts/") || isResults(path)) return true;
  return SEARCH_BOTS.test(request.headers.get("User-Agent") || "");
}

/* The public results page (totals only) opens to everyone once polls close: 8 PM Pacific, October 24, 2026 */
const RESULTS_AT = Date.parse("2026-10-25T03:00:00Z");
function isResults(path) {
  return path === "/results" || path.startsWith("/results/");
}

/* ------------------------------------------------------------------ */
/* Live totals after polls closed                                      */
/* ------------------------------------------------------------------ */
const LIVE_TTL = 300;
const LIVE_WEIGHTS = { low: 0.5, medium: 1, high: 2 };
const PACIFIC_MS = -7 * 3600 * 1000; /* PDT through November 1, 2026; PST (-8) after */

function pacificDay(iso) {
  const t = Date.parse(iso);
  const off = t >= Date.parse("2026-11-01T09:00:00Z") ? -8 * 3600 * 1000 : PACIFIC_MS;
  return new Date(t + off).toISOString().slice(0, 10);
}

/** Closest parties for one person's answers: the quiz's rule, sum(w*s) / sum(w*4), skips and no-position cells left out. */
function liveTops(answers, region) {
  const t = {};
  for (const p of VALID.parties) t[p] = [0, 0];
  const local = new Set(region ? VALID.regions[region] || [] : []);
  for (const [qid, opts] of Object.entries(VALID.scores)) {
    if (VALID.local_qids.includes(qid) && !local.has(qid)) continue;
    const a = answers && answers[qid];
    const c = a && a.c;
    if (!c || c === "skip" || !opts[c]) continue;
    const w = LIVE_WEIGHTS[a.w] || 1;
    const nop = (VALID.nopos && VALID.nopos[qid]) || [];
    for (const p of VALID.parties) {
      if (nop.includes(p)) continue;
      t[p][0] += w * Number(opts[c][p]);
      t[p][1] += w * 4;
    }
  }
  let best = -1, ids = [];
  for (const p of VALID.parties) {
    if (!t[p][1]) continue;
    const r = Math.round((100 * t[p][0]) / t[p][1]);
    if (r > best) { best = r; ids = [p]; } else if (r === best) ids.push(p);
  }
  return ids;
}

async function liveTotals(request, env, ctx) {
  const cache = caches.default;
  const key = new Request(new URL("/api/live", request.url).toString(), { method: "GET" });
  const hit = await cache.match(key);
  if (hit) return hit;
  const since = new Date(RESULTS_AT).toISOString();
  const [comp, people] = await env.DB.batch([
    env.DB.prepare("SELECT created_at, source, count FROM completions WHERE created_at >= ?").bind(since),
    env.DB.prepare("SELECT s.created_at, s.riding, s.region_code, p.answers FROM people p JOIN submissions s ON s.sid = p.sid WHERE s.created_at >= ?").bind(since),
  ]);
  const finishedDaily = {}, sources = {};
  let sessions = 0, finished = 0;
  for (const r of comp.results) {
    sessions += 1;
    finished += r.count || 1;
    const d = pacificDay(r.created_at);
    finishedDaily[d] = (finishedDaily[d] || 0) + (r.count || 1);
    const s = r.source || "unknown";
    sources[s] = (sources[s] || 0) + 1;
  }
  const sharedDaily = {}, best = {};
  let shared = 0, scored = 0;
  for (const r of people.results) {
    const ride = r.riding && VALID.ridings[r.riding] ? VALID.ridings[r.riding] : null;
    if (!ride && r.region_code !== "BC") continue; /* same rule as the totals before polls closed */
    shared += 1;
    const d = pacificDay(r.created_at);
    sharedDaily[d] = (sharedDaily[d] || 0) + 1;
    const ids = liveTops(safeParse(r.answers) || {}, ride ? ride.region : null);
    if (!ids.length) continue;
    scored += 1;
    for (const p of ids) best[p] = (best[p] || 0) + 1 / ids.length;
  }
  const pct = (o, n) => Object.fromEntries(Object.entries(o).map(([k, v]) => [k, n ? Math.round((1000 * v) / n) / 10 : 0]));
  const body = {
    since, updated: new Date().toISOString(),
    finished, sessions, shared, scored,
    deleted: Date.now() >= Date.parse(env.DELETE_AFTER || "2100-01-01"),
    best: pct(best, scored),
    finished_daily: finishedDaily, shared_daily: sharedDaily,
    sources: pct(sources, sessions),
  };
  const res = json(body, 200, { "Cache-Control": `public, max-age=${LIVE_TTL}` });
  ctx.waitUntil(cache.put(key, res.clone()));
  return res;
}

/* Link-preview crawlers (mostly outside Canada) get the page's title, description and image only */
const PREVIEW_BOTS = /facebookexternalhit|facebot|twitterbot|slackbot|slack-imgproxy|discordbot|redditbot|linkedinbot|whatsapp|telegrambot|applebot|skypeuripreview|iframely|embedly|mastodon|bluesky|cardyb/i;
function isPreviewBot(request) {
  return PREVIEW_BOTS.test(request.headers.get("User-Agent") || "");
}

/** The <title> and description/og/twitter <meta> tags from the built page, read once per Worker instance. */
let metaPromise = null;
function pageMeta(request, env) {
  if (!metaPromise) {
    const origin = new URL(request.url).origin;
    metaPromise = env.ASSETS.fetch(new Request(`${origin}/`))
      .then((r) => (r.ok ? r.text() : ""))
      .then((html) => {
        const head = html.slice(0, html.indexOf("</head>") > 0 ? html.indexOf("</head>") : 6000);
        const title = (head.match(/<title>[^<]*<\/title>/) || ["<title>BC Vote Helper 2026</title>"])[0];
        const metas = head.match(/<meta (?:name="(?:description|twitter:[a-z:]+)"|property="og:[a-z:_]+")[^>]*>/g) || [];
        return title + metas.join("");
      })
      .catch(() => { metaPromise = null; return "<title>BC Vote Helper 2026</title>"; });
  }
  return metaPromise;
}

async function previewStub(request, env) {
  const meta = await pageMeta(request, env);
  const html = `<!doctype html><html lang="en-CA"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">${meta}</head>
<body><p>BC Vote Helper 2026 is open to people in Canada.</p></body></html>`;
  const res = new Response(request.method === "HEAD" ? null : html, {
    status: 200,
    headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "public, max-age=3600", ...SECURITY_HEADERS },
  });
  return request.method === "HEAD" ? res : localizeHead(res, new URL(request.url));
}

/**
 * Shared ?lang= links: title, description, locale, canonical URL and text direction in that language, so link
 * previews (WhatsApp, Facebook, iMessage) and search results match the page the reader will see.
 * The page itself still picks the language in the browser; this only changes the <head> and <html> attributes.
 */
function localizeHead(res, url) {
  const lang = url.searchParams.get("lang") || "";
  const m = Object.prototype.hasOwnProperty.call(META_I18N, lang) ? META_I18N[lang] : null;
  if (!m) return res;
  const self = `${url.origin}/?lang=${encodeURIComponent(lang)}`;
  const setContent = (value) => ({ element(el) { el.setAttribute("content", value); } });
  return new HTMLRewriter()
    .on("html", { element(el) { el.setAttribute("lang", lang); el.setAttribute("dir", m.dir); } })
    .on("title", { element(el) { el.setInnerContent(m.title); } })
    .on('meta[name="description"]', setContent(m.desc))
    .on('meta[property="og:title"]', setContent(m.title))
    .on('meta[property="og:description"]', setContent(m.desc))
    .on('meta[name="twitter:title"]', setContent(m.title))
    .on('meta[name="twitter:description"]', setContent(m.desc))
    .on('meta[property="og:locale"]', setContent(m.locale || "en_CA"))
    .on('meta[property="og:url"]', setContent(self))
    .on('link[rel="canonical"]', { element(el) { el.setAttribute("href", self); } })
    .transform(res);
}

async function geoBlocked(request, env) {
  if (new URL(request.url).pathname.startsWith("/api/")) return json({ error: "available_in_canada_only" }, 403);
  const meta = await pageMeta(request, env);
  const html = `<!doctype html><html lang="en-CA"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
${meta}<meta name="robots" content="noindex">
<style>:root{color-scheme:light dark;--bg:#ECEFEE;--ink:#121A1F;--ink2:#4A5661}@media (prefers-color-scheme:dark){:root{--bg:#10171B;--ink:#E8EEF0;--ink2:#A9B6BD}}
body{margin:0;min-height:100vh;display:grid;place-items:center;background:var(--bg);color:var(--ink);font:17px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;padding:16px}
main{max-width:440px}h1{font-size:1.4rem;margin:0 0 8px}p{margin:0 0 8px;color:var(--ink2)}</style></head>
<body><main><h1>Available in Canada only</h1><p>BC Vote Helper 2026 is for voters in British Columbia, so it can only be opened from Canada.</p><p>If you are in Canada and see this, turn off any VPN and reload.</p></main></body></html>`;
  return new Response(html, { status: 403, headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store", ...SECURITY_HEADERS } });
}

/* ------------------------------------------------------------------ */
/* Public: save anonymous answers                                      */
/* ------------------------------------------------------------------ */
async function saveResponse(request, env) {
  const origin = request.headers.get("Origin");
  const self = new URL(request.url).origin;
  if (origin && origin !== self) return json({ error: "bad_origin" }, 403);
  if (!(request.headers.get("Content-Type") || "").includes("application/json")) return json({ error: "bad_type" }, 415);

  if (env.SUBMIT_LIMIT) {
    const { success } = await env.SUBMIT_LIMIT.limit({ key: rlKey(request) });
    if (!success) return json({ error: "rate_limited" }, 429);
  }

  if (Number(request.headers.get("Content-Length") || 0) > MAX_BODY) return json({ error: "too_large" }, 413);
  if (await atCapacity(env)) return json({ error: "full", message: "We are not collecting more answers right now. Your results still work." }, 503);

  const raw = await request.text();
  if (raw.length > MAX_BODY) return json({ error: "too_large" }, 413);
  let body;
  try { body = JSON.parse(raw); } catch { return json({ error: "bad_json" }, 400); }

  let clean = null;
  try { clean = validate(body); } catch { clean = null; }
  if (!clean) return json({ error: "invalid" }, 400);

  const cf = request.cf || {};
  const now = new Date().toISOString();
  const stmts = [
    env.DB.prepare(
      /* lang needs migrate_i18n.sql. Without that column this insert fails (500 and an error log), on purpose: run the migration first. */
      /* source needs migrate_source.sql, same rule as lang */
      `INSERT INTO submissions (sid, created_at, updated_at, count, country, region, region_code, city, data_as_of, riding, lang, source)
       VALUES (?1, ?2, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11)
       ON CONFLICT(sid) DO UPDATE SET updated_at = ?2, count = ?3, data_as_of = ?8, riding = ?9, lang = ?10, source = COALESCE(submissions.source, ?11)`
    ).bind(clean.sid, now, clean.count, str(cf.country, 2), str(cf.region, 64), str(cf.regionCode, 8), str(cf.city, 64), clean.data_as_of, clean.riding, clean.lang, clean.source),
    env.DB.prepare("DELETE FROM people WHERE sid = ?1").bind(clean.sid),
  ];
  clean.people.forEach((p, idx) => {
    stmts.push(
      env.DB.prepare("INSERT INTO people (sid, idx, level, answered, answers) VALUES (?1, ?2, ?3, ?4, ?5)")
        .bind(clean.sid, idx, p.level, p.answered, JSON.stringify(p.answers))
    );
  });
  await env.DB.batch(stmts);
  return json({ ok: true });
}

/** Rate-limit key: IPv4 as is, IPv6 by its /64 network, so one device cannot rotate addresses inside its own block. */
function rlKey(request) {
  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  if (!ip.includes(":")) return ip;
  const [head, tail] = ip.split("::");
  const a = head ? head.split(":") : [];
  const b = tail !== undefined && tail ? tail.split(":") : [];
  const full = tail !== undefined ? [...a, ...Array(Math.max(0, 8 - a.length - b.length)).fill("0"), ...b] : a;
  return full.slice(0, 4).map((h) => (h || "0").toLowerCase().replace(/^0+(?=.)/, "")).join(":") + "::/64";
}

/* Global cap on stored sessions, checked at most once a minute per Worker instance */
const MAX_SESSIONS = 50000;
let capCheck = { at: 0, full: false };
async function atCapacity(env) {
  if (Date.now() - capCheck.at < 60_000) return capCheck.full;
  try {
    const row = await env.DB.prepare("SELECT COUNT(*) AS n FROM submissions").first();
    capCheck = { at: Date.now(), full: Number(row && row.n) > MAX_SESSIONS };
  } catch {
    capCheck = { at: Date.now(), full: false };
  }
  return capCheck.full;
}

function str(v, max) {
  if (v == null) return null;
  return String(v).slice(0, max);
}

function validate(b) {
  if (!b || typeof b !== "object" || b.v !== 1) return null;
  if (typeof b.sid !== "string" || !/^[0-9a-f]{32}$/.test(b.sid)) return null;
  const count = Number(b.count);
  if (!Number.isInteger(count) || count < 1 || count > 4) return null;
  if (!Array.isArray(b.people) || b.people.length !== count) return null;
  const people = [];
  for (const p of b.people) {
    if (!p || typeof p !== "object") return null;
    const level = Number(p.level);
    if (!Number.isInteger(level) || level < 1 || level > 5) return null;
    if (!p.answers || typeof p.answers !== "object" || Array.isArray(p.answers)) return null;
    const answers = {};
    let answered = 0;
    for (const [qid, a] of Object.entries(p.answers)) {
      const opts = Object.hasOwn(VALID.questions, qid) ? VALID.questions[qid] : null;
      if (!Array.isArray(opts) || !a || typeof a !== "object") return null;
      const c = String(a.c);
      if (c !== "skip" && !opts.includes(c)) return null;
      const w = IMPORTANCE.has(a.w) ? a.w : "medium";
      answers[qid] = { c, w };
      if (c !== "skip") answered += 1;
    }
    people.push({ level, answered, answers });
  }
  const asOf = typeof b.data_as_of === "string" && /^\d{4}-\d{2}-\d{2}$/.test(b.data_as_of) ? b.data_as_of : null;
  /* Optional riding: a known 3-letter code, or nothing */
  let riding = null;
  if (b.riding != null && b.riding !== "") {
    if (!validRiding(b.riding)) return null;
    riding = b.riding;
  }
  /* Optional page language: one of LANGS, or nothing (pages from before languages were added) */
  let lang = null;
  if (b.lang != null && b.lang !== "") {
    if (typeof b.lang !== "string" || !LANGS.has(b.lang)) return null;
    lang = b.lang;
  }
  /* Optional traffic source: unknown values are dropped, never rejected, so old and new pages both save */
  return { sid: b.sid, count, people, data_as_of: asOf, riding, lang, source: cleanSource(b.source) };
}

/* ------------------------------------------------------------------ */
/* Public: count a finished quiz (everyone, shared or not)             */
/* ------------------------------------------------------------------ */
/* Stores only the time, page language, source category and number of people. No answers, no session id, no location. */
async function saveCompletion(request, env) {
  const origin = request.headers.get("Origin");
  if (origin && origin !== new URL(request.url).origin) return json({ error: "bad_origin" }, 403);
  if (!(request.headers.get("Content-Type") || "").includes("application/json")) return json({ error: "bad_type" }, 415);
  if (env.SUBMIT_LIMIT) {
    const { success } = await env.SUBMIT_LIMIT.limit({ key: rlKey(request) });
    if (!success) return json({ error: "rate_limited" }, 429);
  }
  const raw = await request.text();
  if (raw.length > 1024) return json({ error: "too_large" }, 413);
  let b;
  try { b = JSON.parse(raw); } catch { return json({ error: "bad_json" }, 400); }
  const count = Number(b && b.count);
  if (!b || b.v !== 1 || !Number.isInteger(count) || count < 1 || count > 4) return json({ error: "invalid" }, 400);
  const lang = typeof b.lang === "string" && LANGS.has(b.lang) ? b.lang : null;
  await env.DB.prepare("INSERT INTO completions (created_at, lang, source, count) VALUES (?1, ?2, ?3, ?4)")
    .bind(new Date().toISOString(), lang, cleanSource(b.source), count).run();
  return json({ ok: true });
}

function validRiding(code) {
  return typeof code === "string" && RIDING_RE.test(code) && Object.hasOwn(VALID.ridings || {}, code);
}

/* ------------------------------------------------------------------ */
/* Public: riding lookup (postal code or location)                     */
/* ------------------------------------------------------------------ */
async function ridingLookup(request, env, ctx) {
  if (env.LOOKUP_LIMIT) {
    const { success } = await env.LOOKUP_LIMIT.limit({ key: rlKey(request) });
    if (!success) return lookupError("rate_limited", "Too many lookups in a row. Wait a minute, or pick your riding from the list.", 429);
  }
  const url = new URL(request.url);
  const pcRaw = url.searchParams.get("pc");
  if (pcRaw != null) {
    const pc = String(pcRaw).toUpperCase().replace(/[^A-Z0-9]/g, "");
    if (!POSTAL_RE.test(pc)) return lookupError("bad_postal_code", "That does not look like a postal code. It should look like V3S 1A1.", 400);
    if (pc[0] !== "V") return lookupError("outside_bc", "That postal code is outside BC. BC postal codes start with V.", 400);
    return await postalLookup(pc, url, env, ctx);
  }
  if (url.searchParams.has("lat") && url.searchParams.has("lon")) {
    const latS = url.searchParams.get("lat"), lonS = url.searchParams.get("lon");
    const num = /^-?\d{1,3}(\.\d{1,10})?$/;
    if (!num.test(latS) || !num.test(lonS)) return lookupError("bad_location", "That location could not be read. Enter a postal code or pick from the list.", 400);
    const lat = Number(latS), lon = Number(lonS);
    if (!(lat >= BC_BOX.south && lat <= BC_BOX.north && lon >= BC_BOX.west && lon <= BC_BOX.east)) {
      return lookupError("outside_bc", "Your location looks to be outside BC. Enter a BC postal code or pick from the list.", 400);
    }
    const hit = pointLookup(await edShapes(env, url), lon, lat);
    if (!hit) return lookupError("outside_bc", "No BC riding was found at your location. Enter a postal code or pick from the list.", 404);
    return found(hit.code, hit.alternatives, false);
  }
  return lookupError("missing", "Enter a postal code or pick your riding from the list.", 400);
}

/**
 * Postal code -> riding. Represent first (cached 30 days). If Represent is slow, rate limited or down,
 * a 60-second breaker skips it and the Worker answers from its own table (GeoNames postal code points
 * placed in the riding shapes). If the table does not know the code, it offers the ridings in that
 * forward sortation area (first 3 characters) as a short pick list.
 */
async function postalLookup(pc, url, env, ctx) {
  if (!(await breakerOpen(url))) {
    try {
      const data = await representCached(`${REPRESENT}/postcodes/${pc}/?format=json`, `${url.origin}/__lookup-cache/postcode/${pc}`, ctx);
      const hit = data && parseRepresent(data);
      if (hit) return found(hit.code, hit.alternatives, false);
    } catch {
      /* No details logged: the URL holds the postal code */
      console.error("riding lookup: upstream failed, using local table");
      ctx.waitUntil(tripBreaker(url));
    }
  }
  const fsa = await fsaTable(env, url, pc.slice(0, 3));
  if (!fsa) return lookupError("not_found", "That postal code was not found. Check it, or pick your riding from the list.", 404);
  const row = fsa.codes && fsa.codes[pc.slice(3)];
  if (row) {
    const [code, ...alts] = String(row).split(" ").filter(validRiding);
    if (code) return found(code, alts, false);
  }
  const choices = (fsa.choices || []).filter(validRiding);
  if (choices.length === 1) return found(choices[0], [], true);
  if (choices.length > 1) {
    return json({ approximate: true, choices: choices.map((c) => ({ code: c, name: NAMES[c] || c })) }, 200, { "Cache-Control": "no-store" });
  }
  return lookupError("not_found", "That postal code was not found. Check it, or pick your riding from the list.", 404);
}

function found(code, alternatives, approximate) {
  const alts = (alternatives || []).filter((c) => validRiding(c) && c !== code);
  const body = { code, name: NAMES[code] || code, alternatives: alts };
  if (approximate) body.approximate = true;
  return json(body, 200, { "Cache-Control": "no-store" });
}

function lookupError(error, message, status) {
  return json({ error, message }, status, { "Cache-Control": "no-store" });
}

/* Breaker: one small cache entry per data centre, alive for 60 seconds */
function breakerKey(url) {
  return new Request(`${url.origin}/__lookup-cache/represent-breaker`, { method: "GET" });
}
async function breakerOpen(url) {
  try { return !!(await caches.default.match(breakerKey(url))); } catch { return false; }
}
async function tripBreaker(url) {
  try {
    await caches.default.put(breakerKey(url), new Response("open", { headers: { "Cache-Control": `public, max-age=${BREAKER_TTL}` } }));
  } catch { /* the breaker is an optimisation only */ }
}

/* Local data, read from the static assets once per Worker instance */
let edPromise = null;
const fsaMemo = new Map();
function assetJson(env, url, path) {
  return env.ASSETS.fetch(new Request(`${url.origin}${path}`)).then((r) => (r.ok ? r.json() : null));
}
function edShapes(env, url) {
  if (!edPromise) edPromise = assetJson(env, url, "/geo/eds.json").then((d) => (d && d.r) || []).catch((e) => { edPromise = null; throw e; });
  return edPromise;
}
async function fsaTable(env, url, fsa) {
  if (!/^V\d[A-Z]$/.test(fsa)) return null;
  if (!fsaMemo.has(fsa)) {
    if (fsaMemo.size > 200) fsaMemo.clear();
    fsaMemo.set(fsa, await assetJson(env, url, `/geo/pc/${fsa}.json`).catch(() => null));
  }
  return fsaMemo.get(fsa);
}

/**
 * Point in polygon over the compact riding shapes (rings are flat [lon, lat, lon, lat, ...] lists).
 * Ridings whose edge is within NEAR_EDGE_M of the point come back as alternatives.
 * A point in the water just off the coast snaps to the nearest riding within OFFSHORE_M.
 */
function pointLookup(shapes, lon, lat) {
  const kx = 111320 * Math.cos((lat * Math.PI) / 180), ky = 110540;
  const pad = OFFSHORE_M / ky;
  let inside = null;
  const dist = [];
  for (const s of shapes) {
    const [w, so, e, n] = s.b;
    if (lon < w - pad * 2 || lon > e + pad * 2 || lat < so - pad || lat > n + pad) continue;
    let crossings = 0, best = Infinity;
    for (const poly of s.p) {
      for (const ring of poly) {
        for (let i = 0, j = ring.length - 2; i < ring.length; j = i, i += 2) {
          const xi = ring[i], yi = ring[i + 1], xj = ring[j], yj = ring[j + 1];
          if ((yi > lat) !== (yj > lat) && lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi) crossings++;
          best = Math.min(best, segDist((xi - lon) * kx, (yi - lat) * ky, (xj - lon) * kx, (yj - lat) * ky));
        }
      }
    }
    if (crossings % 2 === 1 && !inside) inside = s.c;
    else dist.push([s.c, best]);
  }
  dist.sort((a, b) => a[1] - b[1]);
  if (inside) return { code: inside, alternatives: dist.filter((d) => d[1] <= NEAR_EDGE_M).map((d) => d[0]).slice(0, 3) };
  if (dist.length && dist[0][1] <= OFFSHORE_M) return { code: dist[0][0], alternatives: dist.slice(1).filter((d) => d[1] <= NEAR_EDGE_M).map((d) => d[0]).slice(0, 3) };
  return null;
}
/** Distance from the origin (the point) to the segment A-B, coordinates in metres relative to the point. */
function segDist(ax, ay, bx, by) {
  const dx = bx - ax, dy = by - ay, len = dx * dx + dy * dy;
  const t = len ? Math.max(0, Math.min(1, -(ax * dx + ay * dy) / len)) : 0;
  return Math.hypot(ax + t * dx, ay + t * dy);
}

/** Fetch a Represent URL through the Cache API (30 days). Returns parsed JSON, or null for a 404. */
async function representCached(upstream, cacheKey, ctx) {
  const cache = caches.default;
  const key = new Request(cacheKey, { method: "GET" });
  const hit = await cache.match(key);
  if (hit) {
    const t = await hit.text();
    return t === "not_found" ? null : JSON.parse(t);
  }
  const res = await fetch(upstream, {
    headers: { Accept: "application/json", "User-Agent": "bc-vote-helper (votebc.vinceroyer.ca)" },
    signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
  });
  if (res.status === 404) {
    ctx.waitUntil(cache.put(key, new Response("not_found", { headers: { "Cache-Control": `public, max-age=${NOT_FOUND_TTL}` } })));
    return null;
  }
  if (!res.ok) throw new Error("upstream " + res.status);
  const body = await res.text();
  const data = JSON.parse(body);
  const stored = new Response(body, { headers: { "Content-Type": "application/json", "Cache-Control": `public, max-age=${LOOKUP_TTL}` } });
  ctx.waitUntil(cache.put(key, stored));
  return data;
}

/** Represent postcode (boundaries_centroid, boundaries_concordance) or boundary list (objects) -> riding. */
function parseRepresent(d) {
  const codes = [];
  const names = {};
  const add = (b) => {
    if (!b || !b.related || !String(b.related.boundary_set_url || "").includes(BC_SET)) return;
    const c = String(b.external_id || "").toUpperCase();
    if (!validRiding(c) || codes.includes(c)) return;
    codes.push(c);
    names[c] = String(b.name || "");
  };
  ((d && d.boundaries_centroid) || []).forEach(add);
  ((d && d.boundaries_concordance) || []).forEach(add);
  ((d && d.objects) || []).forEach(add);
  if (!codes.length) return null;
  return { code: codes[0], name: names[codes[0]], alternatives: codes.slice(1) };
}

/* ------------------------------------------------------------------ */
/* Admin API                                                           */
/* ------------------------------------------------------------------ */
/* The dashboard and CSV show the newest sessions only, so one request stays inside Worker memory limits */
const ADMIN_ROWS = 20000;
async function adminApi(request, env, path) {
  if (path === "/api/admin/data" && request.method === "GET") {
    const subs = await env.DB.prepare(
      `SELECT sid, created_at, updated_at, count, country, region, region_code, city, data_as_of, riding, lang, source FROM submissions
       ORDER BY created_at DESC LIMIT ${ADMIN_ROWS}`
    ).all();
    /* Finished quizzes from everyone (shared or not), counted from the day the counter went live */
    const dayAgo = new Date(Date.now() - 86400000).toISOString();
    const [compTotal, compBySource] = await env.DB.batch([
      env.DB.prepare("SELECT COUNT(*) AS sessions, COALESCE(SUM(count), 0) AS people, MIN(created_at) AS since, COALESCE(SUM(CASE WHEN created_at >= ?1 THEN count ELSE 0 END), 0) AS last24 FROM completions").bind(dayAgo),
      env.DB.prepare("SELECT COALESCE(source, 'unknown') AS source, COALESCE(SUM(count), 0) AS people FROM completions GROUP BY 1 ORDER BY 2 DESC"),
    ]);
    const people = await env.DB.prepare(
      `SELECT sid, idx, level, answered, answers FROM people
       WHERE sid IN (SELECT sid FROM submissions ORDER BY created_at DESC LIMIT ${ADMIN_ROWS})`
    ).all();
    return json(
      {
        generated_at: new Date().toISOString(),
        completions: { ...(compTotal.results[0] || {}), by_source: compBySource.results },
        submissions: subs.results,
        people: people.results.map((r) => ({ sid: r.sid, idx: r.idx, level: r.level, answered: r.answered, answers: safeParse(r.answers) })),
      },
      200,
      { "Cache-Control": "no-store" }
    );
  }

  if (path === "/api/admin/export.csv" && request.method === "GET") {
    const rows = await env.DB.prepare(
      `SELECT s.sid, s.created_at, s.updated_at, s.count, s.country, s.region_code, s.city, s.data_as_of, s.riding, s.lang, s.source, p.idx, p.level, p.answered, p.answers
       FROM people p JOIN (SELECT * FROM submissions ORDER BY created_at DESC LIMIT ${ADMIN_ROWS}) s ON s.sid = p.sid
       ORDER BY s.created_at, p.idx`
    ).all();
    const qids = Object.keys(VALID.questions);
    const head = ["session", "created_at", "updated_at", "people_in_session", "country", "region", "city", "data_as_of", "riding", "lang", "source", "person", "level", "answered"];
    qids.forEach((q) => head.push(q, q + "_importance"));
    const lines = [head.map(csv).join(",")];
    for (const r of rows.results) {
      const a = safeParse(r.answers) || {};
      const line = [r.sid, r.created_at, r.updated_at, r.count, r.country, r.region_code, r.city, r.data_as_of, r.riding, r.lang, r.source, r.idx + 1, r.level, r.answered];
      qids.forEach((q) => line.push(a[q] ? a[q].c : "", a[q] ? a[q].w : ""));
      lines.push(line.map(csv).join(","));
    }
    const stamp = new Date().toISOString().slice(0, 10);
    return new Response(lines.join("\r\n") + "\r\n", {
      headers: {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": `attachment; filename="votebc-responses-${stamp}.csv"`,
        "Cache-Control": "no-store",
        ...SECURITY_HEADERS,
      },
    });
  }

  if (path === "/api/admin/delete" && request.method === "POST") {
    const origin = request.headers.get("Origin");
    if (origin && origin !== new URL(request.url).origin) return json({ error: "bad_origin" }, 403);
    let body;
    try { body = await request.json(); } catch { return json({ error: "bad_json" }, 400); }
    const sids = Array.isArray(body && body.sids) ? body.sids.filter((s) => typeof s === "string" && /^[0-9a-f]{32}$/.test(s)).slice(0, 200) : [];
    if (!sids.length) return json({ error: "no_sids" }, 400);
    const stmts = [];
    sids.forEach((s) => {
      stmts.push(env.DB.prepare("DELETE FROM people WHERE sid = ?1").bind(s));
      stmts.push(env.DB.prepare("DELETE FROM submissions WHERE sid = ?1").bind(s));
    });
    await env.DB.batch(stmts);
    return json({ ok: true, deleted: sids.length });
  }

  return json({ error: "not_found" }, 404);
}

function csv(v) {
  if (v == null) return "";
  const s = String(v);
  return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}
function safeParse(s) {
  try { return JSON.parse(s); } catch { return null; }
}

/* ------------------------------------------------------------------ */
/* Cloudflare Access JWT verification                                  */
/* ------------------------------------------------------------------ */
let certCache = { at: 0, keys: [] };

async function accessKeys(env, force) {
  const age = Date.now() - certCache.at;
  if (certCache.keys.length && (force ? age < 60_000 : age < 3600_000)) return certCache.keys;
  const res = await fetch(`https://${env.ACCESS_TEAM}/cdn-cgi/access/certs`);
  if (!res.ok) throw new Error("certs " + res.status);
  const data = await res.json();
  certCache = { at: Date.now(), keys: data.keys || [] };
  return certCache.keys;
}

function b64urlBytes(s) {
  const b64 = s.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((s.length + 3) % 4);
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

function cookie(request, name) {
  const all = request.headers.get("Cookie") || "";
  for (const part of all.split(/;\s*/)) {
    const i = part.indexOf("=");
    if (i > 0 && part.slice(0, i) === name) return part.slice(i + 1);
  }
  return null;
}

async function verifyAccess(request, env) {
  if (!env.ACCESS_AUD || !env.ACCESS_TEAM || !env.ADMIN_EMAIL) return null;
  const token = request.headers.get("Cf-Access-Jwt-Assertion") || cookie(request, "CF_Authorization");
  if (!token) return null;
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  let header, payload;
  try {
    header = JSON.parse(new TextDecoder().decode(b64urlBytes(parts[0])));
    payload = JSON.parse(new TextDecoder().decode(b64urlBytes(parts[1])));
  } catch {
    return null;
  }
  if (header.alg !== "RS256") return null;
  let keys = await accessKeys(env, false);
  let jwk = keys.find((k) => k.kid === header.kid);
  if (!jwk) {
    keys = await accessKeys(env, true);
    jwk = keys.find((k) => k.kid === header.kid);
  }
  if (!jwk) return null;
  const key = await crypto.subtle.importKey("jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
  const ok = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, b64urlBytes(parts[2]), new TextEncoder().encode(parts[0] + "." + parts[1]));
  if (!ok) return null;
  const now = Math.floor(Date.now() / 1000);
  const aud = Array.isArray(payload.aud) ? payload.aud : [payload.aud];
  if (!aud.includes(env.ACCESS_AUD)) return null;
  if (typeof payload.exp !== "number" || payload.exp < now) return null;
  if (payload.iss !== `https://${env.ACCESS_TEAM}`) return null;
  if (payload.type !== undefined && payload.type !== "app") return null;
  const email = String(payload.email || "").toLowerCase();
  const allowed = String(env.ADMIN_EMAIL).toLowerCase().split(",").map((s) => s.trim());
  if (!allowed.includes(email)) return null;
  return { email };
}

/* ------------------------------------------------------------------ */
/* Response helpers                                                    */
/* ------------------------------------------------------------------ */
function json(obj, status = 200, extra = {}) {
  return new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json; charset=utf-8", ...SECURITY_HEADERS, ...extra } });
}
function text(s, status = 200, extra = {}) {
  return new Response(s, { status, headers: { "Content-Type": "text/plain; charset=utf-8", ...SECURITY_HEADERS, ...extra } });
}
function withHeaders(res, extra) {
  const out = new Response(res.body, res);
  for (const [k, v] of Object.entries({ ...SECURITY_HEADERS, ...extra })) out.headers.set(k, v);
  return out;
}
