#!/usr/bin/env python3
"""
CyberFortress Health Check
Simple status endpoint + CLI for operational readiness.
"""

import os
import json
import logging
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

from core.circuit_breaker import breaker

logger = logging.getLogger("cf_health")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [HEALTH] %(levelname)s %(message)s")

PORT = int(os.getenv("CF_HEALTH_PORT", "8090"))


def collect_status() -> dict:
    status = {
        "service": "CyberFortress",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "containment_live": os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "true",
        "whatsapp_enabled": os.getenv("CF_WHATSAPP_ENABLED", "false").lower() == "true",
        "identity_provider": os.getenv("CF_IDENTITY_PROVIDER", "local_linux"),
        "circuit_breaker": breaker.status(),
        "paths": {
            "logs_exist": Path("./logs").exists(),
            "evidence_exist": Path("./evidence").exists(),
            "secrets_exist": Path("./secrets").exists(),
        },
        "env_checks": {
            "whatsapp_token_set": bool(os.getenv("CF_WHATSAPP_TOKEN")),
            "whatsapp_admins_set": bool(os.getenv("CF_WHATSAPP_ADMINS")),
            "sentinel_api_set": bool(os.getenv("CF_SENTINEL_API_URL")),
            "mirage_api_set": bool(os.getenv("CF_MIRAGE_API_URL")),
        },
    }
    # Overall readiness
    status["ready_for_pilot"] = (
        status["paths"]["logs_exist"]
        and status["circuit_breaker"]["state"] == "CLOSED"
    )
    return status


class HealthHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info("%s - %s", self.address_string(), format % args)

    def do_GET(self):
        if self.path in ("/", "/health", "/status"):
            body = json.dumps(collect_status(), indent=2).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true", help="Start HTTP health server")
    parser.add_argument("--json", action="store_true", help="Print status as JSON")
    args = parser.parse_args()

    if args.serve:
        logger.info(f"Health server listening on :{PORT}")
        HTTPServer(("0.0.0.0", PORT), HealthHandler).serve_forever()
    else:
        status = collect_status()
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            print("CyberFortress Health")
            print("=" * 40)
            print(f"Containment live : {status['containment_live']}")
            print(f"WhatsApp enabled : {status['whatsapp_enabled']}")
            print(f"Identity provider: {status['identity_provider']}")
            print(f"Circuit breaker  : {status['circuit_breaker']['state']}")
            print(f"Ready for pilot  : {status['ready_for_pilot']}")


if __name__ == "__main__":
    main()
