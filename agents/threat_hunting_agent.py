#!/usr/bin/env python3
"""CyberFortress Threat Hunting Agent — telemetry cycle into fusion."""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone

from core.telemetry.fusion import TelemetryFusion
from core.rules import load_pack, pack_summary
from core.tenant import apply_tenant_env
from core.watchdog import write_heartbeat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [THREAT_AGENT] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_threat_agent")

INTERVAL = int(os.getenv("CF_THREAT_INTERVAL", "60"))


def hunt_cycle(fusion: TelemetryFusion) -> int:
    ts = datetime.now(timezone.utc).isoformat()
    logger.info("Hunting cycle started at %s", ts)
    results = fusion.process()
    n = len(results)
    logger.info("Hunting cycle complete: %s new event(s)", n)
    return n


def main():
    logger.info("CyberFortress Threat Hunting Agent starting...")
    apply_tenant_env()
    load_pack(force=True)
    summary = pack_summary()
    logger.info("Rule pack: %s (%s rules)", summary.get("pack_id"), summary.get("rule_count"))

    auto = os.getenv("CF_AUTO_RESPOND", "true").lower() == "true"
    fusion = TelemetryFusion(auto_respond=auto)
    fusion.register_defaults()
    logger.info("Mode: continuous rules-driven | auto_respond=%s | interval=%ss", auto, INTERVAL)

    while True:
        try:
            write_heartbeat("threat_agent", {"phase": "cycle_start", **pack_summary()})
            n = hunt_cycle(fusion)
            write_heartbeat("threat_agent", {"phase": "cycle_done", "events": n})
            time.sleep(INTERVAL)
        except KeyboardInterrupt:
            logger.info("Shutting down cleanly")
            break
        except Exception as e:
            logger.exception("Hunt cycle error: %s", e)
            write_heartbeat("threat_agent", {"phase": "error", "error": str(e)[:200]})
            time.sleep(10)


if __name__ == "__main__":
    main()
