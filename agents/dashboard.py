#!/usr/bin/env python3
"""CyberFortress interactive client dashboard — http://127.0.0.1:8091"""
from __future__ import annotations

import os, json, logging, base64, hmac
from datetime import datetime, timezone
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from core.circuit_breaker import breaker
import core.whatsapp_report_hooks  # noqa: F401
from agents.dashboard_ui import DASHBOARD_HTML

logger = logging.getLogger("cf_dashboard")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [DASHBOARD] %(levelname)s %(message)s")

PORT = int(os.getenv("CF_DASHBOARD_PORT", "8091"))
BIND = os.getenv("CF_DASHBOARD_BIND", "127.0.0.1")
AUDIT_LOG = Path(os.getenv("CF_AUDIT_PATH", "./logs/cma_audit.jsonl"))
PENDING_DIR = Path(os.getenv("CF_WHATSAPP_PENDING_DIR", "./logs/whatsapp_pending"))
WATCHDOG_STATUS = Path(os.getenv("CF_WATCHDOG_STATUS", "./logs/watchdog_status.json"))
HEARTBEAT_DIR = Path(os.getenv("CF_LOG_DIR", "./logs")) / "heartbeats"
EVIDENCE_DIR = Path(os.getenv("CF_EVIDENCE_DIR", "./evidence"))
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
    import time
    now = time.time()
    for f in PENDING_DIR.glob("*.json"):
        if (PENDING_DIR / f"{f.stem}.decision").exists():
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            data["request_id"] = data.get("request_id") or f.stem
            exp = float(data.get("expires_at") or 0)
            data["seconds_left"] = max(0, int(exp - now)) if exp else None
            try:
                from core.tier2 import risk_card
                data["risk"] = risk_card(str(data.get("action") or "")).get("risk", "HIGH")
            except Exception:
                data.setdefault("risk", "HIGH")
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


def _audit_integrity():
    try:
        from core.audit_chain import verify_chain
        ok, idx, msg = verify_chain(AUDIT_LOG)
        return {"ok": ok, "message": msg, "broken_index": idx}
    except Exception as e:
        return {"ok": False, "message": str(e), "broken_index": None}


def _roe():
    try:
        from core.roe import roe_status
        return roe_status()
    except Exception as e:
        return {"signoff_present": False, "source": "error", "error": str(e), "authorized_actions": []}


