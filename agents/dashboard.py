#!/usr/bin/env python3
"""CyberFortress interactive client dashboard — http://127.0.0.1:8091"""
from __future__ import annotations

import os, json, logging, base64, hmac
from datetime import datetime, timezone
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from core.circuit_breaker import breaker

logger = logging.getLogger("cf_dashboard")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [DASHBOARD] %(levelname)s %(message)s")

PORT = int(os.getenv("CF_DASHBOARD_PORT", "8091"))
BIND = os.getenv("CF_DASHBOARD_BIND", "127.0.0.1")
AUDIT_LOG = Path(os.getenv("CF_AUDIT_PATH", "./logs/cma_audit.jsonl"))
PENDING_DIR = Path(os.getenv("CF_WHATSAPP_PENDING_DIR", "./logs/whatsapp_pending"))
WATCHDOG_STATUS = Path(os.getenv("CF_WATCHDOG_STATUS", "./logs/watchdog_status.json"))
HEARTBEAT_DIR = Path(os.getenv("CF_LOG_DIR", "./logs")) / "heartbeats"
DASH_USER = os.getenv("CF_DASHBOARD_USER", "operator")
DASH_PASS = os.getenv("CF_DASHBOARD_PASS", "")
CLIENT_NAME = os.getenv("CF_CLIENT_NAME", "Client")


def _auth_ok(handler):
    if not DASH_PASS:
        return True
    header = handler.headers.get("Authorization", "")
    if not header.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(header.split(" ", 1)[1]).decode("utf-8")
        user, _, password = decoded.partition(":")
        return hmac.compare_digest(user, DASH_USER) and hmac.compare_digest(password, DASH_PASS)
    except Exception:
        return False


def _read_recent_actions(limit=50):
    actions = []
    if not AUDIT_LOG.exists():
        return actions
    try:
        for line in reversed(AUDIT_LOG.read_text(encoding="utf-8").strip().splitlines()[-limit:]):
            try:
                actions.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except Exception as e:
        logger.warning("audit read: %s", e)
    return actions


def _pending_approvals():
    pending = []
    if not PENDING_DIR.exists():
        return pending
    for f in PENDING_DIR.glob("*.json"):
        if (PENDING_DIR / f"{f.stem}.decision").exists():
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            data["request_id"] = f.stem
            pending.append(data)
        except Exception:
            continue
    return pending


def _watchdog_status():
    if not WATCHDOG_STATUS.exists():
        return {"overall": "UNKNOWN", "issues": [], "warning_count": 0, "critical_count": 0}
    try:
        return json.loads(WATCHDOG_STATUS.read_text(encoding="utf-8"))
    except Exception:
        return {"overall": "UNKNOWN", "issues": [], "warning_count": 0, "critical_count": 0}


def _agent_heartbeats():
    out = {}
    if not HEARTBEAT_DIR.exists():
        return out
    for f in HEARTBEAT_DIR.glob("*.json"):
        try:
            out[f.stem] = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
    return out


def collect_dashboard_data():
    actions = _read_recent_actions(50)
    pending = _pending_approvals()
    wd = _watchdog_status()
    by_severity = {"CRITICAL": 0, "HIGH": 0, "INFO": 0, "MEDIUM": 0, "LOW": 0}
    for a in actions:
        sev = a.get("severity", "INFO")
        by_severity[sev] = by_severity.get(sev, 0) + 1
    live = os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "true"
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "client_name": CLIENT_NAME,
        "containment_live": live,
        "mode_label": "LIVE PROTECTION" if live else "PRACTICE MODE (dry-run)",
        "mode_help": (
            "Real containment actions can run on the network."
            if live
            else "Watching and logging only — firewall is not changed until pilot sign-off."
        ),
        "whatsapp_enabled": os.getenv("CF_WHATSAPP_ENABLED", "false").lower() == "true",
        "identity_provider": os.getenv("CF_IDENTITY_PROVIDER", "local_linux"),
        "circuit_breaker": breaker.status(),
        "watchdog": {
            "overall": wd.get("overall", "UNKNOWN"),
            "issues": wd.get("issues", [])[:8],
            "warning_count": wd.get("warning_count", 0),
            "critical_count": wd.get("critical_count", 0),
        },
        "agents": _agent_heartbeats(),
        "auth_enabled": bool(DASH_PASS),
        "stats": {
            "total_actions_shown": len(actions),
            "pending_approvals": len(pending),
            "by_severity": by_severity,
        },
        "recent_actions": actions[:30],
        "pending_approvals": pending,
    }


DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CyberFortress — Protection Dashboard</title>
<style>
:root{--bg:#0b1220;--card:#151e2e;--border:#2a364a;--text:#e8eef7;--muted:#8b9bb4;--accent:#3b82f6;--green:#22c55e;--red:#ef4444;--amber:#f59e0b}
*{box-sizing:border-box;margin:0;padding:0}body{font-family:system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
header{background:linear-gradient(135deg,#0f172a,#1e293b);border-bottom:1px solid var(--border);padding:1rem 1.25rem;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.6rem}
h1{font-size:1.15rem}h1 span{color:var(--accent)}.client{font-size:.8rem;color:var(--muted)}
.badge{padding:.28rem .65rem;border-radius:999px;font-size:.7rem;font-weight:700;text-transform:uppercase}
.badge.live,.badge.closed,.badge.healthy{background:rgba(34,197,94,.18);color:var(--green)}
.badge.dry,.badge.degraded{background:rgba(245,158,11,.18);color:var(--amber)}
.badge.open,.badge.unhealthy{background:rgba(239,68,68,.18);color:var(--red)}
.badge.unknown{background:rgba(139,155,180,.15);color:var(--muted)}
.btn{background:var(--accent);color:#fff;border:0;border-radius:8px;padding:.4rem .85rem;font-size:.78rem;font-weight:600;cursor:pointer}
.btn.ghost{background:transparent;border:1px solid var(--border);color:var(--text)}.btn:disabled{opacity:.5}
.container{max-width:1200px;margin:0 auto;padding:1rem}
.banner{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:1rem;margin-bottom:1rem}
.mode-title{font-weight:700;font-size:1.05rem}.mode-help{color:var(--muted);font-size:.85rem;margin-top:.25rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:.75rem;margin-bottom:1rem}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:.9rem}
.card h3{font-size:.65rem;text-transform:uppercase;color:var(--muted);margin-bottom:.3rem}
.card .value{font-size:1.25rem;font-weight:700}.card .sub{font-size:.75rem;color:var(--muted);margin-top:.15rem}
.tabs{display:flex;gap:.35rem;flex-wrap:wrap;margin-bottom:.7rem}
.tab{background:transparent;border:1px solid var(--border);color:var(--muted);border-radius:999px;padding:.3rem .7rem;font-size:.72rem;cursor:pointer;font-weight:600}
.tab.active{background:rgba(59,130,246,.2);border-color:var(--accent);color:#fff}
.panels{display:grid;grid-template-columns:1.25fr .9fr;gap:.85rem}@media(max-width:900px){.panels{grid-template-columns:1fr}}
.panel{background:var(--card);border:1px solid var(--border);border-radius:12px;overflow:hidden}
.panel-header{padding:.7rem 1rem;border-bottom:1px solid var(--border);font-weight:600;font-size:.85rem;display:flex;justify-content:space-between}
.panel-body{max-height:420px;overflow-y:auto}
table{width:100%;border-collapse:collapse;font-size:.8rem}
th,td{padding:.5rem .8rem;text-align:left;border-bottom:1px solid var(--border);vertical-align:top}
th{color:var(--muted);font-size:.65rem;text-transform:uppercase;position:sticky;top:0;background:var(--card)}
tr.row{cursor:pointer}tr.row:hover{background:rgba(59,130,246,.06)}
tr.detail td{background:rgba(15,23,42,.55);color:var(--muted);font-size:.75rem}
.sev.CRITICAL{color:var(--red);font-weight:700}.sev.HIGH{color:var(--amber);font-weight:700}.sev.INFO{color:var(--accent)}
.empty{padding:1.5rem;text-align:center;color:var(--muted)}
.agents{display:flex;flex-wrap:wrap;gap:.35rem;padding:.75rem}
.agent-chip{border:1px solid var(--border);border-radius:8px;padding:.35rem .55rem;font-size:.7rem}
.agent-chip .ok{color:var(--green)}.issues{padding:.7rem 1rem;font-size:.78rem;color:var(--amber)}
.toast{position:fixed;bottom:1rem;right:1rem;background:#0f172a;border:1px solid var(--border);padding:.7rem 1rem;border-radius:10px;font-size:.82rem;display:none;z-index:50;max-width:20rem}
.toast.show{display:block}footer{text-align:center;padding:1.2rem;color:var(--muted);font-size:.7rem}
.pulse{width:8px;height:8px;border-radius:50%;background:var(--green);display:inline-block;margin-right:.35rem;animation:p 1.6s infinite}@keyframes p{50%{opacity:.35}}
</style></head><body>
<header>
<div><h1>CYBER<span>FORTRESS</span></h1><div class="client" id="client-label">Protection status</div></div>
<div style="display:flex;gap:.4rem;align-items:center;flex-wrap:wrap">
<span id="mode-badge" class="badge dry">PRACTICE</span>
<span id="wd-badge" class="badge unknown">PLATFORM —</span>
<span id="breaker-badge" class="badge closed">BREAKER CLOSED</span>
<button class="btn ghost" id="btn-copy" type="button">Copy summary</button>
<button class="btn" id="btn-evidence" type="button">Evidence pack</button>
<button class="btn ghost" id="btn-refresh" type="button">Refresh</button>
</div></header>
<div class="container">
<div class="banner"><div class="mode-title"><span class="pulse"></span><span id="mode-val">—</span></div>
<div class="mode-help" id="mode-help">Loading…</div>
<div style="font-size:.78rem;color:var(--muted);margin-top:.4rem">Updated <span id="updated">—</span> · Auto-refresh 5s</div></div>
<div class="grid">
<div class="card"><h3>Platform</h3><div class="value" id="wd-val">—</div><div class="sub" id="wd-sub">Watchdog</div></div>
<div class="card"><h3>Circuit breaker</h3><div class="value" id="breaker-val">—</div><div class="sub" id="breaker-reason">—</div></div>
<div class="card"><h3>Waiting on you</h3><div class="value" id="pending-val">0</div><div class="sub">Approvals</div></div>
<div class="card"><h3>Actions</h3><div class="value" id="actions-val">0</div><div class="sub" id="sev-breakdown">—</div></div>
<div class="card"><h3>WhatsApp</h3><div class="value" style="font-size:1rem" id="wa-val">—</div><div class="sub">HITL channel</div></div>
</div>
<div class="tabs" id="sev-tabs">
<button class="tab active" data-sev="ALL" type="button">All</button>
<button class="tab" data-sev="CRITICAL" type="button">Critical</button>
<button class="tab" data-sev="HIGH" type="button">High</button>
<button class="tab" data-sev="INFO" type="button">Info</button>
</div>
<div class="panels">
<div class="panel"><div class="panel-header"><span>Recent protective actions</span><span style="font-size:.72rem;color:var(--muted)">Tap for details</span></div>
<div class="panel-body"><table><thead><tr><th>When</th><th>Action</th><th>Target</th><th>Level</th></tr></thead>
<tbody id="actions-body"><tr><td colspan="4" class="empty">Loading…</td></tr></tbody></table></div></div>
<div class="panel"><div class="panel-header">Pending WhatsApp approvals</div>
<div class="panel-body"><table><thead><tr><th>Request</th><th>Action</th><th>Target</th></tr></thead>
<tbody id="pending-body"><tr><td colspan="3" class="empty">None waiting</td></tr></tbody></table></div>
<div class="panel-header" style="border-top:1px solid var(--border);border-bottom:0">Agent heartbeats</div>
<div class="agents" id="agents-box"></div>
<div class="issues" id="issues-box" style="display:none"></div></div>
</div></div>
<footer>CyberFortress · TrinTech Digital Defense · Authorized defensive use only</footer>
<div class="toast" id="toast"></div>
<script>
let LAST=null,FILTER='ALL',OPEN_ROW=null;
function fmtTime(iso){if(!iso)return'—';try{return new Date(iso).toLocaleString(undefined,{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit'})}catch(e){return iso}}
function toast(m){const t=document.getElementById('toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),3000)}
function setBadge(el,text,cls){el.textContent=text;el.className='badge '+cls}
function renderActions(actions){const ab=document.getElementById('actions-body');const filtered=(actions||[]).filter(a=>FILTER==='ALL'||(a.severity||'')===FILTER);
if(!filtered.length){ab.innerHTML='<tr><td colspan="4" class="empty">No actions in this view</td></tr>';return}
ab.innerHTML=filtered.map((a,i)=>{const id='a'+i;const just=(a.legislative_justification||'—').replace(/</g,'<');const open=OPEN_ROW===id;
return `<tr class="row" onclick="toggleRow('${id}')"><td>${fmtTime(a.timestamp)}</td><td><code>${a.action||'—'}</code></td><td>${a.target||'—'}</td><td class="sev ${a.severity||''}">${a.severity||'—'}</td></tr>
<tr class="detail" id="${id}" style="display:${open?'table-row':'none'}"><td colspan="4"><strong>Why:</strong> ${just}<br><span style="opacity:.75">Hash: ${(a.entry_hash||'').slice(0,16)}…</span></td></tr>`}).join('')}
function toggleRow(id){OPEN_ROW=OPEN_ROW===id?null:id;if(LAST)renderActions(LAST.recent_actions||[])}
async function refresh(){try{const d=await(await fetch('/api/status')).json();LAST=d;
document.getElementById('client-label').textContent=(d.client_name||'Client')+' · protection status';
const live=!!d.containment_live;document.getElementById('mode-val').textContent=d.mode_label||'—';document.getElementById('mode-help').textContent=d.mode_help||'';
setBadge(document.getElementById('mode-badge'),live?'LIVE':'PRACTICE',live?'live':'dry');
const wd=(d.watchdog&&d.watchdog.overall)||'UNKNOWN';document.getElementById('wd-val').textContent=wd;
document.getElementById('wd-sub').textContent=(d.watchdog&&d.watchdog.critical_count?d.watchdog.critical_count+' critical · ':'')+(d.watchdog&&d.watchdog.warning_count?d.watchdog.warning_count+' warnings':'Self-check OK');
setBadge(document.getElementById('wd-badge'),'PLATFORM '+wd,wd==='HEALTHY'?'healthy':wd==='DEGRADED'?'degraded':wd==='UNHEALTHY'?'unhealthy':'unknown');
const cb=d.circuit_breaker||{};document.getElementById('breaker-val').textContent=cb.state||'—';
document.getElementById('breaker-reason').textContent=cb.reason||(cb.state==='CLOSED'?'Normal':'—');
setBadge(document.getElementById('breaker-badge'),'BREAKER '+(cb.state||'—'),cb.state==='OPEN'?'open':'closed');
document.getElementById('pending-val').textContent=d.stats.pending_approvals;document.getElementById('actions-val').textContent=d.stats.total_actions_shown;
const sev=d.stats.by_severity||{};document.getElementById('sev-breakdown').textContent=`C:${sev.CRITICAL||0} H:${sev.HIGH||0} I:${sev.INFO||0}`;
document.getElementById('wa-val').textContent=d.whatsapp_enabled?'Connected':'Not connected';document.getElementById('updated').textContent=fmtTime(d.timestamp);
renderActions(d.recent_actions||[]);
const pb=document.getElementById('pending-body');pb.innerHTML=(!d.pending_approvals||!d.pending_approvals.length)?'<tr><td colspan="3" class="empty">No approvals waiting</td></tr>':d.pending_approvals.map(p=>`<tr><td style="font-family:monospace;font-size:.7rem">${p.request_id||'—'}</td><td>${p.action||'—'}</td><td>${p.target||'—'}</td></tr>`).join('');
const agents=d.agents||{},box=document.getElementById('agents-box'),names=Object.keys(agents);
box.innerHTML=names.length?names.map(n=>{let age='—';try{age=Math.round((Date.now()-new Date(agents[n].timestamp).getTime())/1000)+'s ago'}catch(e){}return `<div class="agent-chip"><strong>${n}</strong><br><span class="ok">● ${age}</span></div>`}).join(''):'<span class="empty">No heartbeats</span>';
const issues=(d.watchdog&&d.watchdog.issues)||[],ib=document.getElementById('issues-box');
if(issues.length){ib.style.display='block';ib.innerHTML=issues.map(i=>`• [${i.severity}] ${i.message}`).join('<br>')}else{ib.style.display='none';ib.innerHTML=''}
}catch(e){console.error(e);toast('Could not refresh')}}
document.getElementById('sev-tabs').addEventListener('click',ev=>{const t=ev.target.closest('.tab');if(!t)return;FILTER=t.dataset.sev;document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('active',x===t));if(LAST)renderActions(LAST.recent_actions||[])});
document.getElementById('btn-refresh').onclick=()=>{refresh();toast('Refreshed')};
document.getElementById('btn-copy').onclick=()=>{if(!LAST)return;const s=[`CyberFortress — ${LAST.client_name||'Client'}`,`Mode: ${LAST.mode_label}`,`Platform: ${(LAST.watchdog&&LAST.watchdog.overall)||'—'}`,`Breaker: ${(LAST.circuit_breaker&&LAST.circuit_breaker.state)||'—'}`,`Actions: ${LAST.stats.total_actions_shown}`,`Pending: ${LAST.stats.pending_approvals}`,`Time: ${LAST.timestamp}`].join('\n');navigator.clipboard.writeText(s).then(()=>toast('Summary copied')).catch(()=>toast(s))};
document.getElementById('btn-evidence').onclick=async()=>{const btn=document.getElementById('btn-evidence');btn.disabled=true;try{const j=await(await fetch('/api/evidence',{method:'POST'})).json();toast(j.ok?('Evidence pack: '+(j.path||'ok')):(j.error||'Failed'))}catch(e){toast('Evidence request failed')}btn.disabled=false};
refresh();setInterval(refresh,5000);
</script></body></html>
"""


class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info("%s - %s", self.address_string(), format % args)

    def _unauthorized(self):
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="CyberFortress"')
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Authentication required")

    def _json(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not _auth_ok(self):
            return self._unauthorized()
        path = urlparse(self.path).path
        if path in ("/", "/dashboard", "/index.html"):
            body = DASHBOARD_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/api/status":
            self._json(200, collect_dashboard_data())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if not _auth_ok(self):
            return self._unauthorized()
        path = urlparse(self.path).path
        if path == "/api/evidence":
            try:
                from core.evidence.pack import generate_evidence_pack
                name = CLIENT_NAME if CLIENT_NAME != "Client" else "Demo"
                path_out = generate_evidence_pack(client_name=name, create_zip=True)
                self._json(200, {"ok": True, "path": str(path_out)})
            except Exception as e:
                logger.exception("evidence pack failed")
                self._json(500, {"ok": False, "error": str(e)})
        else:
            self.send_response(404)
            self.end_headers()


def main():
    auth = "ENABLED" if DASH_PASS else "DISABLED (set CF_DASHBOARD_PASS)"
    logger.info("Dashboard on http://%s:%s | auth=%s", BIND, PORT, auth)
    HTTPServer((BIND, PORT), DashboardHandler).serve_forever()


if __name__ == "__main__":
    main()
