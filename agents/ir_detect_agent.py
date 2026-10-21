#!/usr/bin/env python3
"""IR Team — DETECT: open/correlate cases from high-severity audit events."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from core.agent_runtime import run_forever
from core.ir.cases import CaseStore
from core.ir.scoring import score_event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [IR-DETECT] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_ir_detect")

INTERVAL = int(os.getenv("CF_IR_DETECT_INTERVAL", "30"))
AUDIT = Path(os.getenv("CF_AUDIT_PATH", "./logs/cma_audit.jsonl"))
STATE = Path(os.getenv("CF_LOG_DIR", "./logs")) / "ir_detect_offset"
STORE = CaseStore()
SEV_OK = {"HIGH", "CRITICAL"}
MIN_SCORE = int(os.getenv("CF_IR_MIN_SCORE", "55"))


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
        return {"opened": 0, "correlated": 0, "note": "no audit yet"}
    lines = AUDIT.read_text(encoding="utf-8").splitlines()
    start = _offset()
    if start > len(lines):
        start = 0
    opened = correlated = skipped = 0
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
        if not (
            action.startswith("detection:")
            or "detection" in action
            or action in ("block_ip", "isolate_endpoint", "terminate_session")
        ):
            continue
        indicator = str(e.get("indicator") or action.replace("detection:", "") or "unknown")
        target = str(e.get("target", "unknown"))
        source = str(e.get("source", "audit"))
        score, conf = score_event(indicator, sev, 0)
        if score < MIN_SCORE:
            skipped += 1
            continue
        match = STORE.find_open_match(indicator, target)
        related = {
            "timestamp": e.get("timestamp"),
            "action": action,
            "severity": sev,
            "indicator": indicator,
            "source": source,
        }
        if match:
            STORE.append_related(match, related)
            correlated += 1
            logger.info("Correlated into %s score→%s", match.case_id, match.score)
            continue
        tags = []
        if "brute" in indicator.lower():
            tags.append("auth")
        if sev == "CRITICAL":
            tags.append("critical")
        case = STORE.create(
            indicator=indicator,
            target=target,
            source=source,
            severity=sev,
            related=related,
            score=score,
            confidence=conf,
            tags=tags,
        )
        opened += 1
        logger.info("Opened %s sev=%s score=%s target=%s", case.case_id, sev, score, target)
    _set_offset(len(lines))
    return {
        "opened": opened,
        "correlated": correlated,
        "skipped_low_score": skipped,
        "audit_lines": len(lines),
        **STORE.summary(),
    }


def main():
    logger.info("IR Detect agent interval=%ss min_score=%s", INTERVAL, MIN_SCORE)
    run_forever("ir_detect", _cycle, INTERVAL, error_sleep=15.0)


if __name__ == "__main__":
    main()
