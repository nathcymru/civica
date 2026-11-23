#!/usr/bin/env python3
"""Generate the simplified UK nations outline used by the reading infographic.

Source: Natural Earth 1:50m Admin 0 map units, release v5.1.2 (public domain).
Natural Earth splits the United Kingdom into England, Scotland, Wales and
Northern Ireland, so no boundary is drawn by hand.

The script downloads the pinned GeoJSON, projects longitude and latitude to a
flat plane (longitude scaled by cos 55 degrees, which keeps Great Britain's
proportions at this size), drops islands too small to see at card size,
simplifies each ring with Douglas-Peucker and writes SVG path data to
docs/data/uk-nations-map.json. The page partial reads that file, so the map is
editable by re-running this script rather than by hand-editing paths.

Usage (from the repository root):
    python3 docs/scripts/generate-uk-nations-map.py            # write
    python3 docs/scripts/generate-uk-nations-map.py --check    # fail if stale
"""
import hashlib
import json
import math
import pathlib
import sys
import urllib.request

SOURCE_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/"
    "geojson/ne_50m_admin_0_map_units.geojson"
)
SOURCE_SHA256 = "b8d421aca6e9e08e8cdf09cc26af111cc3e0deba4fe915611d58ade71e8a4db0"
OUT = pathlib.Path(__file__).resolve().parents[2] / "docs/data/uk-nations-map.json"
NATIONS = ["Scotland", "Northern Ireland", "England", "Wales"]  # draw order
WIDTH = 300.0          # output view box width; height follows the projection
TOLERANCE = 0.6        # Douglas-Peucker tolerance in output units
MIN_AREA = 2.5         # drop rings smaller than this (output units squared)
COS = math.cos(math.radians(55))


def douglas_peucker(points, tolerance):
    if len(points) < 3:
        return points
    start, end = points[0], points[-1]
    dx, dy = end[0] - start[0], end[1] - start[1]
    norm = math.hypot(dx, dy) or 1e-9
    index, distance = 0, 0.0
    for i in range(1, len(points) - 1):
        px, py = points[i]
        d = abs(dy * px - dx * py + end[0] * start[1] - end[1] * start[0]) / norm
        if d > distance:
            index, distance = i, d
    if distance <= tolerance:
        return [start, end]
    left = douglas_peucker(points[: index + 1], tolerance)
    right = douglas_peucker(points[index:], tolerance)
    return left[:-1] + right


def ring_area(points):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]))) / 2


def main():
    raw = urllib.request.urlopen(SOURCE_URL, timeout=90).read()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SOURCE_SHA256:
        sys.exit(f"Source changed: {digest}")
    features = {
        f["properties"]["GEOUNIT"]: f["geometry"]
        for f in json.loads(raw)["features"]
        if f["properties"].get("ADMIN") == "United Kingdom"
    }
    polygons = {}
    for nation in NATIONS:
        geometry = features[nation]
        polys = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
        polygons[nation] = [poly[0] for poly in polys]  # outer rings only
    all_points = [pt for rings in polygons.values() for ring in rings for pt in ring]
    min_x = min(lon * COS for lon, _ in all_points)
    max_x = max(lon * COS for lon, _ in all_points)
    min_y = min(-lat for _, lat in all_points)
    max_y = max(-lat for _, lat in all_points)
    scale = WIDTH / (max_x - min_x)
    height = round((max_y - min_y) * scale, 1)

    paths = {}
    for nation in NATIONS:
        parts = []
        for ring in polygons[nation]:
            pts = [((lon * COS - min_x) * scale, (-lat - min_y) * scale) for lon, lat in ring]
            if ring_area(pts) < MIN_AREA:
                continue
            # A closed ring starts and ends on the same point, so simplify its two
            # halves separately (Douglas-Peucker needs distinct end points).
            half = len(pts) // 2
            pts = douglas_peucker(pts[: half + 1], TOLERANCE)[:-1] + douglas_peucker(pts[half:], TOLERANCE)
            if len(pts) < 4:
                continue
            parts.append("M" + " ".join(f"{x:.1f} {y:.1f}" for x, y in pts[:-1]) + "Z")
        paths[nation] = "".join(parts)

    record = {
        "source": "Natural Earth 1:50m Admin 0 map units, v5.1.2",
        "source_url": SOURCE_URL,
        "licence": "Public domain (Natural Earth terms of use)",
        "generator": "docs/scripts/generate-uk-nations-map.py",
        "view_box": f"0 0 {WIDTH:g} {height:g}",
        "paths": paths,
    }
    text = json.dumps(record, indent=2) + "\n"
    if "--check" in sys.argv:
        if OUT.read_text(encoding="utf-8") != text:
            sys.exit(f"{OUT} is stale; re-run the generator")
        print(f"{OUT} is current")
        return
    OUT.write_text(text, encoding="utf-8")
    print(f"Wrote {OUT}: view box {record['view_box']}, {sum(len(p) for p in paths.values())} path characters")


if __name__ == "__main__":
    main()
