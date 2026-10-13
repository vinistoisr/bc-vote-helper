"""Translatable text in quiz_spec.json, keyed by stable paths.

Keys use ids, not list positions, so they survive reordering:
    questions/q_housing/options/b/text/3
    ridings/ABS/candidates/leah_ballantyne/bio

    python -I i18n_strings.py extract     writes i18n/source.spec.json (key -> English)
    python -I i18n_strings.py status      per language: translated, missing, stale (spec and UI)
    python -I i18n_strings.py merge-ui [lang ...]   i18n/out/<lang>/ui.json -> i18n/<lang>.ui.json (with hashes)

Translations live in i18n/<lang>.spec.json as {key: [src_hash, text]}. The hash is of the
English text the translation was made from; when the English changes, the entry is stale and
the page shows English for that string until it is translated again.
Source labels, URLs, names, ids and scoring notes stay in English on purpose.
"""
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SPEC = ROOT / "quiz_spec.json"
I18N = ROOT / "i18n"
LANGS = ["pa", "zh-Hans", "zh-Hant", "tl", "fr", "ru", "ko", "fa"]

# Paths (with list items named by id/code) that the page shows and that are worth translating.
ALLOW = [re.compile(p) for p in (
    r"^meta/(disclaimer|method_summary)/\d$",
    r"^levels/\d/(label|experience|hint)$",
    r"^parties/[a-z]+/(name|short_name|leader_note)$",
    r"^parties/[a-z]+/(one_liner|record_summary)/\d$",
    r"^other_parties_note/\d$",
    r"^issues/[a-z_]+/label(/\d)?$",
    r"^questions/[a-z_0-9]+/(prompt|context)/\d$",
    r"^questions/[a-z_0-9]+/options/[a-z]/text/\d$",
    r"^questions/[a-z_0-9]+/party_positions/[a-z]+/text/\d$",
    r"^regions/[a-z_]+/name$",
    r"^ridings/[A-Z]{3}/(communities|mla_change)$",
    r"^ridings/[A-Z]{3}/candidates/[a-z0-9_]+/(bio|record_note)$",
    r"^ridings/[A-Z]{3}/others/[a-z0-9_]+/(bio|party_label)$",
    r"^local/(riding_note|scoring_method)$",
    r"^local/context/(competitiveness|demographics|forum_note|polls_projection)$",
    r"^local/context/results_history/[0-9a-z_]+/note$",
    r"^local/candidates/[a-z0-9_]+/(bio|record_note)$",
    r"^how_to_vote/(voting_day|advance_voting|mail_in|eligibility|id_rules|where|other_dates|kid_note)$",
    r"^how_to_vote/links/\d+/label$",
    r"^sources/\d+/used_for$",
)]


def item_key(item, i):
    if isinstance(item, dict):
        for k in ("id", "code"):
            if isinstance(item.get(k), str) and item[k]:
                return item[k]
        if isinstance(item.get("name"), str):
            return re.sub(r"[^a-z0-9]+", "_", item["name"].lower()).strip("_")
        if "year" in item:
            return str(item["year"])
    return str(i)


