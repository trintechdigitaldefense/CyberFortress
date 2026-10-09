#!/usr/bin/env python3
"""
CyberFortress WhatsApp HITL Gateway
Out-of-band approval channel for Tier 2 actions.

MVP: Structured messages + simulated interactive APPROVE/DENY.
Production: Replace with real WhatsApp Business API / Cloud API or Meta Graph API.
"""

import os
import time
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = logging.getLogger("cf_whatsapp_gateway")

# Configuration (prefer environment variables in production)
WHATSAPP_ENABLED = os.getenv("CF_WHATSAPP_ENABLED", "false").lower() == "true"
WHATSAPP_API_URL = os.getenv("CF_WHATSAPP_API_URL", "")
WHATSAPP_TOKEN = os.getenv("CF_WHATSAPP_TOKEN", "")
ADMIN_NUMBERS = [n.strip() for n in os.getenv("CF_WHATSAPP_ADMINS", "").split(",") if n.strip()]
APPROVAL_TIMEOUT_SECONDS = int(os.getenv("CF_APPROVAL_TIMEOUT", "300"))  # 5 minutes default


def _format_approval_message(action: str, target: str, severity: str, justification: str) -> str:
    """Create a clear, actionable WhatsApp message for admins."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return (
        f"🚨 *CyberFortress Tier 2 Approval Required*\n\n"
        f"*Time:* {ts}\n"
        f"*Severity:* {severity}\n"
        f"*Action:* {action}\n"
        f"*Target:* {target}\n"
        f"*Legal Justification:* {justification}\n\n"
        f"Reply with:\n"
        f"✅ *APPROVE*  — execute immediately\n"
        f"❌ *DENY*     — cancel action\n\n"
        f"_Timeout in {APPROVAL_TIMEOUT_SECONDS // 60} minutes. Default = DENY._"
    )


def send_notification(message: str, level: str = "INFO") -> bool:
    """
    Send a one-way notification (Tier 1 visibility).
    Returns True if sent (or simulated).
    """
    if not WHATSAPP_ENABLED:
        logger.info(f"[SIMULATED WhatsApp NOTIFY] {message[:120]}...")
        return True

    # TODO: Real WhatsApp Business API call here
    # Example shape:
    # requests.post(WHATSAPP_API_URL, headers={...}, json={...})
    logger.info(f"[WhatsApp NOTIFY] {message[:80]}...")
    return True


def request_approval(
    action: str,
    target: str,
    severity: str = "HIGH",
    justification: str = "Authorized defensive action under TT Computer Misuse Act",
) -> bool:
    """
    Send interactive approval request and wait for response.
    Returns True only if an authorized admin replies APPROVE within timeout.
    """
    message = _format_approval_message(action, target, severity, justification)

    if not WHATSAPP_ENABLED:
        logger.warning("[SIMULATED] WhatsApp gateway disabled — treating as DENY for safety")
        logger.info(f"Would have sent:\n{message}")
        return False

    # 1. Send the interactive message to all admin numbers
    sent = send_notification(message, level="CRITICAL")
    if not sent:
        logger.error("Failed to send WhatsApp approval request")
        return False

    # 2. Wait for reply (MVP: polling placeholder)
    # In production this would use webhooks or a message store.
    logger.info(f"Waiting up to {APPROVAL_TIMEOUT_SECONDS}s for APPROVE/DENY...")
    deadline = time.time() + APPROVAL_TIMEOUT_SECONDS

    while time.time() < deadline:
        # TODO: Poll WhatsApp API or check inbound webhook store for replies
        # from any number in ADMIN_NUMBERS containing "APPROVE" or "DENY"
        time.sleep(5)

        # Placeholder for real reply detection
        # reply = check_inbound_replies()
        # if reply and reply.upper().startswith("APPROVE"):
        #     return True
        # if reply and reply.upper().startswith("DENY"):
        #     return False

    logger.warning("Approval timed out — defaulting to DENY")
    return False


def notify_tier1(action: str, target: str, justification: str) -> None:
    """Fire-and-forget notification for Tier 1 actions."""
    msg = (
        f"✅ *CyberFortress Tier 1 Action Executed*\n"
        f"Action: {action}\n"
        f"Target: {target}\n"
        f"Justification: {justification}\n"
        f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
    )
    send_notification(msg, level="INFO")
