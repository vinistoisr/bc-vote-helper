"""Public results page: anonymous totals from the answers people chose to share, for release after polls close.

Usage:
  python -I build_results.py <dump.json> [--cutoff 2026-10-25T03:00:00Z] [--out deploy/results]

<dump.json> is the output of
  npx wrangler d1 execute bcvote --remote -c wrangler.live.toml --json --command
    "SELECT s.sid, s.created_at, s.count, s.region_code, s.data_as_of, s.riding, s.lang, p.idx, p.level, p.answers
     FROM people p JOIN submissions s ON s.sid = p.sid"

Writes <out>/results.json (totals only) and <out>/index.html. Nothing per person or per session leaves this script.
BC Election Act s.233.1(2): new results must not be published on final voting day before polls close (8 PM Pacific),
so the page goes live only after the cutoff. Copy <out>/index.html to site/public/results/ at release time.
"""
import argparse
import html
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SPEC = ROOT / "quiz_spec.json"
VERSIONS = ROOT / "research" / "spec_versions" / "options_by_version.json"

SITE_URL = "https://votebc.vinceroyer.ca/"
POLLS_CLOSE = "2026-10-25T03:00:00Z"  # 8 PM Pacific on October 24, 2026

WEIGHTS = {"low": 0.5, "medium": 1, "high": 2}
MIN_RIDING = 20   # ridings with fewer people are counted in the totals but not shown on their own
MIN_GROUP = 30    # same for regions and per-question breakdowns
MARGIN = timedelta(hours=1)  # a page loaded just before a release keeps the old questions for a while

# When each quiz version was live, by the data date the page stored with the answers (UTC).
# An answer counts for a question only if that question had the same options in every version the row could
# have been answered on and in the final version. Otherwise it is left out, as a skip would be.
LIVE = {
    "2026-10-12": [("2026-10-12_fd1b34f", None, None)],
    "2026-10-13": [
        ("2026-10-13_1b821e3", None, "2026-10-14T04:40:00Z"),
        ("2026-10-13_163bfd3", "2026-10-14T04:40:00Z", None),
    ],
    "2026-10-18": [
        ("2026-10-18_8673a2c", None, "2026-10-19T01:25:00Z"),
        ("final", "2026-10-19T01:25:00Z", None),
    ],
}


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def candidate_versions(row):
    """Quiz versions this row could have been answered on, or None when the row predates the tracked versions."""
    windows = LIVE.get(row.get("data_as_of"))
    if not windows:
        return None
    t = ts(row["created_at"])
    out = []
    for name, start, end in windows:
        if start and t < ts(start):
            continue
        if end and t >= ts(end) + MARGIN:
            continue
        out.append(name)
    return out or None


def score(spec_q, answers, riding_region, usable):
    """Same rule as the quiz and the admin page: sum(w*s) / sum(w*4), skips and no-position cells left out."""
    parties = [p["id"] for p in SPEC_DATA["parties"]]
    t = {p: [0.0, 0.0] for p in parties}
    for q in spec_q:
        if q["scope"] != "provincial" and QREG.get(q["id"]) != riding_region:
            continue
        if q["id"] not in usable:
            continue
        a = answers.get(q["id"])
        if not a or not a.get("c") or a["c"] == "skip":
            continue
        opt = OPT[q["id"]].get(a["c"])
        if not opt:
            continue
        w = WEIGHTS.get(a.get("w"), 1)
        for p in parties:
            if p in NOPOS[q["id"]]:
                continue
            t[p][0] += w * float(opt["scores"][p])
            t[p][1] += w * 4
    return {p: (100 * n / d if d else None) for p, (n, d) in t.items()}


def tops(m):
    best, ids = -1, []
    for p, v in m.items():
        if v is None:
            continue
        r = round(v)
        if r > best:
            best, ids = r, [p]
        elif r == best:
            ids.append(p)
    return ids


def share(counter, total):
    return {k: round(100 * v / total, 1) for k, v in counter.items()} if total else {}


def load_rows(path):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = raw[0]["results"] if isinstance(raw, list) else raw["results"]
    return rows


