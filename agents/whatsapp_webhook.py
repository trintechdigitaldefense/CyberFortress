#!/usr/bin/env python3
"""
CyberFortress WhatsApp Webhook Receiver (hardened)

- Only CF_WHATSAPP_ADMINS numbers can approve
- Requires APPROVE <nonce> or DENY <nonce> matching pending request
- Rate limit, body cap, mandatory Meta X-Hub-Signature-256
- Unknown sender → DENY-UNKNOWN-SENDER + log
"""

import json
import logging
import os
import re
import threading
import tempfile
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

DEFAULT_VERIFY_TOKEN = "cf_verify_token_change_me"
VERIFY_TOKEN = os.getenv("CF_WHATSAPP_VERIFY_TOKEN", "").strip()
PORT = int(os.getenv("CF_WHATSAPP_WEBHOOK_PORT", "8089"))
PENDING_DIR.mkdir(parents=True, exist_ok=True)


def validate_startup_config() -> None:
    if not VERIFY_TOKEN or VERIFY_TOKEN == DEFAULT_VERIFY_TOKEN:
        raise RuntimeError("CF_WHATSAPP_VERIFY_TOKEN must be explicitly configured and must not use the placeholder")
    if not os.getenv("CF_WHATSAPP_APP_SECRET", ""):
        raise RuntimeError("CF_WHATSAPP_APP_SECRET must be configured before starting the webhook")


APPROVE_RE = re.compile(r"^APPROVE\s+([A-Fa-f0-9]{4,64})$", re.I)
DENY_RE = re.compile(r"^DENY\s+([A-Fa-f0-9]{4,64})$", re.I)


def record_decision(
    request_id: str,
    decision: str,
    sender: str,
    provided_nonce: str,
) -> bool:
    """Consume one unexpired approval nonce exactly once using exclusive creation."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", request_id):
        return False
    pending_path = PENDING_DIR / f"{request_id}.json"
    decision_path = PENDING_DIR / f"{request_id}.decision"
    try:
        meta = json.loads(pending_path.read_text(encoding="utf-8"))
        expiry = float(meta.get("expires_at", 0))
        expected = str(meta.get("nonce", "")).upper()
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        logger.warning("Invalid or missing pending approval %s", request_id)
        return False
    if not expiry or time.time() >= expiry:
        logger.warning("Expired approval request %s", request_id)
        if expiry:
            expired_payload = {
                "decision": "DENY-EXPIRED",
                "sender_hash": hash_sender(sender),
                "nonce_ok": False,
                "received_at": time.time(),
            }
            fd, expired_temp_name = tempfile.mkstemp(prefix=f".{request_id}.expired.", dir=str(PENDING_DIR))
            expired_temp = Path(expired_temp_name)
            try:
                with os.fdopen(fd, "wb") as stream:
                    os.fchmod(stream.fileno(), 0o600)
                    stream.write((json.dumps(expired_payload, sort_keys=True) + "\n").encode("utf-8"))
                    stream.flush()
                    os.fsync(stream.fileno())
                try:
                    os.link(expired_temp, decision_path)
                except FileExistsError:
                    pass
            finally:
                expired_temp.unlink(missing_ok=True)
        return False
    if not is_allowed_approver(sender):
        logger.warning("Unknown sender ignored for %s hash=%s", request_id, hash_sender(sender))
        return False
    requested = decision.upper()
    if requested not in ("APPROVE", "DENY"):
        return False
    nonce_ok = secrets_compare(expected, provided_nonce.upper().strip())
    final_decision = requested if nonce_ok else "DENY-BAD-NONCE"
    payload = {
        "decision": final_decision,
        "sender_hash": hash_sender(sender),
        "nonce_ok": nonce_ok,
        "received_at": time.time(),
    }
    encoded = (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")
    fd, temp_name = tempfile.mkstemp(prefix=f".{request_id}.decision.", dir=str(PENDING_DIR))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temp_path, decision_path)
        except FileExistsError:
            logger.warning("Approval already consumed for %s", request_id)
            return False
        logger.info("Atomically recorded %s for %s nonce_ok=%s", final_decision, request_id, nonce_ok)
        return True
    finally:
        temp_path.unlink(missing_ok=True)


def secrets_compare(a: str, b: str) -> bool:
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a.encode(), b.encode()):
        result |= x ^ y
    return result == 0


def _find_request_by_nonce(nonce: str):
    nonce = nonce.upper()
    now = time.time()
    for path in PENDING_DIR.glob("*.json"):
        if path.name.endswith(".decision"):
            continue
        try:
            meta = json.loads(path.read_text(encoding="utf-8"))
            expires_at = float(meta.get("expires_at", 0))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
        if expires_at <= now:
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

        if VERIFY_TOKEN and VERIFY_TOKEN != DEFAULT_VERIFY_TOKEN and mode == "subscribe" and token == VERIFY_TOKEN:
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

        app_secret = os.getenv("CF_WHATSAPP_APP_SECRET", "")
        sig = self.headers.get("X-Hub-Signature-256", "")
        if not app_secret or not sig or not verify_meta_signature(app_secret, body, sig):
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
    validate_startup_config()
    logger.info("Starting WhatsApp webhook on port %s", PORT)
    logger.info("Approvals require: APPROVE <nonce> from registered admin only")
    bind = assert_safe_bind(os.getenv("CF_WHATSAPP_WEBHOOK_BIND", "127.0.0.1"), "whatsapp_webhook")
    if os.getenv("CF_ALLOW_PUBLIC_BIND", "false").lower() in ("1", "true", "yes"):
        bind = os.getenv("CF_WHATSAPP_WEBHOOK_BIND", bind)
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
