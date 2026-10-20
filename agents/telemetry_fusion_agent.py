#!/usr/bin/env python3
"""Telemetry Fusion Agent — secondary poll of adapters (API + residual files)."""

from __future__ import annotations

import logging
import os
import time

from core.telemetry.fusion import TelemetryFusion
from core.watchdog import write_heartbeat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [FUSION_AGENT] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_fusion_agent")

INTERVAL = int(os.getenv("CF_FUSION_INTERVAL", "45"))


def main():
    logger.info("CyberFortress Telemetry Fusion Agent starting...")
    write_heartbeat("fusion_agent", {"phase": "starting"})

    auto = os.getenv("CF_AUTO_RESPOND", "true").lower() == "true"
    fusion = TelemetryFusion(auto_respond=auto)
    fusion.register_defaults()
    logger.info("Fusion loop ready | auto_respond=%s interval=%ss", auto, INTERVAL)

    while True:
        try:
            write_heartbeat("fusion_agent", {"phase": "collect"})
            results = fusion.process()
            write_heartbeat("fusion_agent", {"phase": "done", "events": len(results)})
            time.sleep(INTERVAL)
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.exception("Fusion error: %s", e)
            write_heartbeat("fusion_agent", {"phase": "error", "error": str(e)[:200]})
            time.sleep(15)


if __name__ == "__main__":
    main()
