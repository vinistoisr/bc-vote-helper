"""Build index.html for BC Vote Helper 2026.

Reads template.html, quiz_spec.json and logos/logos_datauri.json, injects the
spec and the logos into <script type="application/json"> blocks, and writes
index.html (the claude.ai Artifact page). Re-run after any spec change:

    python -I build_page.py

Languages: i18n/ui.en.json holds the page's English UI strings (embedded in both builds).
i18n/<lang>.ui.json and i18n/<lang>.spec.json hold translations as {key: [src_hash, text]}; only
entries whose hash matches the current English count. Each language becomes one bundle
{ui: {key: text}, spec: {path: text}}: inline <script> blocks in index.html (the artifact cannot
load extra files), and site/public/i18n/<lang>.json on the website, fetched when chosen.
Languages with no translated strings are left out and hidden from the language picker.
"""
import base64
import hashlib
import html as htmllib
import json
import pathlib
import re
import shutil
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import i18n_strings  # noqa: E402  (same folder; python -I leaves it off sys.path)

TEMPLATE = ROOT / "template.html"
SPEC = ROOT / "quiz_spec.json"
LOGOS = ROOT / "logos" / "logos_datauri.json"
OUT = ROOT / "index.html"

SPEC_MARK = "/*__SPEC__*/"
LOGO_MARK = "/*__LOGOS__*/"
BUILD_MARK = "/*__BUILD__*/"
UI_MARK = "/*__UI_EN__*/"
BUNDLES_MARK = "<!--__I18N_BUNDLES__-->"
NOSCRIPT_MARK = "<!--__NOSCRIPT__-->"
# <html lang> / dir per language code (matches LANGS in template.html)
HTML_LANG = {"pa": "pa", "zh-Hans": "zh-Hans", "zh-Hant": "zh-Hant", "tl": "tl", "fr": "fr-CA", "ru": "ru", "ko": "ko", "fa": "fa"}
RTL = {"fa"}
EM_DASH = chr(0x2014)
PH_RE = re.compile(r"\{[a-z0-9_]+\}")


def safe_json(obj):
    """JSON that cannot close or confuse the surrounding <script> element."""
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    return (
        text.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace(chr(0x2028), "\\u2028")
        .replace(chr(0x2029), "\\u2029")
    )


def load_i18n(spec):
    """(English UI strings, {lang: bundle}) with per-language coverage printed. Bad entries are dropped with a note."""
    en = i18n_strings.ui_source()
    if not en:
        sys.exit("i18n/ui.en.json is missing")
    for k, v in en.items():
        if not isinstance(v, str):
            sys.exit(f"ui.en.json: {k} is not a string")
        if EM_DASH in v:
            sys.exit(f"em dash found in ui.en.json ({k})")
        for ph in re.findall(r"\{([^}]*)\}", v):
            if not re.fullmatch(r"[a-z0-9_]+", ph):
                sys.exit(f"ui.en.json: bad placeholder {{{ph}}} in {k}")
    src = i18n_strings.strings(spec)
    bundles = {}
    print(f"languages (UI {len(en)} strings, spec {len(src)} strings):")
    for lang in i18n_strings.LANGS:
        ui, ui_stale = i18n_strings.ui_overlay(en, i18n_strings.load_ui(lang))
        sp, sp_stale = i18n_strings.spec_overlay(src, i18n_strings.load_lang(lang))
        dropped = 0
        for k, v in list(ui.items()):
            want = sorted(PH_RE.findall(i18n_strings.ui_src_text(k, en)))
            if EM_DASH in v or sorted(PH_RE.findall(v)) != want:
                del ui[k]
                dropped += 1
        for k, v in list(sp.items()):
            if EM_DASH in v:
                del sp[k]
                dropped += 1
        ui_n = sum(1 for k in ui if k in en)
        note = f"  dropped {dropped} (em dash or placeholders)" if dropped else ""
        if ui or sp:
            bundles[lang] = {"ui": ui, "spec": sp}
            print(f"  {lang:8} ui {ui_n:4}/{len(en)} ({100 * ui_n / len(en):5.1f}%)  spec {len(sp):5}/{len(src)} ({100 * len(sp) / max(1, len(src)):5.1f}%)  stale ui {ui_stale}, spec {sp_stale}{note}")
        else:
            print(f"  {lang:8} no translations yet: hidden{note}")
    return en, bundles