def collect_dashboard_data():
    try:
        from core.monitoring_metrics import load_persisted
        mon = load_persisted()
    except Exception:
        mon = {}
    try:
        from core.ir.cases import CaseStore
        _store = CaseStore()
        ir_summary = _store.summary()
        ir_open = [c.to_dict() for c in _store.list_open(8)]
    except Exception:
        ir_summary, ir_open = {}, []
    actions = _read_recent_actions(50)
    pending = _pending_approvals()
    wd = _watchdog_status()
    by_severity = {"CRITICAL": 0, "HIGH": 0, "INFO": 0, "MEDIUM": 0, "LOW": 0}
    for a in actions:
        sev = a.get("severity", "INFO")
        by_severity[sev] = by_severity.get(sev, 0) + 1
    live = os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "true"
    audit = _audit_integrity()
    roe = _roe()
    try:
        from core.evidence.pack import list_evidence_packs
        packs = list_evidence_packs(5)
    except Exception:
        packs = []
    try:
        from core.notify_settings import load_settings
        notify = load_settings()
    except Exception as e:
        notify = {"error": str(e), "report_to": "", "daily_enabled": False, "live_alerts_enabled": False}
    try:
        from core.containment.firewall import firewall_status
        fw = firewall_status()
    except Exception as e:
        fw = {"message": str(e), "live_mode": live, "rule_count": 0, "rules": []}
    try:
        from core.tier2 import status_summary as tier2_summary
        tier2 = tier2_summary()
        if pending:
            tier2["pending"] = pending
            tier2["pending_count"] = len(pending)
    except Exception as e:
        tier2 = {"pending_count": len(pending), "pending": pending, "error": str(e)[:80]}
    try:
        from core.rules import pack_summary, list_available_packs, load_pack
        rp = pack_summary()
        pack = load_pack()
        rp["available"] = list_available_packs()
        rp["description"] = pack.get("description") or pack.get("pack_id") or ""
    except Exception as e:
        rp = {"pack_id": "unknown", "rule_count": 0, "available": [], "error": str(e)[:80]}
    return {
        "monitoring": mon,
        "ir": {"summary": ir_summary, "open_cases": ir_open},
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "client_name": CLIENT_NAME,
        "containment_live": live,
        "mode_label": "ACTIVE CONTAINMENT" if live else "MONITORING",
        "mode_help": (
            "Containment is armed — protective actions can add DROP rules to the CF_BLOCK firewall."
            if live
            else "Firewall service is running. Detecting, correlating, and logging. New DROP rules are applied only when containment is armed."
        ),
        "whatsapp_enabled": os.getenv("CF_WHATSAPP_ENABLED", "false").lower() == "true",
        "notify": notify,
        "identity_provider": os.getenv("CF_IDENTITY_PROVIDER", "local_linux"),
        "circuit_breaker": breaker.status(),
        "watchdog": {
            "overall": wd.get("overall", "UNKNOWN"),
            "issues": wd.get("issues", [])[:8],
            "warning_count": wd.get("warning_count", 0),
            "critical_count": wd.get("critical_count", 0),
        },
        "audit_integrity": audit,
        "policy": {
            "authorized_actions": roe.get("authorized_actions", [])[:12],
            "action_count": len(roe.get("authorized_actions") or []),
            "scope": "allow-listed containment only",
        },
        "roe": {
            "authorized_actions": roe.get("authorized_actions", [])[:12],
            "source": roe.get("source", "policy"),
        },
        "agents": _agent_heartbeats(),
        "auth_enabled": bool(DASH_PASS),
        "evidence_packs": packs,
        "firewall": fw,
        "tier2": tier2,
        "rule_pack": rp,
        "stats": {
            "total_actions_shown": len(actions),
            "pending_approvals": len(pending),
            "by_severity": by_severity,
            "evidence_packs": len(packs),
            "firewall_rules": fw.get("rule_count", 0),
            "ir_open": ir_summary.get("open_total", len(ir_open)),
        },
        "recent_actions": actions[:30],
        "pending_approvals": pending,
    }


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
        body = json.dumps(obj, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not _auth_ok(self):
            return self._unauthorized()
        parsed = urlparse(self.path)
        path = parsed.path
        if path in ("/", "/dashboard", "/index.html"):
            html = DASHBOARD_HTML
            if "notify_settings.js" not in html:
                html = html.replace("</body>", '<script src="/static/notify_settings.js"></script></body>')
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/static/notify_settings.js":
            js_path = Path(__file__).resolve().parent / "static" / "notify_settings.js"
            if not js_path.is_file():
                self.send_response(404); self.end_headers(); return
            data = js_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif path == "/api/monitoring":
            try:
                from core.monitoring_metrics import load_persisted
                self._json(200, {"ok": True, **load_persisted()})
            except Exception as e:
                self._json(500, {"ok": False, "error": str(e)})
        elif path == "/api/ir/cases":
            try:
                from core.ir.cases import CaseStore
                store = CaseStore()
                cases = [c.to_dict() for c in store.list_by_status(
                    ("open", "investigating", "awaiting_approval", "contained", "reported"), 50
                )]
                self._json(200, {"ok": True, "cases": cases, "count": len(cases), "summary": store.summary()})
            except Exception as e:
                self._json(500, {"ok": False, "error": str(e)})
        elif path == "/api/status":
            self._json(200, collect_dashboard_data())
        elif path == "/api/settings/whatsapp":
            try:
                from core.notify_settings import load_settings
                self._json(200, {"ok": True, "settings": load_settings()})
            except Exception as e:
                self._json(500, {"ok": False, "error": str(e)})
        elif path == "/api/tier2":
            try:
                from core.tier2 import status_summary
                data = status_summary()
                data["pending"] = _pending_approvals()
                data["pending_count"] = len(data["pending"])
                self._json(200, {"ok": True, **data})
            except Exception as e:
                self._json(500, {"ok": False, "error": str(e)})
        elif path == "/api/rule-packs":
            try:
                from core.rules import pack_summary, list_available_packs, load_pack
                pack = load_pack()
                self._json(200, {
                    "ok": True,
                    **pack_summary(),
                    "available": list_available_packs(),
                    "description": pack.get("description") or "",
                    "rules": [
                        {"id": r.get("id"), "name": r.get("name"), "severity": r.get("severity"), "playbook": r.get("playbook")}
                        for r in (pack.get("rules") or [])
                    ],
                })
            except Exception as e:
                self._json(500, {"ok": False, "error": str(e)})
        elif path == "/api/firewall":
            try:
                from core.containment.firewall import firewall_status
                self._json(200, {"ok": True, **firewall_status()})
            except Exception as e:
                self._json(500, {"ok": False, "error": str(e)})
        elif path == "/api/evidence":
            try:
                from core.evidence.pack import list_evidence_packs
                self._json(200, {"ok": True, "packs": list_evidence_packs(20)})
            except Exception as e:
                self._json(500, {"ok": False, "error": str(e)})
        elif path == "/api/evidence/download":
            qs = parse_qs(parsed.query)
            name = (qs.get("name") or [""])[0]
            safe = Path(name).name
            if not safe.endswith(".zip") or ".." in name:
                self._json(400, {"ok": False, "error": "invalid name"})
                return
            target = (EVIDENCE_DIR / safe).resolve()
            if not str(target).startswith(str(EVIDENCE_DIR.resolve())) or not target.is_file():
                self._json(404, {"ok": False, "error": "not found"})
                return
            data = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition", f'attachment; filename="{safe}"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if not _auth_ok(self):
            return self._unauthorized()
        path = urlparse(self.path).path
        if path == "/api/settings/whatsapp":
            try:
                length = int(self.headers.get("Content-Length", "0") or 0)
                raw = self.rfile.read(length) if length > 0 else b"{}"
                body = json.loads(raw.decode("utf-8") or "{}")
                from core.notify_settings import save_settings
                settings = save_settings(
                    report_to=str(body.get("report_to", "")),
                    daily_enabled=bool(body.get("daily_enabled", True)),
                    live_alerts_enabled=bool(body.get("live_alerts_enabled", True)),
                    min_live_severity=str(body.get("min_live_severity", "HIGH")),
                )
                self._json(200, {"ok": True, "settings": settings})
            except ValueError as e:
                self._json(400, {"ok": False, "error": str(e)})
            except Exception as e:
                logger.exception("settings save failed")
                self._json(500, {"ok": False, "error": str(e)})
        elif path == "/api/evidence":
            try:
                from core.evidence.pack import generate_evidence_pack_with_meta
                name = CLIENT_NAME if CLIENT_NAME else "Client"
                result = generate_evidence_pack_with_meta(client_name=name, create_zip=True)
                self._json(200, result)
            except Exception as e:
                logger.exception("evidence pack failed")
                self._json(500, {"ok": False, "error": str(e)})
        else:
            self.send_response(404)
            self.end_headers()


class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True


def main():
    auth = "ENABLED" if DASH_PASS else "DISABLED (set CF_DASHBOARD_PASS)"
    logger.info("Dashboard on http://%s:%s | auth=%s", BIND, PORT, auth)
    ReusableHTTPServer((BIND, PORT), DashboardHandler).serve_forever()


if __name__ == "__main__":
    main()
