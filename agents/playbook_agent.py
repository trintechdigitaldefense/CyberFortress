#!/usr/bin/env python3
"""SOAR-lite playbook runner."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from core.agent_runtime import run_forever
from core.soc.playbooks import load_playbooks, match_playbook, run_playbook_actions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PLAYBOOK] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_playbook")
INTERVAL = int(os.getenv("CF_PLAYBOOK_INTERVAL", "20"))
AUDIT = Path(os.getenv("CF_AUDIT_PATH", "./logs/cma_audit.jsonl"))
STATE = Path(os.getenv("CF_LOG_DIR", "./logs")) / "playbook_offset"


def _offset() -> int:
    if STATE.exists():
        try:
            return int(STATE.read_text().strip() or "0")
        except Exception:
            return 0
    return 0


def _cycle():
    pbs = load_playbooks()
    if not AUDIT.exists():
        return {"playbooks": len(pbs), "ran": 0}
    lines = AUDIT.read_text(encoding="utf-8").splitlines()
    start = _offset()
    if start > len(lines):
        start = 0
    ran = 0
    for line in lines[start:]:
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if str(e.get("severity", "")).upper() not in ("HIGH", "CRITICAL"):
            continue
        event = {
            "indicator": e.get("indicator") or e.get("action"),
            "target": e.get("target"),
            "severity": e.get("severity"),
            "score": e.get("priority") or 70,
            "tags": e.get("tags") or [],
        }
        for pb in match_playbook(event, pbs):
            results = run_playbook_actions(event, pb)
            ran += len(results)
            logger.info("Playbook %s → %s", pb.get("name"), results)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(str(len(lines)), encoding="utf-8")
    return {"playbooks": len(pbs), "ran": ran, "audit_lines": len(lines)}


def main():
    logger.info("Playbook agent interval=%ss", INTERVAL)
    run_forever("playbook", _cycle, INTERVAL, error_sleep=15.0)


if __name__ == "__main__":
    main()