def main():
    global SPEC_DATA, QREG, OPT, NOPOS
    ap = argparse.ArgumentParser()
    ap.add_argument("dump")
    ap.add_argument("--cutoff", default=POLLS_CLOSE)
    ap.add_argument("--out", default=str(ROOT / "deploy" / "results"))
    ap.add_argument("--completions", help="JSON from SELECT * FROM completions (finished-quiz counter)")
    args = ap.parse_args()

    SPEC_DATA = json.loads(SPEC.read_text(encoding="utf-8"))
    hist = json.loads(VERSIONS.read_text(encoding="utf-8"))["versions"]
    final_opts = {q["id"]: [[o["id"], o["text"]] for o in q["options"]] for q in SPEC_DATA["questions"]}
    hist["final"] = final_opts
    questions = SPEC_DATA["questions"]
    parties = [p["id"] for p in SPEC_DATA["parties"]]
    regions = {r["id"]: r for r in SPEC_DATA["regions"]}
    ridings = {r["code"]: r for r in SPEC_DATA["ridings"]}
    QREG = {q: r["id"] for r in SPEC_DATA["regions"] for q in r.get("local_qids", [])}
    OPT = {q["id"]: {o["id"]: o for o in q["options"]} for q in questions}
    NOPOS = {q["id"]: {p for p, pp in q.get("party_positions", {}).items() if pp.get("no_position") is True} for q in questions}

    if Path(args.dump).name == "results.json":  # restyle only: rebuild the page from saved totals
        Path(args.out).mkdir(parents=True, exist_ok=True)
        write_page(json.loads(Path(args.dump).read_text(encoding="utf-8")), Path(args.out))
        return

    cutoff = ts(args.cutoff)
    rows = load_rows(args.dump)
    kept, dropped = [], Counter()
    for r in rows:
        if ts(r["created_at"]) >= cutoff:
            dropped["after polls closed"] += 1
            continue
        rid = r.get("riding") if r.get("riding") in ridings else None
        if not rid and r.get("region_code") != "BC":
            dropped["outside BC and no riding given"] += 1
            continue
        vers = candidate_versions(r)
        if not vers:
            dropped["answered on a quiz version before October 12"] += 1
            continue
        usable = {qid for qid in final_opts if all(hist[v].get(qid) == final_opts[qid] for v in vers)}
        answers = r["answers"] if isinstance(r["answers"], dict) else json.loads(r["answers"] or "{}")
        kept.append({
            "sid": r["sid"], "created_at": r["created_at"], "riding": rid,
            "region": ridings[rid]["region"] if rid else None, "lang": r.get("lang") or "en",
            "level": r.get("level"), "answers": answers or {}, "usable": usable,
        })

    n = len(kept)
    if not n:
        sys.exit("no rows to report")
    sessions = len({p["sid"] for p in kept})
    first = min(p["created_at"] for p in kept)
    last = max(p["created_at"] for p in kept)

    # Closest party for each person (ties split evenly), and average match
    best = Counter()
    best_by_region = defaultdict(Counter)
    best_by_riding = defaultdict(Counter)
    n_region, n_riding = Counter(), Counter()
    avg = defaultdict(list)
    close = 0
    for p in kept:
        m = score(questions, p["answers"], p["region"], p["usable"])
        ids = tops(m)
        if not ids:
            continue
        vals = sorted((round(v) for v in m.values() if v is not None), reverse=True)
        if len(vals) > 1 and vals[0] - vals[1] <= 3:
            close += 1
        for pid in ids:
            best[pid] += 1 / len(ids)
            if p["region"]:
                best_by_region[p["region"]][pid] += 1 / len(ids)
            if p["riding"]:
                best_by_riding[p["riding"]][pid] += 1 / len(ids)
        if p["region"]:
            n_region[p["region"]] += 1
        if p["riding"]:
            n_riding[p["riding"]] += 1
        for pid, v in m.items():
            if v is not None:
                avg[pid].append(v)
    scored = sum(best.values())

    # Answers per question, among people who were asked it on comparable options
    qout = []
    for q in questions:
        if q["scope"] == "provincial":
            pool = [p for p in kept if q["id"] in p["usable"]]
        else:
            pool = [p for p in kept if p["region"] == QREG.get(q["id"]) and q["id"] in p["usable"]]
        chosen = Counter()
        skipped = high = 0
        for p in pool:
            a = p["answers"].get(q["id"])
            if not a or not a.get("c") or a["c"] == "skip" or a["c"] not in OPT[q["id"]]:
                skipped += 1
                continue
            chosen[a["c"]] += 1
            if a.get("w") == "high":
                high += 1
        answered = sum(chosen.values())
        if len(pool) < MIN_GROUP:
            continue
        issue = next(i for i in SPEC_DATA["issues"] if i["id"] == q["issue_id"])
        qout.append({
            "id": q["id"], "scope": q["scope"], "region": QREG.get(q["id"]),
            "issue": issue["label"].get("3"),
            "prompt": q["prompt"].get("3"),
            "asked": len(pool), "answered": answered, "skipped": skipped,
            "high_pct": round(100 * high / answered, 1) if answered else 0,
            "options": [
                {
                    "id": o["id"], "text": o["text"].get("3"),
                    "pct": round(100 * chosen[o["id"]] / answered, 1) if answered else 0,
                    "n": chosen[o["id"]],
                    "match": [pid for pid in parties if pid not in NOPOS[q["id"]] and int(o["scores"][pid]) == 4],
                }
                for o in q["options"]
            ],
        })

    # Answers that go together: Cramer's V for every pair of province-wide questions, among people asked both
    prov_ids = [q["id"] for q in questions if q["scope"] == "provincial"]
    issue_of = {q["id"]: next(i["label"]["3"] for i in SPEC_DATA["issues"] if i["id"] == q["issue_id"]) for q in questions}

    def picked(p, qid):
        a = p["answers"].get(qid)
        c = a.get("c") if a else None
        return c if qid in p["usable"] and c in OPT[qid] else None

    pairs = []
    for i, q1 in enumerate(prov_ids):
        for q2 in prov_ids[i + 1:]:
            both = [(picked(p, q1), picked(p, q2)) for p in kept]
            both = [x for x in both if x[0] and x[1]]
            m = len(both)
            if m < 1000:
                continue
            c = Counter(both)
            r1, r2 = Counter(x[0] for x in both), Counter(x[1] for x in both)
            chi = sum((c[(a, b)] - r1[a] * r2[b] / m) ** 2 / (r1[a] * r2[b] / m) for a in r1 for b in r2)
            v = math.sqrt(chi / (m * (min(len(r1), len(r2)) - 1)))
            # the clearest link in the pair, read both ways: among people who picked a, share who also picked b
            lb = None
            for qa, qb, ra, rb, flip in ((q1, q2, r1, r2, False), (q2, q1, r2, r1, True)):
                for a in ra:
                    if ra[a] < 300:
                        continue
                    for b in rb:
                        k = c[(b, a) if flip else (a, b)]
                        gap = k / ra[a] - rb[b] / m
                        if lb is None or gap > lb[0]:
                            lb = (gap, qa, a, qb, b, round(100 * k / ra[a], 1), round(100 * rb[b] / m, 1), ra[a])
            pairs.append({"q1": q1, "q2": q2, "v": round(v, 3), "n": m, "link": {
                "if_q": lb[1], "if_opt": lb[2], "if_text": OPT[lb[1]][lb[2]]["text"]["3"], "if_n": lb[7],
                "then_q": lb[3], "then_opt": lb[4], "then_text": OPT[lb[3]][lb[4]]["text"]["3"],
                "then_pct": lb[5], "all_pct": lb[6]}})
    pairs.sort(key=lambda x: -x["v"])

    # How many parties each person's answers matched, among people with 10 or more province-wide answers
    mix = Counter()
    for p in kept:
        seen, k = set(), 0
        for qid in prov_ids:
            c = picked(p, qid)
            if not c:
                continue
            full = [pid for pid in parties if pid not in NOPOS[qid] and int(OPT[qid][c]["scores"][pid]) == 4]
            if full:
                seen.update(full)
                k += 1
        if k >= 10:
            mix[len(seen)] += 1

    # People per day (Pacific dates), and the plain counter of every finished quiz where it exists
    pdt = timezone(timedelta(hours=-7))
    daily = Counter(ts(p["created_at"]).astimezone(pdt).date().isoformat() for p in kept)
    comp_out = None
    if args.completions:
        comp = [c for c in load_rows(args.completions) if ts(c["created_at"]) < cutoff]
        if comp:
            start = min(ts(c["created_at"]) for c in comp)
            shared_since = len({p["sid"] for p in kept if ts(p["created_at"]) >= start})
            fin_daily = Counter()
            for c in comp:
                fin_daily[ts(c["created_at"]).astimezone(pdt).date().isoformat()] += c["count"] or 1
            src = Counter((c["source"] or "unknown") for c in comp)
            comp_out = {
                "since": start.isoformat(timespec="minutes"),
                "sessions": len(comp), "people": sum(c["count"] or 1 for c in comp),
                "shared_sessions": shared_since,
                "daily": dict(sorted(fin_daily.items())),
                "sources": {k: round(100 * v / len(comp), 1) for k, v in src.most_common()},
            }

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cutoff": args.cutoff,
        "first": ts(first).astimezone(timezone(timedelta(hours=-7))).date().isoformat(), "last": ts(last).astimezone(timezone(timedelta(hours=-7))).date().isoformat(),  # Pacific dates only
        "people": n, "sessions": sessions,
        "excluded": dict(dropped),
        "ridings_with_answers": len(n_riding),
        "no_riding": sum(1 for p in kept if not p["riding"]),
        "close_pct": round(100 * close / scored, 1) if scored else 0,
        "min_riding": MIN_RIDING, "min_group": MIN_GROUP,
        "parties": [{k: p[k] for k in ("id", "name", "short_name", "color")} for p in SPEC_DATA["parties"]],
        "best": share(best, scored),
        "avg": {pid: round(sum(v) / len(v), 1) for pid, v in avg.items()},
        "by_region": [
            {"id": rid, "name": regions[rid]["name"], "n": n_region[rid], "best": share(best_by_region[rid], sum(best_by_region[rid].values()))}
            for rid in regions if n_region[rid] >= MIN_GROUP
        ],
        "by_riding": [
            {"code": c, "name": ridings[c]["name"], "region": ridings[c]["region"], "n": n_riding[c],
             "best": share(best_by_riding[c], sum(best_by_riding[c].values()))}
            for c in sorted(ridings, key=lambda c: ridings[c]["name"]) if n_riding[c] >= MIN_RIDING
        ],
        "ridings_hidden": sum(1 for c in n_riding if n_riding[c] < MIN_RIDING),
        "levels": dict(sorted(Counter(p["level"] for p in kept).items())),
        "langs": dict(Counter(p["lang"] for p in kept).most_common()),
        "questions": qout,
        "pairs": pairs,
        "mix": {str(k): v for k, v in sorted(mix.items())},
        "daily": dict(sorted(daily.items())),
        "completions": comp_out,
    }
    od = Path(args.out)
    od.mkdir(parents=True, exist_ok=True)
    (od / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"{n} people in {sessions} sessions ({first} to {last}); excluded {dict(dropped)}")
    print("closest party:", {k: out["best"][k] for k in sorted(out["best"], key=lambda k: -out["best"][k])})
    print("average match:", out["avg"], "| close results:", out["close_pct"], "%")
    print(f"ridings shown {len(out['by_riding'])}, hidden (n<{MIN_RIDING}) {out['ridings_hidden']}, no riding {out['no_riding']}")
    write_page(out, od)


