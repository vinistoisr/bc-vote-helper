"""
Plain-HTML pages for search engines and AI assistants, written into site/public/ by build_page.py.

The quiz is drawn by JavaScript, so crawlers that do not run scripts saw only the title. These pages need no
script: one per riding (candidates, bios with sources, 2024 result, voting dates), a riding index, an About page
with the method, privacy and voting facts, plus sitemap.xml, llms.txt, robots.txt and the IndexNow key file.
English only; the quiz itself is the translated part. Facts come from quiz_spec.json, so a rebuild keeps them current.
"""
import datetime
import html
import json
import re
import unicodedata

SITE = "https://votebc.vinceroyer.ca"
REPO = "https://github.com/vinistoisr/bc-vote-helper"
# IndexNow (Bing, Yandex, Seznam, Naver): the key file proves the site owns the key used for URL submissions
INDEXNOW_KEY = "7c1e4b9a2f6d48e3a05b9c8d1e2f3a47"
LANG_NAMES = ["English", "Punjabi (ਪੰਜਾਬੀ)", "Simplified Chinese (简体中文)", "Traditional Chinese (繁體中文)",
              "Tagalog", "French (français)", "Russian (русский)", "Korean (한국어)", "Farsi (فارسی)"]
LANG_CODES = ["en", "pa", "zh-Hans", "zh-Hant", "tl", "fr", "ru", "ko", "fa"]
PARTY_2024 = {"ndp": "BC NDP", "conservative": "BC Conservatives", "green": "BC Greens", "united": "BC United",
              "independent": "Independent"}

e = html.escape


def slug(name):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def long_date(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d.strftime('%B')} {d.day}, {d.year}"


CSS = """
@font-face{font-family:'Archivo';font-style:normal;font-weight:400 900;font-stretch:62% 125%;font-display:swap;src:url(/fonts/archivo-normal-latin.woff2) format('woff2')}
@font-face{font-family:'Atkinson Hyperlegible Next';font-style:normal;font-weight:200 800;font-display:swap;src:url(/fonts/atkinson-hyperlegible-next-normal-latin.woff2) format('woff2')}
:root{color-scheme:light;--bg:#ECEFEE;--surface:#FFFFFF;--ink:#121A1F;--ink-2:#4A5661;--line:#C7CFD2;--sea:#2B6E7E;--btn:#121A1F;--on-btn:#FFFFFF}
@media (prefers-color-scheme:dark){:root{color-scheme:dark;--bg:#0D1215;--surface:#151C20;--ink:#E8EDEF;--ink-2:#A9B6BD;--line:#2C373E;--sea:#7FC0CF;--btn:#E8EDEF;--on-btn:#0D1215}}
*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.55 'Atkinson Hyperlegible Next',system-ui,-apple-system,'Segoe UI',sans-serif}
.wrap{max-width:760px;margin:0 auto;padding:0 16px}
main.wrap{padding-top:14px}
header.top{border-bottom:1px solid var(--line);padding:14px 0}
header.top a{color:var(--ink);text-decoration:none;font-family:Archivo,system-ui,sans-serif;font-weight:800;font-stretch:90%;font-size:1.1rem}
nav.crumbs{font-size:.9rem;color:var(--ink-2);margin:18px 0 0}
nav.crumbs a{color:var(--ink-2)}
h1,h2,h3{font-family:Archivo,system-ui,sans-serif;font-stretch:92%;line-height:1.2;margin:0}
h1{font-size:clamp(1.6rem,5vw,2.2rem);font-weight:850;margin:10px 0 12px}
h2{font-size:1.3rem;font-weight:800;margin:34px 0 10px}
h3{font-size:1.08rem;font-weight:750}
p{margin:0 0 12px}
a{color:var(--sea)}
.lede{font-size:1.08rem;color:var(--ink-2)}
.cta{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:16px;margin:22px 0}
.cta p{margin:0 0 10px}
.btn{display:inline-block;background:var(--btn);color:var(--on-btn);text-decoration:none;font-weight:700;padding:10px 18px;border-radius:8px}
ul.cands{list-style:none;padding:0;margin:0}
ul.cands li{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:0 0 10px}
.party{color:var(--ink-2);font-weight:600}
.tag{font-size:.82rem;border:1px solid var(--line);border-radius:999px;padding:1px 8px;margin-left:6px;color:var(--ink-2);white-space:nowrap}
.src{font-size:.85rem;color:var(--ink-2);margin:6px 0 0}
.small{font-size:.9rem;color:var(--ink-2)}
dl.facts{display:grid;grid-template-columns:max-content 1fr;gap:6px 14px;margin:0 0 12px}
dl.facts dt{font-weight:700}dl.facts dd{margin:0}
@media (max-width:520px){dl.facts{grid-template-columns:1fr}dl.facts dd{margin-bottom:6px}}
ul.ridings{columns:2 220px;padding-left:18px;margin:0 0 8px}
ul.ridings li{break-inside:avoid;margin:0 0 4px}
footer.foot{border-top:1px solid var(--line);margin-top:40px;padding:20px 0 40px;font-size:.9rem;color:var(--ink-2)}
footer.foot a{color:var(--ink-2)}
"""


