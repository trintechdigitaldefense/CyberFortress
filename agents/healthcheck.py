#!/usr/bin/env python3
"""CyberFortress health endpoint — localhost status for ops and load balancers."""

from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import ThreadingMixIn

from core.watchdog import write_heartbeat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [HEALTH] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_health")

PORT = int(os.getenv("CF_HEALTH_PORT", "8090"))
BIND = os.getenv("CF_HEALTH_BIND", "127.0.0.1")
LOG_DIR = Path(os.getenv("CF_LOG_DIR", "./logs"))
HEARTBEAT_DIR = LOG_DIR / "heartbeats"


def collect_status() -> dict:
    try:
        write_heartbeat("health", {"phase": "probe"})
    except Exception:
        pass

    from core.circuit_breaker import breaker

    status = {
        "service": "CyberFortress",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "containment_live": os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "true",
        "whatsapp_enabled": os.getenv("CF_WHATSAPP_ENABLED", "false").lower() == "true",
        "identity_provider": os.getenv("CF_IDENTITY_PROVIDER", "local_linux"),
        "circuit_breaker": breaker.status(),
        "paths": {
            "logs_exist": LOG_DIR.exists(),
            "evidence_exist": Path(os.getenv("CF_EVIDENCE_DIR", "./evidence")).exists(),
            "secrets_exist": Path(os.getenv("CF_SECRETS_DIR", "./secrets")).exists(),
        },
        "env_checks": {
            "whatsapp_token_set": bool(os.getenv("CF_WHATSAPP_TOKEN")),
            "whatsapp_admins_set": bool(os.getenv("CF_WHATSAPP_ADMINS")),
            "sentinel_api_set": bool(os.getenv("CF_SENTINEL_API_URL")),
            "mirage_api_set": bool(os.getenv("CF_MIRAGE_API_URL")),
        },
    }

    agents = {}
    if HEARTBEAT_DIR.exists():
        for f in HEARTBEAT_DIR.glob("*.json"):
            try:
                agents[f.stem] = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
    status["agents"] = agents
    status["agents_up"] = sum(1 for v in agents.values() if v.get("timestamp"))

    wd_path = Path(os.getenv("CF_WATCHDOG_STATUS", str(LOG_DIR / "watchdog_status.json")))
    if wd_path.exists():
        try:
            status["watchdog"] = json.loads(wd_path.read_text(encoding="utf-8"))
        except Exception:
            status["watchdog"] = {"overall": "UNKNOWN"}
    else:
        status["watchdog"] = {"overall": "UNKNOWN"}

    try:
        from core.monitoring_metrics import load_persisted
        status["monitoring"] = load_persisted()
    except Exception as e:
        status["monitoring"] = {"error": str(e)}

    try:
        from core.containment.firewall import firewall_status
        status["firewall"] = firewall_status()
    except Exception as e:
        status["firewall"] = {"error": str(e)}

    try:
        from core.audit_chain import verify_chain
        audit = Path(os.getenv("CF_AUDIT_PATH", str(LOG_DIR / "cma_audit.jsonl")))
        ok, idx, msg = verify_chain(audit)
        status["audit_integrity"] = {"ok": ok, "message": msg, "broken_index": idx}
    except Exception as e:
        status["audit_integrity"] = {"ok": False, "message": str(e)}

    status["ready_for_pilot"] = (
        status["paths"]["logs_exist"]
        and status["circuit_breaker"].get("state") != "OPEN"
        and status.get("audit_integrity", {}).get("ok", True) is not False
    )
    return status


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info("%s - %s", self.address_string(), format % args)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/health", "/api/status", "/status"):
            body = json.dumps(collect_status()).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true", help="Start HTTP health server (default if no --once)")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.once:
        status = collect_status()
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            print("CyberFortress Health")
            print("=" * 40)
            print(f"Containment live : {status['containment_live']}")
            print(f"WhatsApp enabled : {status['whatsapp_enabled']}")
            print(f"Agents reporting : {status.get('agents_up', 0)}")
            print(f"Watchdog         : {status.get('watchdog', {}).get('overall')}")
            print(f"Circuit breaker  : {status['circuit_breaker']['state']}")
            print(f"Ready for pilot  : {status['ready_for_pilot']}")
        return

    logger.info("Health listening on %s:%s", BIND, PORT)
    write_heartbeat("health", {"phase": "listen", "port": PORT})
    ThreadedHTTPServer((BIND, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
