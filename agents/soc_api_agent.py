#!/usr/bin/env python3
"""Enterprise SOC API — metrics, SIEM ingest, playbooks, HA, intelligence."""

from __future__ import annotations

import base64
import json
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from core.soc import ha, metrics, playbooks, rbac, siem, threat_intel
from core.soc.event_bus import get_bus

try:
    from core.defense import rate_limiter, secure_headers
except Exception:
    rate_limiter = None

    def secure_headers():
        return {}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SOC-API] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_soc_api")
PORT = int(os.getenv("CF_SOC_API_PORT", "8092"))
BIND = os.getenv("CF_SOC_API_BIND", "127.0.0.1")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        logger.info("%s - %s", self.address_string(), fmt % args)

    def _auth(self):
        header = self.headers.get("Authorization", "")
        if header.startswith("Bearer "):
            token = header.split(" ", 1)[1].strip()
            users = os.getenv("CF_SOC_USERS", "")
            if not users and not os.getenv("CF_SOC_REQUIRE_AUTH", "false").lower() in (
                "1",
                "true",
                "yes",
            ):
                return "viewer"
            for part in users.split(","):
                bits = part.strip().split(":")
                if len(bits) >= 3 and bits[2] == token:
                    return bits[1]
            if os.getenv("CF_DASHBOARD_PASS") and token == os.getenv("CF_DASHBOARD_PASS"):
                return "operator"
            return None
        if header.startswith("Basic "):
            try:
                decoded = base64.b64decode(header.split(" ", 1)[1]).decode("utf-8")
                user, _, password = decoded.partition(":")
                return rbac.authenticate(user, password)
            except Exception:
                return None
        if not os.getenv("CF_SOC_REQUIRE_AUTH", "false").lower() in ("1", "true", "yes"):
            return "viewer"
        return None

    def _json(self, code, obj):
        body = json.dumps(obj, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        try:
            for k, v in (secure_headers() or {}).items():
                self.send_header(k, v)
        except Exception:
            pass
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        role = self._auth()
        if role is None:
            self.send_response(401)
            self.end_headers()
            return
        if rate_limiter is not None and not rate_limiter.allow(self.client_address[0]):
            self._json(429, {"ok": False, "error": "rate limited"})
            return
        path = urlparse(self.path).path
        if path in ("/metrics", "/api/metrics"):
            if not rbac.authorize(role, "read:metrics"):
                self._json(403, {"ok": False, "error": "forbidden"})
                return
            text = metrics.prometheus_text().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(text)))
            self.end_headers()
            self.wfile.write(text)
            return
        if path in ("/health", "/api/soc/health"):
            self._json(
                200,
                {
                    "ok": True,
                    "ha": ha.status(),
                    "bus": get_bus().stats(),
                    "ti": threat_intel.status(),
                },
            )
            return
        if path == "/api/soc/playbooks":
            self._json(200, {"ok": True, "playbooks": playbooks.load_playbooks()})
            return
        if path == "/api/soc/bus":
            self._json(200, {"ok": True, **get_bus().stats()})
            return
        if path in ("/api/soc/tier2", "/api/tier2"):
            try:
                from core.tier2 import status_summary

                self._json(200, {"ok": True, **status_summary()})
            except Exception as e:
                self._json(500, {"ok": False, "error": str(e)[:120]})
            return
        self._json(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        role = self._auth()
        if role is None:
            self.send_response(401)
            self.end_headers()
            return
        if rate_limiter is not None and not rate_limiter.allow(self.client_address[0]):
            self._json(429, {"ok": False, "error": "rate limited"})
            return
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = (
            self.rfile.read(min(length, int(os.getenv("CF_MAX_BODY_BYTES", "262144"))))
            if length
            else b"{}"
        )
        if path == "/api/soc/ingest":
            try:
                body = json.loads(raw.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                self._json(400, {"ok": False, "error": "invalid json"})
                return
            if isinstance(body, list):
                n = siem.ingest_batch(body)
            elif isinstance(body, dict) and "events" in body:
                n = siem.ingest_batch(body.get("events") or [])
            else:
                n = siem.ingest_batch([body])
            self._json(200, {"ok": True, "ingested": n, "bus": get_bus().stats()})
            return
        if path == "/api/soc/ingest/cef":
            text = raw.decode("utf-8", errors="replace")
            n = 0
            for line in text.splitlines():
                ev = siem.parse_cef(line)
                if ev and get_bus().publish(ev):
                    n += 1
            self._json(200, {"ok": True, "ingested": n})
            return
        self._json(404, {"ok": False})


class Reusable(HTTPServer):
    allow_reuse_address = True


def main():
    if os.getenv("CF_HA_ENABLED", "true").lower() in ("1", "true", "yes"):
        st = ha.try_become_leader()
        logger.info("HA status: %s", st)
    logger.info("SOC API on http://%s:%s", BIND, PORT)
    Reusable((BIND, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
