"""Quantitative audit of quiz_spec.json scoring.

Run: python -I audit_scoring.py [path/to/quiz_spec.json]
Pure standard library. Deterministic (seeded RNG).

no_position rule: when party_positions[P].no_position is true, P has no
published position on that question. The stored scores for P are placeholders
(2) and the question leaves P's numerator and denominator (per-party
denominators). Ideal voters of P skip such questions. Random voters answer
them; the exclusion applies when their alignment with P is computed.
"""
import itertools
import json
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "quiz_spec.json")
PARTIES = ["ndp", "conservative", "green", "centrebc", "onebc"]
LEVELS = ["1", "2", "3", "4", "5"]
W = {"low": 0.5, "medium": 1.0, "high": 2.0}
N_RANDOM = 20000
SEED = 20261024
SHORT = {"ndp": "NDP", "conservative": "CON", "green": "GRN", "centrebc": "CBC", "onebc": "ONE"}


def hdr(t):
    print()
    print("=" * 78)
    print(t)
    print("=" * 78)


with open(SPEC, encoding="utf-8") as f:
    raw = f.read()
spec = json.loads(raw)
Q = spec["questions"]
NOPOS = [[bool(q["party_positions"].get(p, {}).get("no_position")) for p in PARTIES] for q in Q]

# ----------------------------------------------------------------------------
# 1. Schema completeness
# ----------------------------------------------------------------------------
hdr("1. SCHEMA COMPLETENESS")
problems = []
spec_parties = [p["id"] for p in spec.get("parties", [])]
if sorted(spec_parties) != sorted(PARTIES):
    problems.append(f"parties list {spec_parties} != expected {PARTIES}")
for qi, q in enumerate(Q):
    qid = q.get("id", "?")
    for fld in ("prompt", "context"):
        t = q.get(fld) or {}
        miss = [l for l in LEVELS if not str(t.get(l, "")).strip()]
        if miss:
            problems.append(f"{qid}: {fld} missing levels {miss}")
    opts = q.get("options") or []
    if len(opts) < 2:
        problems.append(f"{qid}: fewer than 2 options")
    ids = [o.get("id") for o in opts]
    if len(set(ids)) != len(ids):
        problems.append(f"{qid}: duplicate option ids {ids}")
    for o in opts:
        miss = [l for l in LEVELS if not str((o.get("text") or {}).get(l, "")).strip()]
        if miss:
            problems.append(f"{qid}/{o.get('id')}: option text missing levels {miss}")
        sc = o.get("scores") or {}
        for p in PARTIES:
            v = sc.get(p)
            if not (isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 4):
                problems.append(f"{qid}/{o.get('id')}: score[{p}]={v!r} not int 0-4")
        extra = set(sc) - set(PARTIES)
        if extra:
            problems.append(f"{qid}/{o.get('id')}: unexpected score keys {extra}")
    pp = q.get("party_positions") or {}
    for p in PARTIES:
        e = pp.get(p)
        if not e or not (e.get("text") or {}):
            problems.append(f"{qid}: party_positions[{p}] missing")
            continue
        if not e.get("sources"):
            problems.append(f"{qid}: party_positions[{p}] has no sources")
    # every scored party must have an option it fully endorses; a no_position
    # party carries placeholder 2s and is excluded from its own alignment
    for pi, p in enumerate(PARTIES):
        vals = [o["scores"][p] for o in opts]
        if NOPOS[qi][pi]:
            if any(v != 2 for v in vals):
                problems.append(f"{qid}: {p} is no_position but scores are {vals}, expected placeholders of 2")
        elif max(vals) < 4:
            problems.append(f"{qid}: {p} has no option scoring 4 (max {max(vals)}); structural ceiling")
    if q.get("scope") not in ("provincial", "local"):
        problems.append(f"{qid}: scope {q.get('scope')!r} not provincial/local")
loc = spec.get("local") or {}
if not str(loc.get("formula", "")).strip():
    problems.append("local.formula missing")
