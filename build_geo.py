"""Build the local riding lookup files (V2), so the site does not depend on Represent's rate limit.

Usage:
  python build_geo.py   (needs: pip install --user shapely pyproj numpy) [--postal-source path\\to\\CA_full.txt] [--check N]

Inputs (all in geo/):
  eds_full/<CODE>.json   full riding shapes from Represent (Open North), BC 2023 redistribution set
  eds_simple.json        Represent's simplified shapes (used only if a full shape is missing)
  ridings.json           code, name, group for all 93 ridings
  postal/geonames_bc_postal.tsv  BC postal codes with a point for each (GeoNames, CC BY 4.0).
                         Refresh it with --postal-source pointing at GeoNames' CA_full.txt.

Outputs:
  site/public/geo/eds.json      compact shapes for "Use my location" (point in polygon in the Worker)
  site/public/geo/pc/<FSA>.json postal code -> riding (+ nearby ridings) for one forward sortation area,
                                plus the ridings that FSA covers, for the fallback pick list
  site/src/riding_names.json    code -> name, bundled into the Worker

--check N compares N random BC postal codes against Represent (one request every 1.2 s) and prints agreement.
"""
import argparse
import json
import os
import random
import sys
import time
import urllib.request
from collections import Counter, defaultdict

import numpy as np
import shapely
from pyproj import Transformer
from shapely.geometry import shape

HERE = os.path.dirname(os.path.abspath(__file__))
GEO = os.path.join(HERE, "geo")
PUB = os.path.join(HERE, "site", "public", "geo")
POSTAL_TSV = os.path.join(GEO, "postal", "geonames_bc_postal.tsv")
URBAN_NEAR_M = 150      # an urban postal code this close to another riding also lists that riding
RURAL_NEAR_M = 5000     # rural codes (second character 0) cover wide areas
OFFSHORE_MAX_M = 20000  # a point in the water snaps to the nearest riding within this distance
FSA_MIN_SHARE = 0.02    # ridings holding under 2% of an FSA's postal codes are left out of its pick list
SIMPLIFY_DEG = 0.0003   # about 30 m, for the location file only
ROUND = 4               # about 10 m


def load_ridings():
    rid = json.load(open(os.path.join(GEO, "ridings.json"), encoding="utf-8"))
    by_name = {r["name"]: r["code"] for r in rid}
    simple = {by_name[o["name"]]: o["simple_shape"] for o in json.load(open(os.path.join(GEO, "eds_simple.json"), encoding="utf-8"))["objects"]}
    geoms, missing = {}, []
    for r in rid:
        p = os.path.join(GEO, "eds_full", r["code"] + ".json")
        if os.path.exists(p):
            d = json.load(open(p, encoding="utf-8"))
            geoms[r["code"]] = shape(d["shape"] if "shape" in d else d)
        else:
            missing.append(r["code"])
            geoms[r["code"]] = shape(simple[r["code"]])
    if missing:
        print(f"WARNING: {len(missing)} ridings use the simplified shape: {', '.join(missing)}")
    return rid, geoms


def refresh_postal(src):
    os.makedirs(os.path.dirname(POSTAL_TSV), exist_ok=True)
    n = 0
    with open(src, encoding="utf-8") as f, open(POSTAL_TSV, "w", encoding="utf-8", newline="\n") as out:
        out.write("postal\tlat\tlon\n")
        for line in f:
            c = line.rstrip("\n").split("\t")
            if len(c) > 10 and c[1].startswith("V") and c[4] == "BC":
                out.write(f"{c[1].replace(' ', '')}\t{c[9]}\t{c[10]}\n")
                n += 1
    print(f"wrote {POSTAL_TSV} ({n} BC postal codes)")


def ring_flat(coords):
    out = []
    for x, y in coords:
        out.append(round(x, ROUND))
        out.append(round(y, ROUND))
    return out


