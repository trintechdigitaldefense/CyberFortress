#!/usr/bin/env python3
"""IR Team — DETECT: open incident cases from high-severity telemetry/audit."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from core.agent_runtime import run_forever
from core.ir.cases import CaseStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [IR-DETECT] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_ir_detect")

INTERVAL = int(os.getenv("CF_IR_DETECT_INTERVAL", "45"))
AUDIT = Path(os.getenv("CF_AUDIT_PATH", "./logs/cma_audit.jsonl"))
STATE = Path(os.getenv("CF_LOG_DIR", "./logs")) / "ir_detect_offset"
STORE = CaseStore()
SEV_OK = {"HIGH", "CRITICAL"}


def _offset() -> int:
    if STATE.exists():
        try:
            return int(STATE.read_text().strip() or "0")
        except Exception:
            return 0
    return 0


def _set_offset(n: int) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(str(n), encoding="utf-8")


def _cycle():
    if not AUDIT.exists():
        return {"opened": 0, "note": "no audit yet"}
    raw = AUDIT.read_text(encoding="utf-8")
    lines = raw.splitlines()
    start = _offset()
    if start > len(lines):
        start = 0
    opened = 0
    for line in lines[start:]:
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        sev = str(e.get("severity", "")).upper()
        if sev not in SEV_OK:
            continue
        action = str(e.get("action", ""))
        if not (action.startswith("detection:") or action in ("block_ip", "isolate_endpoint")):
            if "detection" not in action:
                continue
        indicator = e.get("indicator") or action.replace("detection:", "")
        target = e.get("target", "unknown")
        source = e.get("source", "audit")
        exists = any(
            c.indicator == indicator and c.target == target for c in STORE.list_open(30)
        )
        if exists:
            continue
        case = STORE.create(
            indicator=str(indicator),
            target=str(target),
            source=str(source),
            severity=sev,
        )
        opened += 1
        logger.info("Opened %s severity=%s target=%s", case.case_id, sev, target)
    _set_offset(len(lines))
    return {"opened": opened, "audit_lines": len(lines)}


def main():
    logger.info("IR Detect agent starting interval=%ss", INTERVAL)
    run_forever("ir_detect", _cycle, INTERVAL, error_sleep=15.0)


if __name__ == "__main__":
    main()