def walk(obj, path, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            walk(v, path + [str(k)], out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk(v, path + [item_key(v, i)], out)
    elif isinstance(obj, str) and obj.strip():
        key = "/".join(path)
        base = re.sub(r"/\d$", "", key)  # fields that vary by reading level
        if any(p.match(key) or p.match(base) for p in ALLOW):
            out[key] = obj


def strings(spec):
    out = {}
    walk(spec, [], out)
    return out


def h(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


def apply(spec, lang_entries, source):
    """Return (translated spec copy, stale count, missing count). Untranslated strings stay English."""
    spec = json.loads(json.dumps(spec))
    hits = stale = 0

    def rec(obj, path):
        nonlocal hits, stale
        if isinstance(obj, dict):
            for k, v in list(obj.items()):
                p = path + [str(k)]
                if isinstance(v, str):
                    key = "/".join(p)
                    e = lang_entries.get(key)
                    if e and key in source:
                        if e[0] == h(source[key]):
                            obj[k] = e[1]
                            hits += 1
                        else:
                            stale += 1
                else:
                    rec(v, p)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                p = path + [item_key(v, i)]
                if isinstance(v, str):
                    key = "/".join(p)
                    e = lang_entries.get(key)
                    if e and key in source and e[0] == h(source[key]):
                        obj[i] = e[1]
                        hits += 1
                else:
                    rec(v, p)

    rec(spec, [])
    return spec, stale, len(source) - hits - stale


def load_lang(lang):
    f = I18N / f"{lang}.spec.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def spec_overlay(source, lang_entries):
    """{key: text} for the page's runtime overlay: entries whose hash matches the current English. Returns (overlay, stale)."""
    out, stale = {}, 0
    for k, e in lang_entries.items():
        if k not in source or not isinstance(e, list) or len(e) != 2 or not isinstance(e[1], str):
            continue
        if e[0] == h(source[k]):
            out[k] = e[1]
        else:
            stale += 1
    return out, stale


# UI strings (template.html chrome): i18n/ui.en.json is {key: English}; i18n/<lang>.ui.json is {key: [src_hash, text]}.
# Plurals are key_one / key_other in English. A language with more plural forms may add key_few, key_many,
# key_two or key_zero beside them; those are hashed against the English key_other.
UI_EN = I18N / "ui.en.json"
PLURAL_EXTRA = re.compile(r"^(.+)_(zero|two|few|many)$")


def ui_source():
    return json.loads(UI_EN.read_text(encoding="utf-8")) if UI_EN.exists() else {}


def ui_src_text(key, en):
    """English text a UI key is translated from (extra plural forms use key_other), or None for unknown keys."""
    if key in en:
        return en[key]
    m = PLURAL_EXTRA.match(key)
    if m and m.group(1) + "_other" in en:
        return en[m.group(1) + "_other"]
    return None


def load_ui(lang):
    f = I18N / f"{lang}.ui.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def ui_overlay(en, lang_entries):
    """{key: text} for the UI bundle: entries whose hash matches the current English. Returns (overlay, stale)."""
    out, stale = {}, 0
    for k, e in lang_entries.items():
        src = ui_src_text(k, en)
        if src is None or not isinstance(e, list) or len(e) != 2 or not isinstance(e[1], str):
            continue
        if e[0] == h(src):
            out[k] = e[1]
        else:
            stale += 1
    return out, stale


def merge_ui(lang):
    """i18n/out/<lang>/ui.json ({key: text}, checked with i18n_check.py) -> i18n/<lang>.ui.json with source hashes."""
    en = ui_source()
    src = I18N / "out" / lang / "ui.json"
    tr = json.loads(src.read_text(encoding="utf-8"))
    old = load_ui(lang)
    n = 0
    for k, text in tr.items():
        s = ui_src_text(k, en)
        if s is None or not isinstance(text, str) or not text.strip():
            continue
        old[k] = [h(s), text]
        n += 1
    (I18N / f"{lang}.ui.json").write_text(json.dumps(old, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
    print(f"{lang}: merged {n} UI strings -> i18n/{lang}.ui.json")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    src = strings(spec)
    if cmd == "extract":
        I18N.mkdir(exist_ok=True)
        (I18N / "source.spec.json").write_text(json.dumps(src, ensure_ascii=False, indent=0), encoding="utf-8")
        print(f"{len(src)} strings, {sum(map(len, src.values()))} characters -> i18n/source.spec.json")
    elif cmd == "status":
        en = ui_source()
        for lang in LANGS:
            entries = load_lang(lang)
            ok = sum(1 for k, v in entries.items() if k in src and v[0] == h(src[k]))
            stale = sum(1 for k, v in entries.items() if k in src and v[0] != h(src[k]))
            print(f"{lang:8} spec translated {ok:5}  stale {stale:4}  missing {len(src) - ok - stale:5}  of {len(src)}")
            ui, ui_stale = ui_overlay(en, load_ui(lang))
            ui_ok = sum(1 for k in ui if k in en)
            print(f"{'':8} ui   translated {ui_ok:5}  stale {ui_stale:4}  missing {len(en) - ui_ok - ui_stale:5}  of {len(en)}")
    elif cmd == "merge-ui":
        for lang in sys.argv[2:] or LANGS:
            if (I18N / "out" / lang / "ui.json").exists():
                merge_ui(lang)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
