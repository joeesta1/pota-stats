// W4WJE live POTA status - server-rendered, no JavaScript in the page (works inside QRZ bio)
const API = "https://api.pota.app";
const POTA = "https://pota.app/#/park/";
const TTL = 60; // seconds

const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const base = c => String(c || "").toUpperCase().split("/").sort((a, b) => b.length - a.length)[0];
const utc = s => { if (!s) return null; s = String(s); if (!/[zZ]|[+-]\d\d:?\d\d$/.test(s)) s += "Z"; const d = new Date(s); return isNaN(d) ? null : d; };
const hhmm = d => d ? d.toISOString().slice(11, 16) : "";
const ago = d => { if (!d) return ""; const m = Math.max(0, Math.round((Date.now() - d) / 60000)); return m < 1 ? "just now" : m < 60 ? m + " min ago" : Math.floor(m / 60) + " h " + (m % 60) + " min ago"; };
const mhz = k => { const n = parseFloat(k); if (!n) return esc(k); return n >= 1000 ? (n / 1000).toFixed(3) : n.toFixed(1); };
const band = k => { const f = parseFloat(k) / 1000; const B = [[1.8,2,"160m"],[3.5,4,"80m"],[5.3,5.5,"60m"],[7,7.3,"40m"],[10.1,10.15,"30m"],[14,14.35,"20m"],[18.068,18.168,"17m"],[21,21.45,"15m"],[24.89,24.99,"12m"],[28,29.7,"10m"],[50,54,"6m"],[144,148,"2m"]]; for (const b of B) if (f >= b[0] && f <= b[1]) return b[2]; return ""; };
const isRbn = s => /rbn|skimmer|-#/i.test((s.source || "") + " " + (s.spotter || "") + " " + (s.comments || ""));

async function j(path, ttl = TTL) {
  const r = await fetch(API + path, { cf: { cacheTtl: ttl, cacheEverything: true }, headers: { "User-Agent": "W4WJE-live-status" } });
  if (!r.ok) throw new Error(r.status);
  return r.json();
}

const CSS = `
:root{--card:rgba(255,255,255,.06);--edge:rgba(255,255,255,.14);--ink:#E8EEF7;--muted:#9FB0C8;--line:rgba(255,255,255,.10);
--cyan:#29C4C4;--blue:#2F6FD6;--yellow:#F2E24A;--orange:#F28A2E;--red:#E2363A}
*{box-sizing:border-box}
html,body{background:transparent;margin:0}
body.solo{background:#0F1B33;padding:16px}
body.solo .box{max-width:920px;margin:0 auto}
body:not(.solo) .box{min-height:calc(100vh - 2px)}
body{color:var(--ink);font-family:Overpass,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;font-size:15px;line-height:1.4}
a{color:inherit}
.box{background:#16233F;border:1px solid var(--edge);border-radius:16px;overflow:hidden}
.box::before{content:"";display:block;height:6px;background:linear-gradient(90deg,#1B2A6B,var(--blue),var(--cyan),var(--yellow),var(--orange),var(--red))}
.inner{padding:14px 18px}
.top{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
.badge{display:inline-flex;align-items:center;gap:10px;font-weight:800;letter-spacing:.08em;font-size:15px;padding:6px 14px;border-radius:999px;background:rgba(0,0,0,.3);color:var(--muted);border:1px solid var(--edge)}
.badge i{width:10px;height:10px;border-radius:50%;background:var(--muted);display:inline-block}
.live .badge{color:#fff;background:rgba(226,54,58,.18);border-color:rgba(226,54,58,.7)}
.live .badge i{background:var(--red);animation:ping 1.6s ease-out infinite}
@keyframes ping{0%{box-shadow:0 0 0 0 rgba(226,54,58,.7)}100%{box-shadow:0 0 0 10px rgba(226,54,58,0)}}
@media (prefers-reduced-motion:reduce){.live .badge i{animation:none}}
.upd{font-size:12px;color:var(--muted)}
.park{display:grid;grid-template-columns:1fr auto;gap:6px 16px;align-items:end;margin-top:12px}
.ref{display:inline-block;background:var(--blue);color:#fff;font-weight:700;font-size:14px;padding:2px 10px;border-radius:999px;text-decoration:none;margin-right:8px;vertical-align:2px}
.ref:hover{background:var(--orange)}
.pname{font-size:22px;font-weight:800;color:#fff;line-height:1.2}
.loc{color:var(--muted);font-size:14px;margin-top:2px}
.freq{text-align:right}
.freq .f{font-size:28px;font-weight:800;color:var(--yellow);font-variant-numeric:tabular-nums;line-height:1}
.freq .m{font-size:14px;color:var(--muted);margin-top:4px}
.mode{display:inline-block;font-size:12px;font-weight:700;border-radius:999px;padding:1px 8px;margin-left:6px;border:1px solid var(--edge);color:var(--ink)}
.sp-head{margin:14px 0 4px;font-size:13px;font-weight:800;color:var(--cyan);letter-spacing:.04em;text-transform:uppercase}
.spots{max-height:110px;overflow:auto}
.sp{display:grid;grid-template-columns:52px 112px 90px 1fr;gap:10px;padding:5px 0;border-top:1px solid var(--line);font-size:13px;align-items:baseline}
.sp .t{color:var(--muted);font-variant-numeric:tabular-nums}
.sp .fq{font-weight:700;font-variant-numeric:tabular-nums}
.sp .by{font-weight:700;color:#fff;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sp .c{color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.rbn,.sp .by.rbn{color:var(--orange);font-weight:700}
.sp .x{font-size:11px;color:var(--muted);font-weight:600}
.sum{font-size:13px;color:var(--muted);margin:0 0 6px}.sum b{color:var(--ink)}.sum b.rbn{color:var(--orange)}
.sub{font-size:11px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:var(--orange);padding:6px 0 2px;border-top:1px solid var(--line)}
.recent .pname{font-size:20px}
.stats{text-align:right}
.stats .n{font-size:26px;font-weight:800;color:var(--orange);line-height:1}
.stats .l{font-size:13px;color:var(--muted)}
.msg{color:var(--muted);margin-top:10px}
@media (max-width:560px){.park{grid-template-columns:1fr}.freq,.stats{text-align:left}.sp{grid-template-columns:46px 104px 1fr}.sp .c{display:none}}
`;

