"""Builds index.html with POTA stats baked in (no JavaScript needed).
Run by GitHub Actions on a schedule. Change CALL below if needed."""
import json, os, sys, urllib.request, datetime

RECENT_COUNT = 5   # how many recent activations / hunts to show
from html import escape as e

CALL = os.environ.get("POTA_CALL", "W4WJE")
POTA = "https://pota.app/#/"

CSS = r"""<style>
  :root{
    --bg:#0F1B33; --card:rgba(255,255,255,.06); --edge:rgba(255,255,255,.14);
    --ink:#E8EEF7; --muted:#9FB0C8; --line:rgba(255,255,255,.10);
    --cyan:#29C4C4; --blue:#2F6FD6; --yellow:#F2E24A; --orange:#F28A2E; --red:#E2363A;
    --cw:#29C4C4; --data:#2F6FD6; --phone:#F28A2E;
  }
  *{box-sizing:border-box}
  html{color-scheme:dark}
  body{margin:0;padding:0;background:var(--bg);color:var(--ink);
    font-family:Overpass,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;font-size:16px;line-height:1.5}
  a{color:inherit}
  .wrap{max-width:960px;margin:0 auto}

  .sign{background:var(--card);border:1px solid var(--edge);border-radius:16px;overflow:hidden}
  .sign::before{content:"";display:block;height:6px;
    background:linear-gradient(90deg,#1B2A6B,var(--blue),var(--cyan),var(--yellow),var(--orange),var(--red))}
  .sign-inner{padding:22px 24px;display:grid;grid-template-columns:auto 1fr;gap:18px 22px;align-items:center}
  .avatar{width:80px;height:80px;border-radius:50%;border:3px solid var(--cyan);object-fit:cover;background:#1B2A6B}
  .call{font-size:46px;font-weight:800;letter-spacing:.06em;line-height:1;text-decoration:none;display:inline-block;color:#fff}
  .call:hover,.call:focus-visible{text-decoration:underline;text-underline-offset:6px;text-decoration-color:var(--cyan)}
  .who{margin-top:8px;color:var(--muted)}
  .big{grid-column:1/-1;display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
  .big>div{background:rgba(0,0,0,.25);border-radius:12px;padding:14px 16px}
  .big>div:nth-child(1) .num{color:var(--cyan)}
  .big>div:nth-child(2) .num{color:var(--yellow)}
  .big>div:nth-child(3) .num{color:var(--orange)}
  .num{font-size:40px;font-weight:800;line-height:1;font-variant-numeric:tabular-nums;color:#fff}
  .lbl{font-size:14px;color:var(--muted);margin-top:6px}

  .pair{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}
  .panel{background:var(--card);border:1px solid var(--edge);border-radius:16px;padding:18px 22px}
  .panel h2{margin:0 0 10px;font-size:20px;font-weight:800;color:var(--cyan)}
  .panel:nth-child(2) h2{color:var(--orange)}
  .panel .stats{display:flex;gap:28px;flex-wrap:wrap}
  .panel .num{font-size:30px}

  .recent{margin-top:14px;background:var(--card);border:1px solid var(--edge);border-radius:16px;padding:18px 22px}
  .recent-head{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px;margin-bottom:8px}
  .recent h2{margin:0;font-size:20px;font-weight:800;color:var(--yellow)}
  .legend{display:flex;gap:14px;font-size:14px;color:var(--muted)}
  .legend span::before{content:"";display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-1px;background:var(--c)}

  .act{display:grid;grid-template-columns:110px 104px 1fr 150px 56px;gap:14px;align-items:center;
    padding:10px 0;border-top:1px solid var(--line)}
  .date{color:var(--muted);font-size:15px;font-variant-numeric:tabular-nums}
  .ref{display:inline-block;background:var(--blue);color:#fff;font-weight:700;font-size:14px;
    padding:3px 10px;border-radius:999px;text-decoration:none;text-align:center;font-variant-numeric:tabular-nums}
  .ref:hover,.ref:focus-visible{background:var(--orange)}
  .park{min-width:0}
  .park a{text-decoration:none;font-weight:600;display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#fff}
  .park a:hover{text-decoration:underline}
  .loc{font-size:14px;color:var(--muted)}
  .bar{display:flex;height:10px;border-radius:6px;overflow:hidden;background:var(--line)}
  .bar i{display:block;height:100%}
  .total{text-align:right;font-weight:800;font-size:20px;font-variant-numeric:tabular-nums;color:#fff}

  .foot{margin-top:12px;font-size:13px;color:var(--muted);text-align:right}
  .msg{background:var(--card);border:1px solid var(--edge);border-radius:16px;padding:24px;text-align:center;color:var(--muted)}
  .msg a{color:var(--cyan)}
  a:focus-visible{outline:3px solid var(--yellow);outline-offset:2px;border-radius:4px}

  @media (max-width:640px){
    .call{font-size:34px}
    .num{font-size:30px}
    .big,.pair{grid-template-columns:1fr}
    .act{grid-template-columns:auto 1fr auto;grid-template-areas:"ref park total" "date date bar"}
    .act .refcell{grid-area:ref}.act .park{grid-area:park}.act .total{grid-area:total}
    .act .date{grid-area:date}.act .bar{grid-area:bar;align-self:center}
  }

  .tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-top:14px}
  .tile{background:var(--card);border:1px solid var(--edge);border-radius:14px;padding:14px 16px}
  .tile .num{font-size:30px}
  .tile .sub{font-size:13px;color:var(--muted);margin-top:2px}
  .hunt{display:grid;grid-template-columns:110px 120px 1fr auto;gap:14px;align-items:center;padding:10px 0;border-top:1px solid var(--line)}
  .hcall{font-weight:800;color:#fff;letter-spacing:.03em}
  .tag{display:inline-block;font-size:13px;color:var(--muted);border:1px solid var(--edge);border-radius:999px;padding:1px 9px;margin-left:6px}
  @media (max-width:640px){ .hunt{grid-template-columns:auto 1fr;} .hunt .date{grid-column:1/-1} }

  .mapcard{margin-top:14px;background:var(--card);border:1px solid var(--edge);border-radius:16px;padding:18px 22px}
  .mapcard svg{display:block;width:100%;height:auto;border-radius:12px;margin-top:6px}
  .mapcard svg text{font-family:Overpass,"Segoe UI",Arial,sans-serif}
  .pulse{transform-box:fill-box;transform-origin:center;animation:pulse 2.4s ease-out infinite}
  @keyframes pulse{from{transform:scale(1);opacity:.9}to{transform:scale(4);opacity:0}}
  @media (prefers-reduced-motion:reduce){.pulse{animation:none}}
</style>"""

