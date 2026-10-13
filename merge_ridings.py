"""Merge geo/research/candidates_*.json into spec_parts/80_ridings.json (V2).

Usage: python -I merge_ridings.py
Keeps `regions` as they are, rebuilds `ridings` for every research file present, and keeps the
detailed V1 Surrey-Fleetwood candidate entries (level-keyed bios, record notes) for SRF.
Prints a per-riding report of anything that needs a human look.
"""
import glob
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "spec_parts", "80_ridings.json")
RIDINGS = os.path.join(HERE, "geo", "ridings.json")
V1SRF = os.path.join(HERE, "geo", "srf_v1_candidates.json")  # Surrey-Fleetwood entries from V1
SCORED = {"ndp", "conservative", "green", "centrebc", "onebc"}
GROUP_REGION = {"surrey": "surrey", "vancouver_northshore": "metro", "burnaby_richmond_tricities": "metro",
                "fraser_valley": "fraser_valley", "island_coast": "island_coast", "interior": "interior", "north": "north"}
PARTY_ALIASES = {
    "bc ndp": "ndp", "new democratic party": "ndp", "bc new democratic party": "ndp",
    "conservative party of bc": "conservative", "bc conservative": "conservative", "conservative party": "conservative",
    "bc conservatives": "conservative", "green party": "green", "bc greens": "green", "bc green party": "green",
    "centre bc": "centrebc", "centrebc": "centrebc", "one bc": "onebc", "onebc": "onebc",
}
OTHER_LABELS = {"libertarian": "BC Libertarian", "christian_heritage": "Christian Heritage", "communist": "Communist",
                "independent": "Independent"}
SHARE_KEYS = {"bc_united": "united", "bcunited": "united", "united": "united", "liberal": "liberal",
              "bc_liberal": "liberal", "independent": "independent", "ind": "independent", "other": "other", "others": "other"}


EBC = os.path.join(HERE, "geo", "ebc", "candidates_min.json")
EBC_PARTY = {"BC NDP": "ndp", "Conservative Party": "conservative", "BC Green Party": "green", "CentreBC": "centrebc",
             "OneBC": "onebc"}
EBC_OTHER = {"Independent": "Independent", "Other": "Unaffiliated", "Libertarian": "BC Libertarian",
             "Communist Party of BC": "Communist Party of BC", "Christian Heritage Party of BC": "Christian Heritage Party of BC",
             "CWP": "CanWest Party", "Freedom Party of BC": "Freedom Party of BC",
             "Unaffiliated": "Unaffiliated"}


def name_key(name):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z ]+", "", s).split()


def same_person(a, b):
    ka, kb = name_key(a), name_key(b)
    return bool(ka and kb) and ka[-1] == kb[-1] and (ka[0][0] == kb[0][0] or ka[0] in kb or kb[0] in ka)


def slug(name):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def party_id(raw):
    p = (raw or "").strip()
    low = p.lower()
    if low in SCORED:
        return low, None
    if low in PARTY_ALIASES:
        return PARTY_ALIASES[low], None
    if low.startswith("other:"):
        return None, p.split(":", 1)[1].strip()
    if low in OTHER_LABELS:
        return None, OTHER_LABELS[low]
    return None, p or "Unknown"


