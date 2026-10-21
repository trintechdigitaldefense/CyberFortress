#!/usr/bin/env python3
"""CyberFortress Compliance Logger — hash-chained CMA audit + integrity heartbeats."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from core.audit_chain import append_chained, verify_chain
from core.agent_runtime import run_forever

LOG_DIR = Path(os.getenv("CF_LOG_DIR", "./logs"))
if Path("/app/logs").exists():
    LOG_DIR = Path("/app/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_PATH = Path(os.getenv("CF_AUDIT_PATH", str(LOG_DIR / "cma_audit.jsonl")))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [COMPLIANCE] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_compliance_logger")

INTERVAL = int(os.getenv("CF_COMPLIANCE_INTERVAL", "30"))


def write_cma_entry(action: str, target: str, justification: str, severity: str = "INFO", **extra):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "clock_source": "host_utc",
        "tag": "TT_CMA_TAG",
        "action": action,
        "target": str(target).replace("\n", " ").replace("\r", " "),
        "severity": severity,
        "legislative_justification": str(justification).replace("\n", " ").replace("\r", " "),
        "source": "CyberFortress",
    }
    for k, v in extra.items():
        if k not in entry:
            entry[k] = v

    chained = append_chained(AUDIT_PATH, entry)
    line = (
        f"TT_CMA_TAG | {chained['timestamp']} | {severity} | "
        f"Action={action} | Target={target} | hash={chained.get('entry_hash', '')[:12]}"
    )
    logger.info(line)
    return chained


def _cycle():
    ok, broken, msg = verify_chain(AUDIT_PATH)
    lines = 0
    if AUDIT_PATH.exists():
        try:
            with open(AUDIT_PATH, "r", encoding="utf-8") as f:
                lines = sum(1 for _ in f)
        except Exception:
            lines = -1
    if not ok:
        logger.warning("Audit chain issue: %s (broken_index=%s)", msg, broken)
    return {
        "audit_ok": ok,
        "audit_message": str(msg)[:120],
        "audit_lines": lines,
        "path": str(AUDIT_PATH),
    }


def main():
    logger.info("CyberFortress Compliance Logger started (hash-chained audit)")
    run_forever("compliance_logger", _cycle, INTERVAL)


if __name__ == "__main__":
    main()