def page(path, title, desc, body, ld=None, data_as_of=""):
    url = SITE + path
    lds = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (ld or []))
    return (
        '<!doctype html><html lang="en-CA"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{e(title)}</title>"
        f'<meta name="description" content="{e(desc)}">'
        f'<link rel="canonical" href="{url}">'
        f'<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">'
        f'<meta property="og:type" content="website"><meta property="og:url" content="{url}">'
        '<meta property="og:site_name" content="BC Vote Helper"><meta property="og:locale" content="en_CA">'
        f'<meta property="og:image" content="{SITE}/og.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
        '<meta name="twitter:card" content="summary_large_image">'
        f'<meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(desc)}">'
        f'<meta name="twitter:image" content="{SITE}/og.png">'
        "<link rel=\"icon\" href=\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='12' fill='%23121A1F'/%3E%3Cpath d='M18 33l9 9 19-21' stroke='%23fff' stroke-width='7' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E\">"
        f"<style>{CSS}</style>{lds}</head><body>"
        '<header class="top"><div class="wrap"><a href="/">BC Vote Helper 2026</a></div></header>'
        f'<main class="wrap">{body}</main>'
        '<footer class="foot"><div class="wrap">'
        f"<p>Independent and not connected to any party. Data as of {e(data_as_of)}. Not an endorsement.</p>"
        f'<p><a href="/">Take the quiz</a> · <a href="/ridings/">All 93 ridings</a> · <a href="/about/">About and method</a> · '
        f'<a href="{REPO}">Code and sources</a> · <a href="https://elections.bc.ca/">Elections BC</a></p>'
        "</div></footer></body></html>"
    )


def voting_block(htv):
    return (
        "<h2>How and when to vote</h2>"
        '<dl class="facts">'
        f"<dt>Voting day</dt><dd>{e(htv['voting_day'])}</dd>"
        f"<dt>Advance voting</dt><dd>{e(htv['advance_voting'])}</dd>"
        f"<dt>Where</dt><dd>{e(htv['where'])}</dd>"
        f"<dt>Who can vote</dt><dd>{e(htv['eligibility'])}</dd>"
        f"<dt>By mail</dt><dd>{e(htv['mail_in'])}</dd>"
        "</dl>"
        '<p class="small">From Elections BC: '
        + ", ".join(f'<a href="{e(l["url"])}">{e(l["label"].replace("Elections BC: ", ""))}</a>'
                    for l in htv["links"] if "elections.bc.ca" in l["url"])
        + ".</p>"
    )


def surname(name):
    return name.split()[-1].lower() if name.split() else name.lower()


