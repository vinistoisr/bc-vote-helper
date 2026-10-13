"""Merge spec_parts/*.json into quiz_spec.json and validate the scoring model.

Usage: python -I build_spec.py
Writes quiz_spec.json (UTF-8) and prints validation results plus the
"ideal voter" answer set for each party (used in design_notes.md).

Scoring rules implemented here (mirror meta.method_summary and local.formula):
- score 0-4 per option per party; importance weights low 0.5, medium 1, high 2;
- skipped questions leave numerator and denominator;
- party_positions[P].no_position == true means P has no published position on
  that question: the stored scores are placeholders (2) and the question leaves
  P's numerator and denominator, so denominators differ by party.
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = os.path.join(HERE, "spec_parts")
OUT = os.path.join(HERE, "quiz_spec.json")
PARTIES = ["ndp", "conservative", "green", "centrebc", "onebc"]
LEVELS = ["1", "2", "3", "4", "5"]
WEIGHTS = {"low": 0.5, "medium": 1.0, "high": 2.0}

# Party, leader and campaign-plan names must not appear inside option text
# (they would tell the user which option belongs to whom).
NAME_RE = re.compile(
    r"\b(NDP|New Democrat\w*|Conservatives?|Green Party|Greens|BC Greens?|CentreBC|OneBC|"
    r"Eby|Doerkson|Lowan|Sturko|Brodie|Rustad|Findlay|Milobar|Armstrong|Botterell|"
    r"Fair Share Act|Safe Streets|Energy Superpower|Rustad Rebate|Built in BC)\b")
# Reviewer caveats belong in party_positions or context, not in the option a user endorses.
CAVEAT_RE = re.compile(
    r"\b(uncosted|unaddressed|unpublished|unquantified|unspecified|unverified|"
    r"platform due|platform pending|pending October|no position on|no stated|mechanism unspecified)\b",
    re.IGNORECASE)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def merge():
    spec = load(os.path.join(PARTS, "00_meta.json"))
    questions = []
    for path in sorted(glob.glob(os.path.join(PARTS, "[0-9][0-9]_q_*.json"))):
        questions.extend(load(path))
    spec["questions"] = questions
    tail = load(os.path.join(PARTS, "90_local_vote_sources.json"))
    spec.update(tail)
    spec.update(load(os.path.join(PARTS, "80_ridings.json")))  # V2: regions + all 93 ridings
    rq = os.path.join(PARTS, "82_region_qids.json")  # V2: {region_id: [local question ids]}
    if os.path.exists(rq):
        mapping = load(rq)
        for reg in spec["regions"]:
            if reg["id"] in mapping:
                reg["local_qids"] = mapping[reg["id"]]
    extra = os.path.join(PARTS, "81_issues_v2.json")  # V2: issue labels for the regional local questions
    if os.path.exists(extra):
        spec["issues"] = spec["issues"] + load(extra)
    ordered = {}
    for key in ["meta", "levels", "parties", "other_parties_note", "issues",
                "questions", "regions", "ridings", "local", "how_to_vote", "sources"]:
        ordered[key] = spec[key]
    for key in spec:
        if key not in ordered:
            ordered[key] = spec[key]
    return ordered


def walk_strings(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_strings(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_strings(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj


def nopos(q, p):
    return bool(q["party_positions"].get(p, {}).get("no_position"))


def home_option(q, p):
    """The option on which party p scores highest (ties: first)."""
    return max(q["options"], key=lambda o: o["scores"][p])


def validate(spec):
    errors, warnings = [], []
    # banned characters
    for path, s in walk_strings(spec):
        if "—" in s:
            errors.append(f"em dash at {path}")
        if "–" in s:
            warnings.append(f"en dash at {path}")
    issue_ids = {i["id"] for i in spec["issues"]}
    for i in spec["issues"]:
        for lv in ["1", "3", "5"]:
            if lv not in i["label"]:
                errors.append(f"issue {i['id']} missing label level {lv}")
    qids = set()
    for q in spec["questions"]:
        qid = q["id"]
        if qid in qids:
            errors.append(f"duplicate question id {qid}")
        qids.add(qid)
        if q["issue_id"] not in issue_ids:
            errors.append(f"{qid}: unknown issue {q['issue_id']}")
        if q["scope"] not in ("provincial", "local"):
            errors.append(f"{qid}: bad scope")
        for field in ("prompt", "context"):
            for lv in LEVELS:
                if not q.get(field, {}).get(lv):
                    errors.append(f"{qid}: {field} missing level {lv}")
        if re.search(r"\d", q["prompt"].get("1", "")):
            warnings.append(f"{qid}: digits in level-1 prompt")
        opts = q["options"]
        if not 3 <= len(opts) <= 5:
            errors.append(f"{qid}: {len(opts)} options")
        seen = set()
        for o in opts:
            if o["id"] in seen:
                errors.append(f"{qid}: duplicate option {o['id']}")
            seen.add(o["id"])
            for lv in LEVELS:
                t = o.get("text", {}).get(lv)
                if not t:
                    errors.append(f"{qid}/{o['id']}: text missing level {lv}")
                    continue
                m = NAME_RE.search(t)
                if m:
                    errors.append(f"{qid}/{o['id']} L{lv}: party/leader/plan name in option text: {m.group(0)!r}")
                m = CAVEAT_RE.search(t)
                if m:
                    errors.append(f"{qid}/{o['id']} L{lv}: reviewer caveat in option text: {m.group(0)!r}")
            if re.search(r"\d", o["text"]["1"]):
                warnings.append(f"{qid}/{o['id']}: digits in level-1 option text")
            for p in PARTIES:
                v = o["scores"].get(p)
                if not isinstance(v, int) or not 0 <= v <= 4:
                    errors.append(f"{qid}/{o['id']}: bad score for {p}: {v}")
            if set(o["scores"]) != set(PARTIES):
                errors.append(f"{qid}/{o['id']}: score keys {sorted(o['scores'])}")
            scored = [p for p in PARTIES if not nopos(q, p)]
            if len({o["scores"][p] for p in scored}) == 1:
                warnings.append(f"{qid}/{o['id']}: identical scores for all scored parties")
        for p in PARTIES:
            pp = q["party_positions"].get(p)
            if not pp:
                errors.append(f"{qid}: no party_positions for {p}")
                continue
            for lv in ["1", "3", "5"]:
                if not pp.get("text", {}).get(lv):
                    errors.append(f"{qid}/{p}: position text missing level {lv}")
            if re.search(r"\d", pp.get("text", {}).get("1", "")):
                warnings.append(f"{qid}/{p}: digits in level-1 position text")
            if pp.get("basis") not in ("platform", "record", "both", "inferred"):
                errors.append(f"{qid}/{p}: bad basis")
            if pp.get("confidence") not in ("high", "medium", "low"):
                errors.append(f"{qid}/{p}: bad confidence")
            if not pp.get("sources"):
                errors.append(f"{qid}/{p}: no sources")
            best = max(o["scores"][p] for o in opts)
            if nopos(q, p):
                if any(o["scores"][p] != 2 for o in opts):
                    errors.append(f"{qid}/{p}: no_position cell must carry placeholder scores of 2")
                if pp.get("confidence") != "low":
                    errors.append(f"{qid}/{p}: no_position cell must be low confidence")
            elif best < 4:
                errors.append(f"{qid}: {p} has no option scoring 4 (max {best}); give it a home or mark no_position")
            if pp.get("basis") == "inferred" and pp.get("confidence") != "low":
                errors.append(f"{qid}/{p}: inferred cell must be low confidence")
        if not q.get("scoring_rationale"):
            errors.append(f"{qid}: no scoring_rationale")
        # every scored party should have exactly one home option (a 4)
        for p in PARTIES:
            if nopos(q, p):
                continue
            fours = [o["id"] for o in opts if o["scores"][p] == 4]
            if len(fours) > 1:
                warnings.append(f"{qid}: {p} scores 4 on several options {fours}")
        # discriminating power: does any single option top every scored party?
        tops = {}
        for p in PARTIES:
            if nopos(q, p):
                continue
            m = max(o["scores"][p] for o in opts)
            tops[p] = {o["id"] for o in opts if o["scores"][p] == m}
        common = set.intersection(*tops.values()) if tops else set()
        if common:
            warnings.append(f"{qid}: option(s) {sorted(common)} are a top choice for every party")
        # symmetry: P's score on Q's home option should be within 1 of Q's score on P's home option
        for i, p in enumerate(PARTIES):
            for qp in PARTIES[i + 1:]:
                if nopos(q, p) or nopos(q, qp):
                    continue
                hp, hq = home_option(q, p), home_option(q, qp)
                if hp is hq:
                    continue
                a = hq["scores"][p]   # p on q's home
                b = hp["scores"][qp]  # q on p's home
                if abs(a - b) > 1:
                    warnings.append(f"{qid}: asymmetric cross-score {p} on {qp}'s home ({hq['id']})={a} vs {qp} on {p}'s home ({hp['id']})={b}")
    for c in spec["local"]["candidates"]:
        if c["party_id"] not in PARTIES:
            errors.append(f"candidate {c['id']} party {c['party_id']}")
        for lv in ["1", "3", "5"]:
            if not c["bio"].get(lv):
                errors.append(f"candidate {c['id']} bio missing {lv}")
    return errors, warnings


def alignment(spec, answers, importance=None, local_mult=1.0):
    """answers: {qid: option_id}; importance: {qid: 'low'|'medium'|'high'}.
    Per-party denominators: a party's no_position questions leave both sums for that party."""
    num = {p: 0.0 for p in PARTIES}
    den = {p: 0.0 for p in PARTIES}
    for q in spec["questions"]:
        oid = answers.get(q["id"])
        if oid is None:
            continue
        w = WEIGHTS[(importance or {}).get(q["id"], "medium")]
        m = local_mult if q["scope"] == "local" else 1.0
        opt = next(o for o in q["options"] if o["id"] == oid)
        for p in PARTIES:
            if nopos(q, p):
                continue
            num[p] += w * m * opt["scores"][p]
            den[p] += w * m * 4
    return {p: (100.0 * num[p] / den[p] if den[p] else 0.0) for p in PARTIES}


