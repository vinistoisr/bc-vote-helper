"""Build the admin map's base layers (land and coastline, lakes, rivers, place and water names).

Usage:
  python build_basemap.py   (needs: pip install --user shapely pyshp)

Inputs (geo/basemap/raw/, not committed; download links in geo/SOURCES.txt):
  land3857.zip                         OpenStreetMap simplified land polygons, EPSG:3857 (ODbL, (c) OpenStreetMap contributors)
  ne_10m_lakes.geojson, ne_10m_lakes_north_america.geojson            Natural Earth (public domain)
  ne_10m_rivers_lake_centerlines.geojson, ne_10m_rivers_north_america.geojson   Natural Earth (public domain)
  cities1000.zip                       GeoNames places with 1,000+ people (CC BY 4.0)

Output:
  site/public/geo/basemap.json   {land: [polygon], lakes: [polygon], rivers: [{r, l}], places: [{n, x, y, p}], water: [{n, x, y, t}]}
                                 polygon = [ring, ...], ring = flat [lon, lat, ...]; the admin page projects it.
The riding shapes (site/public/geo/eds.json) run out into the sea, so the map draws land under them and
clips them to it; that is what makes the coast visible.
"""
import io
import json
import math
import os
import sys
import zipfile

import shapefile
from shapely.geometry import LineString, MultiLineString, Polygon, box, shape
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "geo", "basemap", "raw")
OUT = os.path.join(HERE, "site", "public", "geo", "basemap.json")
BBOX = (-140.5, 47.0, -112.5, 61.0)        # BC plus a margin, so the edges of the map look natural
CLIP = box(*BBOX)
ROUND = 4                                   # about 10 m
LAND_TOL, LAKE_TOL, RIVER_TOL = 0.0012, 0.002, 0.003
MIN_ISLAND = 4e-5                           # square degrees, about 0.3 km2 at 50 N
MIN_LAKE = 1.5e-3                           # about 12 km2

# Water bodies and neighbours, for orientation. t = smallest view width (km) that shows the name; 0 = always.
WATER = [
    ("Pacific Ocean", -131.6, 50.2, 0), ("Strait of Georgia", -123.72, 49.33, 700), ("Juan de Fuca Strait", -124.1, 48.33, 500),
    ("Hecate Strait", -130.95, 53.45, 900), ("Queen Charlotte Sound", -129.4, 51.45, 900), ("Dixon Entrance", -132.4, 54.42, 900),
    ("Okanagan Lake", -119.53, 50.02, 250), ("Kootenay Lake", -116.87, 49.62, 300), ("Williston Lake", -123.85, 56.2, 500),
    ("Shuswap Lake", -119.2, 50.95, 250), ("Howe Sound", -123.33, 49.5, 120), ("Burrard Inlet", -123.0, 49.305, 70),
    ("Strait of Georgia", -123.32, 49.12, 120),
]
LAND = [
    ("Vancouver Island", -125.75, 49.75, 0), ("Haida Gwaii", -132.15, 53.25, 0), ("Alberta", -115.6, 55.4, 0),
    ("Washington", -120.6, 47.75, 0), ("Alaska", -134.2, 58.3, 0), ("Yukon", -131.5, 60.55, 0),
]
# GeoNames feature codes for real towns and cities; PPLX (neighbourhoods) and PPLL (localities) are left out
TOWN_CODES = {"PPLC", "PPLA", "PPLA2", "PPLA3", "PPLA4", "PPL"}
# Neighbourhoods GeoNames codes as towns; a map of ridings reads better with municipality names only
NOT_TOWNS = {"Fleetwood", "Strawberry Hill", "Victoria-Fraserview", "Riley Park", "Burquitlam", "Clayburn", "Greektown",
             "West End", "Westridge", "River Springs", "Pemberton Heights", "Essondale", "Tillicum", "Six Mile", "Keating"}


def merc_to_lonlat(x, y):
    return x / 6378137.0 * 180.0 / math.pi, (2 * math.atan(math.exp(y / 6378137.0)) - math.pi / 2) * 180.0 / math.pi


def flat(coords):
    out = []
    for x, y in coords:
        out += [round(x, ROUND), round(y, ROUND)]
    return out


def polys(geom, min_area):
    """Polygon or MultiPolygon -> [[exterior, hole, ...], ...] in flat arrays, dropping slivers."""
    gs = list(geom.geoms) if hasattr(geom, "geoms") else [geom]
    out = []
    for g in gs:
        if g.geom_type != "Polygon" or g.is_empty or g.area < min_area:
            continue
        out.append([flat(g.exterior.coords)] + [flat(i.coords) for i in g.interiors if Polygon(i).area >= min_area])
    return out


def land():
    z = zipfile.ZipFile(os.path.join(RAW, "land3857.zip"))
    base = [n for n in z.namelist() if n.endswith(".shp")][0][:-4]
    r = shapefile.Reader(shp=io.BytesIO(z.read(base + ".shp")), shx=io.BytesIO(z.read(base + ".shx")), dbf=io.BytesIO(z.read(base + ".dbf")))
    x0, y0 = BBOX[0] * 6378137.0 * math.pi / 180, math.log(math.tan(math.pi / 4 + BBOX[1] * math.pi / 360)) * 6378137.0
    x1, y1 = BBOX[2] * 6378137.0 * math.pi / 180, math.log(math.tan(math.pi / 4 + BBOX[3] * math.pi / 360)) * 6378137.0
    keep = []
    for sh in r.iterShapes():
        bx = sh.bbox
        if bx[2] < x0 or bx[0] > x1 or bx[3] < y0 or bx[1] > y1:
            continue
        parts = list(sh.parts) + [len(sh.points)]
        rings = [[merc_to_lonlat(*p) for p in sh.points[parts[i]:parts[i + 1]]] for i in range(len(parts) - 1)]
        g = Polygon(rings[0], rings[1:]).buffer(0)
        g = g.intersection(CLIP)
        if not g.is_empty:
            keep.append(g)
    g = unary_union(keep).simplify(LAND_TOL, preserve_topology=True)
    return polys(g, MIN_ISLAND)


