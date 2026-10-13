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
  CF_APPROVAL_TIMEOUT=900
  CF_WHATSAPP_MOCK=true
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
        f"CyberFortress Tier 2 Approval Required\n\n"
        f"ID: {request_id}\n"
        f"Time: {ts}\n"
        f"Severity: {severity}\n"
        f"Action: {action}\n"
        f"Target: {target}\n"
        f"Legal: {justification}\n\n"
        f"Reply exactly:\n"
        f"APPROVE {nonce}\n"
        f"or\n"
        f"DENY {nonce}\n\n"
        f"Only registered admin numbers can approve.\n"
        f"Timeout in {mins} min → automatic DENY."
    )


def _write_pending(request_id: str, meta: dict) -> None:
    path = PENDING_DIR / f"{request_id}.json"
    path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def _log_approval_decision(
    result: str,
    request_id: str,
    action: str,
    target: str,
    sender_hash: Optional[str] = None,
    nonce: Optional[str] = None,
) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tag": "TT_CMA_TAG",
        "action": f"whatsapp_approval:{result}",
        "target": target,
        "severity": "INFO",
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
    try:
        from core.audit_chain import append_chained

        append_chained(AUDIT_PATH, entry)
    except Exception:
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
    nonce = secrets.token_hex(3).upper()

    meta = {
        "request_id": request_id,
        "nonce": nonce,
        "action": action,
        "target": target,
        "severity": severity,
        "justification": justification,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": time.time() + APPROVAL_TIMEOUT,
    }
    _write_pending(request_id, meta)

    body = _format_approval_message(action, target, severity, justification, request_id, nonce)

    if not ADMIN_NUMBERS:
        logger.warning("No admins configured — treating as DENY")
        _log_approval_decision("DENY-NO-ADMINS", request_id, action, target)
        (PENDING_DIR / f"{request_id}.decision").write_text(
            json.dumps({"decision": "DENY-NO-ADMINS", "nonce_ok": False}),
            encoding="utf-8",
        )
        return False

    for admin in ADMIN_NUMBERS:
        _send_text(admin, body)

    # Poll for decision file (webhook or mock writes it)
    deadline = time.time() + APPROVAL_TIMEOUT
    decision_path = PENDING_DIR / f"{request_id}.decision"
    while time.time() < deadline:
        if decision_path.exists():
            try:
                data = json.loads(decision_path.read_text(encoding="utf-8"))
            except Exception:
                time.sleep(1)
                continue
            decision = str(data.get("decision", "")).upper()
            nonce_ok = bool(data.get("nonce_ok", False))
            if decision == "APPROVE" and nonce_ok:
                _log_approval_decision(
                    "APPROVE",
                    request_id,
                    action,
                    target,
                    sender_hash=data.get("sender_hash"),
                    nonce=nonce,
                )
                return True
            _log_approval_decision(
                decision or "DENY",
                request_id,
                action,
                target,
                sender_hash=data.get("sender_hash"),
                nonce=nonce,
            )
            return False
        time.sleep(2)

    logger.warning(f"Approval timeout for {request_id}")
    _log_approval_decision("DENY-TIMEOUT", request_id, action, target, nonce=nonce)
    (PENDING_DIR / f"{request_id}.decision").write_text(
        json.dumps({"decision": "DENY-TIMEOUT", "nonce_ok": False}),
        encoding="utf-8",
    )
    return False
