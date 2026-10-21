#!/usr/bin/env python3
"""Policy-gated automatic defense agent — continuous Tier-1 under ROE/LIVE."""

from __future__ import annotations

import logging
import os

from core.agent_runtime import run_forever
from core.soc.auto_defense import evaluate_cycle

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [AUTO-DEFENSE] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_auto_defense_agent")
INTERVAL = int(os.getenv("CF_AUTO_DEFENSE_INTERVAL", "15"))


def _cycle():
    result = evaluate_cycle()
    if result.get("executed"):
        logger.info("cycle %s", result)
    return result


def main():
    logger.info(
        "Auto-defense agent interval=%ss (policy-gated; LIVE=%s)",
        INTERVAL,
        os.getenv("CF_CONTAINMENT_LIVE", "false"),
    )
    run_forever("auto_defense", _cycle, INTERVAL, error_sleep=10.0)


if __name__ == "__main__":
    main()