def riding_page(r, spec, regions, by_region, parties):
    as_of = long_date(spec["meta"]["data_as_of"])
    region = regions[r["region"]]
    people = [dict(c, label=parties[c["party_id"]]["short_name"]) for c in r["candidates"]]
    people += [dict(o, label=o["party_label"]) for o in r["others"]]
    people.sort(key=lambda c: (surname(c["name"]), c["name"]))
    n = len(people)

    items = []
    for c in people:
        tag = '<span class="tag">Incumbent</span>' if c.get("incumbent") else ""
        src = ""
        if c.get("sources"):
            src = '<p class="src">Sources: ' + ", ".join(f'<a href="{e(s["url"])}" rel="nofollow">{e(s["label"])}</a>' for s in c["sources"]) + "</p>"
        b = c.get("bio")
        b = b.get("3") or next(iter(b.values()), "") if isinstance(b, dict) else b  # some bios are written per reading level
        bio = f"<p>{e(b)}</p>" if b else ""
        items.append(f'<li><h3>{e(c["name"])}{tag}</h3><p class="party">{e(c["label"])}</p>{bio}{src}</li>')

    res = r.get("result_2024")
    facts = []
    if r.get("communities"):
        facts.append(f"<p>{e(r['name'])} takes in {e(r['communities'])}.</p>")
    if res:
        votes = int(res["margin_votes"])
        facts.append(f"<p>In 2024, {e(res['winner'])} ({e(PARTY_2024.get(res['party'], res['party']))}) won here by "
                     f"{votes:,} vote{'s' if votes != 1 else ''}, {res['margin_pct']} points.</p>")
    if r.get("mla_change"):
        facts.append(f"<p>{e(r['mla_change'])}</p>")

    local = [q for q in spec["questions"] if q["id"] in region.get("local_qids", [])]
    local_html = ""
    if local:
        local_html = (f"<h2>Questions for {e(region['name'])}</h2>"
                      f"<p>Everyone answers 13 province-wide questions. Voters in {e(region['name'])} also get these 3:</p><ul>"
                      + "".join(f"<li>{e(q['prompt']['3'])}</li>" for q in local) + "</ul>")

    near = [x for x in by_region[r["region"]] if x["code"] != r["code"]]
    near_html = (f"<h2>Other ridings in {e(region['name'])}</h2><ul class=\"ridings\">"
                 + "".join(f'<li><a href="/ridings/{slug(x["name"])}/">{e(x["name"])}</a></li>' for x in near) + "</ul>")

    names = ", ".join(c["name"] for c in people)
    title = f"{r['name']} candidates, BC election 2026"
    desc = (f"The {n} candidates running in {r['name']} in the October 24, 2026 BC election: {names}. "
            "Short bios with sources, the 2024 result, and how to vote.")
    body = (
        f'<nav class="crumbs"><a href="/ridings/">All ridings</a> · {e(region["name"])}</nav>'
        f"<h1>{e(r['name'])}: candidates in the 2026 BC election</h1>"
        f'<p class="lede">{n} candidates are on the ballot in {e(r["name"])} for the provincial election on Saturday, October 24, 2026. '
        "They are listed by last name.</p>"
        '<div class="cta"><p>Answer 16 short questions to see which party, and which of these candidates, is closest to your views. '
        "Available in 9 languages.</p>"
        '<a class="btn" href="/">Take the quiz</a></div>'
        f'<h2>Candidates</h2><ul class="cands">{"".join(items)}</ul>'
        f'<p class="small">Candidate list from Elections BC, as of {as_of}.</p>'
        + (f"<h2>About the riding</h2>{''.join(facts)}" if facts else "")
        + local_html
        + voting_block(spec["how_to_vote"])
        + near_html
    )
    ld = [{
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "BC Vote Helper 2026", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Ridings", "item": SITE + "/ridings/"},
            {"@type": "ListItem", "position": 3, "name": r["name"], "item": f"{SITE}/ridings/{slug(r['name'])}/"},
        ],
    }]
    return page(f"/ridings/{slug(r['name'])}/", title, desc, body, ld, as_of)


def index_page(spec, regions, by_region):
    as_of = long_date(spec["meta"]["data_as_of"])
    total = sum(len(r["candidates"]) + len(r["others"]) for r in spec["ridings"])
    parts = []
    for rid, reg in regions.items():
        rs = by_region.get(rid, [])
        if not rs:
            continue
        parts.append(f"<h2>{e(reg['name'])}</h2><ul class=\"ridings\">"
                     + "".join(f'<li><a href="/ridings/{slug(x["name"])}/">{e(x["name"])}</a></li>' for x in rs) + "</ul>")
    title = "Candidates in all 93 BC ridings, 2026 election"
    desc = (f"Every candidate running in the October 24, 2026 British Columbia election, riding by riding: "
            f"{total} candidates in 93 ridings, with short bios and sources.")
    body = (
        "<h1>Candidates in every BC riding</h1>"
        f'<p class="lede">{total} candidates are running in BC\'s 93 ridings for the provincial election on Saturday, October 24, 2026. '
        "Pick your riding to see who is on your ballot.</p>"
        '<div class="cta"><p>Not sure which riding you live in? The quiz finds it from your postal code, then shows your candidates '
        "and which party is closest to your answers.</p>"
        '<a class="btn" href="/">Find my riding and take the quiz</a></div>'
        + "".join(parts)
    )
    return page("/ridings/", title, desc, body, None, as_of)


