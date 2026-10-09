#!/usr/bin/env python3
"""
CyberFortress Autonomy Engine
Implements the tiered Human-in-the-Loop decision model.
Integrates WhatsApp gateway + legal mapper + compliance logging +
real containment drivers + fail-safe circuit breaker.
"""

from enum import Enum
import logging
import os

from core.legal_mapper import get_justification
from core.whatsapp_gateway import request_approval as wa_request_approval, notify_tier1
from agents.compliance_logger import write_cma_entry
from core.containment.drivers import get_driver
from core.circuit_breaker import breaker

logger = logging.getLogger("cf_autonomy")

# Default to dry-run for safety. Set CF_CONTAINMENT_LIVE=true to enable real actions.
DRY_RUN = os.getenv("CF_CONTAINMENT_LIVE", "false").lower() != "true"


class AutonomyTier(Enum):
    TIER_1_FULL = 1      # Instant execution + notification
    TIER_2_GUARDED = 2   # Pause → WhatsApp APPROVE required


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
    if action in TIER_1_ACTIONS and scope == "single":
        return AutonomyTier.TIER_1_FULL
    if action in TIER_2_ACTIONS or scope in ("subnet", "fleet"):
        return AutonomyTier.TIER_2_GUARDED
    return AutonomyTier.TIER_2_GUARDED


def _perform_containment(action: str, target: str) -> dict:
    """Call the real containment driver and return its result."""
    driver = get_driver(action, dry_run=DRY_RUN)
    logger.info(f"Invoking containment driver '{driver.name}' for {action} on {target} (dry_run={DRY_RUN})")
    result = driver.execute(target=target, action=action)
    if result.get("success"):
        logger.info(f"Containment success: {result.get('details')}")
    else:
        logger.error(f"Containment failed: {result.get('details')}")
    return result


def execute_with_autonomy(
    action: str,
    target: str,
    scope: str = "single",
    force: bool = False,
    severity: str = "HIGH",
) -> bool:
    """
    Main entry point used by playbooks and agents.
    Returns True if action was authorized AND containment was attempted.
    Always writes a CMA-mapped compliance log entry.
    """
    tier = classify_action(action, scope)
    mapping = get_justification(action)
    justification = f"{mapping['section']}: {mapping['justification']}"

    logger.info(f"Evaluating action={action} target={target} scope={scope} force={force} tier={tier.name}")

    # --- Circuit Breaker check ---
    if not breaker.allow(force=force):
        write_cma_entry(
            action,
            target,
            justification + f" [BLOCKED BY CIRCUIT BREAKER: {breaker.reason}]",
            severity="CRITICAL",
        )
        logger.error("Action blocked by circuit breaker")
        return False

    # --- FORCE override ---
    if force:
        logger.warning(f"FORCE override — executing {action} on {target}")
        write_cma_entry(action, target, justification + " [FORCE OVERRIDE]", severity="CRITICAL")
        notify_tier1(action, target, justification + " (FORCE)")
        _perform_containment(action, target)
        breaker.record(action, target, severity="CRITICAL", tier=2)
        return True

    # --- Tier 1: execute immediately + notify ---
    if tier == AutonomyTier.TIER_1_FULL:
        logger.info("Tier 1 — executing immediately + notifying")
        write_cma_entry(action, target, justification, severity=severity)
        notify_tier1(action, target, justification)
        _perform_containment(action, target)
        breaker.record(action, target, severity=severity, tier=1)
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
        _perform_containment(action, target)
        breaker.record(action, target, severity=severity, tier=2)
        return True
    else:
        logger.warning("Tier 2 — DENIED or timed out — action held")
        write_cma_entry(
            action,
            target,
            justification + " [HELD — no approval]",
            severity="INFO",
        )
        return False
