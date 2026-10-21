#!/usr/bin/env python3
"""IR Team — FIX/RESPOND: execute ROE-safe playbooks (dry-run unless armed)."""

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

INTERVAL = int(os.getenv("CF_IR_RESPOND_INTERVAL", "50"))
STORE = CaseStore()
AUTO = os.getenv("CF_IR_AUTO_RESPOND", "true").lower() in ("1", "true", "yes")


def _cycle():
    acted = 0
    live = os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "true"
    for case in STORE.list_open(15):
        if case.status not in ("investigating", "open"):
            continue
        if not case.findings:
            continue
        if any(a.get("success") for a in case.actions):
            case.status = "contained"
            STORE.update(case)
            continue
        action = recommend_action(case.indicator, case.severity)
        if not is_action_authorized(action):
            case.actions.append(
                {
                    "at": datetime.now(timezone.utc).isoformat(),
                    "action": action,
                    "success": False,
                    "dry_run": not live,
                    "detail": "blocked by ROE allow-list",
                }
            )
            STORE.update(case)
            logger.warning("%s action %s denied by ROE", case.case_id, action)
            continue
        if not AUTO:
            case.actions.append(
                {
                    "at": datetime.now(timezone.utc).isoformat(),
                    "action": action,
                    "success": False,
                    "dry_run": True,
                    "detail": "CF_IR_AUTO_RESPOND=false — recommendation only",
                }
            )
            STORE.update(case)
            continue
        ok = execute_with_autonomy(
            action=action,
            target=case.target,
            scope="single",
            force=False,
            severity=case.severity,
        )
        case.actions.append(
            {
                "at": datetime.now(timezone.utc).isoformat(),
                "action": action,
                "success": bool(ok),
                "dry_run": not live,
                "detail": "autonomy pipeline",
            }
        )
        if ok or not live:
            case.status = "contained" if ok or not live else case.status
        STORE.update(case)
        acted += 1
        logger.info(
            "%s respond action=%s success=%s live=%s",
            case.case_id,
            action,
            ok,
            live,
        )
    return {"responded": acted, "live": live}


def main():
    logger.info("IR Respond agent starting (respects LIVE + ROE + WhatsApp Tier-2)")
    run_forever("ir_respond", _cycle, INTERVAL, error_sleep=20.0)


if __name__ == "__main__":
    main()
