#!/usr/bin/env python3
"""
CyberFortress Autonomy Engine
Tiered HITL + legal mapper + compliance + containment + circuit breaker.

Safety:
  CF_CONTAINMENT_LIVE=false  → dry-run (default until pilot sign-off)
  CF_ALLOW_FORCE=false       → --force blocked; prefer WhatsApp APPROVE
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

DRY_RUN = os.getenv("CF_CONTAINMENT_LIVE", "false").lower() != "true"
ALLOW_FORCE = os.getenv("CF_ALLOW_FORCE", "false").lower() == "true"


class AutonomyTier(Enum):
    TIER_1_FULL = 1
    TIER_2_GUARDED = 2


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
    tier = classify_action(action, scope)
    mapping = get_justification(action)
    justification = f"{mapping['section']}: {mapping['justification']}"

    logger.info(f"Evaluating action={action} target={target} scope={scope} force={force} tier={tier.name}")

    # Prefer WhatsApp APPROVE — force requires explicit CF_ALLOW_FORCE=true
    if force and not ALLOW_FORCE:
        logger.error("FORCE requested but CF_ALLOW_FORCE is false — refusing")
        write_cma_entry(
            action,
            target,
            justification + " [FORCE BLOCKED — CF_ALLOW_FORCE=false; use WhatsApp APPROVE]",
            severity="INFO",
        )
        return False

    if not breaker.allow(force=force):
        write_cma_entry(
            action,
            target,
            justification + f" [BLOCKED BY CIRCUIT BREAKER: {breaker.reason}]",
            severity="CRITICAL",
        )
        logger.error("Action blocked by circuit breaker")
        return False

    if force:
        logger.warning(f"FORCE override — executing {action} on {target}")
        write_cma_entry(action, target, justification + " [FORCE OVERRIDE]", severity="CRITICAL")
        notify_tier1(action, target, justification + " (FORCE)")
        _perform_containment(action, target)
        breaker.record(action, target, severity="CRITICAL", tier=2)
        return True

    if tier == AutonomyTier.TIER_1_FULL:
        logger.info("Tier 1 — executing immediately + notifying")
        write_cma_entry(action, target, justification, severity=severity)
        notify_tier1(action, target, justification)
        _perform_containment(action, target)
        breaker.record(action, target, severity=severity, tier=1)
        return True

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

    logger.warning("Tier 2 — DENIED or timed out — action held")
    write_cma_entry(
        action,
        target,
        justification + " [HELD — no approval]",
        severity="INFO",
    )
    return False