def write_location_file(rid, geoms):
    items = []
    for r in rid:
        g = geoms[r["code"]].simplify(SIMPLIFY_DEG, preserve_topology=True)
        polys = list(g.geoms) if g.geom_type == "MultiPolygon" else [g]
        rings = []
        for p in polys:
            rings.append([ring_flat(p.exterior.coords)] + [ring_flat(i.coords) for i in p.interiors])
        minx, miny, maxx, maxy = g.bounds
        items.append({"c": r["code"], "b": [round(minx, ROUND), round(miny, ROUND), round(maxx, ROUND), round(maxy, ROUND)], "p": rings})
    os.makedirs(PUB, exist_ok=True)
    path = os.path.join(PUB, "eds.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"v": 1, "set": "british-columbia-electoral-districts-2023-redistribution", "r": items}, f, separators=(",", ":"))
    print(f"wrote {path} ({os.path.getsize(path) / 1024:.0f} KB)")


def write_postal_files(rid, geoms):
    codes = [r["code"] for r in rid]
    to_m = Transformer.from_crs("EPSG:4326", "EPSG:3005", always_xy=True)  # BC Albers, metres
    proj = [shapely.transform(geoms[c], lambda xy: np.column_stack(to_m.transform(xy[:, 0], xy[:, 1]))) for c in codes]
    tree = shapely.STRtree(proj)
    rows = [l.rstrip("\n").split("\t") for l in open(POSTAL_TSV, encoding="utf-8").readlines()[1:]]
    pcs = [r[0] for r in rows]
    lat = np.array([float(r[1]) for r in rows])
    lon = np.array([float(r[2]) for r in rows])
    x, y = to_m.transform(lon, lat)
    pts = shapely.points(x, y)

    primary = [None] * len(pcs)
    pi, gi = tree.query(pts, predicate="within")
    for p, g in zip(pi, gi):
        if primary[p] is None:
            primary[p] = g
    lost = [i for i, v in enumerate(primary) if v is None]
    if lost:
        (li, gi), _ = tree.query_nearest(pts[lost], max_distance=OFFSHORE_MAX_M, return_distance=True, all_matches=False)
        for p, g in zip(li, gi):
            primary[lost[p]] = g
    near = defaultdict(list)
    rural = np.array([pc[1] == "0" for pc in pcs])
    for limit, mask in ((URBAN_NEAR_M, ~rural), (RURAL_NEAR_M, rural)):
        idx = np.nonzero(mask)[0]
        qi, gi = tree.query(pts[idx], predicate="dwithin", distance=limit)
        for p, g in zip(qi, gi):
            near[idx[p]].append(g)
    by_fsa = defaultdict(dict)
    skipped = 0
    for i, pc in enumerate(pcs):
        g = primary[i]
        if g is None:
            skipped += 1
            continue
        others = [o for o in near.get(i, []) if o != g]
        if others:
            others.sort(key=lambda o: shapely.distance(pts[i], proj[o]))
            others = others[:3]
        by_fsa[pc[:3]][pc[3:]] = " ".join([codes[g]] + [codes[o] for o in others])
    out_dir = os.path.join(PUB, "pc")
    os.makedirs(out_dir, exist_ok=True)
    for old in os.listdir(out_dir):
        os.remove(os.path.join(out_dir, old))
    multi = single = 0
    for fsa, m in sorted(by_fsa.items()):
        cnt = Counter(v.split(" ")[0] for v in m.values())
        total = sum(cnt.values())
        choices = [c for c, n in cnt.most_common() if n / total >= FSA_MIN_SHARE]
        if len(choices) > 1:
            multi += 1
        else:
            single += 1
        with open(os.path.join(out_dir, fsa + ".json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump({"fsa": fsa, "choices": choices, "codes": m}, f, separators=(",", ":"))
    size = sum(os.path.getsize(os.path.join(out_dir, n)) for n in os.listdir(out_dir))
    with_alt = sum(1 for m in by_fsa.values() for v in m.values() if " " in v)
    print(f"wrote {len(by_fsa)} FSA files ({size / 1024:.0f} KB): {single} FSAs in one riding, {multi} across several")
    print(f"postal codes: {len(pcs) - skipped} mapped, {skipped} too far from any riding, {with_alt} with a nearby riding listed")
    return by_fsa


def check(by_fsa, n):
    flat = [(f + l, v.split(" ")) for f, m in by_fsa.items() for l, v in m.items()]
    rng = random.Random(2026)
    sample = rng.sample(flat, n)
    agree = alt_ok = 0
    for pc, local in sample:
        req = urllib.request.Request(f"https://represent.opennorth.ca/postcodes/{pc}/?format=json",
                                     headers={"User-Agent": "bc-vote-helper build check (votebc.vinceroyer.ca)"})
        try:
            d = json.loads(urllib.request.urlopen(req, timeout=30).read())
        except Exception as e:
            print(pc, "represent error", e)
            time.sleep(1.2)
            continue
        rep = []
        for b in (d.get("boundaries_centroid") or []) + (d.get("boundaries_concordance") or []):
            if "british-columbia-electoral-districts-2023" in (b.get("related", {}).get("boundary_set_url") or ""):
                c = (b.get("external_id") or "").upper()
                if c not in rep:
                    rep.append(c)
        if rep and rep[0] == local[0]:
            agree += 1
        elif rep and rep[0] in local:
            alt_ok += 1
            print(f"{pc}: Represent {rep[0]}, local {local[0]} (Represent's riding is listed as nearby)")
        else:
            print(f"{pc}: Represent {rep}, local {local}")
        time.sleep(1.2)
    print(f"check: {agree}/{n} same riding, {alt_ok} more where Represent's riding is offered as an alternative")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--postal-source")
    ap.add_argument("--check", type=int, default=0)
    a = ap.parse_args()
    if a.postal_source:
        refresh_postal(a.postal_source)
    if not os.path.exists(POSTAL_TSV):
        sys.exit(f"missing {POSTAL_TSV}; run with --postal-source CA_full.txt from https://download.geonames.org/export/zip/")
    rid, geoms = load_ridings()
    write_location_file(rid, geoms)
    by_fsa = write_postal_files(rid, geoms)
    names = {r["code"]: r["name"] for r in rid}
    with open(os.path.join(HERE, "site", "src", "riding_names.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(names, f, ensure_ascii=False, separators=(",", ":"))
    if a.check:
        check(by_fsa, a.check)


if __name__ == "__main__":
    main()
