#!/usr/bin/env python3
"""IR Team — INVESTIGATE: enrich cases with findings + audit correlation."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from core.agent_runtime import run_forever
from core.ir.cases import CaseStore
from core.ir.playbooks_text import investigate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [IR-INVESTIGATE] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_ir_investigate")

INTERVAL = int(os.getenv("CF_IR_INVESTIGATE_INTERVAL", "25"))
AUDIT = Path(os.getenv("CF_AUDIT_PATH", "./logs/cma_audit.jsonl"))
STORE = CaseStore()


def _audit_for_target(target: str, limit: int = 12):
    if not AUDIT.exists():
        return []
    out = []
    try:
        for line in reversed(AUDIT.read_text(encoding="utf-8").splitlines()):
            if not line.strip():
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(e.get("target")) == str(target):
                out.append(e)
            if len(out) >= limit:
                break
    except Exception as ex:
        logger.warning("audit correlate: %s", ex)
    return list(reversed(out))


def _cycle():
    done = 0
    for case in STORE.list_open(25):
        if case.status not in ("open", "investigating"):
            continue
        recent = _audit_for_target(case.target)
        needs = (not case.findings) or case.status == "open" or len(case.related_events) > 0
        if not needs and case.status == "investigating" and case.findings:
            continue
        case.findings = investigate(
            case.indicator,
            case.target,
            case.severity,
            case.source,
            related_count=len(case.related_events),
            recent_audit=recent,
        )
        case.status = "investigating"
        if case.score >= 80 and "priority" not in case.tags:
            case.tags = list(case.tags) + ["priority"]
        STORE.update(case)
        done += 1
        logger.info("Investigated %s findings=%s score=%s", case.case_id, len(case.findings), case.score)
    return {"investigated": done}


def main():
    logger.info("IR Investigate agent starting")
    run_forever("ir_investigate", _cycle, INTERVAL, error_sleep=15.0)


if __name__ == "__main__":
    main()