# ---------- page ----------

e = html.escape
MAP_COLOR = {"ndp": "#F28A1E"}  # same as the admin map: NDP orange stays apart from CentreBC red
EDS = ROOT / "site" / "public" / "geo" / "eds.json"
BASEMAP = ROOT / "site" / "public" / "geo" / "basemap.json"

# Map panels: whole province, then the two areas where most ridings are too small to see (lon/lat boxes)
PANELS = [
    ("bc", "British Columbia", None, 2.0),
    ("lm", "Metro Vancouver, Surrey and the Fraser Valley", (-123.32, 48.99, -121.72, 49.42), 0.12),
    ("vi", "Greater Victoria and the south Island", (-124.25, 48.30, -123.20, 49.05), 0.10),
]


def albers(lon, lat):
    """Same projection as the admin map (BC Albers, km)."""
    rad = math.pi / 180
    p1, p2, p0, l0, R = 50 * rad, 58.5 * rad, 45 * rad, -126 * rad, 6371
    n = (math.sin(p1) + math.sin(p2)) / 2
    C = math.cos(p1) ** 2 + 2 * n * math.sin(p1)
    r0 = math.sqrt(C - 2 * n * math.sin(p0)) / n
    r = math.sqrt(C - 2 * n * math.sin(lat * rad)) / n
    t = n * (lon * rad - l0)
    return R * r * math.sin(t), -R * (r0 - r * math.cos(t))


def simplify(pts, tol):
    """Douglas-Peucker on projected points."""
    if len(pts) < 4:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (ax, ay), (bx, by) = pts[a], pts[b]
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy)
        far, fi = -1, -1
        for i in range(a + 1, b):
            px, py = pts[i]
            # closed rings start and end on the same point: measure from that point instead of a zero-length line
            d = abs(dy * (px - ax) - dx * (py - ay)) / L if L else math.hypot(px - ax, py - ay)
            if d > far:
                far, fi = d, i
        if far > tol:
            keep[fi] = True
            stack += [(a, fi), (fi, b)]
    return [p for p, k in zip(pts, keep) if k]


def ring_d(flat, tol, box):
    pts = [albers(flat[i], flat[i + 1]) for i in range(0, len(flat), 2)]
    if box:
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        if max(xs) < box[0] or min(xs) > box[2] or max(ys) < box[1] or min(ys) > box[3]:
            return ""
        pad = (box[2] - box[0]) * 0.03
        pts = clip_ring(pts, (box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad))
        if len(pts) < 3:
            return ""
        pts.append(pts[0])
    pts = simplify(pts, tol)
    if len(pts) < 3:
        return ""
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    if (max(xs) - min(xs)) < tol * 2 and (max(ys) - min(ys)) < tol * 2:
        return ""
    return "M" + "L".join(f"{x:.0f} {y:.0f}" if tol >= 1 else f"{x:.1f} {y:.1f}" for x, y in pts) + "Z"


def clip_ring(pts, box):
    """Sutherland-Hodgman clip of a ring to a rectangle, so insets carry only what they show."""
    x0, y0, x1, y1 = box
    edges = [(lambda p: p[0] >= x0, lambda a, b: (x0, a[1] + (b[1] - a[1]) * (x0 - a[0]) / (b[0] - a[0]))),
             (lambda p: p[0] <= x1, lambda a, b: (x1, a[1] + (b[1] - a[1]) * (x1 - a[0]) / (b[0] - a[0]))),
             (lambda p: p[1] >= y0, lambda a, b: (a[0] + (b[0] - a[0]) * (y0 - a[1]) / (b[1] - a[1]), y0)),
             (lambda p: p[1] <= y1, lambda a, b: (a[0] + (b[0] - a[0]) * (y1 - a[1]) / (b[1] - a[1]), y1))]
    out = pts[:-1] if len(pts) > 1 and pts[0] == pts[-1] else pts
    for inside, cross in edges:
        if not out:
            break
        src, out = out, []
        prev = src[-1]
        for cur in src:
            if inside(cur):
                if not inside(prev):
                    out.append(cross(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cross(prev, cur))
            prev = cur
    return out


def proj_box(ll):
    corners = [albers(ll[0], ll[1]), albers(ll[2], ll[1]), albers(ll[0], ll[3]), albers(ll[2], ll[3])]
    return (min(c[0] for c in corners), min(c[1] for c in corners), max(c[0] for c in corners), max(c[1] for c in corners))


def map_svgs(out):
    eds = json.loads(EDS.read_text(encoding="utf-8"))["r"]
    base = json.loads(BASEMAP.read_text(encoding="utf-8")) if BASEMAP.exists() else None
    pcol = {p["id"]: MAP_COLOR.get(p["id"], p["color"]) for p in out["parties"]}
    pname = {p["id"]: p["short_name"] for p in out["parties"]}
    by = {r["code"]: r for r in out["by_riding"]}
    svgs = []
    for key, label, ll, tol in PANELS:
        if ll:
            box = proj_box(ll)
        else:
            pts = [albers(x, y) for r in eds for poly in r["p"] for ring in poly for x, y in zip(ring[0::2], ring[1::2])]
            box = (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))
        pad = (box[2] - box[0]) * 0.02
        vb = (box[0] - pad, box[1] - pad, box[2] - box[0] + 2 * pad, box[3] - box[1] + 2 * pad)
        land = ""
        if base:
            land = "".join(ring_d(ring, tol, box) for poly in base["land"] for ring in poly)
        parts = []
        for r in eds:
            d = "".join(ring_d(ring, tol, box) for poly in r["p"] for ring in poly)
            if not d:
                continue
            row = by.get(r["c"])
            if row:
                top = max(row["best"], key=row["best"].get)
                fill = pcol[top]
                tip = f"{row['name']}: {row['n']} people. " + ", ".join(
                    f"{pname[k]} {v:.0f}%" for k, v in sorted(row["best"].items(), key=lambda kv: -kv[1]))
            else:
                fill = "var(--nodata)"
                name = next((x["name"] for x in SPEC_DATA["ridings"] if x["code"] == r["c"]), r["c"])
                tip = f"{name}: fewer than {out['min_riding']} people, not shown"
            parts.append(f'<path d="{d}" fill="{fill}"><title>{e(tip)}</title></path>')
        clip = f'<clipPath id="land-{key}"><path d="{land}"/></clipPath>' if land else ""
        g_attr = f' clip-path="url(#land-{key})"' if land else ""
        svgs.append(
            f'<figure class="map map-{key}"><svg viewBox="{vb[0]:.1f} {vb[1]:.1f} {vb[2]:.1f} {vb[3]:.1f}" role="img" '
            f'aria-label="{e(label)}: ridings shaded by the party most often closest to quiz answers">'
            f'<defs>{clip}</defs>'
            + (f'<path class="land" d="{land}"/>' if land else "")
            + f'<g class="eds"{g_attr} stroke-width="{max(tol * 0.6, 0.06):.2f}">{"".join(parts)}</g></svg>'
            f"<figcaption>{e(label)}</figcaption></figure>"
        )
    return svgs


