// W4WJE live POTA status - server-rendered, no JavaScript in the page (works inside QRZ bio)
// Bindings: KV namespace as LIVE (optional; without it the worker runs stateless). Cron: * * * * *
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

// Full park name: the spot list has it ("Crawfords State Forest"); /park/ splits it into name + parktypeDesc.
const fullName = (s, p) => {
  if (s && s.name) return s.name;
  if (p && p.name) { const t = p.parktypeDesc || p.parkTypeDesc || ""; return t && !p.name.toLowerCase().includes(t.toLowerCase()) ? p.name + " " + t : p.name; }
  return (s && s.parkName) || "";
};

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
.live .badge{animation:glow 2s ease-in-out infinite}
.live .badge i{background:var(--red);animation:ping 2s ease-out infinite}
@keyframes ping{0%{box-shadow:0 0 0 0 rgba(226,54,58,.8)}70%,100%{box-shadow:0 0 0 12px rgba(226,54,58,0)}}
@keyframes glow{0%,100%{background:rgba(226,54,58,.16);border-color:rgba(226,54,58,.6);box-shadow:0 0 0 0 rgba(226,54,58,0)}
50%{background:rgba(226,54,58,.36);border-color:rgba(255,110,110,.95);box-shadow:0 0 14px 2px rgba(226,54,58,.45)}}
.yagi{display:block;margin-left:2px;margin-right:-4px;overflow:visible}
.yagi .w{opacity:.15;animation:wave 1.5s ease-out infinite}
.yagi .w2{animation-delay:.25s}.yagi .w3{animation-delay:.5s}
@keyframes wave{0%{opacity:.15}25%{opacity:1}70%,100%{opacity:.15}}
@media (prefers-reduced-motion:reduce){.live .badge,.live .badge i,.yagi .w{animation:none}.yagi .w{opacity:.8}}
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
.sp{display:grid;grid-template-columns:52px 112px 116px 1fr;gap:10px;padding:5px 0;border-top:1px solid var(--line);font-size:13px;align-items:baseline}
.sp .t{color:var(--muted);font-variant-numeric:tabular-nums}
.sp .fq{font-weight:700;font-variant-numeric:tabular-nums}
.sp .by{font-weight:700;color:#fff;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sp .c{color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.rbn,.sp .by.rbn{color:var(--orange);font-weight:700}
.sp .x{font-size:11px;color:var(--muted);font-weight:600}
.sp.self{background:rgba(41,196,196,.10);border-left:3px solid var(--cyan);padding-left:6px}
.sp.self .by{color:var(--cyan)}
.sp .tag{display:inline-block;font-size:10px;font-weight:800;letter-spacing:.06em;color:#0F1B33;background:var(--cyan);border-radius:4px;padding:0 5px;margin-right:6px;vertical-align:1px}
.sum b.selfc{color:var(--cyan)}
.sum{font-size:13px;color:var(--muted);margin:0 0 6px}.sum b{color:var(--ink)}.sum b.rbn{color:var(--orange)}
.sub{font-size:11px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:var(--orange);padding:6px 0 2px;border-top:1px solid var(--line)}
.recent .pname{font-size:20px}
.stats{text-align:right}
.stats .n{font-size:26px;font-weight:800;color:var(--orange);line-height:1}
.stats .l{font-size:13px;color:var(--muted)}
.msg{color:var(--muted);margin-top:10px}
.qrt .badge{color:#C9D3E2;background:rgba(255,255,255,.08);border-color:rgba(255,255,255,.25)}
.qrt .badge i{background:#7D8AA0}
.qrt .freq .f{color:var(--muted)}
.qrt .ref{background:#4A5A78}
@media (max-width:560px){.park{grid-template-columns:1fr}.freq,.stats{text-align:left}.sp{grid-template-columns:46px 104px 1fr}.sp .c{display:none}}
`;

// Yagi (side view: boom, mast, 4 elements, reflector longest) with 3 radio-wave arcs to the right
const YAGI = `<svg class="yagi" viewBox="0 0 64 26" width="64" height="26" aria-hidden="true">
<g stroke="#fff" stroke-linecap="round" fill="none">
<path stroke-width="1.8" d="M2 10H33"/><path stroke-width="1.6" d="M17 10V25"/>
<path stroke-width="1.6" d="M3 1.5V18.5"/><path stroke-width="1.6" d="M12 3V17"/><path stroke-width="1.6" d="M22 4.5V15.5"/><path stroke-width="1.6" d="M32 6V14"/>
</g>
<g stroke="#FF7A7A" stroke-width="2" stroke-linecap="round" fill="none">
<path class="w w1" d="M38 6Q41.5 10 38 14"/><path class="w w2" d="M44 3.2Q49.5 10 44 16.8"/><path class="w w3" d="M50 0.8Q57.5 10 50 19.2"/>
</g></svg>`;

function page(cls, status, inner, call, solo) {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="${TTL}"><title>${esc(call)} On the Air</title>
<link href="https://fonts.googleapis.com/css2?family=Overpass:wght@400;600;800&display=swap" rel="stylesheet">
<style>${CSS}</style></head><body${solo ? ' class="solo"' : ""}>
<div class="box ${cls}"><div class="inner"><div class="top"><span class="badge"><i></i><span>${status}</span>${cls === "live" ? YAGI : ""}</span>
<span class="upd">pota.app · checked ${hhmm(new Date())}z</span></div>${inner}</div></div></body></html>`;
}

async function renderStateless(call, solo) {
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
    const me = base(s.activator);
    const isSelf = h => !isRbn(h) && base(h.spotter) === me;
    const selfs = hist.filter(isSelf);
    const hunters = hist.filter(h => !isRbn(h) && !isSelf(h));
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
    const row = (h, n, self) => `<div class="sp${self ? " self" : ""}"><div class="t">${hhmm(utc(h.spotTime))}z</div><div class="fq">${mhz(h.frequency)}<span class="mode">${esc(h.mode)}</span></div><div class="by${isRbn(h) ? " rbn" : ""}" title="${esc(h.spotter)}">${self ? '<span class="tag">SELF</span>' : ""}${esc(h.spotter)}${n > 1 ? ` <span class="x">×${n}</span>` : ""}</div><div class="c" title="${esc(h.comments)}">${esc(h.comments)}</div></div>`;
    const rows = (selfs.length ? row(selfs[0], selfs.length, true) : "") +
      hunters.slice(0, 25).map(h => row(h, 1)).join("") +
      (hunters.length && rbn.length ? '<div class="sub">RBN skimmers</div>' : "") +
      rbn.slice(0, 25).map(g => row(g.h, g.n)).join("");
    const plural = (n, w) => n + " " + w + (n === 1 ? "" : "s");
    const summary = `<div class="sum"><b>${plural(hunters.length, "hunter spot")}</b> · ${selfs.length ? `<b class="selfc">${plural(selfs.length, "self-spot")}</b> · ` : ""}<b class="rbn">${rbnAll.length} RBN</b>${rbnAll.length ? " from " + plural(skimmers, "skimmer") : ""}${bands.length ? " · heard on " + esc(bands.join(", ")) : ""}</div>`;
    const name = fullName(s, p);
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

// ---------------------------------------------------------------------------
// KV-backed activation memory (binding: LIVE). A cron trigger polls every minute
// so activations are captured even when nobody is viewing the page.
//   ACTIVE  - spotted in the last 30 min and your newest self-spot isn't "QRT"
//   QRT     - your own self-spot says QRT (others' QRT comments are ignored), or
//             no spots for 30 min. Shown for 2 h with the frozen spot list.
//   ENDED   - after the 2 h hold: "NOT ON THE AIR" + last activation's spots,
//             kept until the next activation starts.
// A new activation = a spot at a different park, or 12 h+ after the last spot.
// ---------------------------------------------------------------------------
const IDLE = 30 * 60 * 1000;
const HOLD = 2 * 3600 * 1000;
const GAP = 12 * 3600 * 1000;
const MAXHIST = 400;
const KEY = call => "act:" + call;
const isQrtText = h => /\bQRT\b/i.test(h.comments || "");
const sid = h => h.spotId != null ? String(h.spotId) : [h.spotTime, h.spotter, h.frequency].join("|");
const newest = a => a.slice().sort((x, y) => (utc(y.spotTime) || 0) - (utc(x.spotTime) || 0));
const slim = h => ({ spotId: h.spotId, spotTime: h.spotTime, spotter: h.spotter, frequency: h.frequency, mode: h.mode, source: h.source, comments: h.comments });

async function poll(env, call) {
  const prev = await env.LIVE.get(KEY(call), "json");
  const spots = await j("/spot/activator", 30);
  const mine = newest((spots || []).filter(s => base(s.activator) === call));
  if (!mine.length) return { act: prev, ok: true };

  const s = mine[0];
  const sT = utc(s.spotTime);
  let act = prev ? JSON.parse(JSON.stringify(prev)) : null;
  if (!act || act.ref !== s.reference || (sT && act.last && sT - utc(act.last) > GAP)) {
    act = { activator: s.activator, ref: s.reference, hist: [] };
  }
  const [p, c] = await Promise.all([
    act.loc ? null : j("/park/" + encodeURIComponent(s.reference), 86400).catch(() => ({})),
    j("/spot/comments/" + encodeURIComponent(s.activator) + "/" + encodeURIComponent(s.reference), 30).catch(() => [])
  ]);
  if (p) { act.loc = p.locationDesc || s.locationDesc || ""; act.pname = fullName(null, p); }
  act.name = s.name || act.pname || act.name || "";
  act.activator = s.activator;
  act.grid = s.grid6 || s.grid4 || act.grid || "";
  act.freq = s.frequency; act.mode = s.mode; act.spotTime = s.spotTime;

  const map = new Map(act.hist.map(h => [sid(h), h]));
  for (const h of (Array.isArray(c) ? c : []).concat(mine)) {
    if (h.reference && h.reference !== act.ref) continue;
    map.set(sid(h), slim(h));
  }
  let hist = newest([...map.values()]);
  const top = hist.length ? utc(hist[0].spotTime) : null;
  hist = hist.filter(h => { const t = utc(h.spotTime); return t && top - t < GAP; }).slice(0, MAXHIST);
  act.hist = hist;
  act.last = hist.length ? hist[0].spotTime : s.spotTime;
  act.start = hist.length ? hist[hist.length - 1].spotTime : s.spotTime;

  if (JSON.stringify(act) !== JSON.stringify(prev)) await env.LIVE.put(KEY(call), JSON.stringify(act));
  return { act, ok: true };
}

function decide(act, now) {
  const me = base(act.activator);
  for (const h of act.hist) {
    if (!isRbn(h) && base(h.spotter) === me) {
      if (isQrtText(h)) return { state: "qrt", at: utc(h.spotTime), self: true };
      break; // newest self-spot without QRT = still (or back) on the air
    }
  }
  const lastT = utc(act.last);
  if (!lastT || now - lastT > IDLE) return { state: "qrt", at: new Date(+lastT + IDLE), self: false, lastT };
  return { state: "active" };
}

function spotBlock(act) {
  const me = base(act.activator);
  const hist = act.hist;
  const isSelf = h => !isRbn(h) && base(h.spotter) === me;
  const selfs = hist.filter(isSelf);
  const hunters = hist.filter(h => !isRbn(h) && !isSelf(h));
  const rbnAll = hist.filter(isRbn);
  const rbnMap = new Map();
  for (const h of rbnAll) {
    const k = String(h.spotter || "").toUpperCase() + "|" + Math.round(parseFloat(h.frequency) || 0);
    const g = rbnMap.get(k);
    if (g) g.n++; else rbnMap.set(k, { h, n: 1 });
  }
  const rbn = [...rbnMap.values()];
  const skimmers = new Set(rbnAll.map(h => String(h.spotter || "").toUpperCase())).size;
  const bands = [...new Set(hist.map(h => band(h.frequency)).filter(Boolean))];
  const row = (h, n, self) => `<div class="sp${self ? " self" : ""}"><div class="t">${hhmm(utc(h.spotTime))}z</div><div class="fq">${mhz(h.frequency)}<span class="mode">${esc(h.mode)}</span></div><div class="by${isRbn(h) ? " rbn" : ""}" title="${esc(h.spotter)}">${self ? '<span class="tag">SELF</span>' : ""}${esc(h.spotter)}${n > 1 ? ` <span class="x">×${n}</span>` : ""}</div><div class="c" title="${esc(h.comments)}">${esc(h.comments)}</div></div>`;
  const rows = (selfs.length ? row(selfs[0], selfs.length, true) : "") +
    hunters.slice(0, 40).map(h => row(h, 1)).join("") +
    (hunters.length && rbn.length ? '<div class="sub">RBN skimmers</div>' : "") +
    rbn.slice(0, 40).map(g => row(g.h, g.n)).join("");
  const plural = (n, w) => n + " " + w + (n === 1 ? "" : "s");
  const summary = `<div class="sum"><b>${plural(hunters.length, "hunter spot")}</b> · ${selfs.length ? `<b class="selfc">${plural(selfs.length, "self-spot")}</b> · ` : ""}<b class="rbn">${rbnAll.length} RBN</b>${rbnAll.length ? " from " + plural(skimmers, "skimmer") : ""}${bands.length ? " · heard on " + esc(bands.join(", ")) : ""}</div>`;
  return { summary, rows };
}

const parkHead = act => `<div><div class="pname"><a class="ref" href="${POTA}${esc(act.ref)}" target="_blank" rel="noopener">${esc(act.ref)}</a>${esc(act.name || "")}</div>
<div class="loc">${esc(act.loc || "")}${act.grid ? " · " + esc(act.grid) : ""}</div></div>`;

const niceDate = d => { try { return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" }); } catch (e) { return d.toISOString().slice(0, 10); } };

async function renderKV(call, solo, env) {
  let act = null, err = false;
  try { act = (await poll(env, call)).act; }
  catch (e) { err = true; try { act = await env.LIVE.get(KEY(call), "json"); } catch (e2) {} }
  if (!act || !act.hist || !act.hist.length) return err
    ? page("", "POTA STATUS", '<div class="msg">Couldn’t reach pota.app right now. Retrying shortly.</div>', call, solo)
    : renderStateless(call, solo);

  const now = Date.now();
  const d = decide(act, now);
  const { summary, rows } = spotBlock(act);
  const spotsHtml = `${summary}<div class="spots">${rows || '<div class="msg">No spot history yet.</div>'}</div>`;
  const legend = '<span style="color:var(--muted);font-weight:400;text-transform:none">· <span class="rbn">orange</span> = RBN skimmer</span>';

  if (d.state === "active" || now - d.at < HOLD) {
    const qrt = d.state === "qrt";
    const status = !qrt ? "ACTIVE ON THE AIR" : d.self ? "QRT · " + hhmm(d.at) + "z" : "QRT · last spot " + hhmm(d.lastT) + "z";
    const inner = `<div class="park">${parkHead(act)}
<div class="freq"><div class="f">${mhz(act.freq)} <span style="font-size:15px;color:var(--muted)">MHz</span></div>
<div class="m">${esc(band(act.freq))}<span class="mode">${esc(act.mode)}</span> · ${qrt ? "last spotted" : "spotted"} ${ago(utc(act.last))}</div></div></div>
<div class="sp-head">Spots this activation ${legend}</div>${spotsHtml}`;
    return page(qrt ? "qrt" : "live", status, inner, call, solo);
  }

  // Ended: keep showing the last activation until the next one starts.
  const start = utc(act.start), last = utc(act.last);
  let prof = {};
  try { prof = await j("/profile/" + encodeURIComponent(call), 1800); } catch (e) {}
  const a = (((prof && prof.recent_activity) || {}).activations || [])[0];
  const aDate = a ? String(a.date || "").slice(0, 10) : "";
  // A newer activation on pota.app that KV never saw (e.g. never spotted): show the profile view instead.
  if (a && aDate > last.toISOString().slice(0, 10) && a.reference !== act.ref) return renderStateless(call, solo);
  const match = a && a.reference === act.ref && aDate >= start.toISOString().slice(0, 10) && aDate <= last.toISOString().slice(0, 10);
  const stats = match
    ? `<div class="stats"><div class="n">${esc(a.total)}</div><div class="l">QSOs · CW ${esc(a.cw || 0)} · Data ${esc(a.data || 0)} · Phone ${esc(a.phone || 0)}</div></div>`
    : `<div class="stats"><div class="l">QSO count appears<br>after log upload</div></div>`;
  const inner = `<div class="sp-head" style="margin-top:12px">Last activation · ${esc(niceDate(start))} · ${hhmm(start)}–${hhmm(last)}z</div>
<div class="park" style="margin-top:2px">${parkHead(act)}${stats}</div>
<div class="sp-head">Spots from that activation ${legend}</div>${spotsHtml}
<div class="msg" style="font-size:13px">This box switches to live spots automatically when ${esc(call)} is spotted on pota.app.</div>`;
  return page("recent", "NOT ON THE AIR", inner, call, solo);
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const home = (env.CALL || "W4WJE").toUpperCase();
    const call = (url.searchParams.get("call") || home).toUpperCase().replace(/[^A-Z0-9\/]/g, "").slice(0, 15) || home;
    const solo = url.searchParams.has("solo");
    const cacheKey = new Request(url.origin + "/?call=" + call + (solo ? "&solo" : ""));
    const cache = caches.default;
    let res = await cache.match(cacheKey);
    if (res) return res;
    // KV memory only for the home callsign, so other ?call= lookups can't use up KV writes.
    const html = env.LIVE && call === home ? await renderKV(call, solo, env) : await renderStateless(call, solo);
    res = new Response(html, { headers: { "content-type": "text/html; charset=utf-8", "cache-control": "public, max-age=" + TTL } });
    ctx.waitUntil(cache.put(cacheKey, res.clone()));
    return res;
  },
  async scheduled(event, env, ctx) {
    if (env.LIVE) ctx.waitUntil(poll(env, (env.CALL || "W4WJE").toUpperCase()).catch(() => {}));
  }
};
