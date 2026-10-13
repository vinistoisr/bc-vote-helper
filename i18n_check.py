"""Check translated chunks before they are merged.

    python -I i18n_check.py <lang> NN       one chunk (i18n/out/<lang>/NN.json against i18n/chunks/NN.en.json)
    python -I i18n_check.py <lang> all      every chunk present for that language
    python -I i18n_check.py <lang> ui       the UI strings (i18n/out/<lang>/ui.json against i18n/ui.en.json)

Errors: bad JSON, missing or extra keys, non-string values, em dashes or Chinese double dashes, digit
groups that differ from the English, placeholders like {name} that differ, wrong script for the language.
Warnings: values left identical to a long English string.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
I18N = ROOT / "i18n"
SCRIPT = {  # characters that must make up most of the letters
    "pa": re.compile(r"[਀-੿]"),
    "zh-Hans": re.compile(r"[一-鿿]"),
    "zh-Hant": re.compile(r"[一-鿿]"),
    "ru": re.compile(r"[Ѐ-ӿ]"),
    "tl": re.compile(r"[A-Za-z]"),
    "fr": re.compile(r"[A-Za-zÀ-ÿ]"),
    "ko": re.compile(r"[가-힯ᄀ-ᇿ㄰-㆏]"),
    "fa": re.compile(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]"),
}
# A few characters that only one Chinese script uses, to catch the wrong one.
# Common function words, to catch French in a Tagalog file and the reverse (both use Latin script).
WORDS = {
    "tl": {"ang", "ng", "mga", "sa", "na", "ay", "at", "para", "hindi", "ito", "niya", "nila", "kung", "may", "si", "ni", "kay", "nang", "rin", "din", "lang", "pa", "o", "mas", "wala"},
    "fr": {"le", "la", "les", "des", "et", "est", "du", "un", "une", "pour", "dans", "qui", "que", "sur", "au", "aux", "de", "en", "l", "d", "qu", "ne", "pas", "plus", "ou", "par", "avec", "son", "sa", "ses", "aucun", "aucune"},
}
SIMP_ONLY = set("们这国说对时会为发经过还进后应该学让认实现关间点头问题条么与产业东车")
TRAD_ONLY = set("們這國說對時會為發經過還進後應該學讓認實現關間點頭問題條麼與產業東車")


PERSIAN = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩٬٫", "01234567890123456789,.")


def fold(s, lang):
    """Persian digits to ASCII, thousands separators out, decimal mark as '.'.
    English, Chinese, Korean, Punjabi, Tagalog: ',' groups thousands and '.' is the decimal point.
    French and Russian: spaces group thousands and ',' is the decimal mark."""
    s = s.translate(PERSIAN)
    if lang in ("fr", "ru"):
        s = re.sub(r"(?<!\d)\d{1,3}(?:[ \u00A0\u202F]\d{3})+(?!\d)", lambda m: re.sub(r"\D", "", m.group(0)), s)
        s = re.sub(r"(?<=\d),(?=\d)", ".", s)
    else:
        s = re.sub(r"(?<=\d)[,'\u066C](?=\d{3}(?!\d))", "", s)
    # Chinese and Korean month numbers (English spells months out)
    return re.sub(r"(?<![\d.])(1[0-2]|[1-9])(?=\s?(月|월))", "", s)


def digits(s, lang="en"):
    """Sorted digit groups after fold(), so 1,050 / 1 050 / ۱٬۰۵۰ all read 1050."""
    return sorted(re.findall(r"\d+(?:\.\d+)?", fold(s, lang)))


# Words after a number that scale it. Lets 13.3億 / 133억 match "1.33 billion", 50萬 match "500,000".
MULT = [
    (r"B\b|bn\b", 1e9, "$"),  # only right after a dollar amount: "$3B", not "Phase 3B"
    (r"M\b", 1e6, "$"),
    (r"G\$", 1e9, 0),
    (r"M\$", 1e6, 0),
    (r"billions?|milliards?|млрд\.?|миллиард\w*|bilyon|میلیارد|ਬਿਲੀਅਨ|十億|十亿|십억", 1e9, re.I),
    (r"천만|千萬|千万", 1e7, 0),
    (r"millions?|млн\.?|миллион\w*|milyon|میلیون|ਮਿਲੀਅਨ|百萬|百万|백만", 1e6, re.I),
    (r"億|亿|억", 1e8, 0),
    (r"ਕਰੋੜ", 1e7, 0),
    (r"ਲੱਖ", 1e5, 0),
    (r"萬|万|만", 1e4, 0),
    (r"thousand|тыс\.?|тысяч\w*|هزار|libo|千|천|ਹਜ਼ਾਰ", 1e3, re.I),
]


def values(s, lang="en"):
    """Numbers as values with scale words applied."""
    s = fold(s, lang)
    out = []
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s?(?:\$\s?)?", s):
        v = float(m.group(1))
        rest = re.sub(r"^[-\s\u00A0]+", "", s[m.end():m.end() + 16])
        dollar = m.start() > 0 and s[m.start() - 1] == "$"
        for pat, f, flags in MULT:
            if flags == "$":
                if not dollar:
                    continue
                flags = 0
            if re.match(r"(?:" + pat + r")", rest, flags):
                v *= f
                break
        out.append(round(v, 4))
    return sorted(out)


def pm_variant(en):
    """English 8 p.m. -> 20, for languages that write the 24-hour clock."""
    return re.sub(r"(?<![\d:])(\d{1,2})(?=(?::\d\d)?\s?p\.m\.)", lambda m: str(int(m.group(1)) % 12 + 12), en)


def numbers_match(en, t, lang="en"):
    variants = (en, pm_variant(en))
    if any(digits(t, lang) == digits(e) for e in variants):
        return True
    return values(t, lang) in [values(e) for e in variants]


def check_pair(lang, src, out, label):
    errs, warns = [], []
    if not isinstance(out, dict):
        return [f"{label}: not a JSON object"], []
    for k in src:
        if k not in out:
            errs.append(f"{label}: missing key {k}")
    for k in out:
        if k not in src:
            base = re.sub(r"_(zero|two|few|many)$", "", k)
            if base != k and base + "_other" in src:
                continue  # extra plural forms (Russian few/many) are allowed
            errs.append(f"{label}: extra key {k}")
    for k, en in src.items():
        t = out.get(k)
        if k not in out:
            continue
        if not isinstance(t, str) or not t.strip():
            errs.append(f"{k}: empty or not a string")
            continue
        if "—" in t or "——" in t:
            errs.append(f"{k}: em dash")
        if sorted(re.findall(r"\{[a-z_0-9]+\}", t)) != sorted(re.findall(r"\{[a-z_0-9]+\}", en)):
            errs.append(f"{k}: placeholders differ from English {re.findall(r'{[a-z_0-9]+}', en)}")
        if not numbers_match(en, t, lang):
            errs.append(f"{k}: numbers differ: English {digits(en)} vs {digits(t, lang)}")
        letters = re.findall(r"[^\W\d_]", t)
        own = len(SCRIPT[lang].findall(t))
        if lang in ("pa", "zh-Hans", "zh-Hant", "ru", "ko", "fa") and not k.endswith("/communities") and len(en) > 60 and letters and own / len(letters) < 0.15:
            errs.append(f"{k}: mostly not in the target script")
        words = set(re.findall(r"[a-zà-ÿ]+", t.lower()))
        if lang in WORDS and len(t) > 80 and not k.endswith("/communities") and len(words & WORDS[lang]) < (1 if len(t) < 200 else 2):
            errs.append(f"{k}: does not read as {lang} (few common {lang} words)")
        if lang == "zh-Hans" and len(set(t) & TRAD_ONLY) >= 2:
            errs.append(f"{k}: Traditional characters in Simplified text: {''.join(sorted(set(t) & TRAD_ONLY))}")
        if lang == "zh-Hant" and len(set(t) & SIMP_ONLY) >= 2:
            errs.append(f"{k}: Simplified characters in Traditional text: {''.join(sorted(set(t) & SIMP_ONLY))}")
        if t.strip() == en.strip() and len(en) > 30 and " " in en:
            warns.append(f"{k}: identical to English")
    return errs, warns


def load(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return e


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    lang, which = sys.argv[1], sys.argv[2]
    if lang not in SCRIPT:
        sys.exit(f"unknown language {lang}")
    if which == "ui":
        pairs = [("ui", I18N / "ui.en.json", I18N / "out" / lang / "ui.json")]
    elif which == "all":
        pairs = [(p.stem, I18N / "chunks" / f"{p.stem}.en.json", p) for p in sorted((I18N / "out" / lang).glob("[0-9][0-9].json"))]
    else:
        n = f"{int(which):02d}"
        pairs = [(n, I18N / "chunks" / f"{n}.en.json", I18N / "out" / lang / f"{n}.json")]
    total_e = 0
    for label, sp, op in pairs:
        if not op.exists():
            print(f"{label}: {op} not found")
            total_e += 1
            continue
        src, out = load(sp), load(op)
        if isinstance(out, Exception):
            print(f"{label}: invalid JSON: {out}")
            total_e += 1
            continue
        if label == "ui" and isinstance(out, dict):
            # Extra plural forms (Russian key_few / key_many etc.) are allowed beside an English key_other
            for k in out:
                m = re.match(r"^(.+)_(zero|two|few|many)$", k)
                if m and k not in src and m.group(1) + "_other" in src:
                    src[k] = src[m.group(1) + "_other"]
        errs, warns = check_pair(lang, src, out, label)
        for e in errs:
            print("ERROR", e)
        for w in warns:
            print("warn ", w)
        total_e += len(errs)
        print(f"{label}: {len(out)} keys, {len(errs)} errors, {len(warns)} warnings")
    sys.exit(1 if total_e else 0)


if __name__ == "__main__":
    main()