if "no_position" not in str(loc.get("formula", "")) and "no_position" not in json.dumps(spec["meta"].get("method_summary", {})):
    problems.append("no_position rule not described in meta.method_summary or local.formula")
cand_parties = [c.get("party_id") for c in loc.get("candidates", [])]
if sorted(cand_parties) != sorted(PARTIES):
    problems.append(f"local candidates party_ids {cand_parties} do not cover each party once")
em = raw.count("—") + raw.lower().count("\\u2014")
en = raw.count("–") + raw.lower().count("\\u2013")
if em:
    problems.append(f"{em} em dash characters (U+2014) in file")
pp_levels = sorted({l for q in Q for p in PARTIES for l in q["party_positions"][p]["text"]})
np_count = sum(sum(r) for r in NOPOS)
print(f"Questions: {len(Q)}  ({sum(q['scope']=='local' for q in Q)} local)")
print(f"Options per question: {[len(q['options']) for q in Q]}")
print(f"party_positions text levels present: {pp_levels} (1/3/5 by design; UI maps 2->1, 4->5)")
print(f"no_position cells: {np_count} -> " + ", ".join(f"{Q[qi]['id']}/{SHORT[PARTIES[pi]]}" for qi in range(len(Q)) for pi in range(len(PARTIES)) if NOPOS[qi][pi]))
print(f"Em dashes (U+2014): {em}   En dashes (U+2013, info only): {en}")
print(f"local.formula present: {bool(str(loc.get('formula','')).strip())}")
if problems:
    print(f"FAIL: {len(problems)} problem(s)")
    for p in problems:
        print("  -", p)
else:
    print("PASS: no schema problems found")

# ----------------------------------------------------------------------------
# Scoring helpers (mirror meta.method_summary level 5 and local.formula)
# ----------------------------------------------------------------------------
S = [[[o["scores"][p] for p in PARTIES] for o in q["options"]] for q in Q]  # S[q][opt][party]
NQ, NP = len(Q), len(PARTIES)
LOCALM = [2.0 if q["scope"] == "local" else 1.0 for q in Q]


def align(choices, weights, mult=None):
    """choices[q] = option index or None (skip); weights[q] = importance weight.
    Per-party denominators: a no_position cell leaves both sums for that party."""
    num = [0.0] * NP
    den = [0.0] * NP
    for qi, oi in enumerate(choices):
        if oi is None:
            continue
        w = weights[qi] * (mult[qi] if mult else 1.0)
        for pi in range(NP):
            if NOPOS[qi][pi]:
                continue
            den[pi] += w * 4
            num[pi] += w * S[qi][oi][pi]
    return [100 * num[i] / den[i] if den[i] else 0.0 for i in range(NP)]


def rank(scores):
    return sorted(range(NP), key=lambda i: -scores[i])


def fmt(scores):
    return "  ".join(f"{SHORT[PARTIES[i]]} {scores[i]:5.1f}" for i in range(NP))


def scored_parties(qi):
    return [pi for pi in range(NP) if not NOPOS[qi][pi]]


def ideal_choice(qi, pi):
    """Option index the party's ideal voter picks, or None when the party has no position."""
    if NOPOS[qi][pi]:
        return None
    opts = S[qi]
    best = max(o[pi] for o in opts)
    cands = [k for k, o in enumerate(opts) if o[pi] == best]
    others = [j for j in scored_parties(qi) if j != pi]
    # tie-break: lowest total for other scored parties, then lowest max for them
    return min(cands, key=lambda k: (sum(opts[k][j] for j in others), max((opts[k][j] for j in others), default=0)))


def distinctiveness(qi, pi):
    k = ideal_choice(qi, pi)
    if k is None:
        return (-99, -99)
    o = S[qi][k]
    others = [o[j] for j in scored_parties(qi) if j != pi]
    if not others:
        return (0, 0)
    return (o[pi] - statistics.mean(others), o[pi] - max(others))


