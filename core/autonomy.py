#!/usr/bin/env python3
"""
CyberFortress Autonomy Engine
Implements the tiered Human-in-the-Loop decision model.
Integrates WhatsApp gateway + legal mapper + compliance logging.
"""

from enum import Enum
from typing import Optional
import logging

from core.legal_mapper import get_justification
from core.whatsapp_gateway import request_approval as wa_request_approval, notify_tier1
from agents.compliance_logger import write_cma_entry

logger = logging.getLogger("cf_autonomy")


class AutonomyTier(Enum):
    TIER_1_FULL = 1      # Instant execution + notification
    TIER_2_GUARDED = 2   # Pause → WhatsApp APPROVE required


# Actions classified by tier
TIER_1_ACTIONS = {
    "block_ip",
    "terminate_session",
    "deploy_decoy",
}

TIER_2_ACTIONS = {
    "isolate_endpoint",
    "subnet_isolation",
    "credential_rotation",
    "halt_operations",
}


def classify_action(action: str, scope: str = "single") -> AutonomyTier:
    """
    Decide which autonomy tier an action falls under.
    scope = "single" | "subnet" | "fleet"
    """
    if action in TIER_1_ACTIONS and scope == "single":
        return AutonomyTier.TIER_1_FULL
    if action in TIER_2_ACTIONS or scope in ("subnet", "fleet"):
        return AutonomyTier.TIER_2_GUARDED
    # Default safe side
    return AutonomyTier.TIER_2_GUARDED


def execute_with_autonomy(
    action: str,
    target: str,
    scope: str = "single",
    force: bool = False,
    severity: str = "HIGH",
) -> bool:
    """
    Main entry point used by playbooks and agents.
    Returns True if action was allowed to proceed.
    Always writes a CMA-mapped compliance log entry.
    """
    tier = classify_action(action, scope)
    mapping = get_justification(action)
    justification = f"{mapping['section']}: {mapping['justification']}"

    logger.info(f"Evaluating action={action} target={target} scope={scope} force={force} tier={tier.name}")

    # --- FORCE override (still logged) ---
    if force:
        logger.warning(f"FORCE override — executing {action} on {target}")
        write_cma_entry(action, target, justification + " [FORCE OVERRIDE]", severity="CRITICAL")
        notify_tier1(action, target, justification + " (FORCE)")
        return True

    # --- Tier 1: execute immediately + notify ---
    if tier == AutonomyTier.TIER_1_FULL:
        logger.info(f"Tier 1 — executing immediately + notifying")
        write_cma_entry(action, target, justification, severity=severity)
        notify_tier1(action, target, justification)
        return True

    # --- Tier 2: request WhatsApp approval ---
    logger.info(f"Tier 2 — requesting WhatsApp APPROVE for {action} on {target}")
    approved = wa_request_approval(
        action=action,
        target=target,
        severity=severity,
        justification=justification,
    )

    if approved:
        logger.info(f"Tier 2 — APPROVED — executing {action}")
        write_cma_entry(action, target, justification + " [APPROVED via WhatsApp]", severity=severity)
        return True
    else:
        logger.warning(f"Tier 2 — DENIED or timed out — action held")
        write_cma_entry(
            action,
            target,
            justification + " [HELD — no approval]",
            severity="INFO",
        )
        return False
