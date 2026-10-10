#!/usr/bin/env python3
"""
CyberFortress Compliance Logger
Append-only CMA audit with SHA-256 hash chain (tamper-evident).
"""

import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from core.audit_chain import append_chained
from core.watchdog import write_heartbeat

LOG_DIR = Path(os.getenv("CF_LOG_DIR", "./logs"))
if Path("/app/logs").exists():
    LOG_DIR = Path("/app/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_PATH = Path(os.getenv("CF_AUDIT_PATH", str(LOG_DIR / "cma_audit.jsonl")))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [COMPLIANCE] %(levelname)s %(message)s",
)
logger = logging.getLogger("cf_compliance_logger")


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


def main():
    logger.info("CyberFortress Compliance Logger started (hash-chained audit)")
    while True:
        write_heartbeat("compliance_logger", {"phase": "alive"})
        time.sleep(60)


if __name__ == "__main__":
    main()