def fmt_pct(v):
    return f"{v:.0f}%" if v >= 10 or v == 0 else f"{v:.1f}%"


def long_dt(iso):
    t = ts(iso).astimezone(timezone(timedelta(hours=-7)))  # Pacific Daylight Time through November 1, 2026
    h = t.hour % 12 or 12
    return f"{t.strftime('%B')} {t.day} at {h}:{t.minute:02d} {'AM' if t.hour < 12 else 'PM'} Pacific"


CSS_EXTRA = """
:root{--nodata:#D5DBDE;--track:#DFE5E7;--neutral:#8A979E}
@media (prefers-color-scheme:dark){:root{--nodata:#2A343A;--track:#222C31;--neutral:#5D6B72}}
::selection{background:var(--sea);color:var(--on-btn)}
a{text-underline-offset:.18em}
a:focus-visible,summary:focus-visible{outline:2px solid var(--sea);outline-offset:3px;border-radius:4px}
.wrap{max-width:1080px}
main.wrap p{max-width:68ch}
.num{font-variant-numeric:tabular-nums}
.dot{display:inline-block;width:.72em;height:.72em;border-radius:50%;margin:0 5px 0 0;vertical-align:-.04em}
h1.big{font-size:clamp(2.1rem,6vw,3.6rem);font-weight:880;font-stretch:88%;letter-spacing:-.02em;line-height:1.02;margin:22px 0 14px;max-width:16ch;text-wrap:balance}
.dek{font-size:1.12rem;color:var(--ink-2);margin:0 0 26px}
.dek a{color:var(--ink)}
.hero{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:clamp(16px,3vw,28px)}
.hero h2{margin:0 0 4px;font-size:clamp(1.15rem,2.4vw,1.45rem)}
.hero .sub{color:var(--ink-2);margin:0 0 18px;font-size:.98rem}
.stack{display:flex;height:clamp(52px,8vw,76px);border-radius:10px;overflow:hidden;gap:3px}
.stack span{display:flex;align-items:center;justify-content:center;font:850 clamp(.95rem,2.2vw,1.35rem)/1 Archivo,system-ui,sans-serif;font-stretch:90%;min-width:0;overflow:hidden}
@media (prefers-reduced-motion:no-preference){.hero .stack{animation:reveal 1.2s cubic-bezier(.16,1,.3,1) .1s both}
@keyframes reveal{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}}
.parties{display:grid;grid-template-columns:repeat(5,1fr);gap:14px 18px;margin:18px 0 0}
.parties div{min-width:0}
.parties b{display:block;font:850 clamp(1.7rem,4vw,2.6rem)/1 Archivo,system-ui,sans-serif;font-stretch:88%;letter-spacing:-.01em;margin:0 0 4px}
.parties span{font-size:.95rem;color:var(--ink-2)}
@media (max-width:640px){.parties{grid-template-columns:repeat(3,1fr)}}
@media (min-width:720px){.parties{display:flex;gap:3px}.parties div{padding-right:10px}}
.hero .foot{margin:20px 0 0;padding:14px 0 0;border-top:1px solid var(--line);font-size:.92rem;color:var(--ink-2);max-width:none}
section{margin:64px 0 0}
section>h2{font-size:clamp(1.45rem,3vw,2rem);font-weight:850;font-stretch:90%;letter-spacing:-.01em;margin:0 0 8px}
section>.intro{color:var(--ink-2);margin:0 0 22px}
.legend{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:.92rem;margin:0 0 14px}
.maps{display:grid;grid-template-columns:1.15fr 1fr;gap:14px;align-items:start}
.maps .side{display:grid;gap:14px}
@media (max-width:760px){.maps{grid-template-columns:1fr}}
.map{margin:0;background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:10px}
.map svg{display:block;width:100%;height:auto}
.map .land{fill:var(--nodata);opacity:.55}
.map .eds path{stroke:var(--surface);stroke-linejoin:round}
.map .eds path:hover{opacity:.78}
.map figcaption{font-size:.88rem;color:var(--ink-2);padding:6px 4px 0}
.regions{display:grid;gap:18px}
.region .lab{display:flex;justify-content:space-between;gap:12px;align-items:baseline;margin:0 0 6px}
.region .lab b{font-family:Archivo,system-ui,sans-serif;font-weight:800;font-stretch:92%}
.region .lab span{font-size:.88rem;color:var(--ink-2)}
.region .stack{height:34px;border-radius:7px;gap:2px}
.region .stack span{font-size:.82rem;font-weight:800}
.stack em{font-style:normal;background:var(--surface);color:var(--ink);padding:3px 7px;border-radius:999px;line-height:1;white-space:nowrap}
@media (max-width:520px){.stack em{padding:2px 4px;font-size:.74rem}}
.qs{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,470px),1fr));gap:18px}
.q{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:18px 18px 14px;display:flex;flex-direction:column}
.q h3{font-size:1.2rem;font-weight:820;margin:0 0 4px}
.q .prompt{color:var(--ink-2);font-size:.95rem;margin:0 0 16px}
.opt{margin:0 0 12px}
.opt .t{display:flex;justify-content:space-between;gap:14px;align-items:baseline;font-size:.93rem;line-height:1.35}
.opt .t b{font:850 1.05rem/1 Archivo,system-ui,sans-serif;font-variant-numeric:tabular-nums;white-space:nowrap}
.opt.top .t{font-size:1rem;font-weight:700}
.opt.top .t b{font-size:1.75rem}
.bar{height:10px;background:var(--track);border-radius:5px;margin:5px 0 3px;overflow:hidden}
.opt.top .bar{height:16px;border-radius:6px}
.bar i{display:block;height:100%;border-radius:inherit}
.who{font-size:.8rem;color:var(--ink-2)}
.q .meta{margin:auto 0 0;padding:10px 0 0;border-top:1px solid var(--line);font-size:.84rem;color:var(--ink-2);max-width:none}
details.local{background:var(--surface);border:1px solid var(--line);border-radius:14px;margin:0 0 12px}
details.local>summary{cursor:pointer;padding:14px 18px;font-family:Archivo,system-ui,sans-serif;font-weight:800;font-size:1.08rem}
details.local>summary span{font-family:'Atkinson Hyperlegible Next',system-ui,sans-serif;font-weight:400;font-size:.92rem;color:var(--ink-2);margin-left:6px}
details.local .qs{padding:0 14px 14px}
details.local .q{background:var(--bg)}
.levels{display:grid;gap:8px;max-width:680px}
.lv{display:grid;grid-template-columns:minmax(0,16rem) 1fr 4.5rem;gap:12px;align-items:center;font-size:.93rem}
.lv .bar{margin:0;height:14px}
.lv .bar i{background:var(--sea)}
.lv b{text-align:right;font-variant-numeric:tabular-nums}
@media (max-width:560px){.lv{grid-template-columns:1fr 4rem}.lv .bar{grid-column:1/-1;grid-row:2}}
table{border-collapse:collapse;width:100%;font-size:.93rem;background:var(--surface)}
th,td{border-bottom:1px solid var(--line);padding:7px 10px;text-align:left;vertical-align:top}
th{font-size:.85rem;color:var(--ink-2)}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:12px}
details.table{margin:14px 0 0}
details.table>summary{cursor:pointer;font-weight:700;padding:8px 0;color:var(--sea)}
.limits{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:20px 22px}
.limits ul{margin:0;padding-left:20px;max-width:68ch}.limits li{margin:0 0 8px}
#live{margin:28px 0 0}
#live .live-panel{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:clamp(16px,3vw,24px)}
#live h2{font-size:clamp(1.15rem,2.4vw,1.45rem);margin:0 0 4px}
#live .live-when{font-size:.88rem;color:var(--ink-2);margin:0 0 14px}
#live .live-when::before{content:"";display:inline-block;width:.6em;height:.6em;border-radius:50%;background:var(--sea);margin-right:7px;vertical-align:.05em}
#live .live-lede{font-size:1.08rem;font-weight:700;margin:0 0 6px}
#live .live-h{font-size:1rem;margin:22px 0 10px}
#live .stack{height:40px}
#live .parties b{font-size:clamp(1.3rem,3vw,1.8rem)}
#live .live-days{height:150px;justify-content:flex-start}
#live .live-days .day{max-width:72px}
#live .live-note{margin-top:12px}

.quotes{columns:3 280px;column-gap:18px}
.quote{break-inside:avoid;margin:0 0 18px;background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:18px 20px}
.quote blockquote{margin:0;font-size:1rem;line-height:1.5}
.quote blockquote::before{content:"“";display:block;font:900 2.6rem/.7 Archivo,system-ui,sans-serif;color:var(--sea);margin:6px 0 2px}
.quote.big blockquote{font:650 clamp(1.05rem,1.6vw,1.2rem)/1.45 Archivo,system-ui,sans-serif;font-stretch:98%}
.quote figcaption{margin:10px 0 0;font-size:.85rem;color:var(--ink-2)}
.quote figcaption a{color:var(--ink-2)}

.mix{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;align-items:end;height:220px;max-width:640px;margin:8px 0 0}
.mix div{display:flex;flex-direction:column;justify-content:flex-end;height:100%;text-align:center}
.mix i{display:block;background:var(--sea);border-radius:6px 6px 0 0;min-height:2px}
.mix b{font:850 1.25rem/1.1 Archivo,system-ui,sans-serif;margin:0 0 4px}
.mix span{font-size:.85rem;color:var(--ink-2);padding:6px 0 0;border-top:1px solid var(--line)}
.hub{display:grid;gap:7px;max-width:760px}
.hub .lv{grid-template-columns:minmax(0,17rem) 1fr 3.5rem}
.links{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,470px),1fr));gap:18px;margin:22px 0 0}
.link{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:18px}
.link h3{font-size:1.08rem;margin:0 0 10px}
.link p{font-size:.95rem;margin:0 0 14px}
.link .cmp{display:grid;grid-template-columns:7.5rem 1fr 3.4rem;gap:6px 10px;align-items:center;font-size:.88rem}
.link .cmp .bar{margin:0;height:14px}
.link .cmp b{text-align:right;font-variant-numeric:tabular-nums}
.link .v{font-size:.82rem;color:var(--ink-2);margin:12px 0 0}
.days{display:flex;gap:6px;align-items:flex-end;height:240px;margin:10px 0 0}
.day{flex:1 1 0;min-width:0;display:flex;flex-direction:column;justify-content:flex-end;height:100%;text-align:center;position:relative}
.day .col{position:relative;display:flex;align-items:flex-end;justify-content:center;flex:1}
.day .fin{position:absolute;bottom:0;left:0;right:0;border:2px dashed var(--line-strong,#85929A);border-bottom:0;border-radius:6px 6px 0 0}
.day .sh{position:relative;width:100%;background:var(--sea);border-radius:6px 6px 0 0}
.day b{font:800 .8rem/1.2 Archivo,system-ui,sans-serif;font-variant-numeric:tabular-nums;margin:0 0 3px;display:block}
.day span{font-size:.78rem;color:var(--ink-2);padding:5px 0 0;border-top:1px solid var(--line);white-space:nowrap}
.key{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:.88rem;color:var(--ink-2);margin:10px 0 0}
.key i{display:inline-block;width:14px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-1px;background:var(--sea)}
.key i.d{background:none;border:2px dashed #85929A}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:18px;margin:26px 0 0}
.stats h3{font-size:1rem;margin:0 0 10px}
.src .lv{grid-template-columns:7rem 1fr 3.5rem}
@media (max-width:640px){.days{gap:3px;height:200px}.day b{display:none}.day .m{display:none}.day span{font-size:.72rem}.src .lv,.hub .lv{grid-template-columns:1fr 4rem}}
"""


