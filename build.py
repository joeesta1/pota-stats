"""Builds index.html with POTA stats baked in (no JavaScript needed).
Run by GitHub Actions on a schedule. Change CALL below if needed."""
import json, os, sys, urllib.request, datetime
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

def build(p):
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
    for a in ((p.get("recent_activity") or {}).get("activations") or []):
        cw, dt, ph = n(a.get("cw")), n(a.get("data")), n(a.get("phone"))
        total = n(a.get("total")) or (cw + dt + ph)
        tot = (cw + dt + ph) or 1
        seg = "".join(f'<i style="width:{c/tot*100:.1f}%;background:var({v})"></i>'
                      for c, v in [(cw, "--cw"), (dt, "--data"), (ph, "--phone")] if c)
        ref = str(a.get("reference") or a.get("ref") or "")
        url = POTA + "park/" + e(ref)
        name = a.get("name") or ref
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

<div class="recent">
<div class="recent-head"><h2>Recent activations</h2>
<div class="legend"><span style="--c:var(--cw)">CW</span><span style="--c:var(--data)">Data</span><span style="--c:var(--phone)">Phone</span></div></div>
{''.join(rows)}
</div>

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
    with open("index.html", "w", encoding="utf-8") as fh:
        fh.write(build(profile))
    print("index.html updated")
