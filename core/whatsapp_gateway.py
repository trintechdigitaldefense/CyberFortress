#!/usr/bin/env python3
"""
CyberFortress WhatsApp HITL Gateway — hardened Tier 2 approvals

Security controls:
  - Approver allow-list (CF_WHATSAPP_ADMINS only)
  - Per-request nonce: approver must send APPROVE <code>
  - Timeout → automatic DENY (default 15 minutes)
  - Every decision logged with hashed sender for evidence packs

Env:
  CF_WHATSAPP_ENABLED=true
  CF_WHATSAPP_TOKEN=...
  CF_WHATSAPP_PHONE_NUMBER_ID=...
  CF_WHATSAPP_ADMINS=+1868xxxxxxxx,+1868yyyyyyyy
  CF_WHATSAPP_VERIFY_TOKEN=...
  CF_APPROVAL_TIMEOUT=900   # seconds (default 15 min)
  CF_WHATSAPP_MOCK=true     # demo without live Meta API
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger("cf_whatsapp_gateway")

WHATSAPP_ENABLED = os.getenv("CF_WHATSAPP_ENABLED", "false").lower() == "true"
WHATSAPP_MOCK = os.getenv("CF_WHATSAPP_MOCK", "false").lower() == "true"
WHATSAPP_TOKEN = os.getenv("CF_WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("CF_WHATSAPP_PHONE_NUMBER_ID", "")
ADMIN_NUMBERS = [n.strip() for n in os.getenv("CF_WHATSAPP_ADMINS", "").split(",") if n.strip()]
# Default 15 minutes per Task 3
APPROVAL_TIMEOUT = int(os.getenv("CF_APPROVAL_TIMEOUT", "900"))
GRAPH_URL = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages" if PHONE_NUMBER_ID else ""

PENDING_DIR = Path(os.getenv("CF_WHATSAPP_PENDING_DIR", "./logs/whatsapp_pending"))
PENDING_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_PATH = Path(os.getenv("CF_AUDIT_PATH", "./logs/cma_audit.jsonl"))


def _normalize_number(num: str) -> str:
    return num.strip().lstrip("+").replace(" ", "")


def _admin_set() -> set:
    return {_normalize_number(n) for n in ADMIN_NUMBERS}


def is_allowed_approver(sender: str) -> bool:
    if not ADMIN_NUMBERS:
        return False
    return _normalize_number(sender) in _admin_set()


def hash_sender(sender: str) -> str:
    """One-way hash for evidence packs (do not store raw numbers in exports)."""
    return hashlib.sha256(_normalize_number(sender).encode()).hexdigest()[:16]


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }


def _send_text(to: str, body: str) -> bool:
    if WHATSAPP_MOCK or not WHATSAPP_ENABLED or not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        logger.info(f"[SIMULATED/MOCK WhatsApp → {to}] {body[:160]}")
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


def _format_approval_message(
    action: str, target: str, severity: str, justification: str, request_id: str, nonce: str
) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    mins = max(1, APPROVAL_TIMEOUT // 60)
    return (
        f"🚨 *CyberFortress Tier 2 Approval Required*\n\n"
        f"*ID:* `{request_id}`\n"
        f"*Time:* {ts}\n"
        f"*Severity:* {severity}\n"
        f"*Action:* {action}\n"
        f"*Target:* {target}\n"
        f"*Legal:* {justification}\n\n"
        f"Reply exactly:\n"
        f"`APPROVE {nonce}`\n"
        f"or\n"
        f"`DENY {nonce}`\n\n"
        f"Only registered admin numbers can approve.\n"
        f"_Timeout in {mins} min → automatic DENY._"
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


def _write_pending(request_id: str, meta: dict) -> None:
    path = PENDING_DIR / f"{request_id}.json"
    path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def _read_decision(request_id: str) -> Optional[dict]:
    """Decision file is JSON: {decision, sender_hash, nonce_ok, ...}"""
    decision_file = PENDING_DIR / f"{request_id}.decision"
    if not decision_file.exists():
        return None
    raw = decision_file.read_text(encoding="utf-8").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Legacy plain APPROVE/DENY
        return {"decision": raw.upper(), "sender_hash": None, "nonce_ok": False, "legacy": True}


def log_approval_event(
    request_id: str,
    action: str,
    target: str,
    result: str,
    sender_hash: Optional[str] = None,
    nonce: Optional[str] = None,
) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tag": "TT_CMA_TAG",
        "action": f"whatsapp_approval:{result}",
        "target": target,
        "severity": "INFO" if result == "APPROVE" else "INFO",
        "legislative_justification": (
            f"HITL decision for {action} on {target} | "
            f"request={request_id} | result={result} | "
            f"sender_hash={sender_hash or 'n/a'} | nonce={nonce or 'n/a'}"
        ),
        "source": "CyberFortress",
        "request_id": request_id,
        "approval_result": result,
        "sender_hash": sender_hash,
        "nonce": nonce,
    }
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    logger.info(f"Approval audit: {result} for {request_id}")


def request_approval(
    action: str,
    target: str,
    severity: str = "HIGH",
    justification: str = "Authorized defensive action under TT Computer Misuse Act",
) -> bool:
    request_id = f"CF-{int(time.time())}-{secrets.token_hex(3)}"
    nonce = secrets.token_hex(3).upper()  # 6 hex chars

    meta = {
        "action": action,
        "target": target,
        "severity": severity,
        "justification": justification,
        "created": datetime.now(timezone.utc).isoformat(),
        "nonce": nonce,
        "request_id": request_id,
        "timeout_seconds": APPROVAL_TIMEOUT,
    }
    _write_pending(request_id, meta)

    if not ADMIN_NUMBERS:
        logger.warning("No admins configured — treating as DENY")
        log_approval_event(request_id, action, target, "DENY-NO-ADMINS", nonce=nonce)
        return False

    message = _format_approval_message(action, target, severity, justification, request_id, nonce)
    for num in ADMIN_NUMBERS:
        _send_text(num, message)

    # Mock path for demos without live Meta: write a helper file operators can use
    if WHATSAPP_MOCK or not WHATSAPP_ENABLED:
        helper = PENDING_DIR / f"{request_id}.mock_hint"
        helper.write_text(
            f"MOCK MODE — to approve in demo:\n"
            f"python3 -c \"from agents.whatsapp_webhook import record_decision; "
            f"record_decision('{request_id}', 'APPROVE', '{ADMIN_NUMBERS[0]}', '{nonce}')\"\n",
            encoding="utf-8",
        )
        logger.info(f"Mock approval hint written: {helper}")

    logger.info(f"Waiting up to {APPROVAL_TIMEOUT}s for APPROVE {nonce} on {request_id}...")
    deadline = time.time() + APPROVAL_TIMEOUT

    while time.time() < deadline:
        dec = _read_decision(request_id)
        if dec:
            decision = str(dec.get("decision", "")).upper()
            sender_hash = dec.get("sender_hash")
            nonce_ok = bool(dec.get("nonce_ok"))

            if dec.get("legacy"):
                # Plain APPROVE without nonce is no longer accepted
                logger.warning(f"Legacy decision without nonce rejected for {request_id}")
                log_approval_event(request_id, action, target, "DENY-INVALID-FORMAT", sender_hash, nonce)
                return False

            if decision == "APPROVE" and nonce_ok:
                log_approval_event(request_id, action, target, "APPROVE", sender_hash, nonce)
                return True
            if decision == "APPROVE" and not nonce_ok:
                log_approval_event(request_id, action, target, "DENY-BAD-NONCE", sender_hash, nonce)
                return False
            if decision == "DENY":
                log_approval_event(request_id, action, target, "DENY", sender_hash, nonce)
                return False
            if decision in ("DENY-UNKNOWN-SENDER", "DENY-BAD-NONCE"):
                log_approval_event(request_id, action, target, decision, sender_hash, nonce)
                return False
        time.sleep(2)

    logger.warning(f"Request {request_id} timed out — TIMEOUT-DENY")
    log_approval_event(request_id, action, target, "TIMEOUT-DENY", nonce=nonce)
    # Persist decision for operators
    (PENDING_DIR / f"{request_id}.decision").write_text(
        json.dumps({"decision": "TIMEOUT-DENY", "sender_hash": None, "nonce_ok": False}),
        encoding="utf-8",
    )
    return False