def noscript_html(en, bundles):
    """The no-JavaScript notice in English and every bundled language (the page cannot pick one without JavaScript)."""
    out = ['<p class="notice">' + htmllib.escape(en["noscript"]) + "</p>"]
    for lang, b in bundles.items():
        msg = b["ui"].get("noscript")
        if msg:
            d = ' dir="rtl"' if lang in RTL else ""
            out.append(f'<p class="notice" lang="{HTML_LANG.get(lang, lang)}"{d}>' + htmllib.escape(msg) + "</p>")
    return "".join(out)


def fill(template, spec, logos, info, en, inline_bundles, noscript):
    blocks = "".join(f'<script type="application/json" id="bcvh-i18n-{lang}">{safe_json(b)}</script>\n' for lang, b in inline_bundles.items())
    return (
        template.replace(SPEC_MARK, safe_json(spec))
        .replace(LOGO_MARK, safe_json(logos))
        .replace(BUILD_MARK, safe_json(info))
        .replace(UI_MARK, safe_json(en))
        .replace(BUNDLES_MARK + "\n", blocks)
        .replace(BUNDLES_MARK, blocks)
        .replace(NOSCRIPT_MARK, noscript)
    )


def png_size(data_uri):
    head, b64 = data_uri.split(",", 1)
    if "image/png" not in head:
        raise ValueError("logo is not a PNG data URI")
    raw = base64.b64decode(b64[:64] + "=" * (-len(b64[:64]) % 4))
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("bad PNG signature")
    w, h = struct.unpack(">II", raw[16:24])
    return w, h


SITE_DIR = ROOT / "site"
# Public address of the website build.
SITE_URL = "https://votebc.vinceroyer.ca/"
GFONTS_PRECONNECT = '<link rel="preconnect" href="https://fonts.googleapis.com">'
GFONTS_PRECONNECT_STATIC = '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
GFONTS_LINK = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900&amp;'
               'family=Atkinson+Hyperlegible+Mono:wght@400..700&amp;family=Atkinson+Hyperlegible+Next:ital,wght@0,200..800;1,200..800&amp;display=swap">')
JSPDF_CDN = "https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"
OG_ALT = "Which party and candidate match your views? 16 short questions, all 93 BC ridings. votebc.vinceroyer.ca"
FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
           "%3Crect x='6' y='10' width='52' height='44' rx='6' fill='%23121A1F'/%3E"
           "%3Cpath d='M20 33l9 9 16-18' stroke='%23F7F9F9' stroke-width='6' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E")


