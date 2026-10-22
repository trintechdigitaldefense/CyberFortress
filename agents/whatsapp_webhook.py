#!/usr/bin/env python3
"""
CyberFortress WhatsApp Webhook Receiver (hardened)

- Only CF_WHATSAPP_ADMINS numbers can approve
- Requires APPROVE <nonce> or DENY <nonce> matching pending request
- Rate limit, body cap, optional Meta X-Hub-Signature-256
- Unknown sender → DENY-UNKNOWN-SENDER + log
"""

import json
import logging
import os
import re
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from core.defense import (
    rate_limit_allow,
    read_body_limited,
    verify_meta_signature,
    assert_safe_bind,
)
from core.watchdog import write_heartbeat
from core.whatsapp_gateway import (
    is_allowed_approver,
    hash_sender,
    PENDING_DIR,
)

logger = logging.getLogger("cf_whatsapp_webhook")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [WHATSAPP_WEBHOOK] %(levelname)s %(message)s")

VERIFY_TOKEN = os.getenv("CF_WHATSAPP_VERIFY_TOKEN", "cf_verify_token_change_me")
PORT = int(os.getenv("CF_WHATSAPP_WEBHOOK_PORT", "8089"))
PENDING_DIR.mkdir(parents=True, exist_ok=True)

APPROVE_RE = re.compile(r"^APPROVE\s+([A-Fa-f0-9]{4,12})$", re.I)
DENY_RE = re.compile(r"^DENY\s+([A-Fa-f0-9]{4,12})$", re.I)


def record_decision(
    request_id: str,
    decision: str,
    sender: str,
    provided_nonce: str,
) -> None:
    pending_path = PENDING_DIR / f"{request_id}.json"
    if not pending_path.exists():
        logger.warning("No pending request %s", request_id)
        return

    meta = json.loads(pending_path.read_text(encoding="utf-8"))
    expected = str(meta.get("nonce", "")).upper()
    provided = provided_nonce.upper().strip()

    if not is_allowed_approver(sender):
        payload = {
            "decision": "DENY-UNKNOWN-SENDER",
            "sender_hash": hash_sender(sender),
            "nonce_ok": False,
        }
        (PENDING_DIR / f"{request_id}.decision").write_text(json.dumps(payload), encoding="utf-8")
        logger.warning("Unknown sender denied for %s hash=%s", request_id, payload["sender_hash"])
        return

    nonce_ok = secrets_compare(expected, provided)
    if decision.upper() == "APPROVE" and not nonce_ok:
        payload = {
            "decision": "DENY-BAD-NONCE",
            "sender_hash": hash_sender(sender),
            "nonce_ok": False,
        }
    else:
        payload = {
            "decision": decision.upper(),
            "sender_hash": hash_sender(sender),
            "nonce_ok": nonce_ok,
        }

    (PENDING_DIR / f"{request_id}.decision").write_text(json.dumps(payload), encoding="utf-8")
    logger.info("Recorded %s for %s nonce_ok=%s", payload["decision"], request_id, nonce_ok)


def secrets_compare(a: str, b: str) -> bool:
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a.encode(), b.encode()):
        result |= x ^ y
    return result == 0


def _find_request_by_nonce(nonce: str):
    nonce = nonce.upper()
    for path in PENDING_DIR.glob("*.json"):
        if path.name.endswith(".decision"):
            continue
        try:
            meta = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if str(meta.get("nonce", "")).upper() == nonce:
            if (PENDING_DIR / f"{path.stem}.decision").exists():
                continue
            return path.stem
    return None


class WebhookHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info("%s - %s", self.address_string(), format % args)

    def do_GET(self):
        client = self.client_address[0] if self.client_address else "unknown"
        if not rate_limit_allow(f"wa-get:{client}", limit=30):
            self.send_response(429)
            self.end_headers()
            return
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
        client = self.client_address[0] if self.client_address else "unknown"
        if not rate_limit_allow(f"wa:{client}", limit=60):
            logger.warning("Webhook rate limited client=%s", client)
            self.send_response(429)
            self.end_headers()
            self.wfile.write(b"rate limited")
            return

        body, err = read_body_limited(self)
        if err:
            logger.warning("Webhook body rejected: %s", err)
            self.send_response(413)
            self.end_headers()
            return

        sig = self.headers.get("X-Hub-Signature-256")
        if not verify_meta_signature(body, sig):
            logger.warning("Invalid Meta signature from %s", client)
            self.send_response(403)
            self.end_headers()
            return

        try:
            data = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"EVENT_RECEIVED")

        try:
            for entry in data.get("entry") or []:
                for change in entry.get("changes") or []:
                    value = change.get("value") or {}
                    for msg in value.get("messages") or []:
                        self._handle_message(msg)
        except Exception as e:
            logger.exception("Error processing webhook payload: %s", e)

    def _handle_message(self, msg: dict):
        sender = str(msg.get("from", ""))
        msg_type = msg.get("type")
        text = ""

        if msg_type == "text":
            text = msg.get("text", {}).get("body", "").strip()
        elif msg_type == "interactive":
            logger.info("Interactive button ignored; reply APPROVE <nonce> as text")
            return
        else:
            return

        m_ok = APPROVE_RE.match(text)
        m_no = DENY_RE.match(text)
        if not m_ok and not m_no:
            logger.info("Ignoring non-decision text from hash=%s", hash_sender(sender))
            return

        decision = "APPROVE" if m_ok else "DENY"
        nonce = (m_ok or m_no).group(1)
        request_id = _find_request_by_nonce(nonce)
        if not request_id:
            logger.warning("No pending request for nonce from hash=%s", hash_sender(sender))
            return

        record_decision(request_id, decision, sender, nonce)


class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True


def _heartbeat_loop():
    """Keep WhatsApp agent visible on the client dashboard."""
    interval = int(os.getenv("CF_WHATSAPP_HEARTBEAT_S", "30"))
    while True:
        try:
            write_heartbeat(
                "whatsapp",
                {
                    "phase": "listen",
                    "port": PORT,
                    "enabled": os.getenv("CF_WHATSAPP_ENABLED", "false").lower() == "true",
                },
            )
        except Exception as e:
            logger.debug("heartbeat failed: %s", e)
        time.sleep(max(15, interval))


def main():
    logger.info("Starting WhatsApp webhook on port %s", PORT)
    logger.info("Approvals require: APPROVE <nonce> from registered admin only")
    bind = assert_safe_bind(os.getenv("CF_WHATSAPP_WEBHOOK_BIND", "127.0.0.1"), "whatsapp_webhook")
    if os.getenv("CF_ALLOW_PUBLIC_BIND", "false").lower() in ("1", "true", "yes"):
        bind = os.getenv("CF_WHATSAPP_WEBHOOK_BIND", "0.0.0.0")
    logger.info("Webhook bind=%s port=%s", bind, PORT)
    write_heartbeat("whatsapp", {"phase": "starting", "port": PORT})
    threading.Thread(target=_heartbeat_loop, name="wa-hb", daemon=True).start()
    server = ReusableHTTPServer((bind, PORT), WebhookHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()