def norm_shares(shares):
    out = {}
    for k, v in (shares or {}).items():
        try:
            v = float(v)
        except (TypeError, ValueError):
            continue
        kk = k.strip().lower().replace(" ", "_")
        kk = kk if kk in SCORED else SHARE_KEYS.get(kk, kk)
        out[kk] = out.get(kk, 0) + v
    out = {k: round(v, 3) for k, v in out.items()}
    if out and sum(out.values()) <= 1.5:  # some research files give fractions, not percentages
        out = {k: round(v * 100, 1) for k, v in out.items()}
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def main():
    base = json.load(open(OUT, encoding="utf-8"))
    canon = {r["code"]: r for r in json.load(open(RIDINGS, encoding="utf-8"))}
    v1srf = json.load(open(V1SRF, encoding="utf-8"))["candidates"]
    by_code = {r["code"]: r for r in base["ridings"]}
    ebc = {}
    for row in json.load(open(EBC, encoding="utf-8")):
        ebc.setdefault(row["ED Code"], []).append(row)
    problems = []
    files = sorted(glob.glob(os.path.join(HERE, "geo", "research", "candidates_*.json")))
    seen_files = []
    for path in files:
        try:
            data = json.load(open(path, encoding="utf-8"))
        except Exception as e:  # research still being written
            problems.append(f"{os.path.basename(path)}: unreadable ({e})")
            continue
        seen_files.append(os.path.basename(path))
        for r in data.get("ridings", []):
            code = (r.get("code") or "").upper()
            if code not in canon:
                match = [c for c, x in canon.items() if x["name"].lower() == (r.get("name") or "").lower()]
                if not match:
                    problems.append(f"{os.path.basename(path)}: unknown riding {r.get('code')} {r.get('name')}")
                    continue
                code = match[0]
            cn = canon[code]
            entry = {"code": code, "name": cn["name"], "region": GROUP_REGION[cn["group"]],
                     "communities": (r.get("communities") or "").strip(), "result_2024": None,
                     "mla_change": r.get("mla_changes_since_2024") or None, "candidates": [], "others": [],
                     "list_status": r.get("candidate_list_status") or "unverified"}
            res = r.get("result_2024") or {}
            if res.get("winner"):
                shares = norm_shares(res.get("shares"))
                vals = sorted(shares.values(), reverse=True)
                wp, _ = party_id(res.get("party"))
                entry["result_2024"] = {
                    "winner": res["winner"], "party": wp or SHARE_KEYS.get(str(res.get("party")).lower(), str(res.get("party")).lower()),
                    "margin_votes": int(res.get("margin_votes") or 0),
                    "margin_pct": round(vals[0] - vals[1], 1) if len(vals) > 1 else None,
                    "shares": shares, "source": res.get("source")}
            else:
                problems.append(f"{code}: no 2024 result")
            ids = set()
            research = list(r.get("candidates", []))
            for row in ebc.get(code, []):
                name = row["Candidate Ballot Name"].strip()
                aff = row["Affiliation"].strip()
                pid = EBC_PARTY.get(aff)
                label = None if pid else EBC_OTHER.get(aff, aff)
                found = [c for c in research if same_person(c.get("name") or "", name)]
                c = found[0] if found else {}
                if not found:
                    problems.append(f"{code}: no research entry for {name} ({aff})")
                bio = (c.get("bio") or "").strip()
                if re.search(r"no (public |published )?(bio|biograph)|biography not found|no details? (found|available)", bio, re.I):
                    bio = ""  # the page says "No biography published"
                srcs = [x for x in (c.get("sources") or []) if isinstance(x, dict) and x.get("url")][:2]
                if not srcs:
                    srcs = [{"label": "Elections BC: 2026 candidate list", "url": "https://elections.bc.ca/2026-provincial-election/candidate-list/"}]
                if pid:
                    cid = slug(name)
                    while cid in ids:
                        cid += "_2"
                    ids.add(cid)
                    entry["candidates"].append({"id": cid, "name": name, "party_id": pid, "incumbent": bool(c.get("incumbent")),
                                                "bio": bio, "sources": srcs})
                else:
                    entry["others"].append({"name": name, "party_label": label, "incumbent": bool(c.get("incumbent")),
                                            "bio": bio, "sources": srcs})
                if chr(0x2014) in bio:
                    problems.append(f"{code}: em dash in bio of {name}")
            for c in research:
                if not any(same_person(c.get("name") or "", row["Candidate Ballot Name"]) for row in ebc.get(code, [])):
                    problems.append(f"{code}: research lists {c.get('name')} who is not on the Elections BC list")
            if ebc.get(code):
                entry["list_status"] = "official"
            if code == "SRF":  # keep the deeper V1 entries, add anything new
                v1c = {c["name"]: c for c in v1srf}
                entry["candidates"] = [v1c.get(c["name"], c) for c in entry["candidates"]]
            if not entry["candidates"]:
                problems.append(f"{code}: no scored candidates")
            missing = SCORED - {c["party_id"] for c in entry["candidates"]}
            if missing and entry["candidates"]:
                entry["missing_parties"] = sorted(missing)
            by_code[code] = entry
    for code, rows in ebc.items():  # ridings with no research file yet: ballot list only
        if by_code.get(code, {}).get("list_status") == "official":
            continue
        e = by_code[code]
        e["candidates"], e["others"], ids = [], [], set()
        for row in rows:
            name, aff = row["Candidate Ballot Name"].strip(), row["Affiliation"].strip()
            src = [{"label": "Elections BC: 2026 candidate list", "url": "https://elections.bc.ca/2026-provincial-election/candidate-list/"}]
            if aff in EBC_PARTY:
                cid = slug(name)
                while cid in ids:
                    cid += "_2"
                ids.add(cid)
                e["candidates"].append({"id": cid, "name": name, "party_id": EBC_PARTY[aff], "incumbent": False, "bio": "", "sources": src})
            else:
                e["others"].append({"name": name, "party_label": EBC_OTHER.get(aff, aff), "incumbent": False, "bio": "", "sources": src})
        e["list_status"] = "official_no_bios"
        e["missing_parties"] = sorted(SCORED - {c["party_id"] for c in e["candidates"]})
    base["ridings"] = [by_code[c] for c in sorted(by_code, key=lambda c: by_code[c]["name"])]
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(base, f, ensure_ascii=False, indent=1)
    filled = [r for r in base["ridings"] if r["candidates"]]
    print(f"files: {', '.join(seen_files) or 'none'}")
    print(f"ridings with candidates: {len(filled)}/93; scored candidates {sum(len(r['candidates']) for r in filled)}; others {sum(len(r['others']) for r in filled)}")
    from collections import Counter
    print("missing parties:", Counter(p for r in filled for p in r.get("missing_parties", [])))
    print("list status:", Counter(r["list_status"] for r in base["ridings"]))
    for p in problems:
        print("CHECK", p)


if __name__ == "__main__":
    main()
