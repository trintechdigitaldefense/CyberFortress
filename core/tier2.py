#!/usr/bin/env python3
"""Tier-2 guarded response helpers."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

logger = logging.getLogger("cf_tier2")

TIER2_RISK: Dict[str, Dict[str, str]] = {
    "isolate_endpoint": {
        "risk": "HIGH",
        "impact": "Host loses network access except management paths if configured",
        "rollback": "restore_endpoint",
    },
    "subnet_isolation": {
        "risk": "CRITICAL",
        "impact": "Entire subnet segment may lose connectivity",
        "rollback": "restore_subnet",
    },
    "credential_rotation": {
        "risk": "HIGH",
        "impact": "Active sessions using old credentials may fail",
        "rollback": "manual identity restore",
    },
    "halt_operations": {
        "risk": "CRITICAL",
        "impact": "Business services may stop",
        "rollback": "manual restart / restore playbook",
    },
    "restore_subnet": {
        "risk": "MEDIUM",
        "impact": "Re-opens previously isolated segment",
        "rollback": "re-isolate if needed",
    },
}


def risk_card(action: str) -> Dict[str, str]:
    return TIER2_RISK.get(
        action,
        {
            "risk": "HIGH",
            "impact": "Elevated change — operator judgment required",
            "rollback": "see runbook",
        },
    )


def list_open_requests() -> List[Dict[str, Any]]:
    try:
        from core.whatsapp_gateway import list_pending

        return list_pending()
    except Exception as e:
        logger.warning("list_pending failed: %s", e)
        return []


def status_summary() -> Dict[str, Any]:
    pending = list_open_requests()
    return {
        "tier": 2,
        "pending_count": len(pending),
        "pending": [
            {
                "request_id": p.get("request_id"),
                "action": p.get("action"),
                "target": p.get("target"),
                "severity": p.get("severity"),
                "seconds_left": p.get("seconds_left"),
                "risk": risk_card(str(p.get("action") or "")).get("risk"),
            }
            for p in pending
        ],
        "timeout_s": int(os.getenv("CF_APPROVAL_TIMEOUT", "900")),
        "require_whatsapp_approve": True,
        "allow_force": os.getenv("CF_ALLOW_FORCE", "false").lower() == "true",
    }


def request_tier2(
    action: str,
    target: str,
    severity: str = "HIGH",
    justification: str = "",
) -> bool:
    from core.autonomy import execute_with_autonomy

    card = risk_card(action)
    just = justification or f"Tier-2 {action}: {card.get('impact')}"
    just = f"{just} | risk={card.get('risk')} | rollback={card.get('rollback')}"
    return execute_with_autonomy(
        action=action,
        target=target,
        scope="single" if action != "subnet_isolation" else "subnet",
        force=False,
        severity=severity,
    )
