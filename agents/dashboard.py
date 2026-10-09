#!/usr/bin/env python3
"""
CyberFortress Real-Time Dashboard
Lightweight web UI for operators.

Shows:
- Platform health & mode
- Circuit breaker state
- Recent CMA-mapped actions
- Pending WhatsApp approvals
- Quick stats

Run:
  python3 -m agents.dashboard
  Then open http://localhost:8091
"""

import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from core.circuit_breaker import breaker

logger = logging.getLogger("cf_dashboard")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [DASHBOARD] %(levelname)s %(message)s")

PORT = int(os.getenv("CF_DASHBOARD_PORT", "8091"))
AUDIT_LOG = Path(os.getenv("CF_AUDIT_PATH", "./logs/cma_audit.jsonl"))
PENDING_DIR = Path(os.getenv("CF_WHATSAPP_PENDING_DIR", "./logs/whatsapp_pending"))


def _read_recent_actions(limit: int = 50) -> list:
    actions = []
    if not AUDIT_LOG.exists():
        return actions
    try:
        lines = AUDIT_LOG.read_text(encoding="utf-8").strip().splitlines()
        for line in reversed(lines[-limit:]):
            try:
                actions.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except Exception as e:
        logger.warning(f"Could not read audit log: {e}")
    return actions


def _pending_approvals() -> list:
    pending = []
    if not PENDING_DIR.exists():
        return pending
    for f in PENDING_DIR.glob("*.json"):
        decision = PENDING_DIR / f"{f.stem}.decision"
        if decision.exists():
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            data["request_id"] = f.stem
            pending.append(data)
        except Exception:
            continue
    return pending


def collect_dashboard_data() -> dict:
    actions = _read_recent_actions(40)
    pending = _pending_approvals()

    by_severity = {"CRITICAL": 0, "HIGH": 0, "INFO": 0, "MEDIUM": 0, "LOW": 0}
    for a in actions:
        sev = a.get("severity", "INFO")
        by_severity[sev] = by_severity.get(sev, 0) + 1

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "containment_live": os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "true",
        "whatsapp_enabled": os.getenv("CF_WHATSAPP_ENABLED", "false").lower() == "true",
        "identity_provider": os.getenv("CF_IDENTITY_PROVIDER", "local_linux"),
        "circuit_breaker": breaker.status(),
        "stats": {
            "total_actions_shown": len(actions),
            "pending_approvals": len(pending),
            "by_severity": by_severity,
        },
        "recent_actions": actions[:25],
        "pending_approvals": pending,
    }


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CyberFortress Dashboard</title>
<style>
  :root {
    --bg: #0f1419;
    --card: #1a2332;
    --border: #2d3a4f;
    --text: #e7ecf3;
    --muted: #8b9bb4;
    --accent: #3b82f6;
    --green: #22c55e;
    --red: #ef4444;
    --amber: #f59e0b;
    --purple: #a78bfa;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    line-height: 1.5;
  }
  header {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border-bottom: 1px solid var(--border);
    padding: 1rem 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.75rem;
  }
  header h1 {
    font-size: 1.25rem;
    font-weight: 700;
    letter-spacing: 0.02em;
  }
  header h1 span { color: var(--accent); }
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.25rem 0.65rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
  }
  .badge.live { background: rgba(34,197,94,0.15); color: var(--green); }
  .badge.dry { background: rgba(245,158,11,0.15); color: var(--amber); }
  .badge.open { background: rgba(239,68,68,0.15); color: var(--red); }
  .badge.closed { background: rgba(34,197,94,0.15); color: var(--green); }
  .container { max-width: 1400px; margin: 0 auto; padding: 1.25rem; }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
    margin-bottom: 1.25rem;
  }
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.15rem;
  }
  .card h3 {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--muted);
    margin-bottom: 0.35rem;
  }
  .card .value {
    font-size: 1.5rem;
    font-weight: 700;
  }
  .card .sub { font-size: 0.8rem; color: var(--muted); margin-top: 0.15rem; }
  .panels {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }
  @media (max-width: 900px) { .panels { grid-template-columns: 1fr; } }
  .panel {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
  }
  .panel-header {
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--border);
    font-weight: 600;
    font-size: 0.9rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .panel-body { max-height: 420px; overflow-y: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
  th, td { padding: 0.55rem 0.85rem; text-align: left; border-bottom: 1px solid var(--border); }
  th { color: var(--muted); font-weight: 600; font-size: 0.7rem; text-transform: uppercase; position: sticky; top: 0; background: var(--card); }
  tr:hover td { background: rgba(255,255,255,0.02); }
  .sev { font-weight: 600; font-size: 0.75rem; }
  .sev.CRITICAL { color: var(--red); }
  .sev.HIGH { color: var(--amber); }
  .sev.INFO, .sev.LOW, .sev.MEDIUM { color: var(--muted); }
  .empty { padding: 2rem; text-align: center; color: var(--muted); font-size: 0.9rem; }
  footer {
    text-align: center;
    padding: 1.5rem;
    color: var(--muted);
    font-size: 0.75rem;
  }
  .refresh { font-size: 0.75rem; color: var(--muted); }
  .dot {
    width: 8px; height: 8px; border-radius: 50%;
    display: inline-block; margin-right: 4px;
  }
  .dot.on { background: var(--green); box-shadow: 0 0 6px var(--green); }
  .dot.off { background: var(--muted); }
</style>
</head>
<body>
<header>
  <h1>CYBER<span>FORTRESS</span> Dashboard</h1>
  <div style="display:flex;gap:0.5rem;align-items:center;flex-wrap:wrap;">
    <span id="mode-badge" class="badge dry">DRY-RUN</span>
    <span id="breaker-badge" class="badge closed">BREAKER CLOSED</span>
    <span class="refresh">Updated <span id="updated">—</span></span>
  </div>
</header>

<div class="container">
  <div class="grid">
    <div class="card">
      <h3>Mode</h3>
      <div class="value" id="mode-val">—</div>
      <div class="sub" id="wa-val">WhatsApp: —</div>
    </div>
    <div class="card">
      <h3>Circuit Breaker</h3>
      <div class="value" id="breaker-val">—</div>
      <div class="sub" id="breaker-reason">—</div>
    </div>
    <div class="card">
      <h3>Pending Approvals</h3>
      <div class="value" id="pending-val">0</div>
      <div class="sub">Tier 2 waiting</div>
    </div>
    <div class="card">
      <h3>Recent Actions</h3>
      <div class="value" id="actions-val">0</div>
      <div class="sub" id="sev-breakdown">—</div>
    </div>
    <div class="card">
      <h3>Identity Provider</h3>
      <div class="value" style="font-size:1.1rem" id="idp-val">—</div>
      <div class="sub">Credential rotation backend</div>
    </div>
  </div>

  <div class="panels">
    <div class="panel">
      <div class="panel-header">
        Recent CMA Actions
        <span class="refresh">live</span>
      </div>
      <div class="panel-body">
        <table>
          <thead>
            <tr><th>Time</th><th>Action</th><th>Target</th><th>Severity</th></tr>
          </thead>
          <tbody id="actions-body">
            <tr><td colspan="4" class="empty">Loading…</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">
        Pending WhatsApp Approvals
        <span class="refresh">live</span>
      </div>
      <div class="panel-body">
        <table>
          <thead>
            <tr><th>ID</th><th>Action</th><th>Target</th><th>Severity</th></tr>
          </thead>
          <tbody id="pending-body">
            <tr><td colspan="4" class="empty">None pending</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<footer>
  CyberFortress · TrinTech Digital Defense · Trinidad & Tobago<br>
  Auto-refreshes every 5 seconds · Authorized defensive use only
</footer>

<script>
function fmtTime(iso) {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, { month:'short', day:'numeric', hour:'2-digit', minute:'2-digit', second:'2-digit' });
  } catch { return iso; }
}