# ----------------------------------------------------------------------------
# 2. Ideal-voter test
# ----------------------------------------------------------------------------
hdr("2. IDEAL-VOTER TEST (a party's ideal voter skips its no_position questions)")
ideal = {}
all_ok = True
for pi, p in enumerate(PARTIES):
    ch = [ideal_choice(qi, pi) for qi in range(NQ)]
    ideal[p] = ch
    for label, wts in (("medium on all", [1.0] * NQ),):
        sc = align(ch, wts)
        r = rank(sc)
        ok = r[0] == pi and sc[r[0]] > sc[r[1]]
        all_ok &= ok
        print(f"\n{p.upper()} ideal voter ({label}, answers {sum(c is not None for c in ch)} of {NQ}): {fmt(sc)}")
        print(f"  first: {PARTIES[r[0]]}  {'OK' if ok else 'FAIL'}   margin over 2nd ({PARTIES[r[1]]}): {sc[r[0]]-sc[r[1]]:.1f} pts")
    dist = sorted([qi for qi in range(NQ) if ch[qi] is not None], key=lambda qi: distinctiveness(qi, pi), reverse=True)[:3]
    wts = [2.0 if qi in dist else 1.0 for qi in range(NQ)]
    sc = align(ch, wts)
    r = rank(sc)
    ok = r[0] == pi and sc[r[0]] > sc[r[1]]
    all_ok &= ok
    print(f"  high on {[Q[qi]['id'] for qi in dist]}: {fmt(sc)}")
    print(f"  first: {PARTIES[r[0]]}  {'OK' if ok else 'FAIL'}   margin over 2nd ({PARTIES[r[1]]}): {sc[r[0]]-sc[r[1]]:.1f} pts")
    scored_q = [qi for qi in range(NQ) if not NOPOS[qi][pi]]
    ceil = sum(max(o[pi] for o in S[qi]) for qi in scored_q) / (4 * len(scored_q)) * 100
    print(f"  ceiling (best achievable for {p} over its {len(scored_q)} scored questions): {ceil:.1f}%")
    # local formula
    scl = align(ch, [1.0] * NQ, LOCALM)
    rl = rank(scl)
    ok_l = rl[0] == pi and scl[rl[0]] > scl[rl[1]]
    all_ok &= ok_l
    print(f"  local formula: {fmt(scl)}  first {PARTIES[rl[0]]} {'OK' if ok_l else 'FAIL'}")
print(f"\nIdeal-voter test overall: {'PASS' if all_ok else 'FAIL'}")

print("\nIdeal-voter option choices (option id per question; '-' = no position, skipped):")
print(f"  {'question':28s} " + " ".join(f"{SHORT[p]:>4s}" for p in PARTIES))
for qi, q in enumerate(Q):
    print(f"  {q['id']:28s} " + " ".join(f"{(q['options'][ideal[p][qi]]['id'] if ideal[p][qi] is not None else '-'):>4s}" for p in PARTIES))

# ----------------------------------------------------------------------------
# 3. Random-voter bias
# ----------------------------------------------------------------------------
hdr(f"3. RANDOM-VOTER BIAS ({N_RANDOM} voters, uniform option, uniform importance)")
rng = random.Random(SEED)