# Public Reddit replies to the quiz posts, quoted word for word (cuts marked with an ellipsis), shown without usernames.
# Each links to the original comment so readers can check it.
RC = "https://www.reddit.com/r/{sub}/comments/{post}/_/{cid}/"
QUOTES = [
    ("I wasn't going to vote because it's been very difficult to research what each option stands for, but thanks to this "
     "site I now know exactly who to pick. The biggest help was the reading level option. I'm not very book smart and "
     "political stuff goes completely over my head, so having everything explained in simple terms made it make sense.",
     "VictoriaBC", "1x8wfg3", "phq3go5"),
    ("My son is voting for the first time this year, and he really appreciated the reading levels. Not going to lie... "
     "I did too lol", "VictoriaBC", "1x4lipj", "pghzz7a"),
    ("This helped me immensely have more confidence in my vote. Thanks!", "VictoriaBC", "1x4lipj", "19rlryhtww2ar"),
    ("Everyone deserves to understand politics and what's happening in their community and shouldn't feel limited by "
     "political jargon.", "VictoriaBC", "1x609kg", "pgrqij5"),
    ("This is the best made vote compass type thing I've taken to date. Great work.", "VictoriaBC", "1x4lipj", "pgftucq"),
    ("Great quiz. Truly. I was skeptical but I think this is a good tool.", "VictoriaBC", "1x609kg", "pgrr1ig"),
    ("The reading level function on this is excellent. I lowered it for the question on logging policy because I had no "
     "idea what it was talking about.", "VictoriaBC", "1x4lipj", "pgf0y1d"),
    ("...useful as hell for those who just moved into a new riding like I did and don't have the time to research everyone!",
     "VictoriaBC", "1x4lipj", "pgfmcu0"),
    ("Every voter should engage with this tool if only to become more informed of what's on offer.", "BCpolitics", "1x77s05", "ph6c2vv"),
    ("This helped me a lot, thank you stranger for building this!", "VictoriaBC", "1x4lipj", "phsgb6x"),
]


