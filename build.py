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
    return ('<div