def get_profile():
    req = urllib.request.Request(
        "https://api.pota.app/profile/" + CALL,
        headers={"User-Agent": "pota-stats page for " + CALL, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def n(v):
    try: return int(v)
    except (TypeError, ValueError): return 0

def f(v): return f"{n(v):,}"

MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
def nice_date(s):
    s = str(s or "")
    try:
        y, m, d = s[:10].split("-")
        return f"{MONTHS[int(m)-1]} {int(d)}, {y}"
    except Exception:
        return s

def stat(v, label):
    return f'<div><div class="num">{f(v)}</div><div class="lbl">{e(label)}</div></div>'

def other_calls(oc):
    if not oc: return ""
    if isinstance(oc, str): items = oc.replace(",", " ").split()
    elif isinstance(oc, dict): items = list(oc.values())
    else: items = list(oc)
    out = []
    for x in items:
        if isinstance(x, str): out.append(x)
        elif isinstance(x, dict): out.append(x.get("callsign") or x.get("call") or "")
    out = [x for x in out if x]
    return "Also " + ", ".join(out) if out else ""

def pick(d, *keys):
    for k in keys:
        if isinstance(d, dict) and d.get(k) not in (None, ""):
            return d.get(k)
    return None

def tile(value, label, sub=""):
    return (f'<div class="tile"><div class="num">{e(str(value))}</div>'
            f'<div class="lbl">{e(label)}</div>' + (f'<div class="sub">{e(sub)}</div>' if sub else '') + '</div>')

def numbers(p, extra=""):
    s = p.get("stats") or {}
    act, hunt = s.get("activator") or {}, s.get("hunter") or {}
    acts, parks, aq = n(act.get("activations")), n(act.get("parks")), n(act.get("qsos"))
    hp, hq = n(hunt.get("parks")), n(hunt.get("qsos"))
    out = []
    if acts: out.append(tile(f"{aq/acts:.0f}", "QSOs per activation", "career average"))
    out.append(tile(f(aq + hq), "Total POTA QSOs", "activator + hunter"))
    recent = (p.get("recent_activity") or {}).get("activations") or []
    if recent:
        cw = sum(n(a.get("cw")) for a in recent); tot = sum(n(a.get("cw"))+n(a.get("data"))+n(a.get("phone")) for a in recent) or 1
        out.append(tile(f"{cw/tot*100:.0f}%", "CW lately", f"of QSOs in last {len(recent)} activations"))
    return '<div class="tiles">' + "".join(out) + extra + '</div>'

def hunted(p):
    """Recently hunted stations, if pota.app includes them in the public profile."""
    ra = p.get("recent_activity") or {}
    lst = None
    for k in ("hunter_qsos", "hunterQsos", "hunted", "hunts", "hunter", "qsos"):
        if isinstance(ra.get(k), list) and ra.get(k):
            lst = ra[k]; break
    if not lst:
        for k, v in ra.items():
            if k != "activations" and isinstance(v, list) and v and isinstance(v[0], dict):
                lst = v; break
    if not lst:
        return ""
    rows = []
    for q in lst[:RECENT_COUNT]:
        callsign = pick(q, "activator", "activatorCallsign", "worked", "callsign", "call") or ""
        ref = pick(q, "reference", "ref") or ""
        pname = pick(q, "park", "name", "parkName", "park_name") or ""
        band, mode = pick(q, "band") or "", pick(q, "mode") or ""
        url = POTA + "park/" + e(str(ref))
        rows.append(
            f'<div class="hunt"><div class="date">{e(nice_date(pick(q, "qso_date", "date", "qsoDate") or ""))}</div>'
            f'<div class="hcall">{e(str(callsign))}</div>'
            f'<div class="park">' + (f'<a href="{url}" target="_blank" rel="noopener">{e(str(ref))} {e(str(pname))}</a>' if ref else '') + '</div>'
            f'<div>' + "".join(f'<span class="tag">{e(str(t))}</span>' for t in (band, mode) if t) + '</div></div>')
    return ('<div class="recent"><div class="recent-head"><h2 style="color:var(--cyan)">Recently hunted</h2></div>'
            + "".join(rows) + '</div>')

# ------------------------------------------------------------------ maps
import csv, io, math, re, time

HOME = (38.84, -77.28)          # Fairfax County, VA (lat, lon) - map center + distances
GEO_US = "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
GEO_WORLD = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"
ALL_PARKS = "https://pota.app/all_parks_ext.csv"
REF_RE = re.compile(r"^[A-Z0-9]{1,4}-\d{4,5}$")

def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "pota-stats page for " + CALL})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def park_db():
    """All POTA parks -> {ref: (lat, lon, name, loc)}. Cached in data/ and refreshed weekly."""
    os.makedirs("data", exist_ok=True)
    path, stamp = "data/parks.csv", "data/parks.stamp"
    try:
        old = float(open(stamp).read().strip())
    except Exception:
        old = 0
    if time.time() - old > 7 * 86400 or not os.path.exists(path):
        try:
            raw = fetch(ALL_PARKS, 120)
            open(path, "wb").write(raw)
            open(stamp, "w").write(str(time.time()))
        except Exception as ex:
            print("park list download failed:", ex)
    db = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8", errors="replace") as fh:
            for row in csv.DictReader(fh):
                try:
                    db[row["reference"].strip()] = (float(row["latitude"]), float(row["longitude"]),
                                                    row.get("name", ""), row.get("locationDesc", ""))
                except Exception:
                    pass
    return db