function page(cls, status, inner, call, solo) {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="${TTL}"><title>${esc(call)} On the Air</title>
<link href="https://fonts.googleapis.com/css2?family=Overpass:wght@400;600;800&display=swap" rel="stylesheet">
<style>${CSS}</style></head><body${solo ? ' class="solo"' : ""}>
<div class="box ${cls}"><div class="inner"><div class="top"><span class="badge"><i></i><span>${status}</span></span>
<span class="upd">pota.app · checked ${hhmm(new Date())}z</span></div>${inner}</div></div></body></html>`;
}

async function render(call, solo) {
  let spots;
  try { spots = await j("/spot/activator", 30); }
  catch (e) { return page("", "POTA STATUS", '<div class="msg">Couldn’t reach pota.app right now. Retrying shortly.</div>', call, solo); }
  const mine = (spots || []).filter(s => base(s.activator) === call).sort((x, y) => (utc(y.spotTime) || 0) - (utc(x.spotTime) || 0));

  if (mine.length) {
    const s = mine[0];
    const [p, c] = await Promise.all([
      j("/park/" + encodeURIComponent(s.reference), 86400).catch(() => ({})),
      j("/spot/comments/" + encodeURIComponent(s.activator) + "/" + encodeURIComponent(s.reference), 30).catch(() => [])
    ]);
    let hist = Array.isArray(c) && c.length ? c : mine;
    hist = hist.slice().sort((x, y) => (utc(y.spotTime) || 0) - (utc(x.spotTime) || 0));
    // split hunters vs RBN; merge repeat RBN reports (same skimmer, same ~1 kHz)
    const hunters = hist.filter(h => !isRbn(h));
    const rbnAll = hist.filter(isRbn);
    const rbnMap = new Map();
    for (const h of rbnAll) {
      const k = String(h.spotter || "").toUpperCase() + "|" + Math.round(parseFloat(h.frequency) || 0);
      const g = rbnMap.get(k);
      if (g) g.n++; else rbnMap.set(k, { h, n: 1 }); // hist is newest-first, so first seen = newest
    }
    const rbn = [...rbnMap.values()];
    const skimmers = new Set(rbnAll.map(h => String(h.spotter || "").toUpperCase())).size;
    const bands = [...new Set(hist.map(h => band(h.frequency)).filter(Boolean))];
    const row = (h, n) => `<div class="sp"><div class="t">${hhmm(utc(h.spotTime))}z</div><div class="fq">${mhz(h.frequency)}<span class="mode">${esc(h.mode)}</span></div><div class="by${isRbn(h) ? " rbn" : ""}" title="${esc(h.spotter)}">${esc(h.spotter)}${n > 1 ? ` <span class="x">×${n}</span>` : ""}</div><div class="c" title="${esc(h.comments)}">${esc(h.comments)}</div></div>`;
    const rows = hunters.slice(0, 25).map(h => row(h, 1)).join("") +
      (hunters.length && rbn.length ? '<div class="sub">RBN skimmers</div>' : "") +
      rbn.slice(0, 25).map(g => row(g.h, g.n)).join("");
    const plural = (n, w) => n + " " + w + (n === 1 ? "" : "s");
    const summary = `<div class="sum"><b>${plural(hunters.length, "hunter spot")}</b> · <b class="rbn">${rbnAll.length} RBN</b>${rbnAll.length ? " from " + plural(skimmers, "skimmer") : ""}${bands.length ? " · heard on " + esc(bands.join(", ")) : ""}</div>`;
    const name = (p && p.name) || s.name || s.parkName || "";
    const loc = (p && p.locationDesc) || s.locationDesc || "";
    const inner = `<div class="park"><div><div class="pname"><a class="ref" href="${POTA}${esc(s.reference)}" target="_blank" rel="noopener">${esc(s.reference)}</a>${esc(name)}</div>
<div class="loc">${esc(loc)}${s.grid6 || s.grid4 ? " · " + esc(s.grid6 || s.grid4) : ""}</div></div>
<div class="freq"><div class="f">${mhz(s.frequency)} <span style="font-size:15px;color:var(--muted)">MHz</span></div>
<div class="m">${esc(band(s.frequency))}<span class="mode">${esc(s.mode)}</span> · spotted ${ago(utc(s.spotTime))}</div></div></div>
<div class="sp-head">Spots this activation <span style="color:var(--muted);font-weight:400;text-transform:none">· <span class="rbn">orange</span> = RBN skimmer</span></div>
${summary}
<div class="spots">${rows || '<div class="msg">No spot history yet.</div>'}</div>`;
    return page("live", "ACTIVE ON THE AIR", inner, call, solo);
  }

  let prof = {};
  try { prof = await j("/profile/" + encodeURIComponent(call), 1800); } catch (e) {}
  const a = (((prof && prof.recent_activity) || {}).activations || [])[0];
  if (!a) return page("recent", "NOT ON THE AIR", '<div class="msg">No recent activations listed on pota.app.</div>', call, solo);
  const d = String(a.date || "").slice(0, 10);
  let nice = d; try { nice = new Date(d + "T12:00:00Z").toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" }); } catch (e) {}
  const inner = `<div class="sp-head" style="margin-top:12px">Most recent activation · ${esc(nice)}</div>
<div class="park" style="margin-top:2px"><div><div class="pname"><a class="ref" href="${POTA}${esc(a.reference)}" target="_blank" rel="noopener">${esc(a.reference)}</a>${esc(a.park || a.name || "")}</div>
<div class="loc">${esc(a.location || a.locationDesc || "")}</div></div>
<div class="stats"><div class="n">${esc(a.total)}</div><div class="l">QSOs · CW ${esc(a.cw || 0)} · Data ${esc(a.data || 0)} · Phone ${esc(a.phone || 0)}</div></div></div>
<div class="msg" style="font-size:13px">This box switches to live spots automatically when ${esc(call)} is spotted on pota.app.</div>`;
  return page("recent", "NOT ON THE AIR", inner, call, solo);
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const call = (url.searchParams.get("call") || "W4WJE").toUpperCase().replace(/[^A-Z0-9\/]/g, "").slice(0, 15) || "W4WJE";
    const solo = url.searchParams.has("solo");
    const cacheKey = new Request(url.origin + "/?call=" + call + (solo ? "&solo" : ""));
    const cache = caches.default;
    let res = await cache.match(cacheKey);
    if (res) return res;
    const html = await render(call, solo);
    res = new Response(html, { headers: { "content-type": "text/html; charset=utf-8", "cache-control": "public, max-age=" + TTL } });
    ctx.waitUntil(cache.put(cacheKey, res.clone()));
    return res;
  }
};
