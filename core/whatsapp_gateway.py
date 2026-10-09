#!/usr/bin/env python3
"""
CyberFortress WhatsApp HITL Gateway — Production Meta Cloud API

Supports:
- Tier 1 one-way notifications
- Tier 2 interactive APPROVE / DENY buttons
- Webhook-driven decision store

Required env vars for live mode:
  CF_WHATSAPP_ENABLED=true
  CF_WHATSAPP_TOKEN=<permanent access token>
  CF_WHATSAPP_PHONE_NUMBER_ID=<phone number id>
  CF_WHATSAPP_ADMINS=+1868xxxxxxxx,+1868yyyyyyyy
  CF_WHATSAPP_VERIFY_TOKEN=<webhook verify token>
  CF_APPROVAL_TIMEOUT=300
"""

import os
import time
import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pathlib import Path

import requests

logger = logging.getLogger("cf_whatsapp_gateway")

WHATSAPP_ENABLED = os.getenv("CF_WHATSAPP_ENABLED", "false").lower() == "true"
WHATSAPP_TOKEN = os.getenv("CF_WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("CF_WHATSAPP_PHONE_NUMBER_ID", "")
ADMIN_NUMBERS = [n.strip() for n in os.getenv("CF_WHATSAPP_ADMINS", "").split(",") if n.strip()]
APPROVAL_TIMEOUT = int(os.getenv("CF_APPROVAL_TIMEOUT", "300"))
GRAPH_URL = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages" if PHONE_NUMBER_ID else ""

PENDING_DIR = Path(os.getenv("CF_WHATSAPP_PENDING_DIR", "./logs/whatsapp_pending"))
PENDING_DIR.mkdir(parents=True, exist_ok=True)


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }


def _send_text(to: str, body: str) -> bool:
    if not WHATSAPP_ENABLED or not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        logger.info(f"[SIMULATED WhatsApp → {to}] {body[:120]}...")
        return True

    payload = {
        "messaging_product": "whatsapp",
        "to": to.lstrip("+"),
        "type": "text",
        "text": {"body": body},
    }
    try:
        r = requests.post(GRAPH_URL, headers=_headers(), json=payload, timeout=30)
        if r.status_code in (200, 201):
            logger.info(f"WhatsApp message sent to {to}")
            return True
        logger.error(f"WhatsApp API error {r.status_code}: {r.text}")
        return False
    except Exception as e:
        logger.exception(f"Failed to send WhatsApp message: {e}")
        return False


def _send_interactive_buttons(to: str, body: str, request_id: str) -> bool:
    if not WHATSAPP_ENABLED or not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        logger.info(f"[SIMULATED interactive WhatsApp → {to}] {body[:100]}...")
        return True

    payload = {
        "messaging_product": "whatsapp",
        "to": to.lstrip("+"),
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": f"approve_{request_id}", "title": "APPROVE"}},
                    {"type": "reply", "reply": {"id": f"deny_{request_id}", "title": "DENY"}},
                ]
            },
        },
    }
    try:
        r = requests.post(GRAPH_URL, headers=_headers(), json=payload, timeout=30)
        if r.status_code in (200, 201):
            logger.info(f"WhatsApp interactive message sent to {to}")
            return True
        logger.error(f"WhatsApp interactive API error {r.status_code}: {r.text}")
        return False
    except Exception as e:
        logger.exception(f"Failed to send interactive WhatsApp: {e}")
        return False


def _format_approval_message(action: str, target: str, severity: str, justification: str, request_id: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return (
        f"🚨 *CyberFortress Tier 2 Approval Required*\n\n"
        f"*ID:* {request_id}\n"
        f"*Time:* {ts}\n"
        f"*Severity:* {severity}\n"
        f"*Action:* {action}\n"
        f"*Target:* {target}\n"
        f"*Legal Justification:* {justification}\n\n"
        f"Tap APPROVE or DENY below.\n"
        f"_Timeout in {APPROVAL_TIMEOUT // 60} minutes. Default = DENY._"
    )


def send_notification(message: str, level: str = "INFO") -> bool:
    if not ADMIN_NUMBERS:
        logger.warning("No CF_WHATSAPP_ADMINS configured")
        return False
    ok = True
    for num in ADMIN_NUMBERS:
        if not _send_text(num, message):
            ok = False
    return ok


def notify_tier1(action: str, target: str, justification: str) -> None:
    msg = (
        f"✅ *CyberFortress Tier 1 Action Executed*\n"
        f"Action: {action}\n"
        f"Target: {target}\n"
        f"Justification: {justification}\n"
        f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
    )
    send_notification(msg, level="INFO")


def _write_pending(request_id: str, meta: dict):
    path = PENDING_DIR / f"{request_id}.json"
    path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def _read_reply(request_id: str) -> Optional[str]:
    decision_file = PENDING_DIR / f"{request_id}.decision"
    if decision_file.exists():
        return decision_file.read_text(encoding="utf-8").strip().upper()
    return None


def request_approval(
    action: str,
    target: str,
    severity: str = "HIGH",
    justification: str = "Authorized defensive action under TT Computer Misuse Act",
) -> bool:
    request_id = f"CF-{int(time.time())}-{secrets.token_hex(3)}"
    message = _format_approval_message(action, target, severity, justification, request_id)

    _write_pending(request_id, {
        "action": action,
        "target": target,
        "severity": severity,
        "justification": justification,
        "created": datetime.now(timezone.utc).isoformat(),
    })

    if not ADMIN_NUMBERS:
        logger.warning("No admins configured — treating as DENY")
        return False

    for num in ADMIN_NUMBERS:
        _send_interactive_buttons(num, message, request_id)

    logger.info(f"Waiting up to {APPROVAL_TIMEOUT}s for approval of {request_id}...")
    deadline = time.time() + APPROVAL_TIMEOUT

    while time.time() < deadline:
        decision = _read_reply(request_id)
        if decision == "APPROVE":
            logger.info(f"Request {request_id} APPROVED via WhatsApp")
            return True
        if decision == "DENY":
            logger.info(f"Request {request_id} DENIED via WhatsApp")
            return False
        time.sleep(3)

    logger.warning(f"Request {request_id} timed out — defaulting to DENY")
    return False
