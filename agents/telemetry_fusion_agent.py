#!/usr/bin/env python3
"""
CyberFortress Telemetry Fusion Agent
Continuously pulls from Sentinel / Mirage / local sources,
fuses events, escalates, and optionally triggers playbooks.
"""

import time
import logging
from core.telemetry.fusion import TelemetryFusion

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [FUSION_AGENT] %(levelname)s %(message)s",
)
logger = logging.getLogger("cf_fusion_agent")


def main():
    logger.info("CyberFortress Telemetry Fusion Agent starting...")
    fusion = TelemetryFusion(auto_respond=False)  # set True for full autonomous response
    fusion.register_defaults()

    logger.info("Adapters registered: Sentinel, Mirage, Local")
    logger.info("Running continuous fusion loop (Ctrl+C to stop)")

    while True:
        try:
            results = fusion.process()
            if results:
                logger.info(f"Processed {len(results)} new event(s)")
            time.sleep(30)  # poll interval — tune as needed
        except KeyboardInterrupt:
            logger.info("Shutting down cleanly")
            break
        except Exception as e:
            logger.exception(f"Fusion cycle error: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()