# Live section: filled in the browser from /api/live (Worker totals since polls closed, cached 5 minutes)
LIVE_JS = r"""(function () {
  var box = document.getElementById("live");
  if (!box || !window.fetch) return;
  var P = JSON.parse(document.getElementById("live-parties").textContent);
  function el(tag, cls, txt) { var n = document.createElement(tag); if (cls) n.className = cls; if (txt != null) n.textContent = txt; return n; }
  function n(v) { return Number(v).toLocaleString("en-CA"); }
  function pct(v) { return (v >= 10 || v === 0 ? Math.round(v) : v.toFixed(1)) + "%"; }
  function day(d) { var m = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]; var x = d.split("-"); return m[+x[1] - 1] + " " + (+x[2]); }
  fetch("/api/live", { headers: { Accept: "application/json" } }).then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
    if (!d) return;
    var body = box.querySelector(".live-body");
    var t = new Date(d.updated);
    box.querySelector(".live-when").textContent = "Updated " + t.toLocaleString("en-CA", { timeZone: "America/Vancouver", month: "long", day: "numeric", hour: "numeric", minute: "2-digit" }) + " Pacific. Numbers update every few minutes.";
    body.appendChild(el("p", "live-lede", n(d.finished) + " more " + (d.finished === 1 ? "person has" : "people have") + " finished the quiz since polls closed, and " + n(d.shared) + " shared their answers."));
    if (d.deleted) body.appendChild(el("p", "small", "Stored answers were deleted on November 23, 2026, as promised. Counts of finished quizzes continue."));
    if (d.scored >= 30) {
      body.appendChild(el("h3", "live-h", "Closest party for people who shared since polls closed"));
      var order = P.map(function (p) { return p.id; }).filter(function (id) { return d.best[id] != null; }).sort(function (a, b) { return d.best[b] - d.best[a]; });
      var st = el("div", "stack"); st.setAttribute("role", "img");
      st.setAttribute("aria-label", order.map(function (id) { var p = P.filter(function (x) { return x.id === id; })[0]; return p.name + " " + pct(d.best[id]); }).join(", "));
      var ps = el("div", "parties");
      order.forEach(function (id) {
        var p = P.filter(function (x) { return x.id === id; })[0];
        var seg = el("span"); seg.style.flex = d.best[id] + " 1 0"; seg.style.background = p.color; st.appendChild(seg);
        var c = el("div"); c.style.flex = d.best[id] + " 1 0";
        c.appendChild(el("b", "num", pct(d.best[id])));
        var lab = el("span"); var dot = el("span", "dot"); dot.style.background = p.color; lab.appendChild(dot); lab.appendChild(document.createTextNode(p.name)); c.appendChild(lab);
        ps.appendChild(c);
      });
      body.appendChild(st); body.appendChild(ps);
      body.appendChild(el("p", "small live-note", "Based on " + n(d.scored) + " people. Compare with the totals above, from before polls closed."));
    } else if (d.shared > 0) {
      body.appendChild(el("p", "small", "A closest-party split appears here once 30 or more people have shared since polls closed."));
    }
    var days = Object.keys(d.finished_daily).sort();
    if (days.length) {
      var top = Math.max.apply(null, days.map(function (k) { return d.finished_daily[k]; }));
      body.appendChild(el("h3", "live-h", "Finished per day since polls closed"));
      var row = el("div", "days live-days");
      days.forEach(function (k) {
        var f = d.finished_daily[k], s = d.shared_daily[k] || 0;
        var c = el("div", "day"); c.appendChild(el("b", null, n(f)));
        var col = el("div", "col");
        var fi = el("i", "fin"); fi.style.height = (100 * f / top) + "%"; col.appendChild(fi);
        var si = el("i", "sh"); si.style.height = (100 * s / top) + "%"; col.appendChild(si);
        c.appendChild(col); c.appendChild(el("span", null, day(k))); row.appendChild(c);
      });
      body.appendChild(row);
      var key = el("div", "key");
      var k1 = el("span"); k1.appendChild(el("i")); k1.appendChild(document.createTextNode("Shared their answers"));
      var k2 = el("span"); k2.appendChild(el("i", "d")); k2.appendChild(document.createTextNode("Everyone who finished"));
      key.appendChild(k1); key.appendChild(k2); body.appendChild(key);
    }
    box.hidden = false;
  }).catch(function () {});
})();
"""


def party_chips(ids, pname, pcol):
    return ", ".join(f'<span class="dot" style="background:{pcol[i]}"></span>{e(pname[i])}' for i in ids)


def stack(shares, order, pname, pcol, min_label=9):
    segs = []
    for pid in order:
        v = shares.get(pid, 0)
        if v <= 0:
            continue
        lab = f"<em>{fmt_pct(v)}</em>" if v >= min_label else ""
        segs.append(f'<span style="flex:{v:.2f} 1 0;background:{pcol[pid]}" '
                    f'title="{e(pname[pid])} {fmt_pct(v)}">{lab}</span>')
    aria = ", ".join(f"{pname[p]} {fmt_pct(shares.get(p, 0))}" for p in order)
    return f'<div class="stack" role="img" aria-label="{e(aria)}">' + "".join(segs) + "</div>"


def bar_fill(ids, pcol):
    if not ids:
        return "var(--neutral)"
    if len(ids) == 1:
        return pcol[ids[0]]
    step = 100 / len(ids)
    return "linear-gradient(" + ",".join(f"{pcol[c]} {i * step:.0f}% {(i + 1) * step:.0f}%" for i, c in enumerate(ids)) + ")"


def question_card(q, pname, pcol):
    rows = []
    for i, o in enumerate(sorted(q["options"], key=lambda o: -o["pct"])):
        who = (f'<div class="who">Matches {party_chips(o["match"], pname, pcol)}</div>' if o["match"]
               else '<div class="who">No party\'s position is a full match</div>')
        rows.append(
            f'<div class="opt{" top" if i == 0 and q["answered"] else ""}"><div class="t"><span>{e(o["text"])}</span>'
            f'<b>{fmt_pct(o["pct"])}</b></div>'
            f'<div class="bar"><i style="width:{o["pct"]:.1f}%;background:{bar_fill(o["match"], pcol)}"></i></div>{who}</div>'
        )
    skip_pct = 100 * q["skipped"] / q["asked"] if q["asked"] else 0
    return (
        f'<article class="q" id="{e(q["id"])}"><h3>{e(q["issue"])}</h3><p class="prompt">{e(q["prompt"])}</p>'
        + "".join(rows)
        + f'<p class="meta num">{q["answered"]:,} answers · {fmt_pct(skip_pct)} skipped or not sure · '
        f'{fmt_pct(q["high_pct"])} marked it high importance</p></article>'
    )


