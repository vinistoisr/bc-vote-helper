"""Word-limit and style check for the V2 regional local question files (16-20).

Usage: python -I check_local_lengths.py [16 17 ...]   (default: 16 to 20)
Reports every string over the V2 limits, em dashes, childish words at levels 1-2,
digits at level 1, and acronyms at levels 1-3.
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = os.path.join(HERE, "spec_parts")
LIMITS = {
    "prompt": {"1": 16, "2": 22, "3": 26, "4": 30, "5": 34},
    "context": {"1": 45, "2": 60, "3": 80, "4": 110, "5": 140},
    "option": {"1": 14, "2": 20, "3": 24, "4": 34, "5": 40},
    "position": {"1": 30, "3": 60, "5": 90},
}
BANNED = re.compile(r"\b(grown-ups|team|little kids|big kids)\b", re.I)
ACRONYM = re.compile(r"\b(ER|ERs|ALR|LNG|DRIPA|UNDRIP|RCMP|LTC|TOA|SSMUH|NCTL|MHA|FID|IMG|UBCM|JIBC|COFI|BCTS|CHC|HPOA)\b")


def check(text, kind, lvl, where):
    out = []
    n = len(text.split())
    lim = LIMITS[kind].get(lvl)
    if lim and n > lim:
        out.append(f"LONG {where}: {n} words (limit {lim})")
    if "—" in text:
        out.append(f"EM DASH {where}")
    if lvl in "12" and BANNED.search(text):
        out.append(f"CHILDISH {where}: {BANNED.search(text).group(0)}")
    if lvl == "1" and re.search(r"\d", text):
        out.append(f"DIGITS L1 {where}")
    if lvl in "123" and kind != "position":
        m = ACRONYM.search(text)
        if m:
            out.append(f"ACRONYM L{lvl} {where}: {m.group(0)}")
    return out


def main():
    prefixes = sys.argv[1:] or ["16", "17", "18", "19", "20"]
    problems = []
    for pre in prefixes:
        paths = glob.glob(os.path.join(PARTS, f"{pre}_q_*.json"))
        if not paths:
            print(f"missing {pre}")
            continue
        qs = json.load(open(paths[0], encoding="utf-8"))
        for q in qs:
            qid = q["id"]
            for field in ("prompt", "context"):
                for lvl, t in q[field].items():
                    problems += check(t, field, lvl, f"{qid}.{field}.{lvl}")
            for o in q["options"]:
                for lvl, t in o["text"].items():
                    problems += check(t, "option", lvl, f"{qid}/{o['id']}.{lvl}")
            for p, pp in q["party_positions"].items():
                for lvl, t in pp["text"].items():
                    problems += check(t, "position", lvl, f"{qid}/{p}.{lvl}")
    for p in problems:
        print(p)
    print("OK" if not problems else f"{len(problems)} problems")


if __name__ == "__main__":
    main()
