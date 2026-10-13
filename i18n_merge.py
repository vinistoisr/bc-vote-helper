"""Merge checked translator output into the files the build reads.

    python -I i18n_merge.py <lang>|all

Reads i18n/out/<lang>/NN.json (spec chunks) and i18n/out/<lang>/ui.json (UI strings), skips any file that
fails i18n_check.py, and writes i18n/<lang>.spec.json and i18n/<lang>.ui.json as {key: [src_hash, text]}.
The hash is taken from the English in the chunk the translator worked from, so a translation of text that has
changed since stays stale (and shows English) until it is translated again. Existing entries for keys not in this run's files are kept.
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))  # python -I leaves the script folder off sys.path
from i18n_strings import I18N, LANGS, h  # noqa: E402


def ok(lang, which):
    r = subprocess.run([sys.executable, "-I", str(ROOT / "i18n_check.py"), lang, which], capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        print(f"  {lang} {which}: failed check, skipped\n" + "\n".join("    " + l for l in r.stdout.splitlines()[-5:]))
    return r.returncode == 0


def merge(lang):
    out = I18N / "out" / lang
    if not out.exists():
        print(f"{lang}: no output yet")
        return
    src = json.loads((I18N / "source.spec.json").read_text(encoding="utf-8"))
    dest = I18N / f"{lang}.spec.json"
    have = json.loads(dest.read_text(encoding="utf-8")) if dest.exists() else {}
    n = 0
    for f in sorted(out.glob("[0-9][0-9].json")):
        if not ok(lang, f.stem):
            continue
        # Fingerprint = the English the translator worked from (the chunk's own copy), not today's English:
        # a translation of text that has since changed must stay stale until it is translated again.
        chunk_en = json.loads((I18N / "chunks" / f"{f.stem}.en.json").read_text(encoding="utf-8"))
        for k, t in json.loads(f.read_text(encoding="utf-8")).items():
            if k in src and k in chunk_en:
                have[k] = [h(chunk_en[k]), t]
                n += 1
    dest.write_text(json.dumps(have, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
    msg = f"{lang}: spec {n} merged, {len(have)}/{len(src)} in file"
    ui_out, ui_en = out / "ui.json", I18N / "ui.en.json"
    if ui_out.exists() and ui_en.exists() and ok(lang, "ui"):
        en = json.loads(ui_en.read_text(encoding="utf-8"))
        tr = json.loads(ui_out.read_text(encoding="utf-8"))
        ui = {k: [h(en[k]), tr[k]] for k in en if k in tr}
        for k in tr:  # extra plural forms (few/many) hash against the English _other form
            base = k.rsplit("_", 1)[0]
            if k not in en and base + "_other" in en:
                ui[k] = [h(en[base + "_other"]), tr[k]]
        (I18N / f"{lang}.ui.json").write_text(json.dumps(ui, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
        msg += f"; ui {len(ui)}/{len(en)}"
    print(msg)


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else sys.exit(__doc__)
    for lang in (LANGS if arg == "all" else [arg]):
        merge(lang)