def write_page(out, od):
    sys.path.insert(0, str(ROOT))
    import build_seo

    pname = {p["id"]: p["short_name"] for p in out["parties"]}
    pcol = {p["id"]: MAP_COLOR.get(p["id"], p["color"]) for p in out["parties"]}
    order = sorted(out["best"], key=lambda k: -out["best"][k])
    n = out["people"]
    with_region = sum(r["n"] for r in out["by_region"]) or 1
    reg_sorted = sorted(out["by_region"], key=lambda r: -r["n"])
    big2 = reg_sorted[:2]
    prov = [q for q in out["questions"] if q["scope"] == "provincial"]
    local = [q for q in out["questions"] if q["scope"] != "provincial"]
    regions = {r["id"]: r["name"] for r in SPEC_DATA["regions"]}
    first_d = datetime.fromisoformat(out["first"])
    langs_other = n - out["langs"].get("en", 0)
    legend = '<div class="legend">' + "".join(
        f'<span><span class="dot" style="background:{pcol[p]}"></span>{e(pname[p])}</span>' for p in order)

    b = [f"<style>{CSS_EXTRA}</style>"]
    b.append(f'<h1 class="big">How {n:,} BC quiz-takers answered</h1>')
    b.append(
        f'<p class="dek">Answers people chose to share from BC Vote Helper, {first_d.strftime("%B")} {first_d.day} to the close '
        f'of polls on October 24, 2026, from all {out["ridings_with_answers"]} ridings. '
        '<a href="#limits">Not a poll</a>: people chose to take the quiz, and it never asked how anyone would vote.</p>'
    )

    b.append('<div class="hero"><h2>Whose published positions were closest to their answers</h2>'
             '<p class="sub">Share of quiz-takers for whom each party scored highest. Ties are split evenly.</p>')
    b.append(stack(out["best"], order, pname, pcol, min_label=101))
    b.append('<div class="parties">' + "".join(
        f'<div style="flex:{out["best"][p]:.2f} 1 0"><b class="num">{fmt_pct(out["best"][p])}</b><span><span class="dot" style="background:{pcol[p]}"></span>{e(pname[p])}</span></div>'
        for p in order) + "</div>")
    b.append(f'<p class="foot">For {fmt_pct(out["close_pct"])} of people the top two parties were within 3 points. '
             "Average match across everyone: "
             + ", ".join(f"{e(pname[p])} {out['avg'][p]:.0f}%" for p in sorted(out["avg"], key=lambda k: -out["avg"][k]))
             + ". A closest party is a match on published positions, not a vote or a forecast.</p></div>")

    # live totals since polls closed (filled by /results/live.js; stays hidden without JavaScript)
    plist = [{"id": pid, "name": pname[pid], "color": pcol[pid]} for pid in order]
    b.append('<section id="live" hidden><div class="live-panel"><h2>Since polls closed</h2><p class="live-when"></p>'
             '<div class="live-body"></div></div></section>'
             f'<script type="application/json" id="live-parties">{json.dumps(plist)}</script>'
             '<script src="/results/live.js" defer></script>')

    svgs = map_svgs(out)
    b.append("<section><h2>Closest party, riding by riding</h2>")
    b.append(f'<p class="intro">Each riding is shaded by the party most often closest to its quiz-takers. Many ridings have only '
             f"a few dozen people, so read these as rough. Ridings with fewer than {out['min_riding']} people are grey. "
             "Hover or tap a riding for its numbers.</p>")
    b.append(legend + f'<span><span class="dot" style="background:var(--nodata)"></span>Fewer than {out["min_riding"]} people</span></div>')
    b.append(f'<div class="maps"><div class="side">{svgs[0]}{svgs[1]}</div><div class="side">{svgs[2]}</div></div>')
    b.append(f'<details class="table"><summary>Table of {len(out["by_riding"])} ridings</summary><div class="scroll"><table><thead><tr><th>Riding</th>'
             '<th class="n">People</th>' + "".join(f'<th class="n">{e(pname[p])}</th>' for p in order) + "</tr></thead><tbody>")
    for r in out["by_riding"]:
        b.append(f"<tr><td>{e(r['name'])}</td><td class=\"n\">{r['n']:,}</td>"
                 + "".join(f'<td class="n">{fmt_pct(r["best"].get(p, 0))}</td>' for p in order) + "</tr>")
    b.append("</tbody></table></div></details></section>")

    b.append("<section><h2>By region</h2>")
    b.append(f'<p class="intro">The same measure for each of the {len(reg_sorted)} regions. '
             f'{out["no_riding"]:,} people did not give a riding and count only in the province-wide totals.</p>')
    b.append(legend + "</div>")
    b.append('<div class="regions">' + "".join(
        f'<div class="region"><div class="lab"><b>{e(r["name"])}</b><span class="num">{r["n"]:,} people</span></div>'
        + stack(r["best"], order, pname, pcol, min_label=11) + "</div>" for r in reg_sorted) + "</div></section>")

    # what people said
    def qlink(sub, post, cid):
        return RC.format(sub=sub, post=post, cid=cid)
    b.append("<section><h2>What people said about it</h2>")
    b.append('<p class="intro">A few of the public replies on Reddit, word for word. Usernames are left off; each one links to the original comment.</p>')
    b.append('<div class="quotes">' + "".join(
        f'<figure class="quote{" big" if i < 2 else ""}"><blockquote>{e(t)}</blockquote>'
        f'<figcaption>Reddit, <a href="{e(qlink(sub, post, cid))}">r/{e(sub)}</a></figcaption></figure>'
        for i, (t, sub, post, cid) in enumerate(QUOTES)) + "</div></section>")

    # answers that go together
    if out.get("pairs"):
        qmeta = {q["id"]: q for q in out["questions"]}
        b.append("<section><h2>Answers that go together</h2>")
        mix = {int(k): v for k, v in out.get("mix", {}).items()}
        tot = sum(mix.values()) or 1
        if mix:
            four_plus = sum(v for k, v in mix.items() if k >= 4)
            b.append(f'<p class="intro">Few people answered like a single party. Of the {tot:,} people with at least 10 '
                     f"province-wide answers counted here, {mix.get(1, 0):,} picked answers that matched only one party's position. "
                     f"{fmt_pct(100 * four_plus / tot)} picked answers matching four or all five parties.</p>")
            mxv = max(mix.values())
            b.append('<h3 style="margin:0 0 4px">How many parties a person\'s answers matched</h3>'
                     '<div class="mix" role="img" aria-label="'
                     + e(", ".join(f"{k} parties: {fmt_pct(100 * v / tot)}" for k, v in sorted(mix.items()))) + '">'
                     + "".join(f'<div><b class="num">{fmt_pct(100 * mix.get(k, 0) / tot)}</b><i style="height:{100 * mix.get(k, 0) / mxv:.1f}%"></i>'
                               f'<span>{k} {"party" if k == 1 else "parties"}</span></div>' for k in range(1, 6)) + "</div>")
        # how strongly each question is linked to the rest
        link = defaultdict(list)
        for pr in out["pairs"]:
            link[pr["q1"]].append(pr["v"])
            link[pr["q2"]].append(pr["v"])
        hub = sorted(((sum(v) / len(v), q) for q, v in link.items()), reverse=True)
        top = hub[0][1]
        b.append(f'<h3 style="margin:40px 0 4px">Which answers say the most about the rest</h3>'
                 f'<p class="intro" style="margin-bottom:14px">How closely a person\'s answer to each question goes with their other answers, '
                 f"on average. {e(qmeta[top]['issue'])} is linked to the rest more than anything else. A long bar means the answer to that "
                 "question goes with particular answers elsewhere; a short bar means people's answers on it mixed freely.</p>")
        hm = hub[0][0]
        b.append('<div class="hub">' + "".join(
            f'<div class="lv"><span>{e(qmeta[q]["issue"])}</span><div class="bar"><i style="width:{100 * v / hm:.1f}%"></i></div><b>{v:.2f}</b></div>'
            for v, q in hub) + "</div>")
        b.append('<p class="small" style="margin-top:8px">Average Cramer\'s V with the other 12 questions: 0 means answers are unrelated, 1 means one answer '
                 "always predicts the other.</p>")
        b.append('<h3 style="margin:40px 0 4px">The strongest pairs</h3>'
                 '<p class="intro" style="margin-bottom:0">For each of the six most closely linked pairs of questions, the clearest link between two answers. '
                 "These show which answers went together. They do not show why.</p>")
        cards = []
        for pr in out["pairs"][:6]:
            L = pr["link"]
            i1, i2 = qmeta[L["if_q"]]["issue"], qmeta[L["then_q"]]["issue"]
            cards.append(
                f'<article class="link"><h3>{e(i1)} and {e(i2)}</h3>'
                f'<p>Of the {L["if_n"]:,} people who picked <b>&ldquo;{e(L["if_text"].rstrip("."))}&rdquo;</b> on the {e(i1)} question, '
                f'{fmt_pct(L["then_pct"])} also picked <b>&ldquo;{e(L["then_text"].rstrip("."))}&rdquo;</b> on {e(i2)}.</p>'
                f'<div class="cmp"><span>That group</span><div class="bar"><i style="width:{L["then_pct"]:.1f}%;background:var(--sea)"></i></div><b>{fmt_pct(L["then_pct"])}</b>'
                f'<span>Everyone</span><div class="bar"><i style="width:{L["all_pct"]:.1f}%;background:var(--neutral)"></i></div><b>{fmt_pct(L["all_pct"])}</b></div>'
                f'<p class="v num">Link strength {pr["v"]:.2f} · {pr["n"]:,} people answered both</p></article>')
        b.append('<div class="links">' + "".join(cards) + "</div></section>")

    b.append("<section><h2>How people answered each question</h2>")
    b.append('<p class="intro">Answers on the 13 province-wide questions, most picked first. Each bar takes the colour of the '
             "party whose published position it fully matches. Wording is the plain-language reading level most people chose.</p>")
    b.append('<div class="qs">' + "".join(question_card(q, pname, pcol) for q in prov) + "</div></section>")

    b.append("<section><h2>Local questions</h2>")
    b.append(f'<p class="intro">People who gave their riding also answered three questions for their region. '
             f"Questions with fewer than {out['min_group']} answers are not shown.</p>")
    for rid in regions:
        qs = [q for q in local if q["region"] == rid]
        if qs:
            b.append(f'<details class="local"><summary>{e(regions[rid])}<span class="num">{qs[0]["asked"]:,} people</span></summary>'
                     '<div class="qs">' + "".join(question_card(q, pname, pcol) for q in qs) + "</div></details>")
    b.append("</section>")

    lv = {lvl["id"]: lvl["label"] for lvl in SPEC_DATA["levels"]}
    mx = max(out["levels"].values())
    b.append("<section><h2>Who answered</h2>")
    b.append(f'<p class="intro">{n:,} people in {out["sessions"]:,} quiz sessions; up to four people could answer together, '
             f"and each person counts once. {langs_other:,} answered in a language other than English. "
             "The reading level each person picked changes the wording only, not the answers or scores.</p>")
    b.append('<div class="levels">' + "".join(
        f'<div class="lv"><span>{e(lv.get(int(lid), f"Level {lid}"))}</span><div class="bar"><i style="width:{100 * c / mx:.1f}%"></i></div>'
        f'<b>{c:,}</b></div>' for lid, c in out["levels"].items()) + "</div>")

    # people per day, with every finished quiz where the counter existed
    daily = out.get("daily") or {}
    comp = out.get("completions")
    if daily:
        fin = dict(comp["daily"]) if comp else {}
        first_full = (ts(comp["since"]).astimezone(timezone(timedelta(hours=-7))).date() + timedelta(days=1)).isoformat() if comp else None
        fin = {d: v for d, v in fin.items() if first_full and d >= first_full}
        top_day = max(list(daily.values()) + list(fin.values()))
        cols = []
        for d, v in daily.items():
            dt = datetime.fromisoformat(d)
            f = fin.get(d)
            cols.append(
                f'<div class="day"><b>{v:,}</b><div class="col">'
                + (f'<i class="fin" style="height:{100 * f / top_day:.1f}%" title="{f:,} finished"></i>' if f else "")
                + f'<i class="sh" style="height:{100 * v / top_day:.1f}%"></i></div><span><em class="m" style="font-style:normal">{dt.strftime("%b")} </em>{dt.day}</span></div>')
        b.append('<h3 style="margin:34px 0 4px">People per day</h3>'
                 '<div class="days" role="img" aria-label="' + e(", ".join(f"{d}: {v} shared" for d, v in daily.items())) + '">' + "".join(cols) + "</div>")
        busiest = max(daily, key=daily.get)
        bd = datetime.fromisoformat(busiest)
        key = '<div class="key"><span><i></i>People who shared their answers</span>'
        if fin:
            key += '<span><i class="d"></i>Everyone who finished (counted from October 20)</span>'
        b.append(key + "</div>")
        b.append(f'<p class="small" style="margin-top:8px">The busiest day was {bd.strftime("%B")} {bd.day}, with {daily[busiest]:,} people sharing their answers.</p>')
    if comp:
        st = ts(comp["since"]).astimezone(timezone(timedelta(hours=-7)))
        names = {"direct": "Direct or shared link", "reddit": "Reddit", "search": "Search", "classroom": "Classroom",
                 "facebook": "Facebook", "instagram": "Instagram", "other": "Other sites", "unknown": "Not recorded"}
        srcs = [(k, v) for k, v in comp["sources"].items() if v >= 1]
        mx = max(v for _, v in srcs)
        b.append(
            '<div class="stats">'
            f'<div><h3>Everyone who finished</h3><p class="small">From {e(long_dt(comp["since"]))}, the site also counted every finished quiz, '
            f"whether or not people shared. In that time {comp['people']:,} people finished in {comp['sessions']:,} sessions, and "
            f"{fmt_pct(100 * comp['shared_sessions'] / comp['sessions'])} of sessions shared their answers.</p></div>"
            '<div class="src"><h3>Where people came from</h3><div class="levels">'
            + "".join(f'<div class="lv"><span>{e(names.get(k, k.title()))}</span><div class="bar"><i style="width:{100 * v / mx:.1f}%"></i></div><b>{fmt_pct(v)}</b></div>'
                      for k, v in srcs)
            + '</div><p class="small" style="margin-top:8px">Finished sessions since then, by' + " the kind of site people arrived from. "
            "Only the category is recorded, never the address.</p></div></div>")
    b.append("</section>")

    b.append('<section id="limits"><h2>Read these numbers with care</h2><div class="limits"><ul>'
             "<li>This is not a poll. People chose to take the quiz and chose to share their answers. They are not a random "
             "sample of BC voters, and the quiz never asked anyone how they would vote.</li>"
             f"<li>Most answers came from {e(big2[0]['name'])} ({fmt_pct(100 * big2[0]['n'] / with_region)}) and "
             f"{e(big2[1]['name'])} ({fmt_pct(100 * big2[1]['n'] / with_region)}) among people who gave a riding. "
             "The quiz was shared online and in some classrooms, so not everyone who answered is old enough to vote.</li>"
             "<li>The closest party is the one whose published positions best matched a person's answers. It is not a vote "
             "and not a forecast.</li>"
             "<li>Some questions were changed when parties released new platforms. Answers given before a change are left out "
             "of that question, so the number of answers differs from question to question.</li>"
             "</ul></div>")
    b.append(
        '<h3 style="margin:30px 0 8px">How these numbers were made</h3>'
        "<p>Only people who left the share box ticked are counted. Names and IP addresses were never collected. "
        f"Answers after polls closed are not included. Rows without a BC riding or a BC location are left out "
        f"({sum(out['excluded'].values()):,} in total). "
        "Every answer is scored again with the final version of the quiz, which used party positions published by October 18, 2026.</p>"
        f'<p>The totals are in <a href="/results/results.json">results.json</a>. The scoring code, every party score and its '
        f'sources are public at <a href="{build_seo.REPO}">github.com/vinistoisr/bc-vote-helper</a>. All stored answers will be '
        "deleted on November 23, 2026.</p>"
        f'<p class="small">Totals made {e(long_dt(out["generated_at"]))}. This page is in English only.</p></section>'
    )

    desc = (f"Answers from {n:,} people who took BC Vote Helper before the October 24, 2026 BC election: how they answered "
            "each question and which party's positions were closest. Not a poll.")
    ld = [{
        "@context": "https://schema.org", "@type": "Dataset",
        "name": "BC Vote Helper 2026 quiz answers (totals)",
        "description": desc, "url": SITE_URL + "results/",
        "temporalCoverage": f"{out['first'][:10]}/2026-10-24",
        "spatialCoverage": "British Columbia, Canada",
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": SITE_URL + "results/results.json"}],
    }]
    page = build_seo.page("/results/", f"How {n:,} BC quiz-takers answered", desc, "".join(b), ld=ld, data_as_of="October 18, 2026")
    if chr(0x2014) in page:
        sys.exit("em dash in results page")
    (od / "index.html").write_text(page, encoding="utf-8", newline="\n")
    (od / "live.js").write_text(LIVE_JS, encoding="utf-8", newline="\n")
    print(f"wrote {od / 'index.html'} ({(od / 'index.html').stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
