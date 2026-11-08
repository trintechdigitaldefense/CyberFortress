#!/usr/bin/env python3
"""
CyberFortress Autonomy Engine
Tiered HITL + legal mapper + compliance + containment + circuit breaker + ROE allow-list.

Safety:
  CF_CONTAINMENT_LIVE=false  → dry-run (default until pilot sign-off)
  CF_ALLOW_FORCE=false       → --force blocked; prefer WhatsApp APPROVE
  ROE allow-list             → only authorized_actions from pilot_signoff.json
"""

from enum import Enum
import logging
import os

from core.legal_mapper import get_justification
import core.whatsapp_report_hooks  # noqa: F401 — dashboard number + live alerts
from core.whatsapp_gateway import request_approval as wa_request_approval, notify_tier1, send_live_alert
from agents.compliance_logger import write_cma_entry
from core.containment.drivers import get_driver
from core.circuit_breaker import breaker
from core.roe import is_action_authorized

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
    "unblock_ip",
    "restore_endpoint",
}

TIER_2_ACTIONS = {
    "isolate_endpoint",
    "subnet_isolation",
    "credential_rotation",
    "halt_operations",
    "restore_subnet",
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
    try:
        result = driver.execute(target=target, action=action)
    except Exception as exc:
        logger.exception("Containment driver raised for %s on %s", action, target)
        return {"success": False, "driver": driver.name, "action": action, "target": target, "details": f"driver exception: {type(exc).__name__}"}
    if not isinstance(result, dict) or result.get("success") is not True:
        logger.error("Containment failed: %s", result.get("details") if isinstance(result, dict) else "invalid driver result")
        return result if isinstance(result, dict) else {"success": False, "details": "invalid driver result"}
    if result.get("dry_run") is True:
        logger.info("Containment simulated only; no live action was executed")
        return {**result, "success": False, "simulated": True}
    verification = result.get("verify")
    if isinstance(verification, dict):
        if action in ("block_ip", "isolate_endpoint", "subnet_isolation") and verification.get("verified") is False:
            return {**result, "success": False, "details": "post-action verification failed"}
        if action in ("unblock_ip", "restore_endpoint", "restore_subnet") and verification.get("cleared") is False:
            return {**result, "success": False, "details": "rollback verification failed"}
    logger.info("Containment driver reports verified success: %s", result.get("details"))
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

    if not is_action_authorized(action):
        write_cma_entry(
            action,
            target,
            justification + " [BLOCKED — not in ROE authorized_actions]",
            severity="CRITICAL",
        )
        logger.error(f"ROE deny: {action}")
        return False

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
        result = _perform_containment(action, target)
        if not isinstance(result, dict) or result.get("success") is not True:
            write_cma_entry(action, target, justification + " [EXECUTION FAILED — FORCE path]", severity="CRITICAL", execution_result=result)
            return False
        write_cma_entry(action, target, justification + " [EXECUTION VERIFIED — FORCE path]", severity="CRITICAL", execution_result=result)
        breaker.record(action, target, severity="CRITICAL", tier=2)
        return True

    if tier == AutonomyTier.TIER_1_FULL:
        logger.info("Tier 1 — executing immediately + notifying")
        write_cma_entry(action, target, justification, severity=severity)
        notify_tier1(action, target, justification)
        result = _perform_containment(action, target)
        if not isinstance(result, dict) or result.get("success") is not True:
            write_cma_entry(action, target, justification + " [EXECUTION FAILED — Tier 1]", severity="CRITICAL", execution_result=result)
            return False
        write_cma_entry(action, target, justification + " [EXECUTION VERIFIED — Tier 1]", severity=severity, execution_result=result)
        breaker.record(action, target, severity=severity, tier=1)
        return True

    logger.info(f"Tier 2 — requesting WhatsApp APPROVE for {action} on {target}")
    try:
        from core.tier2 import risk_card

        card = risk_card(action)
        justification = (
            f"{justification} | risk={card.get('risk')} | "
            f"impact={card.get('impact')} | rollback={card.get('rollback')}"
        )
    except Exception:
        pass
    try:
        send_live_alert(
            title="Tier-2 approval requested",
            detail=str(justification or "")[:300],
            severity=str(severity or "HIGH"),
            action=action,
            target=target,
        )
    except Exception:
        pass
    approved = wa_request_approval(
        action=action,
        target=target,
        severity=severity,
        justification=justification,
    )

    if approved:
        logger.info(f"Tier 2 — APPROVED — executing {action}")
        write_cma_entry(action, target, justification + " [APPROVED via WhatsApp]", severity=severity)
        result = _perform_containment(action, target)
        if not isinstance(result, dict) or result.get("success") is not True:
            write_cma_entry(action, target, justification + " [EXECUTION FAILED — Tier 2]", severity="CRITICAL", execution_result=result)
            return False
        write_cma_entry(action, target, justification + " [EXECUTION VERIFIED — Tier 2]", severity=severity, execution_result=result)
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
