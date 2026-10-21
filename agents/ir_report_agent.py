#!/usr/bin/env python3
"""IR Team — REPORT: write incident reports for contained/investigated cases."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from core.agent_runtime import run_forever
from core.ir.cases import CaseStore
from core.ir.playbooks_text import build_incident_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [IR-REPORT] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_ir_report")

INTERVAL = int(os.getenv("CF_IR_REPORT_INTERVAL", "60"))
REPORT_DIR = Path(os.getenv("CF_IR_REPORT_DIR", "./evidence/ir_reports"))
STORE = CaseStore()


def _cycle():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for case in STORE.list_by_status(("contained", "investigating"), 30):
        if case.report_path and Path(case.report_path).exists():
            if case.status == "contained":
                case.status = "reported"
                STORE.update(case)
            continue
        md = build_incident_report(case.to_dict())
        path = REPORT_DIR / f"{case.case_id}.md"
        path.write_text(md, encoding="utf-8")
        case.report_path = str(path)
        if case.status == "contained":
            case.status = "reported"
        STORE.update(case)
        written += 1
        logger.info("Wrote report %s", path)
        try:
            if os.getenv("CF_IR_NOTIFY_REPORTS", "true").lower() in ("1", "true", "yes"):
                from core.whatsapp_report_hooks import send_live_alert

                send_live_alert(
                    f"IR report ready: {case.case_id} ({case.severity}) target={case.target}"
                )
        except Exception:
            pass
    return {"reports_written": written}


def main():
    logger.info("IR Report agent starting → %s", REPORT_DIR)
    run_forever("ir_report", _cycle, INTERVAL, error_sleep=20.0)


if __name__ == "__main__":
    main()