def build_site(template, spec, logos, build_info, en, bundles):
    """Write site/public/ for votebc.vinceroyer.ca: the same page in a full document, plus the admin dashboard."""
    import html

    # Language bundles are separate files, fetched only when a reader picks that language
    pub = SITE_DIR / "public"
    i18n_dir = pub / "i18n"
    i18n_dir.mkdir(parents=True, exist_ok=True)
    versions = {}
    for lang, b in bundles.items():
        text = json.dumps(b, ensure_ascii=False, separators=(",", ":"))
        (i18n_dir / f"{lang}.json").write_text(text, encoding="utf-8", newline="\n")
        versions[lang] = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
    for old in i18n_dir.glob("*.json"):
        if old.stem not in bundles:
            old.unlink()
    info = dict(build_info, collect=True, langs=list(bundles), i18n_base="/i18n/", i18n_v=versions)
    party_ids = [p["id"] for p in spec["parties"]]
    body = fill(template, spec, logos, info, en, {}, noscript_html(en, bundles))
    m = re.match(r"\s*<title>(.*?)</title>\s*", body, re.S)
    if not m:
        sys.exit("template must start with <title>")
    title = m.group(1)
    body = body[m.end():]
    # The website serves its own fonts and PDF library (strict CSP, no third-party requests); the artifact keeps the CDNs.
    fonts_css = (ROOT / "assets" / "fonts" / "fonts.css").read_text(encoding="utf-8")
    for link in (GFONTS_PRECONNECT, GFONTS_PRECONNECT_STATIC, GFONTS_LINK):
        if link not in body:
            sys.exit("template font link changed; update GFONTS_* in build_page.py")
    body = (body.replace(GFONTS_PRECONNECT + "\n", "").replace(GFONTS_PRECONNECT_STATIC + "\n", "")
            .replace(GFONTS_LINK, "<style>\n" + fonts_css + "</style>"))
    if JSPDF_CDN not in body:
        sys.exit("template jsPDF script changed; update JSPDF_CDN in build_page.py")
    body = body.replace(JSPDF_CDN, "/vendor/jspdf.umd.min.js")
    desc = ("Answer short questions about the October 24, 2026 BC election and see which party, "
            "and which candidate in your riding, is closest to your views. Up to 4 people can take turns or answer together.")
    head = (
        '<!doctype html><html lang="en-CA"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        f"<title>{title}</title>"
        f'<meta name="description" content="{html.escape(desc)}">'
        f'<meta property="og:title" content="{html.escape(title)}">'
        f'<meta property="og:description" content="{html.escape(desc)}">'
        '<meta property="og:type" content="website">'
        f'<meta property="og:url" content="{SITE_URL}">'
        f'<link rel="canonical" href="{SITE_URL}">'
        '<meta property="og:site_name" content="BC Vote Helper">'
        '<meta property="og:locale" content="en_CA">'
        f'<meta property="og:image" content="{SITE_URL}og.png">'
        '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
        f'<meta property="og:image:alt" content="{html.escape(OG_ALT)}">'
        '<meta name="twitter:card" content="summary_large_image">'
        f'<meta name="twitter:title" content="{html.escape(title)}">'
        f'<meta name="twitter:description" content="{html.escape(desc)}">'
        f'<meta name="twitter:image" content="{SITE_URL}og.png">'
        f'<link rel="icon" href="{FAVICON}">'
        "<style>*,*::before,*::after{box-sizing:border-box}html,body{margin:0;padding:0}</style>"
        "</head><body>"
    )
    (pub / "admin").mkdir(parents=True, exist_ok=True)
    (pub / "index.html").write_text(head + body + "</body></html>", encoding="utf-8", newline="\n")
    shutil.copyfile(ROOT / "assets" / "og.png", pub / "og.png")  # link preview, drawn by make_og.py
    shutil.copytree(ROOT / "assets" / "fonts", pub / "fonts", dirs_exist_ok=True)  # from fetch_fonts.py
    (pub / "fonts" / "fonts.css").unlink(missing_ok=True)
    (pub / "vendor").mkdir(exist_ok=True)
    shutil.copyfile(ROOT / "assets" / "vendor" / "jspdf.umd.min.js", pub / "vendor" / "jspdf.umd.min.js")  # jsPDF 2.5.1, MIT
    (pub / "robots.txt").write_text("User-agent: *\nAllow: /\nDisallow: /admin/\n", encoding="utf-8", newline="\n")

    admin_tpl = (SITE_DIR / "admin_template.html").read_text(encoding="utf-8")
    if chr(0x2014) in admin_tpl:
        sys.exit("em dash found in admin_template.html")
    slim = {
        "meta": spec["meta"],
        "parties": [{k: p[k] for k in ("id", "name", "short_name", "color")} for p in spec["parties"]],
        "regions": [{"id": r["id"], "name": r["name"], "local_qids": r.get("local_qids", [])} for r in spec.get("regions", [])],
        "ridings": [
            {
                "code": r["code"], "name": r["name"], "region": r["region"],
                "candidates": [{k: c[k] for k in ("id", "name", "party_id")} for c in r.get("candidates", []) if c.get("party_id") in party_ids],
            }
            for r in spec.get("ridings", [])
        ],
        "issues": spec["issues"],
        "levels": spec["levels"],
        "questions": [
            {
                "id": q["id"], "issue_id": q["issue_id"], "scope": q["scope"],
                "no_pos": [pid for pid, pp in q.get("party_positions", {}).items() if pp.get("no_position") is True],
                "prompt": q["prompt"].get("3") or next(iter(q["prompt"].values())),
                "options": [{"id": o["id"], "text": o["text"].get("3") or next(iter(o["text"].values())), "scores": o["scores"]} for o in q["options"]],
            }
            for q in spec["questions"]
        ],
    }
    (pub / "admin" / "index.html").write_text(admin_tpl.replace(SPEC_MARK, safe_json(slim)), encoding="utf-8", newline="\n")
    # Valid ids for server-side checks (every region's questions, every riding)
    valid = {
        "questions": {q["id"]: [o["id"] for o in q["options"]] for q in spec["questions"]},
        "parties": party_ids,
        "scores": {q["id"]: {o["id"]: o["scores"] for o in q["options"]} for q in spec["questions"]},
        "local_qids": [q["id"] for q in spec["questions"] if q["scope"] != "provincial"],
        "regions": {r["id"]: r.get("local_qids", []) for r in spec.get("regions", [])},
        "ridings": {
            r["code"]: {
                "region": r["region"],
                "candidates": [{"id": c["id"], "party_id": c["party_id"]} for c in r.get("candidates", []) if c.get("party_id") in party_ids],
            }
            for r in spec.get("ridings", [])
        },
        "data_as_of": spec["meta"].get("data_as_of"),
    }
    (SITE_DIR / "src" / "spec_valid.json").write_text(json.dumps(valid, separators=(",", ":")), encoding="utf-8")
    sizes = ", ".join(f"{lang} {(i18n_dir / (lang + '.json')).stat().st_size / 1024:.0f} KB" for lang in bundles)
    print(f"wrote site/public (index {(pub / 'index.html').stat().st_size / 1024:.0f} KB, admin, i18n: {sizes or 'none'}) and site/src/spec_valid.json")


