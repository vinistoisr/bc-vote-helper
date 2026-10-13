"""Second-opinion review of translations by the Codex CLI, then apply its fixes.

    python -I i18n_review.py run <lang>[,<lang>...] [--jobs 6] [--chunks 00-37]
    python -I i18n_review.py apply <lang>[,<lang>...]
    python -I i18n_review.py report <lang>[,<lang>...]

run:    for each translated chunk i18n/out/<lang>/NN.json that passes i18n_check, asks Codex (read-only)
        to compare it with the English and return problems with a corrected translation, saved to
        i18n/review/<lang>/NN.json. Chunks already reviewed since their last change are skipped.
apply:  writes each high or medium fix into i18n/out/<lang>/NN.json when the fixed string still passes
        the checker; keeps a log in i18n/review/<lang>/applied.jsonl.
report: counts by severity.
"""
import concurrent.futures as cf
import json
import pathlib
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))  # python -I leaves the script folder off sys.path
import i18n_check  # noqa: E402

I18N = ROOT / "i18n"
NAMES = {
    "pa": "Punjabi (Gurmukhi), for BC's Punjabi community",
    "zh-Hans": "Simplified Chinese, for Mandarin readers",
    "zh-Hant": "Traditional Chinese with Hong Kong conventions, for Cantonese readers",
    "tl": "Filipino/Tagalog, for Filipino-Canadians",
    "fr": "Canadian French",
    "ru": "Russian, for Russian-speaking Canadians",
    "ko": "Korean, for Korean-Canadians",
    "fa": "Persian (Farsi), for Iranian-Canadians; Persian digits and Gregorian dates are intended",
}
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["fixes", "overall"],
    "properties": {
        "overall": {"type": "string"},
        "fixes": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["key", "severity", "problem", "fix"],
                "properties": {
                    "key": {"type": "string"},
                    "severity": {"type": "string", "enum": ["high", "medium", "low"]},
                    "problem": {"type": "string"},
                    "fix": {"type": "string"},
                },
            },
        },
    },
}
PROMPT = """You are a professional translation reviewer for a neutral BC (Canada) provincial election quiz.
Language under review: {name} (code {lang}).
Read these files (paths relative to the working folder):
- i18n/BRIEF.txt: the translation rules (follow them; names of people, ridings and places stay in Latin script on purpose).
- i18n/glossary.{lang}.json: the agreed terms. A translation that follows the glossary is correct even if you would choose differently.
- {review_file}: items, each with a key, the English (EN) and the translation (TR).
Keys ending /1 are the simplest reading level and /5 the most detailed.
If the file is the page text (keys without slashes), i18n/ui.notes.json says where each string appears and what each {{placeholder}} holds; every {{placeholder}} must stay exactly as in the English, and buttons and chips must stay short.

Report only real problems:
(1) meaning changed, added or dropped, including hedges ("says", "promises", "would", "rather than", "about");
(2) wrong numbers, dates, ages or amounts (also boundaries: "under 25" excludes 25);
(3) wording that makes a party, candidate or policy sound better or worse than the English does;
(4) wrong terms (job titles, institutions, legal terms) or language a native reader in BC would stumble on;
(5) a /1 or /2 item that is not simple;
(6) a person's gender stated when the English does not state it;
(7) an em dash (U+2014) or Chinese double dash.
Skip style preferences. For each problem give the complete corrected translation of that item in "fix" (the whole string, not a fragment), following the brief and glossary and keeping every number's value.
Severity: high = changes what a voter would understand about a party, candidate or fact; medium = noticeable error or clumsy enough to confuse; low = minor.
Do not modify any files."""


def src_path(n):
    """English source of a chunk: i18n/chunks/NN.en.json, or i18n/ui.en.json for the page text ("ui")."""
    return I18N / "ui.en.json" if n == "ui" else I18N / "chunks" / f"{n}.en.json"


def chunk_ids(spec):
    if spec == "ui":
        return ["ui"]
    if not spec:
        return [f"{i:02d}" for i in range(38)]
    a, b = spec.split("-")
    return [f"{i:02d}" for i in range(int(a), int(b) + 1)]


