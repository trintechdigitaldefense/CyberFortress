#!/usr/bin/env python3
"""IR Team — RESPOND: ROE-safe playbooks via autonomy (dry-run unless armed)."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from core.agent_runtime import run_forever
from core.autonomy import execute_with_autonomy
from core.ir.cases import CaseStore
from core.ir.playbooks_text import recommend_action
from core.roe import is_action_authorized

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [IR-RESPOND] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_ir_respond")

INTERVAL = int(os.getenv("CF_IR_RESPOND_INTERVAL", "35"))
STORE = CaseStore()
AUTO = os.getenv("CF_IR_AUTO_RESPOND", "true").lower() in ("1", "true", "yes")
MIN_SCORE = int(os.getenv("CF_IR_RESPOND_MIN_SCORE", "60"))


def _cycle():
    acted = held = denied = 0
    live = os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "true"
    for case in STORE.list_open(20):
        if case.status in ("contained", "reported", "closed", "suppressed"):
            continue
        if case.status not in ("investigating", "open", "awaiting_approval"):
            continue
        if not case.findings:
            continue
        if case.score < MIN_SCORE:
            continue
        if any(a.get("success") for a in case.actions):
            case.status = "contained"
            STORE.update(case)
            continue

        action = recommend_action(case.indicator, case.severity)
        now = datetime.now(timezone.utc).isoformat()

        if not is_action_authorized(action):
            case.actions.append(
                {
                    "at": now,
                    "action": action,
                    "success": False,
                    "dry_run": not live,
                    "detail": "blocked by ROE allow-list",
                }
            )
            STORE.update(case)
            denied += 1
            logger.warning("%s ROE denied %s", case.case_id, action)
            continue

        if not AUTO:
            case.actions.append(
                {
                    "at": now,
                    "action": action,
                    "success": False,
                    "dry_run": True,
                    "detail": "CF_IR_AUTO_RESPOND=false — recommendation only",
                }
            )
            STORE.update(case)
            held += 1
            continue

        ok = execute_with_autonomy(
            action=action,
            target=case.target,
            scope="single",
            force=False,
            severity=case.severity,
        )
        if ok:
            status_after = "contained"
            detail = "autonomy pipeline"
        elif live:
            status_after = "awaiting_approval"
            detail = "live mode — may be waiting WhatsApp APPROVE or breaker"
        else:
            status_after = "contained"
            detail = "MONITORING dry-run — action planned/logged via autonomy"

        case.actions.append(
            {
                "at": now,
                "action": action,
                "success": bool(ok) or (not live),
                "dry_run": not live,
                "detail": detail,
            }
        )
        case.status = status_after
        STORE.update(case)
        acted += 1
        logger.info(
            "%s action=%s ok=%s live=%s status=%s",
            case.case_id,
            action,
            ok,
            live,
            status_after,
        )
    return {"responded": acted, "held": held, "denied": denied, "live": live}


def main():
    logger.info("IR Respond agent (LIVE+ROE+Tier-2) min_score=%s", MIN_SCORE)
    run_forever("ir_respond", _cycle, INTERVAL, error_sleep=20.0)


if __name__ == "__main__":
    main()