def ne(name):
    with open(os.path.join(RAW, name + ".geojson"), encoding="utf-8") as f:
        return json.load(f)["features"]


def lakes():
    gs = []
    for fn in ("ne_10m_lakes", "ne_10m_lakes_north_america"):
        for f in ne(fn):
            if not f["geometry"]:
                continue
            g = shape(f["geometry"]).buffer(0)
            if g.intersects(CLIP):
                gs.append(g.intersection(CLIP))
    g = unary_union(gs).simplify(LAKE_TOL, preserve_topology=True)
    return polys(g, MIN_LAKE)


def rivers():
    out = []
    for fn in ("ne_10m_rivers_lake_centerlines", "ne_10m_rivers_north_america"):
        for f in ne(fn):
            if not f["geometry"]:
                continue
            g = shape(f["geometry"])
            if not g.intersects(CLIP):
                continue
            g = g.intersection(CLIP).simplify(RIVER_TOL)
            rank = f["properties"].get("scalerank")
            rank = 12 if rank is None else int(rank)
            for line in (g.geoms if hasattr(g, "geoms") else [g]):
                if line.geom_type == "LineString" and line.length > 0.02:
                    out.append({"r": rank, "l": flat(line.coords)})
    return out


# River names: t as above. The label sits on the river itself, at the point of its longest stretch nearest the middle
# (or nearest `near`, for a second label where a river crosses a dense area).
RIVER_NAMES = [
    ("Fraser", "Fraser River", 900, None), ("Fraser", "Fraser River", 150, (-122.62, 49.18)), ("Columbia", "Columbia River", 900, None),
    ("Peace", "Peace River", 900, None), ("Skeena", "Skeena River", 900, None), ("Stikine", "Stikine River", 900, None),
    ("Liard", "Liard River", 900, None), ("Thompson", "Thompson River", 450, None), ("Nass", "Nass River", 450, None),
    ("Kootenay", "Kootenay River", 450, None), ("Nechako", "Nechako River", 450, None), ("Chilcotin", "Chilcotin River", 300, None),
]


def river_labels():
    bc = unary_union([Polygon([(r[i], r[i + 1]) for i in range(0, len(r), 2)]).buffer(0)
                      for d in [json.load(open(os.path.join(HERE, "site", "public", "geo", "eds.json"), encoding="utf-8"))["r"]]
                      for e in d for poly in e["p"] for r in poly[:1]])
    lines = {}
    for fn in ("ne_10m_rivers_lake_centerlines", "ne_10m_rivers_north_america"):
        for f in ne(fn):
            n = (f["properties"].get("name") or "").strip()
            if f["geometry"] and n:
                g = shape(f["geometry"])
                for line in (g.geoms if hasattr(g, "geoms") else [g]):
                    lines.setdefault(n, []).append(line)
    out = []
    for key, label, t, near in RIVER_NAMES:
        cands = [ln.intersection(bc) for ln in lines.get(key, [])]
        parts = [p for c in cands for p in (c.geoms if hasattr(c, "geoms") else [c]) if p.geom_type == "LineString" and not p.is_empty]
        if not parts:
            print("no river line for", key); continue
        if near:
            from shapely.geometry import Point
            pt = Point(near)
            best = min(parts, key=lambda p: p.distance(pt))
            q = best.interpolate(best.project(pt))
        else:
            best = max(parts, key=lambda p: p.length)
            q = best.interpolate(0.5, normalized=True)
        out.append({"n": label, "x": round(q.x, ROUND), "y": round(q.y, ROUND), "t": t})
    return out


def places():
    z = zipfile.ZipFile(os.path.join(RAW, "cities1000.zip"))
    rows = z.read(z.namelist()[0]).decode("utf-8").splitlines()
    out = []
    for line in rows:
        c = line.split("\t")
        if c[8] != "CA" or c[10] != "02" or c[7] not in TOWN_CODES or c[1] in NOT_TOWNS:
            continue
        out.append({"n": c[1], "x": round(float(c[5]), ROUND), "y": round(float(c[4]), ROUND), "p": int(c[14] or 0)})
    out.sort(key=lambda p: -p["p"])
    # one label per name (GeoNames repeats a few places under two codes)
    seen, uniq = set(), []
    for p in out:
        if p["n"] in seen:
            continue
        seen.add(p["n"])
        uniq.append(p)
    return uniq


def main():
    data = {
        "v": 1,
        "credit": "Coastline (c) OpenStreetMap contributors (ODbL); lakes and rivers Natural Earth; places GeoNames (CC BY 4.0)",
        "land": land(),
        "lakes": lakes(),
        "rivers": rivers(),
        "places": places(),
        "water": [{"n": n, "x": x, "y": y, "t": t} for n, x, y, t in WATER] + river_labels(),
        "regions": [{"n": n, "x": x, "y": y, "t": t} for n, x, y, t in LAND],
    }
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, separators=(",", ":"), ensure_ascii=False)
    pts = lambda ps: sum(len(r) // 2 for p in ps for r in p)
    print(f"wrote {OUT} ({os.path.getsize(OUT) / 1024:.0f} KB): land {len(data['land'])} polygons / {pts(data['land'])} points, "
          f"lakes {len(data['lakes'])}, rivers {len(data['rivers'])}, places {len(data['places'])}")


if __name__ == "__main__":
    sys.exit(main())
