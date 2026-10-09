#!/usr/bin/env python3
"""
CyberFortress Watchdog Agent — 24/7 self-monitoring loop

Usage:
  python3 -m agents.watchdog_agent
  python3 -m agents.watchdog_agent --once   # single check
"""

import argparse
import logging
import time

from core.watchdog import (
    CHECK_INTERVAL,
    run_checks,
    notify_if_needed,
    maybe_auto_safe_mode,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WATCHDOG] %(levelname)s %(message)s",
)
logger = logging.getLogger("cf_watchdog_agent")


def main():
    parser = argparse.ArgumentParser(description="CyberFortress 24/7 Watchdog")
    parser.add_argument("--once", action="store_true", help="Run a single check and exit")
    args = parser.parse_args()

    logger.info("CyberFortress Watchdog starting")
    logger.info(f"Check interval: {CHECK_INTERVAL}s")

    last_notified = None

    while True:
        try:
            status = run_checks()
            overall = status["overall"]
            logger.info(
                f"Status={overall} critical={status['critical_count']} "
                f"warnings={status['warning_count']} pending={status['pending_approvals']}"
            )
            for issue in status.get("issues", []):
                logfn = logger.error if issue["severity"] == "CRITICAL" else logger.warning
                logfn(f"[{issue['code']}] {issue['message']}")

            last_notified = notify_if_needed(status, last_notified)
            maybe_auto_safe_mode(status)

        except Exception as e:
            logger.exception(f"Watchdog cycle error: {e}")

        if args.once:
            break
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