function shortJust(j) {
  if (!j) return '';
  return j.length > 60 ? j.slice(0, 57) + '…' : j;
}

async function refresh() {
  try {
    const r = await fetch('/api/status');
    const d = await r.json();

    const live = d.containment_live;
    document.getElementById('mode-val').textContent = live ? 'LIVE' : 'DRY-RUN';
    document.getElementById('mode-badge').textContent = live ? 'LIVE' : 'DRY-RUN';
    document.getElementById('mode-badge').className = 'badge ' + (live ? 'live' : 'dry');

    document.getElementById('wa-val').textContent = 'WhatsApp: ' + (d.whatsapp_enabled ? 'Enabled' : 'Disabled');
    document.getElementById('idp-val').textContent = d.identity_provider || '—';

    const cb = d.circuit_breaker || {};
    document.getElementById('breaker-val').textContent = cb.state || '—';
    document.getElementById('breaker-reason').textContent = cb.reason || (cb.state === 'CLOSED' ? 'Normal operation' : '—');
    document.getElementById('breaker-badge').textContent = 'BREAKER ' + (cb.state || '—');
    document.getElementById('breaker-badge').className = 'badge ' + (cb.state === 'OPEN' ? 'open' : 'closed');

    document.getElementById('pending-val').textContent = d.stats.pending_approvals;
    document.getElementById('actions-val').textContent = d.stats.total_actions_shown;

    const sev = d.stats.by_severity || {};
    document.getElementById('sev-breakdown').textContent =
      `C:${sev.CRITICAL||0} H:${sev.HIGH||0} I:${sev.INFO||0}`;

    document.getElementById('updated').textContent = fmtTime(d.timestamp);

    // Actions table
    const ab = document.getElementById('actions-body');
    if (!d.recent_actions || d.recent_actions.length === 0) {
      ab.innerHTML = '<tr><td colspan="4" class="empty">No actions recorded yet</td></tr>';
    } else {
      ab.innerHTML = d.recent_actions.map(a => `
        <tr>
          <td>${fmtTime(a.timestamp)}</td>
          <td title="${(a.legislative_justification||'').replace(/"/g,'"')}">${a.action || '—'}</td>
          <td>${a.target || '—'}</td>
          <td class="sev ${a.severity||''}">${a.severity || '—'}</td>
        </tr>`).join('');
    }

    // Pending table
    const pb = document.getElementById('pending-body');
    if (!d.pending_approvals || d.pending_approvals.length === 0) {
      pb.innerHTML = '<tr><td colspan="4" class="empty">No pending approvals</td></tr>';
    } else {
      pb.innerHTML = d.pending_approvals.map(p => `
        <tr>
          <td style="font-family:monospace;font-size:0.75rem">${p.request_id || '—'}</td>
          <td>${p.action || '—'}</td>
          <td>${p.target || '—'}</td>
          <td class="sev ${p.severity||''}">${p.severity || '—'}</td>
        </tr>`).join('');
    }
  } catch (e) {
    console.error('Refresh failed', e);
  }
}

refresh();
setInterval(refresh, 5000);
</script>
</body>
</html>
"""


class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info("%s - %s", self.address_string(), format % args)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/dashboard", "/index.html"):
            body = DASHBOARD_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif path == "/api/status":
            data = collect_dashboard_data()
            body = json.dumps(data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        else:
            self.send_response(404)
            self.end_headers()


def main():
    logger.info(f"CyberFortress Dashboard starting on http://0.0.0.0:{PORT}")
    server = HTTPServer(("0.0.0.0", PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Dashboard shutting down")
        server.server_close()


if __name__ == "__main__":
    main()
