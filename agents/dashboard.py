#!/usr/bin/env python3
"""
CyberFortress Real-Time Dashboard — client-friendly interactive UI.

  export CF_DASHBOARD_USER=operator
  export CF_DASHBOARD_PASS=strong-password
  python3 -m agents.dashboard
  # http://127.0.0.1:8091

If CF_DASHBOARD_PASS is unset, auth is disabled (localhost-only still recommended).
"""

from __future__ import annotations

import os
import json
import logging
import base64
import hmac
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


def _auth_ok(handler: BaseHTTPRequestHandler) -> bool:
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


def _read_recent_actions(limit: int = 80) -> list:
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
        if (PENDING_DIR / f"{f.stem}.decision").exists():
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            data["request_id"] = f.stem
            pending.append(data)
        except Exception:
            continue
    return pending


def _watchdog_status() -> dict:
    if not WATCHDOG_STATUS.exists():
        return {"overall": "UNKNOWN", "issues": [], "heartbeats": {}}
    try:
        return json.loads(WATCHDOG_STATUS.read_text(encoding="utf-8"))
    except Exception:
        return {"overall": "UNKNOWN", "issues": [], "heartbeats": {}}


def _agent_heartbeats() -> dict:
    out = {}
    if not HEARTBEAT_DIR.exists():
        return out
    for f in HEARTBEAT_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            out[f.stem] = data
        except Exception:
            continue
    return out


def collect_dashboard_data() -> dict:
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


# HTML UI loaded from companion constant below
from agents._dashboard_html import DASHBOARD_HTML  # type: ignore


class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info("%s - %s", self.address_string(), format % args)

    def _unauthorized(self):
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="CyberFortress"')
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Authentication required")

    def _json(self, code: int, obj: dict):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not _auth_ok(self):
            self._unauthorized()
            return
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
            self._unauthorized()
            return
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
    auth_state = "ENABLED" if DASH_PASS else "DISABLED (set CF_DASHBOARD_PASS)"
    logger.info(f"Dashboard on http://{BIND}:{PORT} | auth={auth_state}")
    server = HTTPServer((BIND, PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()
