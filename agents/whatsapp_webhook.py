#!/usr/bin/env python3
"""
CyberFortress WhatsApp Webhook Receiver

Receives Meta Cloud API webhook callbacks for interactive button replies
and writes decisions into the pending-approval store used by the gateway.

Run with a simple WSGI/ASGI server or behind ngrok / Cloudflare Tunnel
for public HTTPS endpoint required by Meta.

Environment:
  CF_WHATSAPP_VERIFY_TOKEN   — must match what you set in Meta Developer Console
  CF_WHATSAPP_PENDING_DIR    — shared with gateway (default ./logs/whatsapp_pending)
"""

import os
import json
import logging
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger("cf_whatsapp_webhook")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [WHATSAPP_WEBHOOK] %(levelname)s %(message)s")

VERIFY_TOKEN = os.getenv("CF_WHATSAPP_VERIFY_TOKEN", "cf_verify_token_change_me")
PENDING_DIR = Path(os.getenv("CF_WHATSAPP_PENDING_DIR", "./logs/whatsapp_pending"))
PENDING_DIR.mkdir(parents=True, exist_ok=True)
PORT = int(os.getenv("CF_WHATSAPP_WEBHOOK_PORT", "8089"))


class WebhookHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info("%s - %s", self.address_string(), format % args)

    def do_GET(self):
        """Meta webhook verification challenge."""
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        mode = qs.get("hub.mode", [None])[0]
        token = qs.get("hub.verify_token", [None])[0]
        challenge = qs.get("hub.challenge", [None])[0]

        if mode == "subscribe" and token == VERIFY_TOKEN:
            logger.info("Webhook verified successfully")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(challenge.encode())
        else:
            logger.warning("Webhook verification failed")
            self.send_response(403)
            self.end_headers()

    def do_POST(self):
        """Incoming message / button reply."""
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body.decode())
        except Exception:
            self.send_response(400)
            self.end_headers()
            return

        self._process_payload(data)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def _process_payload(self, data: dict):
        try:
            entries = data.get("entry", [])
            for entry in entries:
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    for msg in messages:
                        self._handle_message(msg)
        except Exception as e:
            logger.exception(f"Error processing webhook payload: {e}")

    def _handle_message(self, msg: dict):
        """Extract button reply or text APPROVE/DENY."""
        msg_type = msg.get("type")
        request_id = None
        decision = None

        if msg_type == "interactive":
            interactive = msg.get("interactive", {})
            if interactive.get("type") == "button_reply":
                button_id = interactive.get("button_reply", {}).get("id", "")
                if button_id.startswith("approve_"):
                    request_id = button_id[len("approve_"):]
                    decision = "APPROVE"
                elif button_id.startswith("deny_"):
                    request_id = button_id[len("deny_"):]
                    decision = "DENY"

        elif msg_type == "text":
            text = msg.get("text", {}).get("body", "").strip().upper()
            if text in ("APPROVE", "YES", "OK"):
                # Without request_id we cannot safely match — log only
                logger.info(f"Received free-text APPROVE from {msg.get('from')} (no request_id)")
                return
            if text in ("DENY", "NO", "CANCEL"):
                logger.info(f"Received free-text DENY from {msg.get('from')} (no request_id)")
                return

        if request_id and decision:
            decision_file = PENDING_DIR / f"{request_id}.decision"
            decision_file.write_text(decision, encoding="utf-8")
            logger.info(f"Recorded decision {decision} for request {request_id}")


def main():
    logger.info(f"Starting WhatsApp webhook receiver on port {PORT}")
    logger.info(f"Verify token: {VERIFY_TOKEN}")
    logger.info(f"Pending dir: {PENDING_DIR}")
    server = HTTPServer(("0.0.0.0", PORT), WebhookHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down webhook receiver")
        server.server_close()


if __name__ == "__main__":
    main()
