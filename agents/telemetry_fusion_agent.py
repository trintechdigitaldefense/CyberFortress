#!/usr/bin/env python3
"""
CyberFortress Telemetry Fusion Agent
Continuously pulls from Sentinel / Mirage / local sources,
fuses events, escalates, and optionally triggers playbooks.
"""

import os
import time
import logging

from core.telemetry.fusion import TelemetryFusion
from core.watchdog import write_heartbeat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [FUSION_AGENT] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_fusion_agent")


def main():
    logger.info("CyberFortress Telemetry Fusion Agent starting...")
    write_heartbeat("fusion_agent", {"phase": "starting"})

    auto = os.getenv("CF_AUTO_RESPOND", "false").lower() == "true"
    fusion = TelemetryFusion(auto_respond=auto)
    fusion.register_defaults()

    logger.info("Adapters registered: Sentinel, Mirage, Local, API connectors")
    logger.info(f"auto_respond={auto} (set CF_AUTO_RESPOND=true to execute playbooks from fusion)")
    logger.info("Running continuous fusion loop (Ctrl+C to stop)")

    while True:
        try:
            write_heartbeat("fusion_agent", {"phase": "cycle_start"})
            results = fusion.process()
            write_heartbeat("fusion_agent", {"phase": "cycle_done", "events": len(results)})
            if results:
                logger.info(f"Processed {len(results)} new event(s)")
            time.sleep(30)
        except KeyboardInterrupt:
            logger.info("Shutting down cleanly")
            break
        except Exception as e:
            logger.exception(f"Fusion cycle error: {e}")
            write_heartbeat("fusion_agent", {"phase": "error", "error": str(e)})
            time.sleep(10)


if __name__ == "__main__":
    main()