def simulate(skip_p=0.0, mult=None, n=N_RANDOM, first_bias=0.0, middle_bias=0.0):
    wins = [0.0] * NP
    tot = [0.0] * NP
    allsc = [[] for _ in range(NP)]
    for _ in range(n):
        ch, wt = [], []
        for qi in range(NQ):
            k = len(S[qi])
            if rng.random() < skip_p:
                ch.append(None)
            elif first_bias and rng.random() < first_bias:
                ch.append(0)
            elif middle_bias and rng.random() < middle_bias:
                ch.append(k // 2)
            else:
                ch.append(rng.randrange(k))
            wt.append(rng.choice((0.5, 1.0, 2.0)))
        if all(c is None for c in ch):
            continue
        sc = align(ch, wt, mult)
        m = max(sc)
        top = [i for i in range(NP) if sc[i] == m]
        for i in top:
            wins[i] += 1 / len(top)
        for i in range(NP):
            tot[i] += sc[i]
            allsc[i].append(sc[i])
    return [t / n for t in tot], [100 * w / n for w in wins], allsc


def report_sim(title, mean, win):
    print(f"\n{title}")
    print(f"  {'party':14s} {'mean align %':>13s} {'wins first %':>13s}  flag")
    for i, p in enumerate(PARTIES):
        flag = "HIGH (>35%)" if win[i] > 35 else ("LOW (<8%)" if win[i] < 8 else "")
        print(f"  {p:14s} {mean[i]:13.1f} {win[i]:13.1f}  {flag}")


mean, win, allsc = simulate()
report_sim("Provincial scoring, no skips:", mean, win)
mean_s, win_s, _ = simulate(skip_p=0.3)
report_sim("Provincial scoring, 30% of questions skipped at random:", mean_s, win_s)
mean_l, win_l, _ = simulate(mult=LOCALM)
report_sim("Local formula (local questions x2), no skips:", mean_l, win_l)
mean_f, win_f, _ = simulate(first_bias=0.4)
report_sim("Stored-order primacy (40% pick the first stored option; the UI shuffles, so this is the unshuffled worst case):", mean_f, win_f)
mean_m, win_m, _ = simulate(middle_bias=0.4)
report_sim("Middle-option bias (40% pick the middle stored option):", mean_m, win_m)

print("\nPer-question expected score under random answering (mean of option scores, 0-4; 'np' = no position, excluded):")
print(f"  {'question':28s} " + " ".join(f"{SHORT[p]:>5s}" for p in PARTIES) + "   row mean  top-minus-bottom")
colsum = [0.0] * NP
colcnt = [0] * NP
dev = [[0.0] * NP for _ in range(NQ)]
for qi, q in enumerate(Q):
    m = [None if NOPOS[qi][pi] else statistics.mean(o[pi] for o in S[qi]) for pi in range(NP)]
    vals = [v for v in m if v is not None]
    rm = statistics.mean(vals)
    for i in range(NP):
        if m[i] is not None:
            colsum[i] += m[i]
            colcnt[i] += 1
            dev[qi][i] = m[i] - rm
    print(f"  {q['id']:28s} " + " ".join(("   np" if v is None else f"{v:5.2f}") for v in m) + f"   {rm:5.2f}     {max(vals)-min(vals):4.2f}")
print(f"  {'MEAN over scored q':28s} " + " ".join(f"{colsum[i]/colcnt[i]:5.2f}" for i in range(NP)))
print(f"  {'as % of max':28s} " + " ".join(f"{100*colsum[i]/(4*colcnt[i]):5.1f}" for i in range(NP)))

print("\nPer-question contribution to skew (party mean minus row mean over scored parties, summed = total skew):")
for pi, p in enumerate(PARTIES):
    tot = sum(dev[qi][pi] for qi in range(NQ))
    top = sorted(range(NQ), key=lambda qi: -abs(dev[qi][pi]))[:4]
    print(f"  {p:13s} total {tot:+5.2f}  largest: " + ", ".join(f"{Q[qi]['id']} {dev[qi][pi]:+.2f}" for qi in top))

print("\nScore-mass per party over scored cells (count of 0s / 4s, total points across all options):")
for pi, p in enumerate(PARTIES):
    vals = [o[pi] for qi, qo in enumerate(S) if not NOPOS[qi][pi] for o in qo]
    print(f"  {p:13s} zeros {vals.count(0):3d}  ones {vals.count(1):3d}  twos {vals.count(2):3d}  threes {vals.count(3):3d}  fours {vals.count(4):3d}  sum {sum(vals):3d}  mean {statistics.mean(vals):.2f}  (n={len(vals)})")

print("\nOptions where a party gets a middling 2-3 while another party is at 4 (hedge scores), scored cells only:")
hedges = {p: 0 for p in PARTIES}
for qi, qo in enumerate(S):
    for o in qo:
        if max(o) == 4:
            for pi in range(NP):
                if not NOPOS[qi][pi] and o[pi] in (2, 3):
                    hedges[PARTIES[pi]] += 1
print("  " + "  ".join(f"{p}: {v}" for p, v in hedges.items()))

# ----------------------------------------------------------------------------
# 4. Discrimination per question
# ----------------------------------------------------------------------------
hdr("4. DISCRIMINATION PER QUESTION (scored parties only)")


def pairdist(qi, a, b):
    return statistics.mean(abs(o[a] - o[b]) for o in S[qi])


print(f"  {'question':28s} {'mean range':>10s} {'mean SD':>8s} {'pair dist':>9s} {'min pair (party pair: dist)':>32s}")
weak = []
for qi, q in enumerate(Q):
    sp = scored_parties(qi)
    rngs = [max(o[j] for j in sp) - min(o[j] for j in sp) for o in S[qi]]
    sds = [statistics.pstdev([o[j] for j in sp]) for o in S[qi]]
    pds = {(a, b): pairdist(qi, a, b) for a, b in itertools.combinations(sp, 2)}
    mp = min(pds, key=pds.get)
    mpd = statistics.mean(pds.values())
    flag = ""
    if mpd < 1.5:
        flag = "  WEAK overall"
    near = [f"{SHORT[PARTIES[a]]}-{SHORT[PARTIES[b]]}" for (a, b), v in pds.items() if v <= 0.5]
    if near:
        flag += f"  near-identical: {', '.join(near)}"
        weak.append((q["id"], near))
    print(f"  {q['id']:28s} {statistics.mean(rngs):10.2f} {statistics.mean(sds):8.2f} {mpd:9.2f} {SHORT[PARTIES[mp[0]]]+'-'+SHORT[PARTIES[mp[1]]]+': '+format(pds[mp], '.2f'):>32s}{flag}")
print("\n  pair dist = mean |s_A - s_B| over options, averaged over the scored party pairs.")
print("  Flag: near-identical = a pair differs by <= 0.5 points per option on average.")

# ----------------------------------------------------------------------------
# 5. Party-pair distinctness
# ----------------------------------------------------------------------------
hdr("5. PARTY-PAIR DISTINCTNESS")
print(f"  {'pair':10s} {'A ideal: A-B':>13s} {'B ideal: B-A':>13s} {'mean |dA-dB|':>13s} {'corr':>6s}  separating questions (max option gap)")


def corr(x, y):
    mx, my = statistics.mean(x), statistics.mean(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    den = (sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y)) ** 0.5
    return num / den if den else 0.0


hard = []
for a, b in itertools.combinations(range(NP), 2):
    sa = align(ideal[PARTIES[a]], [1.0] * NQ)
    sb = align(ideal[PARTIES[b]], [1.0] * NQ)
    ma, mb = sa[a] - sa[b], sb[b] - sb[a]
    both = [qi for qi in range(NQ) if not NOPOS[qi][a] and not NOPOS[qi][b]]
    xa = [o[a] for qi in both for o in S[qi]]
    xb = [o[b] for qi in both for o in S[qi]]
    md = statistics.mean(abs(x - y) for x, y in zip(xa, xb))
    c = corr(xa, xb)
    sep = sorted(both, key=lambda qi: -max(abs(o[a] - o[b]) for o in S[qi]))
    sep_s = ", ".join(f"{Q[qi]['id'].replace('q_','')}({max(abs(o[a]-o[b]) for o in S[qi])})" for qi in sep[:3])
    tag = f"{SHORT[PARTIES[a]]}-{SHORT[PARTIES[b]]}"
    flag = " HARD" if min(ma, mb) < 5 else (" close" if min(ma, mb) < 15 else "")
    if min(ma, mb) < 15:
        hard.append((tag, ma, mb))
    print(f"  {tag:10s} {ma:13.1f} {mb:13.1f} {md:13.2f} {c:6.2f}  {sep_s}{flag}")
print("\n  'A ideal: A-B' = points by which A's ideal voter rates A above B (medium importance).")
print("  HARD = under 5 points; close = under 15 points. Pair statistics use questions where both parties are scored.")

print("\n  50/50 split voters (half of questions answered as A's ideal, half as B's, 2,000 random splits each):")
rng_split = random.Random(SEED + 1)
for a, b in itertools.combinations(range(NP), 2):
    wa = wb = 0.0
    n = 2000
    for _ in range(n):
        ch = []
        for qi in range(NQ):
            pick = ideal[PARTIES[a]][qi] if rng_split.random() < 0.5 else ideal[PARTIES[b]][qi]
            if pick is None:
                pick = ideal[PARTIES[b]][qi] if ideal[PARTIES[b]][qi] is not None else ideal[PARTIES[a]][qi]
            ch.append(pick)
        sc = align(ch, [1.0] * NQ)
        if sc[a] > sc[b]:
            wa += 1
        elif sc[b] > sc[a]:
            wb += 1
        else:
            wa += 0.5
            wb += 0.5
    print(f"    {SHORT[PARTIES[a]]}-{SHORT[PARTIES[b]]}: {SHORT[PARTIES[a]]} {100*wa/n:5.1f}%  {SHORT[PARTIES[b]]} {100*wb/n:5.1f}%")

print("\n  Questions where a pair has identical score vectors (cannot separate them at all):")
anyid = False
for qi, q in enumerate(Q):
    for a, b in itertools.combinations(scored_parties(qi), 2):
        if all(o[a] == o[b] for o in S[qi]):
            print(f"    {q['id']}: {PARTIES[a]} = {PARTIES[b]}")
            anyid = True
if not anyid:
    print("    none")

# ----------------------------------------------------------------------------
# 6. Local formula
# ----------------------------------------------------------------------------
hdr("6. LOCAL FORMULA")
print("  formula:", loc.get("formula", "")[:300])
pidx = {p: i for i, p in enumerate(PARTIES)}
cands = loc.get("candidates", [])
for label, ch_name in [(f"{p} ideal voter, medium", p) for p in PARTIES]:
    ch = ideal[ch_name]
    loc_sc = align(ch, [1.0] * NQ, LOCALM)
    out = []
    for c in cands:
        out.append(f"{c['name']} ({SHORT[c['party_id']]}) {loc_sc[pidx[c['party_id']]]:.1f}")
    print(f"  {label:32s} " + " | ".join(out))
# Spot-check vs a hand calculation for one candidate on a mixed answer set
ch = [0] * NQ
wt = [1.0] * NQ
wt[0] = 2.0
ch_skip = list(ch)
ch_skip[1] = None
pi0 = pidx[cands[0]["party_id"]]
hand_num = sum(wt[qi] * LOCALM[qi] * S[qi][ch_skip[qi]][pi0] for qi in range(NQ) if ch_skip[qi] is not None and not NOPOS[qi][pi0])
hand_den = sum(wt[qi] * LOCALM[qi] * 4 for qi in range(NQ) if ch_skip[qi] is not None and not NOPOS[qi][pi0])
calc = align(ch_skip, wt, LOCALM)[pi0]
print(f"\n  Hand check (all option a, q1 high, q2 skipped) for {cands[0]['name']}: hand {100*hand_num/hand_den:.3f} vs function {calc:.3f}  {'OK' if abs(100*hand_num/hand_den-calc)<1e-9 else 'MISMATCH'}")
print(f"  Candidates: {len(cands)}; every candidate computes: {all(c['party_id'] in pidx for c in cands)}")
print(f"  Local multiplier shifts random-voter wins: " + ", ".join(f"{SHORT[p]} {win[i]:.1f}->{win_l[i]:.1f}" for i, p in enumerate(PARTIES)))

# ----------------------------------------------------------------------------
# 7. Sensitivity: low-confidence and inferred scores
# ----------------------------------------------------------------------------
hdr("7. SENSITIVITY: LOW-CONFIDENCE AND INFERRED SCORES")
LOWC = [[(q["party_positions"][p].get("confidence") == "low") and not NOPOS[qi][pi] for pi, p in enumerate(PARTIES)] for qi, q in enumerate(Q)]
INF = [[q["party_positions"][p].get("basis") == "inferred" for p in PARTIES] for q in Q]
print("  Low-confidence scored cells per party: " + ", ".join(f"{SHORT[p]} {sum(LOWC[qi][pi] for qi in range(NQ))}" for pi, p in enumerate(PARTIES)))
print("  Inferred cells: " + (", ".join(f"{Q[qi]['id']}/{SHORT[PARTIES[pi]]}" for qi in range(NQ) for pi in range(NP) if INF[qi][pi]) or "none"))
for pi, p in enumerate(PARTIES):
    lows = [qi for qi in range(NQ) if LOWC[qi][pi]]
    exc = sum(dev[qi][pi] for qi in lows)
    print(f"  {p:13s} skew from low-confidence questions {exc:+5.2f} of total {sum(dev[qi][pi] for qi in range(NQ)):+5.2f}  ({', '.join(Q[qi]['id'] for qi in lows) or 'none'})")


def align_nolow(choices, weights):
    """Variant: low-confidence cells are also excluded for that party."""
    out = []
    for pi in range(NP):
        num = den = 0.0
        for qi, oi in enumerate(choices):
            if oi is None or LOWC[qi][pi] or NOPOS[qi][pi]:
                continue
            num += weights[qi] * S[qi][oi][pi]
            den += weights[qi] * 4
        out.append(100 * num / den if den else 0.0)
    return out


rng2 = random.Random(SEED)
wins2 = [0.0] * NP
tot2 = [0.0] * NP
for _ in range(N_RANDOM):
    ch = [rng2.randrange(len(S[qi])) for qi in range(NQ)]
    wt = [rng2.choice((0.5, 1.0, 2.0)) for _ in range(NQ)]
    sc = align_nolow(ch, wt)
    m = max(sc)
    top = [i for i in range(NP) if sc[i] == m]
    for i in top:
        wins2[i] += 1 / len(top)
    for i in range(NP):
        tot2[i] += sc[i]
report_sim("Variant: low-confidence cells also treated as 'no stated position' (excluded per party):",
           [t / N_RANDOM for t in tot2], [100 * w / N_RANDOM for w in wins2])
print("  Ideal voters under this variant:")
for pi, p in enumerate(PARTIES):
    sc = align_nolow(ideal[p], [1.0] * NQ)
    r = rank(sc)
    print(f"    {p:13s} {fmt(sc)}  first {PARTIES[r[0]]} {'OK' if r[0]==pi else 'FAIL'} margin {sc[r[0]]-sc[r[1]]:.1f}")

# ----------------------------------------------------------------------------
# 8. How decisive are random-voter results?
# ----------------------------------------------------------------------------
hdr("8. RANDOM-VOTER MARGIN BETWEEN 1ST AND 2ND")
gaps = []
for k in range(len(allsc[0])):
    v = sorted((allsc[i][k] for i in range(NP)), reverse=True)
    gaps.append(v[0] - v[1])
gaps.sort()
for t in (2, 3, 5):
    print(f"  share of random voters with 1st-2nd gap under {t} pts: {100*sum(g < t for g in gaps)/len(gaps):.1f}%")
print(f"  median gap: {gaps[len(gaps)//2]:.1f} pts")

print()
print("OVERALL:", "PASS" if (not problems and all_ok) else "FAIL")
