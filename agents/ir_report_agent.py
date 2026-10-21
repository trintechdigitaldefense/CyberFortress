#!/usr/bin/env python3
"""IR Team — REPORT: MD+HTML incident reports; optional WhatsApp notify."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from core.agent_runtime import run_forever
from core.ir.cases import CaseStore
from core.ir.playbooks_text import build_incident_html, build_incident_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [IR-REPORT] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_ir_report")

INTERVAL = int(os.getenv("CF_IR_REPORT_INTERVAL", "45"))
REPORT_DIR = Path(os.getenv("CF_IR_REPORT_DIR", "./evidence/ir_reports"))
STORE = CaseStore()


def _cycle():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for case in STORE.list_by_status(
        ("contained", "investigating", "awaiting_approval", "reported"), 40
    ):
        md_path = REPORT_DIR / f"{case.case_id}.md"
        html_path = REPORT_DIR / f"{case.case_id}.html"
        data = case.to_dict()
        md = build_incident_report(data)
        html = build_incident_html(data)
        rewrite = not md_path.exists() or case.status in (
            "contained",
            "investigating",
            "awaiting_approval",
        )
        if not rewrite:
            continue
        md_path.write_text(md, encoding="utf-8")
        html_path.write_text(html, encoding="utf-8")
        case.report_path = str(md_path)
        if case.status == "contained":
            case.status = "reported"
        STORE.update(case)
        written += 1
        logger.info("Report %s (%s)", case.case_id, case.status)
        try:
            if os.getenv("CF_IR_NOTIFY_REPORTS", "true").lower() in ("1", "true", "yes"):
                if case.status == "reported" or case.severity in ("HIGH", "CRITICAL"):
                    from core.whatsapp_report_hooks import send_live_alert

                    send_live_alert(
                        f"IR {case.case_id}: {case.severity} {case.indicator} on {case.target} "
                        f"status={case.status} score={case.score}"
                    )
        except Exception:
            pass
    return {"reports_written": written, "report_dir": str(REPORT_DIR), **STORE.summary()}


def main():
    logger.info("IR Report agent → %s", REPORT_DIR)
    run_forever("ir_report", _cycle, INTERVAL, error_sleep=20.0)


if __name__ == "__main__":
    main()
