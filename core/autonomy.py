#!/usr/bin/env python3
"""
CyberFortress Autonomy Engine
Implements the tiered Human-in-the-Loop decision model.
"""

from enum import Enum
from typing import Optional


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
    "isolate_endpoint",   # can be Tier 1 or 2 depending on scope
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


def request_approval(action: str, target: str) -> bool:
    """
    Placeholder for WhatsApp interactive prompt.
    In production this will call core.whatsapp_gateway and wait for APPROVE.
    """
    print(f"[HITL] Tier 2 action '{action}' on {target} requires WhatsApp APPROVE")
    print("[HITL] (MVP) Simulating wait for human approval...")
    # TODO: real WhatsApp API integration
    return False  # default deny until real gateway is wired


def execute_with_autonomy(action: str, target: str, scope: str = "single", force: bool = False) -> bool:
    """
    Main entry point used by playbooks and agents.
    Returns True if action was allowed to proceed.
    """
    tier = classify_action(action, scope)

    if force:
        print(f"[AUTONOMY] FORCE override — executing {action} on {target}")
        return True

    if tier == AutonomyTier.TIER_1_FULL:
        print(f"[AUTONOMY] Tier 1 — executing immediately + notifying")
        return True

    # Tier 2
    approved = request_approval(action, target)
    if approved:
        print(f"[AUTONOMY] Tier 2 — APPROVED — executing {action}")
        return True
    else:
        print(f"[AUTONOMY] Tier 2 — DENIED or pending — action held")
        return False
