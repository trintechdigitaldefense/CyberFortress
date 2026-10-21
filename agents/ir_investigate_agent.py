#!/usr/bin/env python3
"""IR Team — FIND/INVESTIGATE: enrich open cases with structured findings."""

from __future__ import annotations

import logging
import os

from core.agent_runtime import run_forever
from core.ir.cases import CaseStore
from core.ir.playbooks_text import investigate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [IR-INVESTIGATE] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_ir_investigate")

INTERVAL = int(os.getenv("CF_IR_INVESTIGATE_INTERVAL", "40"))
STORE = CaseStore()


def _cycle():
    done = 0
    for case in STORE.list_open(20):
        if case.status not in ("open", "investigating"):
            continue
        if case.findings and case.status == "investigating":
            continue
        case.findings = investigate(case.indicator, case.target, case.severity, case.source)
        case.status = "investigating"
        STORE.update(case)
        done += 1
        logger.info("Investigated %s (%s findings)", case.case_id, len(case.findings))
    return {"investigated": done}


def main():
    logger.info("IR Investigate agent starting")
    run_forever("ir_investigate", _cycle, INTERVAL, error_sleep=15.0)


if __name__ == "__main__":
    main()