def review_one(lang, n):
    out_file = I18N / "out" / lang / f"{n}.json"
    rev_dir = I18N / "review" / lang
    rev_dir.mkdir(parents=True, exist_ok=True)
    res = rev_dir / f"{n}.json"
    if not out_file.exists():
        return f"{lang} {n}: no translation yet"
    if res.exists() and res.stat().st_mtime > out_file.stat().st_mtime:
        return f"{lang} {n}: already reviewed"
    src = json.loads(src_path(n).read_text(encoding="utf-8"))
    tr = json.loads(out_file.read_text(encoding="utf-8"))
    errs, _ = i18n_check.check_pair(lang, src, tr, n)
    if errs:
        return f"{lang} {n}: fails checker ({len(errs)} errors), not reviewed"
    inp = rev_dir / f"{n}.in.txt"
    inp.write_text("\n".join(f"### {k}\nEN: {src[k]}\nTR: {tr[k]}\n" for k in src), encoding="utf-8")
    schema = rev_dir / "schema.json"
    schema.write_text(json.dumps(SCHEMA), encoding="utf-8")
    prompt = PROMPT.format(name=NAMES[lang], lang=lang, review_file=inp.relative_to(ROOT).as_posix())
    tmp = rev_dir / f"{n}.last.json"
    t0 = time.time()
    # The prompt goes in on stdin: a multi-line argument does not survive Windows command-line quoting.
    r = subprocess.run(
        [shutil.which("codex") or "codex", "exec", "-s", "read-only", "--skip-git-repo-check", "-C", str(ROOT),
         "--output-schema", str(schema), "-o", str(tmp), "-"],
        input=prompt, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800,
    )
    try:
        data = json.loads(tmp.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return f"{lang} {n}: codex failed (exit {r.returncode}): {e}; {r.stderr[-300:]}"
    res.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    sev = [f["severity"] for f in data["fixes"]]
    return f"{lang} {n}: {len(src)} items, high {sev.count('high')}, medium {sev.count('medium')}, low {sev.count('low')} ({time.time() - t0:.0f}s)"


def apply(lang):
    rev_dir = I18N / "review" / lang
    log = rev_dir / "applied.jsonl"
    done = applied = rejected = 0
    for res in sorted(list(rev_dir.glob("[0-9][0-9].json")) + list(rev_dir.glob("ui.json"))):
        n = res.stem
        out_file = I18N / "out" / lang / f"{n}.json"
        src = json.loads(src_path(n).read_text(encoding="utf-8"))
        tr = json.loads(out_file.read_text(encoding="utf-8"))
        data = json.loads(res.read_text(encoding="utf-8"))
        changed = False
        for f in data["fixes"]:
            if f["severity"] == "low" or f["key"] not in src or not f["fix"].strip() or f.get("applied"):
                continue
            done += 1
            errs, _ = i18n_check.check_pair(lang, {f["key"]: src[f["key"]]}, {f["key"]: f["fix"]}, n)
            entry = {"chunk": n, "key": f["key"], "severity": f["severity"], "problem": f["problem"], "old": tr[f["key"]], "new": f["fix"]}
            if errs:
                rejected += 1
                entry["rejected"] = errs
            else:
                tr[f["key"]] = f["fix"]
                applied += 1
                changed = True
                f["applied"] = True
            with log.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        if changed:
            out_file.write_text(json.dumps(tr, ensure_ascii=False, indent=1), encoding="utf-8")
            res.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            # keep the review newer than the file it reviewed, so `run` does not redo it
            t = time.time() + 1
            import os
            os.utime(res, (t, t))
    print(f"{lang}: {applied} fixes applied, {rejected} rejected by the checker (of {done})")


def report(lang):
    c = {"high": 0, "medium": 0, "low": 0}
    n = items = 0
    rev = I18N / "review" / lang
    for res in sorted(list(rev.glob("[0-9][0-9].json")) + list(rev.glob("ui.json"))):
        n += 1
        items += len(json.loads(src_path(res.stem).read_text(encoding="utf-8")))
        for f in json.loads(res.read_text(encoding="utf-8"))["fixes"]:
            c[f["severity"]] += 1
    print(f"{lang}: {n} chunks, {items} items reviewed; high {c['high']}, medium {c['medium']}, low {c['low']}")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cmd, langs = sys.argv[1], sys.argv[2].split(",")
    args = sys.argv[3:]
    jobs = int(args[args.index("--jobs") + 1]) if "--jobs" in args else 6
    chunks = chunk_ids(args[args.index("--chunks") + 1] if "--chunks" in args else "")
    if cmd == "run":
        with cf.ThreadPoolExecutor(jobs) as ex:
            futs = [ex.submit(review_one, lang, n) for lang in langs for n in chunks]
            for f in cf.as_completed(futs):
                print(f.result(), flush=True)
    elif cmd == "apply":
        for lang in langs:
            apply(lang)
    elif cmd == "report":
        for lang in langs:
            report(lang)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