def park_lookup(ref, db):
    if ref in db:
        return db[ref]
    try:
        j = json.loads(fetch("https://api.pota.app/park/" + ref, 20))
        v = (float(j["latitude"]), float(j["longitude"]), j.get("name", ""), j.get("locationDesc", ""))
        db[ref] = v
        return v
    except Exception:
        return None

def read_export(fname):
    """Read a pota.app CSV export you uploaded (activated.csv / hunted.csv) -> {ref: count}."""
    out = {}
    if not os.path.exists(fname):
        return out
    with open(fname, encoding="utf-8-sig", errors="replace") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        return out
    head = [h.strip().lower() for h in rows[0]]
    cnt_col = next((i for i, h in enumerate(head) if h in ("activations", "qsos", "attempts", "count")), None)
    for r in rows[1:]:
        ref = next((c.strip() for c in r if REF_RE.match(c.strip())), None)
        if not ref:
            continue
        c = 1
        if cnt_col is not None and cnt_col < len(r):
            c = n(r[cnt_col]) or 1
        out[ref] = out.get(ref, 0) + c
    return out

def miles(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 3958.8 * 2 * math.asin(math.sqrt(h))

def destination(start, bearing_deg, dist_mi):
    la1, lo1 = math.radians(start[0]), math.radians(start[1])
    d, b = dist_mi / 3958.8, math.radians(bearing_deg)
    la2 = math.asin(math.sin(la1)*math.cos(d) + math.cos(la1)*math.sin(d)*math.cos(b))
    lo2 = lo1 + math.atan2(math.sin(b)*math.sin(d)*math.cos(la1), math.cos(d)-math.sin(la1)*math.sin(la2))
    return math.degrees(la2), (math.degrees(lo2) + 540) % 360 - 180

class Proj:
    def __init__(self, lat0, lat1, lon0, lon1, W=920, Hmin=320, Hmax=560):
        mid = math.radians((lat0 + lat1) / 2)
        self.k = max(math.cos(mid), 0.35)
        # fit aspect ratio
        def h(): return W * (lat1 - lat0) / ((lon1 - lon0) * self.k)
        if h() < Hmin:
            extra = (Hmin * (lon1 - lon0) * self.k / W - (lat1 - lat0)) / 2
            lat0, lat1 = lat0 - extra, lat1 + extra
        elif h() > Hmax:
            extra = ((lat1 - lat0) * W / (Hmax * self.k) - (lon1 - lon0)) / 2
            lon0, lon1 = lon0 - extra, lon1 + extra
        self.lat0, self.lat1, self.lon0, self.lon1 = lat0, lat1, lon0, lon1
        self.s = W / ((lon1 - lon0) * self.k)
        self.W, self.H = W, round((lat1 - lat0) * self.s)
    def xy(self, lat, lon):
        return ((lon - self.lon0) * self.k * self.s, (self.lat1 - lat) * self.s)

def geo_paths(features, P):
    out = []
    for f in features:
        g = f.get("geometry") or {}
        polys = g.get("coordinates") or []
        if g.get("type") == "Polygon":
            polys = [polys]
        d = []
        for poly in polys:
            for ring in poly:
                lons = [p[0] for p in ring]; lats = [p[1] for p in ring]
                if max(lons) < P.lon0 - 2 or min(lons) > P.lon1 + 2 or max(lats) < P.lat0 - 2 or min(lats) > P.lat1 + 2:
                    continue
                pts, last = [], None
                for lon, lat in ring:
                    x, y = P.xy(lat, lon)
                    pt = (round(x), round(y))
                    if pt != last:
                        pts.append(pt); last = pt
                if len(pts) > 2:
                    d.append("M" + "L".join(f"{x} {y}" for x, y in pts) + "Z")
        if d:
            out.append("".join(d))
    return out

def svg_map(title, points, color, P, base, rings=False, sub=""):
    """points: list of (lat, lon, size, label)"""
    W, H = P.W, P.H
    parts = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{e(title)}">',
             '<defs><filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3"/></filter>'
             '<radialGradient id="sea" cx="50%" cy="40%" r="75%"><stop offset="0" stop-color="#16294D"/><stop offset="1" stop-color="#0B1428"/></radialGradient></defs>',
             f'<rect width="{W}" height="{H}" fill="url(#sea)"/>']
    # lat/lon graticule
    step = 10 if (P.lon1 - P.lon0) > 40 else (5 if (P.lon1 - P.lon0) > 12 else 1)
    g = []
    for lon in range(int(P.lon0 // step * step), int(P.lon1) + step, step):
        x, _ = P.xy(0, lon); g.append(f"M{x:.0f} 0V{H}")
    for lat in range(int(P.lat0 // step * step), int(P.lat1) + step, step):
        _, y = P.xy(lat, 0); g.append(f"M0 {y:.0f}H{W}")
    parts.append(f'<path d="{"".join(g)}" stroke="#ffffff" stroke-opacity=".05" fill="none"/>')
    parts.append('<g fill="#1C3360" stroke="#3B5A92" stroke-width=".8" stroke-linejoin="round">' +
                 "".join(f'<path d="{d}"/>' for d in base) + '</g>')
    hx, hy = P.xy(*HOME)
    if rings:
        for r in (500, 1000, 2000, 5000):
            pts = [P.xy(*destination(HOME, b, r)) for b in range(0, 361, 4)]
            dd, prev = "", None
            for x, y in pts:   # start a new segment where the ring wraps around the map edge
                dd += ("M" if prev is None or abs(x - prev) > W / 2 else "L") + f"{x:.0f} {y:.0f}"
                prev = x
            parts.append(f'<path d="{dd}" fill="none" stroke="#F2E24A" stroke-opacity=".35" stroke-dasharray="4 6"/>')
            lx, ly = P.xy(*destination(HOME, 0, r))
            if 0 < ly < H:
                parts.append(f'<text x="{lx:.0f}" y="{ly-4:.0f}" fill="#F2E24A" fill-opacity=".7" font-size="12" text-anchor="middle">{r:,} mi</text>')
    dots, glow = [], []
    for lat, lon, size, label in points:
        x, y = P.xy(lat, lon)
        if not (-5 < x < W + 5 and -5 < y < H + 5):
            continue
        r = size
        glow.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r*2:.1f}"/>')
        dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}"><title>{e(label)}</title></circle>')
    parts.append(f'<g fill="{color}" opacity=".45" filter="url(#glow)">{"".join(glow)}</g>')
    parts.append(f'<g fill="{color}" stroke="#0B1428" stroke-width=".6">{"".join(dots)}</g>')
    parts.append(f'<circle class="pulse" cx="{hx:.1f}" cy="{hy:.1f}" r="6" fill="none" stroke="#E2363A" stroke-width="2"/>'
                 f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="5" fill="#E2363A" stroke="#fff" stroke-width="1.5"><title>Home QTH</title></circle>')
    parts.append('</svg>')
    return (f'<div class="mapcard"><div class="recent-head"><h2 style="color:{color}">{e(title)}</h2>'
            f'<div class="legend">{e(sub)}</div></div>{"".join(parts)}</div>')

def bbox(pts, pad=0.6, min_span=3):
    lats = [p[0] for p in pts] + [HOME[0]]; lons = [p[1] for p in pts] + [HOME[1]]
    lat0, lat1, lon0, lon1 = min(lats), max(lats), min(lons), max(lons)
    if lat1 - lat0 < min_span:
        c = (lat0 + lat1) / 2; lat0, lat1 = c - min_span/2, c + min_span/2
    if lon1 - lon0 < min_span:
        c = (lon0 + lon1) / 2; lon0, lon1 = c - min_span/2, c + min_span/2
    return lat0 - pad, lat1 + pad, lon0 - pad, lon1 + pad

def maps_section(p):
    """Returns (html, extra_tiles_html, names {ref: name})."""
    try:
        db = park_db()
        us = json.loads(fetch(GEO_US))["features"]
        world = [f for f in json.loads(fetch(GEO_WORLD))["features"]
                 if (f.get("properties") or {}).get("name") != "United States of America"]
    except Exception as ex:
        print("map data failed:", ex)
        return "", "", {}

    activated = read_export("activated.csv")
    hunted = read_export("hunted.csv")
    for a in ((p.get("recent_activity") or {}).get("activations") or []):
        ref = a.get("reference")
        if ref and ref not in activated:
            activated[ref] = 1
    names = {}

    def located(d):
        out = []
        for ref, c in d.items():
            v = park_lookup(ref, db)
            if v:
                names[ref] = v[2]
                out.append((v[0], v[1], c, ref, v[2], v[3]))
        return out

    A, Hh = located(activated), located(hunted)
    html, tiles = [], []

    if A:
        P = Proj(*bbox([(a[0], a[1]) for a in A]))
        base = geo_paths(world, P) + geo_paths(us, P)
        pts = [(a[0], a[1], 3 + min(math.sqrt(a[2]) * 1.6, 12), f"{a[3]} {a[4]} ({a[2]})") for a in A]
        sub = f"{len(A)} parks" + (" plotted, sized by activations" if os.path.exists("activated.csv") else " from recent activations")
        html.append(svg_map("Where I activate", pts, "#F28A2E", P, base, sub=sub))

    if Hh:
        lats = [h[0] for h in Hh]; lons = [h[1] for h in Hh]
        if min(lons) < -130 or max(lons) > -50 or min(lats) < 22:
            P = Proj(-56, 78, -170, 190, Hmin=300, Hmax=520)
            base = geo_paths(world, P) + geo_paths(us, P)
        else:
            P = Proj(*bbox(list(zip(lats, lons)), pad=1.5))
            base = geo_paths(world, P) + geo_paths(us, P)
        pts = [(h[0], h[1], 2.2, f"{h[3]} {h[4]}") for h in Hh]
        html.append(svg_map("Parks I've hunted", pts, "#29C4C4", P, base, rings=True,
                            sub=f"{len(Hh):,} parks, rings from home"))
        far = max(Hh, key=lambda h: miles(HOME, h))
        tiles.append(tile(f"{miles(HOME, far):,.0f} mi", "Farthest park hunted", f"{far[3]} {far[5]}"))
        tiles.append(tile(str(len({h[5] for h in Hh if h[5]})), "Places hunted", "states / provinces / DX"))
        prefixes = {h[3].split("-")[0] for h in Hh}
        tiles.append(tile(str(len(prefixes)), "POTA programs hunted", "countries / entities"))

    return "".join(html), "".join(tiles), names

def build(p):
    map_html, map_tiles, NAMES = maps_section(p)
    s = p.get("stats") or {}
    act = s.get("activator") or {}
    hunt = s.get("hunter") or {}
    call = p.get("callsign") or CALL
    who = ", ".join(x for x in [p.get("name"), p.get("qth")] if x)
    also = other_calls(p.get("other_callsigns"))
    avatar = (f'<img class="avatar" src="https://www.gravatar.com/avatar/{e(p["gravatar"])}?s=168&amp;d=mp" alt="">'
              if p.get("gravatar") else '<div class="avatar"></div>')
    prof = POTA + "profile/" + e(call)

    if s.get("awards") is not None or s.get("endorsements") is not None:
        p2 = ("Awards", stat(s.get("awards"), "Awards") + stat(s.get("endorsements"), "Endorsements"))
    else:
        at = s.get("attempts") or {}
        p2 = ("Attempts", stat(at.get("activations"), "Attempts") + stat(at.get("parks"), "Parks"))

    rows = []
    for a in (((p.get("recent_activity") or {}).get("activations") or [])[:RECENT_COUNT]):
        cw, dt, ph = n(a.get("cw")), n(a.get("data")), n(a.get("phone"))
        total = n(a.get("total")) or (cw + dt + ph)
        tot = (cw + dt + ph) or 1
        seg = "".join(f'<i style="width:{c/tot*100:.1f}%;background:var({v})"></i>'
                      for c, v in [(cw, "--cw"), (dt, "--data"), (ph, "--phone")] if c)
        ref = str(a.get("reference") or a.get("ref") or "")
        url = POTA + "park/" + e(ref)
        name = a.get("name") or a.get("park") or a.get("parkName") or a.get("park_name") or NAMES.get(ref) or ref
        loc = a.get("locationDesc") or a.get("location") or ""
        rows.append(
            f'<div class="act"><div class="date">{e(nice_date(a.get("date")))}</div>'
            f'<div class="refcell"><a class="ref" href="{url}" target="_blank" rel="noopener">{e(ref)}</a></div>'
            f'<div class="park"><a href="{url}" target="_blank" rel="noopener" title="{e(name)}">{e(name)}</a>'
            f'<div class="loc">{e(loc)}</div></div>'
            f'<div class="bar" title="CW {cw}, Data {dt}, Phone {ph}">{seg}</div>'
            f'<div class="total">{f(total)}</div></div>')
    if not rows:
        rows.append('<div class="loc">No recent activations listed on pota.app.</div>')

    updated = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(call)} POTA stats</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Overpass:wght@400;600;800&display=swap" rel="stylesheet">
{CSS}
</head>
<body>
<div class="wrap">
<div class="sign"><div class="sign-inner">
{avatar}
<div>
<a class="call" href="{prof}" target="_blank" rel="noopener">{e(call)}</a>
{f'<div class="who">{e(who)}</div>' if who else ''}
{f'<div class="who" style="font-size:14px;margin-top:2px">{e(also)}</div>' if also else ''}
</div>
<div class="big">{stat(act.get("activations"), "Activations")}{stat(act.get("parks"), "Parks activated")}{stat(act.get("qsos"), "Activator QSOs")}</div>
</div></div>

<div class="pair">
<div class="panel"><h2>Hunting</h2><div class="stats">{stat(hunt.get("parks"), "Parks hunted")}{stat(hunt.get("qsos"), "Hunter QSOs")}</div></div>
<div class="panel"><h2>{p2[0]}</h2><div class="stats">{p2[1]}</div></div>
</div>

{numbers(p, map_tiles)}

{map_html}

<div class="recent">
<div class="recent-head"><h2>Recent activations</h2>
<div class="legend"><span style="--c:var(--cw)">CW</span><span style="--c:var(--data)">Data</span><span style="--c:var(--phone)">Phone</span></div></div>
{''.join(rows)}
</div>

{hunted(p)}

<div class="foot">From <a href="https://pota.app" target="_blank" rel="noopener">pota.app</a>, updated {updated}</div>
</div>
</body>
</html>
"""

if __name__ == "__main__":
    try:
        profile = get_profile()
    except Exception as ex:
        print("Could not fetch POTA profile, keeping the last page:", ex)
        sys.exit(1)
    with open("profile.json", "w", encoding="utf-8") as fh:
        json.dump(profile, fh, indent=1)
    with open("index.html", "w", encoding="utf-8") as fh:
        fh.write(build(profile))
    print("index.html updated")