def check_ridings(spec):
    """Regions and ridings must point at things that exist, so the page never meets a dangling id."""
    qids = {q["id"]: q for q in spec["questions"]}
    party_ids = {p["id"] for p in spec["parties"]}
    regions = {r["id"]: r for r in spec.get("regions", [])}
    if not regions or not spec.get("ridings"):
        sys.exit("spec needs regions and ridings")
    for r in regions.values():
        for qid in r.get("local_qids", []):
            if qid not in qids:
                sys.exit(f"region {r['id']}: unknown question {qid}")
            if qids[qid]["scope"] == "provincial":
                sys.exit(f"region {r['id']}: {qid} is a provincial question")
        if len(r.get("local_qids", [])) > 3:
            print(f"note: region {r['id']} has {len(r['local_qids'])} local questions (the page is tuned for 0 to 3)")
    codes = set()
    for rd in spec["ridings"]:
        code = rd.get("code", "")
        if len(code) != 3 or not code.isalpha() or code != code.upper():
            sys.exit(f"bad riding code {code!r}")
        if code in codes:
            sys.exit(f"duplicate riding code {code}")
        codes.add(code)
        if rd.get("region") not in regions:
            sys.exit(f"riding {code}: unknown region {rd.get('region')}")
        for c in rd.get("candidates", []):
            if c.get("party_id") not in party_ids:
                sys.exit(f"riding {code}: candidate {c.get('id')} has party {c.get('party_id')}, which is not scored")
    local_owned = [q for r in regions.values() for q in r.get("local_qids", [])]
    if len(local_owned) != len(set(local_owned)):
        sys.exit("a local question belongs to more than one region")
    for q in spec["questions"]:
        if q["scope"] != "provincial" and q["id"] not in local_owned:
            print(f"note: local question {q['id']} is in no region, so it is never asked")


def main():
    template = TEMPLATE.read_text(encoding="utf-8")
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    logos_raw = json.loads(LOGOS.read_text(encoding="utf-8"))

    party_ids = [p["id"] for p in spec["parties"]]
    missing = [p for p in party_ids if p not in logos_raw]
    if missing:
        sys.exit(f"missing logos for: {', '.join(missing)}")

    logos = {}
    for pid in party_ids:
        uri = logos_raw[pid]
        w, h = png_size(uri)
        logos[pid] = {"src": uri, "w": w, "h": h}

    check_ridings(spec)

    for mark in (SPEC_MARK, LOGO_MARK, UI_MARK, BUNDLES_MARK, NOSCRIPT_MARK):
        if template.count(mark) != 1:
            sys.exit(f"template must contain {mark} exactly once")

    # Guard the house rule: no em dashes in anything we publish.
    for name, text in (("template.html", template), ("quiz_spec.json", SPEC.read_text(encoding="utf-8"))):
        if chr(0x2014) in text:
            sys.exit(f"em dash found in {name}")

    build_info = {
        "data_as_of": spec["meta"].get("data_as_of"),
        "questions": len(spec["questions"]),
        "parties": len(spec["parties"]),
    }
    en, bundles = load_i18n(spec)
    # The artifact carries every bundle inline
    art_info = dict(build_info, langs=list(bundles))
    page = fill(template, spec, logos, art_info, en, bundles, noscript_html(en, bundles))
    OUT.write_text(page, encoding="utf-8", newline="\n")

    build_site(template, spec, logos, build_info, en, bundles)

    head = page[:8192]
    if "<title>" not in head:
        sys.exit("<title> is not in the first 8KB of index.html")
    size = OUT.stat().st_size
    print(f"wrote {OUT} ({size / 1024:.0f} KB; {build_info['questions']} questions, {build_info['parties']} parties, data as of {build_info['data_as_of']})")


if __name__ == "__main__":
    main()
