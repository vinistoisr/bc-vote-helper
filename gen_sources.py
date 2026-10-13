"""Write the "All sources" section of README.md from quiz_spec.json.

Usage: python -I gen_sources.py
Replaces everything between <!-- SOURCES:START --> and <!-- SOURCES:END --> in README.md.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
START, END = "<!-- SOURCES:START -->", "<!-- SOURCES:END -->"
PARTY_ORDER = ["ndp", "conservative", "green", "centrebc", "onebc"]


def lvl(v):
    """Level-keyed text -> the level 3 version (or the closest one)."""
    if isinstance(v, dict):
        for k in ("3", "4", "2", "5", "1"):
            if v.get(k):
                return v[k]
        return next(iter(v.values()), "")
    return v or ""


def esc(t):
    return re.sub(r"([\[\]|<>*_`])", r"\\\1", str(t)).strip()


def link(src):
    if isinstance(src, str):
        return f"- <{src}>"
    url = src.get("url", "")
    label = src.get("label") or url
    return f"- [{esc(label)}]({url})" if url else f"- {esc(label)}"


def uniq(srcs):
    seen, out = set(), []
    for s in srcs or []:
        key = s if isinstance(s, str) else s.get("url") or s.get("label")
        if key and key not in seen:
            seen.add(key)
            out.append(s)
    return out


def details(summary, body_lines):
    return ["<details>", f"<summary>{summary}</summary>", "", *body_lines, "", "</details>", ""]


def main():
    spec = json.load(open(os.path.join(HERE, "quiz_spec.json"), encoding="utf-8"))
    parties = {p["id"]: p for p in spec["parties"]}
    out, total = [], set()

    def count(srcs):
        for s in srcs or []:
            u = s if isinstance(s, str) else s.get("url")
            if u:
                total.add(u)

    # 1. Questions and party positions
    regions = {r["id"]: r for r in spec.get("regions", [])}
    q_region = {}
    for r in regions.values():
        for qid in r.get("local_qids", []):
            q_region.setdefault(qid, []).append(r["name"])
    out.append("### Party positions, question by question")
    out.append("")
    out.append("For each question: the sources behind each party's position. The written reason for every score is in `scoring_rationale` in `quiz_spec.json`.")
    out.append("")
    for q in spec["questions"]:
        where = "Province-wide" if q["scope"] == "provincial" else "Regional: " + ", ".join(q_region.get(q["id"], ["Surrey"]))
        body = []
        for pid in PARTY_ORDER:
            pp = q["party_positions"].get(pid, {})
            name = parties[pid]["short_name"]
            srcs = uniq(pp.get("sources"))
            count(srcs)
            tag = "no published position" if pp.get("no_position") else f"basis: {pp.get('basis', '?')}, confidence: {pp.get('confidence', '?')}"
            body.append(f"**{esc(name)}** ({tag})")
            body.append("")
            body.extend([link(s) for s in srcs] or ["- No source: no published position"])
            body.append("")
        out.extend(details(f"<b>{esc(lvl(q['prompt']))}</b> ({where}, <code>{q['id']}</code>)", body))

    # 2. Parties
    body = []
    for pid in PARTY_ORDER:
        srcs = uniq(parties[pid].get("sources"))
        count(srcs)
        body.append(f"**{esc(parties[pid]['name'])}**")
        body.append("")
        body.extend(link(s) for s in srcs)
        body.append("")
    out.append("### Parties: leaders, records and summaries")
    out.append("")
    out.extend(details("Sources for each party's summary and 2016 to 2026 record", body))

    # 3. General bibliography
    srcs = uniq(spec.get("sources"))
    count(srcs)
    out.append("### Background, polling, election facts and context")
    out.append("")
    out.extend(details(f"{len(srcs)} general sources", [link(s) for s in srcs]))

    # 4. Ridings and candidates
    out.append("### Ridings: 2024 results and candidates")
    out.append("")
    out.append("Candidate lists come from Elections BC's official 2026 candidate list. Bios and 2024 results link to their sources.")
    out.append("")
    by_region = {}
    for r in spec.get("ridings", []):
        by_region.setdefault(r["region"], []).append(r)
    for rid, rows in by_region.items():
        body = []
        for r in rows:
            body.append(f"**{esc(r['name'])}** (`{r['code']}`)")
            body.append("")
            res = r.get("result_2024") or {}
            if res.get("source"):
                count([res["source"]])
                body.append(f"- 2024 result: <{res['source']}>")
            for c in r.get("candidates", []) + r.get("others", []):
                party = parties[c["party_id"]]["short_name"] if c.get("party_id") in parties else c.get("party_label", "")
                srcs = uniq(c.get("sources"))
                count(srcs)
                links = ", ".join(f"[{esc(s.get('label') or 'source')}]({s['url']})" for s in srcs if isinstance(s, dict) and s.get("url"))
                body.append(f"- {esc(c['name'])} ({esc(party)}): {links or 'no source'}")
            body.append("")
        name = regions.get(rid, {}).get("name", rid)
        out.extend(details(f"{esc(name)} ({len(rows)} ridings)", body))

    # 5. Surrey context, how to vote
    local = spec.get("local") or {}
    srcs = uniq(((local.get("context") or {}).get("sources")) or [])
    srcs += uniq([{"label": l.get("label"), "url": l.get("url")} for l in (spec.get("how_to_vote") or {}).get("links", [])])
    count(srcs)
    out.append("### Surrey local context and how to vote")
    out.append("")
    out.extend(details("Local context and Elections BC voting information", [link(s) for s in srcs]))

    # 6. Geography and data files
    geo = [
        "- Riding boundaries (2023 redistribution, used for the 2024 and 2026 elections) and postal code lookup: [Open North, Represent API](https://represent.opennorth.ca/api/), boundary set `british-columbia-electoral-districts-2023-redistribution`. Boundaries originate from Elections BC.",
        "- Official candidate list: [Elections BC, 2026 provincial election candidate list](https://elections.bc.ca/2026-provincial-election/candidate-list/), copied into `geo/ebc/candidates_min.json` on October 12, 2026.",
    ]
    geo += [
        "- Postal code points for the backup lookup: [GeoNames postal code data for Canada](https://download.geonames.org/export/zip/), CC BY 4.0, credit [GeoNames](https://www.geonames.org/). 122,424 BC postal codes, fetched October 12, 2026.",
        "- Fonts: Archivo and Atkinson Hyperlegible (Next and Mono) from [Google Fonts](https://fonts.google.com/), SIL Open Font License, served from this site. PDF export: [jsPDF](https://github.com/parallax/jsPDF) 2.5.1, MIT.",
        "- How the lookup data is built: [`geo/SOURCES.txt`](geo/SOURCES.txt) and `build_geo.py`.",
    ]
    out.append("### Geography and data files")
    out.append("")
    out.extend(geo)
    out.append("")

    # 7. Research notes in this repository
    notes = []
    for folder in ("research", os.path.join("geo", "research")):
        root = os.path.join(HERE, folder)
        if os.path.isdir(root):
            for dp, _, files in os.walk(root):
                for f in sorted(files):
                    if f.endswith((".md", ".json")):
                        rel = os.path.relpath(os.path.join(dp, f), HERE).replace(os.sep, "/")
                        notes.append(f"- [`{rel}`]({rel.replace(' ', '%20')})")
    out.append("### Research notes in this repository")
    out.append("")
    out.append("The working notes the positions and candidate bios were written from, with their own inline citations.")
    out.append("")
    out.extend(details(f"{len(notes)} files", notes))

    out.insert(0, f"**{len(total)} unique links.**")
    out.insert(1, "")
    readme = os.path.join(HERE, "README.md")
    text = open(readme, encoding="utf-8").read()
    a, b = text.index(START) + len(START), text.index(END)
    text = text[:a] + "\n" + "\n".join(out) + "\n" + text[b:]
    if chr(0x2014) in text:
        raise SystemExit("em dash in README")
    open(readme, "w", encoding="utf-8", newline="\n").write(text)
    print(f"README sources: {len(total)} unique links, {len(text) // 1024} KB")


if __name__ == "__main__":
    main()