def about_page(spec):
    m = spec["meta"]
    as_of = long_date(m["data_as_of"])
    parties = spec["parties"]
    party_list = "".join(
        f"<li><b>{e(p['name'])}</b> ({e(p['short_name'])}), leader {e(p['leader'])}, "
        f"{p['candidates_running']} candidates</li>" for p in parties)
    faq = [
        ("What is BC Vote Helper 2026?",
         "A quiz for the British Columbia provincial election on October 24, 2026. You answer 16 short questions and see which "
         "party, and which candidate in your riding, is closest to your views. It covers all 93 ridings."),
        ("Is it connected to a party?",
         "No. It is independent and not connected to any party, campaign or government. It compares your answers with what "
         "the parties have published and done. It does not tell you how to vote."),
        ("Who made it?",
         "Vincent Royer, a voter in Surrey, BC, made it to help his family decide. Everything is public and open source, "
         "including the scoring and every source, on GitHub."),
        ("Which languages does it support?",
         "English, Punjabi, Simplified Chinese, Traditional Chinese, Tagalog, French, Russian, Korean and Farsi."),
        ("How are parties scored?", m["method_summary"]["3"]),
        ("Which parties are scored?",
         "BC NDP, BC Conservatives, BC Greens, CentreBC and OneBC. " + spec["other_parties_note"]["3"]),
        ("Can several people take it together?",
         "Yes. Up to 4 people can take turns or answer together on one screen, each at their own reading level."),
        ("What happens to my answers?",
         "Your postal code is used only to find your riding and is never stored. If you leave the share box ticked, your answers are "
         "stored anonymously, with no name and no IP address. All stored answers are deleted on November 23, 2026."),
        ("Who can use it?", "It is open to people in Canada and is meant for BC voters."),
    ]
    faq_html = "".join(f"<h3>{e(q)}</h3><p>{e(a)}</p>" for q, a in faq)
    body = (
        "<h1>About BC Vote Helper 2026</h1>"
        '<p class="lede">An independent quiz for the British Columbia provincial election on Saturday, October 24, 2026. '
        "Answer 16 short questions and see which party, and which candidate in your riding, is closest to your views.</p>"
        '<div class="cta"><a class="btn" href="/">Take the quiz</a></div>'
        "<h2>What it does</h2><ul>"
        "<li>Finds your riding from your postal code, your location, or a list of all 93 ridings.</li>"
        "<li>Asks 13 province-wide questions and 3 about your region, at one of 5 reading levels.</li>"
        "<li>Shows how close each party is to your answers, then the candidates on your ballot.</li>"
        "<li>Up to 4 people can take turns or answer together.</li>"
        f"<li>Works in {len(LANG_NAMES)} languages: {e(', '.join(LANG_NAMES))}.</li></ul>"
        "<h2>How the matching works</h2>"
        f"<p>{e(m['method_summary']['3'])}</p>"
        f"<p>{e(m['disclaimer']['3'])}</p>"
        "<h2>Parties in the quiz</h2>"
        f"<ul>{party_list}</ul><p>{e(spec['other_parties_note']['3'])}</p>"
        "<h2>Sources</h2>"
        f"<p>Every party position links to its sources: party platforms and announcements, legislative records, Elections BC, "
        f"and news reports. Data as of {as_of}. The full list and the scoring are on "
        f'<a href="{REPO}">GitHub</a>.</p>'
        + voting_block(spec["how_to_vote"])
        + f"<h2>Questions and answers</h2>{faq_html}"
    )
    ld = [
        {"@context": "https://schema.org", "@type": "FAQPage",
         "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]},
        home_ld(spec),
    ]
    title = "About BC Vote Helper 2026: method, sources and privacy"
    desc = ("How BC Vote Helper 2026 matches your answers with BC parties and candidates for the October 24, 2026 election: "
            "the method, the sources, the languages and what happens to your answers.")
    return page("/about/", title, desc, body, ld, as_of)


def home_ld(spec):
    return {
        "@context": "https://schema.org", "@type": "WebApplication",
        "name": "BC Vote Helper 2026", "url": SITE + "/",
        "description": ("Answer 16 short questions about the October 24, 2026 British Columbia election and see which party, "
                        "and which candidate in your riding, is closest to your views. Covers all 93 ridings, in 9 languages."),
        "applicationCategory": "ReferenceApplication", "operatingSystem": "Any",
        "inLanguage": LANG_CODES,
        "author": {"@type": "Person", "name": "Vincent Royer"},
        "isBasedOn": REPO,
        "dateModified": spec["meta"]["data_as_of"],
        "about": {"@type": "Event", "name": "2026 British Columbia general election", "startDate": spec["meta"]["election_date"],
                  "location": {"@type": "AdministrativeArea", "name": "British Columbia, Canada"}},
    }


def llms_txt(spec, regions, by_region):
    m = spec["meta"]
    lines = [
        "# BC Vote Helper 2026",
        "",
        "> An independent, non-partisan quiz for the British Columbia provincial election on Saturday, October 24, 2026. "
        "Voters answer 16 short questions and see which party, and which candidate in their riding, is closest to their views. "
        "It covers all 93 ridings and works in 9 languages (English, Punjabi, Simplified and Traditional Chinese, Tagalog, French, "
        "Russian, Korean, Farsi). Not connected to any party. Everything is public and open source.",
        "",
        f"Data as of {long_date(m['data_as_of'])}. Advance voting runs October 16 to 21, 2026. "
        "Scored parties: " + ", ".join(f"{p['short_name']} ({p['leader']})" for p in spec["parties"]) + ".",
        "",
        "## Main pages",
        f"- [The quiz]({SITE}/): postal code lookup, 16 questions, results by party and by local candidate. Add ?lang=pa, zh-Hans, zh-Hant, tl, fr, ru, ko or fa for another language.",
        f"- [About and method]({SITE}/about/): how answers are scored, sources, privacy, how to vote.",
        f"- [Candidates in all 93 ridings]({SITE}/ridings/): one page per riding with every candidate, short bios with sources and the 2024 result.",
        f"- [Source code, scoring and all sources]({REPO})",
        "",
        "## Ridings",
    ]
    for rid, reg in regions.items():
        rs = by_region.get(rid, [])
        if rs:
            lines.append(f"- {reg['name']}: " + ", ".join(f"[{x['name']}]({SITE}/ridings/{slug(x['name'])}/)" for x in rs))
    lines += ["", "## Official election information", "- [Elections BC](https://elections.bc.ca/)", ""]
    return "\n".join(lines)


def write(pub, spec):
    """Write the plain-HTML pages and crawler files into site/public/. Returns the list of page URLs."""
    regions = {r["id"]: r for r in spec["regions"]}
    parties = {p["id"]: p for p in spec["parties"]}
    by_region = {}
    for r in sorted(spec["ridings"], key=lambda x: x["name"]):
        by_region.setdefault(r["region"], []).append(r)
    slugs = [slug(r["name"]) for r in spec["ridings"]]
    if len(set(slugs)) != len(slugs):
        raise SystemExit("two ridings share a page slug")

    out = {}
    out["about/index.html"] = about_page(spec)
    out["ridings/index.html"] = index_page(spec, regions, by_region)
    for r in spec["ridings"]:
        out[f"ridings/{slug(r['name'])}/index.html"] = riding_page(r, spec, regions, by_region, parties)

    ridings_dir = pub / "ridings"
    if ridings_dir.exists():
        keep = {f"ridings/{s}/index.html" for s in slugs}
        for old in ridings_dir.glob("*/index.html"):
            if old.relative_to(pub).as_posix() not in keep:
                old.unlink()
                old.parent.rmdir()
    for rel, text in out.items():
        if chr(0x2014) in text:
            raise SystemExit(f"em dash in {rel}")
        f = pub / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8", newline="\n")

    lastmod = spec["meta"]["data_as_of"]
    urls = [SITE + "/", SITE + "/about/", SITE + "/ridings/"] + [f"{SITE}/ridings/{s}/" for s in sorted(slugs)]
    alt = "".join(f'<xhtml:link rel="alternate" hreflang="{l}" href="{SITE}/?lang={l}"/>' for l in LANG_CODES) + \
        f'<xhtml:link rel="alternate" hreflang="x-default" href="{SITE}/"/>'
    entries = []
    for u in urls:
        extra = alt if u == SITE + "/" else ""
        entries.append(f"<url><loc>{u}</loc><lastmod>{lastmod}</lastmod>{extra}</url>")
    for l in LANG_CODES[1:]:
        entries.append(f"<url><loc>{SITE}/?lang={l}</loc><lastmod>{lastmod}</lastmod>{alt}</url>")
    (pub / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(entries) + "\n</urlset>\n", encoding="utf-8", newline="\n")
    (pub / "llms.txt").write_text(llms_txt(spec, regions, by_region), encoding="utf-8", newline="\n")
    (pub / "robots.txt").write_text(
        "User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /api/\n\n"
        f"Sitemap: {SITE}/sitemap.xml\n", encoding="utf-8", newline="\n")
    (pub / f"{INDEXNOW_KEY}.txt").write_text(INDEXNOW_KEY, encoding="utf-8", newline="\n")
    return urls + [f"{SITE}/?lang={l}" for l in LANG_CODES[1:]]