def ideal_answers(spec, party):
    """For each question pick the option that maximizes party's score,
    breaking ties by largest margin over the best rival. A no_position
    question is skipped: the party's ideal voter has no cue there."""
    answers = {}
    for q in spec["questions"]:
        if nopos(q, party):
            continue

        def key(o):
            own = o["scores"][party]
            rival = max(o["scores"][p] for p in PARTIES if p != party and not nopos(q, p))
            return (own, own - rival)
        answers[q["id"]] = max(q["options"], key=key)["id"]
    return answers


def main():
    spec = merge()
    errors, warnings = validate(spec)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"wrote {OUT} ({os.path.getsize(OUT):,} bytes)")
    print(f"questions: {len(spec['questions'])} "
          f"(provincial {sum(q['scope']=='provincial' for q in spec['questions'])}, "
          f"local {sum(q['scope']=='local' for q in spec['questions'])}); "
          f"options: {sum(len(q['options']) for q in spec['questions'])}")
    print(f"issues: {len(spec['issues'])}; parties: {len(spec['parties'])}; "
          f"candidates: {len(spec['local']['candidates'])}")
    np_cells = [(q["id"], p) for q in spec["questions"] for p in PARTIES if nopos(q, p)]
    inf_cells = [(q["id"], p) for q in spec["questions"] for p in PARTIES
                 if q["party_positions"][p].get("basis") == "inferred"]
    print(f"no_position cells: {len(np_cells)} -> " + ", ".join(f"{q}/{p}" for q, p in np_cells))
    print(f"inferred cells: {len(inf_cells)} -> " + ", ".join(f"{q}/{p}" for q, p in inf_cells))
    print("\nERRORS:" if errors else "\nERRORS: none")
    for e in errors:
        print("  -", e)
    print("\nWARNINGS:" if warnings else "\nWARNINGS: none")
    for w in warnings:
        print("  -", w)

    print("\nIDEAL VOTER TEST (medium importance everywhere, provincial formula)")
    table = {}
    win_ok = True
    for p in PARTIES:
        ans = ideal_answers(spec, p)
        table[p] = ans
        res = alignment(spec, ans)
        ranked = sorted(res.items(), key=lambda kv: -kv[1])
        winner = ranked[0][0]
        ok = winner == p and ranked[0][1] > ranked[1][1]
        win_ok &= ok
        print(f"  {p:12s} -> " + ", ".join(f"{k} {v:5.1f}" for k, v in ranked)
              + ("   OK" if ok else "   FAIL"))
        res_local = alignment(spec, ans, local_mult=2.0)
        rl = sorted(res_local.items(), key=lambda kv: -kv[1])
        print(f"  {'':12s}    local formula: " + ", ".join(f"{k} {v:5.1f}" for k, v in rl))
    print("\nIDEAL ANSWER SET BY QUESTION ('-' = party has no position, question skipped)")
    qids = [q["id"] for q in spec["questions"]]
    print("  question".ljust(30) + "".join(p[:5].ljust(7) for p in PARTIES))
    for qid in qids:
        print(("  " + qid).ljust(30) + "".join(table[p].get(qid, "-").ljust(7) for p in PARTIES))

    print("\nSPREAD CHECK: each party's best score per question ('np' = no position)")
    for q in spec["questions"]:
        bests = ["np" if nopos(q, p) else str(max(o["scores"][p] for o in q["options"])) for p in PARTIES]
        print(f"  {q['id']:28s} best-by-party {bests}")

    if errors or not win_ok:
        print("\nVALIDATION FAILED")
        sys.exit(1)
    print("\nVALIDATION PASSED")


if __name__ == "__main__":
    main()
