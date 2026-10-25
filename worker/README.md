# w4wje-live Worker

Live POTA on-air box for the W4WJE QRZ bio, plus the spot archive (`/archive`, `/archive/<id>.json|.csv`)
that the Apps Script in `apps-script/` copies to Google Drive.

**Deploys automatically.** Cloudflare Workers Builds is connected to this repo
(dashboard: w4wje-live → Settings → Builds, root directory `/worker`, watch path `worker/*`).
Any push to `main` that touches this folder runs `npx wrangler deploy`.

- `worker.js` – the Worker code
- `wrangler.toml` – the Worker's settings (KV binding `LIVE`, every-minute cron, logs).
  Change settings here, not in the dashboard, or the next deploy will undo them.

Notes:
- The cron (`scheduled` → `poll`) is the only thing that writes to KV. Page views only read it.
- The Worker only serves W4WJE. A `?call=` parameter is accepted but ignored.
