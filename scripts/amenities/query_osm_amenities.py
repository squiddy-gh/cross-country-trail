"""
query_osm_amenities.py
----------------------
Queries OpenStreetMap via Overpass for drinking-water and toilet nodes
within a given radius of a GPX track.

Usage:
    python3 query_osm_amenities.py                          # defaults below
    python3 query_osm_amenities.py --radius 150 --step 100  # wider search
    python3 query_osm_amenities.py --query-only             # print query, don't run

Requirements: standard library only (no pip installs needed)

Outputs:
    osm_amenities.json   - raw Overpass response
    osm_amenities.csv    - cleaned table ready to import into your POI workflow
"""

import xml.etree.ElementTree as ET
import math, json, csv, argparse, sys, time
import urllib.request, urllib.parse

# ── Config ────────────────────────────────────────────────────────────────────
GPX_FILE  = 'gerry-connolly-cross-county-trail.gpx'
RADIUS_M  = 100      # search radius around trail (meters)
STEP_M    = 80       # thin track to one point per this distance (meters)
                     # must be < RADIUS_M to guarantee no gaps in coverage
AMENITIES = ['drinking_water', 'toilets']
OVERPASS_URL = 'https://overpass-api.de/api/interpreter'
TIMEOUT   = 90       # seconds

# ── GPX parsing ───────────────────────────────────────────────────────────────
def parse_gpx(path):
    NS = 'http://www.topografix.com/GPX/1/1'
    root = ET.parse(path).getroot()
    return [[float(p.attrib['lat']), float(p.attrib['lon'])]
            for p in root.iter(f'{{{NS}}}trkpt')]

def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin(math.radians(lat2-lat1)/2)**2
         + math.cos(p1)*math.cos(p2)*math.sin(math.radians(lon2-lon1)/2)**2)
    return 2*R*math.asin(math.sqrt(a))

def thin_track(pts, step_m):
    out = [pts[0]]
    for p in pts[1:]:
        if haversine_m(*out[-1], *p) >= step_m:
            out.append(p)
    return out

# ── Trail-mile lookup (nearest point along track) ────────────────────────────
def build_mile_index(pts):
    """Returns list of (lat, lon, cumulative_miles)."""
    index = [(pts[0][0], pts[0][1], 0.0)]
    cum = 0.0
    for i in range(1, len(pts)):
        cum += haversine_m(*pts[i-1], *pts[i]) / 1609.34
        index.append((pts[i][0], pts[i][1], cum))
    return index

def nearest_mile(mile_index, lat, lon):
    best_d, best_mi = float('inf'), 0.0
    for mlat, mlon, mi in mile_index:
        d = haversine_m(lat, lon, mlat, mlon)
        if d < best_d:
            best_d, best_mi = d, mi
    return round(best_mi, 2), round(best_d, 1)

# ── Overpass query ────────────────────────────────────────────────────────────
def build_query(thinned, radius, amenities, timeout):
    coord_str = ','.join(f'{p[0]},{p[1]}' for p in thinned)
    nodes = '\n'.join(
        f'  node["amenity"="{a}"](around:{radius},{coord_str});'
        for a in amenities
    )
    return f'[out:json][timeout:{timeout}];\n(\n{nodes}\n);\nout body;\n'

def run_query(query, url, timeout):
    data = urllib.parse.urlencode({'data': query}).encode()
    req = urllib.request.Request(url, data=data,
          headers={'User-Agent': 'CCT-trail-guide/1.0 (trail amenity research)'})
    print(f"Querying Overpass ({len(query):,} char query)...", flush=True)
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout+30) as resp:
        raw = resp.read().decode()
    print(f"  Done in {time.time()-t0:.1f}s — {len(raw):,} bytes received")
    return json.loads(raw)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gpx',        default=GPX_FILE)
    ap.add_argument('--radius',     type=int, default=RADIUS_M)
    ap.add_argument('--step',       type=int, default=STEP_M)
    ap.add_argument('--query-only', action='store_true')
    args = ap.parse_args()

    print(f"Parsing {args.gpx}...")
    pts = parse_gpx(args.gpx)
    print(f"  {len(pts)} track points")

    # Reverse so mile 0 = Occoquan (southern end), matching project convention
    if pts[0][0] > pts[-1][0]:   # if first point is further north, reverse
        pts = pts[::-1]
        print(f"  Reversed track direction: mile 0 = Occoquan (south)")

    thinned = thin_track(pts, args.step)
    print(f"  Thinned to {len(thinned)} points at ~{args.step}m spacing")

    mile_index = build_mile_index(pts)
    total_mi = mile_index[-1][2]
    print(f"  Total trail length: {total_mi:.2f} miles")

    query = build_query(thinned, args.radius, AMENITIES, TIMEOUT)

    if args.query_only:
        print("\n── OVERPASS QUERY ──────────────────────────────────────────────────")
        print(query)
        print("────────────────────────────────────────────────────────────────────")
        print("\nPaste this at https://overpass-turbo.eu to run interactively")
        return

    # Run query
    try:
        result = run_query(query, OVERPASS_URL, TIMEOUT)
    except Exception as e:
        print(f"\nError contacting Overpass: {e}")
        print("You can run the query manually at https://overpass-turbo.eu")
        print("Saving query to overpass_query.txt...")
        with open('overpass_query.txt', 'w') as f:
            f.write(query)
        return

    elements = result.get('elements', [])
    print(f"\nFound {len(elements)} amenity nodes within {args.radius}m of trail")

    # Enrich with trail mile + distance
    rows = []
    for el in elements:
        tags = el.get('tags', {})
        mi, dist_m = nearest_mile(mile_index, el['lat'], el['lon'])
        rows.append({
            'osm_id':    el['id'],
            'amenity':   tags.get('amenity', ''),
            'name':      tags.get('name', ''),
            'trail_mile': mi,
            'dist_m':    dist_m,
            'lat':       el['lat'],
            'lon':       el['lon'],
            'access':    tags.get('access', ''),
            'fee':       tags.get('fee', ''),
            'opening_hours': tags.get('opening_hours', ''),
            'operator':  tags.get('operator', ''),
            'note':      tags.get('note', tags.get('description', '')),
        })

    rows.sort(key=lambda r: r['trail_mile'])

    # Print summary
    from collections import Counter
    counts = Counter(r['amenity'] for r in rows)
    for amenity, n in counts.items():
        print(f"  {amenity}: {n}")

    print("\n── Results (sorted by trail mile) ──────────────────────────────────")
    for r in rows:
        print(f"  mi {r['trail_mile']:5.2f}  {r['dist_m']:4.0f}m  "
              f"{r['amenity']:15s} {r['name'] or '(unnamed)':30s} "
              f"access={r['access'] or '?'}  fee={r['fee'] or '?'}")

    # Save outputs
    with open('osm_amenities.json', 'w') as f:
        json.dump(result, f, indent=2)
    print("\nSaved: osm_amenities.json")

    fields = list(rows[0].keys())
    with open('osm_amenities.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print("Saved: osm_amenities.csv")
    print("\nTo add to the map: import osm_amenities.csv as a new layer using")
    print("the same pattern as transit.csv (layer='amenity' in the data pipeline)")

if __name__ == '__main__':
    main()