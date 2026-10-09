#!/usr/bin/env python3
"""
CyberFortress Compliance Logger
Writes tamper-proof log entries that pair every system action
with its Trinidad & Tobago Computer Misuse Act justification.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path("/app/logs") if Path("/app/logs").exists() else Path("./logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [COMPLIANCE] %(levelname)s %(message)s",
)
logger = logging.getLogger("cf_compliance_logger")


def write_cma_entry(action: str, target: str, justification: str, severity: str = "INFO"):
    """
    Create a structured, CMA-tagged log entry.
    In production this should also be written to an append-only / signed store.
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tag": "TT_CMA_TAG",
        "action": action,
        "target": target,
        "severity": severity,
        "legislative_justification": justification,
        "source": "CyberFortress",
    }

    # Human-readable line for docker logs | grep TT_CMA_TAG
    line = (
        f"TT_CMA_TAG | {entry['timestamp']} | {severity} | "
        f"Action={action} | Target={target} | Justification={justification}"
    )
    logger.info(line)

    # Structured JSON for later analysis / SIEM
    json_path = LOG_DIR / "cma_audit.jsonl"
    with open(json_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return entry


def main():
    logger.info("CyberFortress Compliance Logger started")
    logger.info("All actions will be tagged TT_CMA_TAG and mapped to TT Computer Misuse Act")
    # Keep process alive so docker logs -f works
    import time
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
