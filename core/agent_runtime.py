#!/usr/bin/env python3
"""Shared agent runtime — heartbeats, backoff, structured cycles."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, Optional

from core.watchdog import write_heartbeat

logger = logging.getLogger("cf_agent_runtime")


def run_forever(
    name: str,
    cycle: Callable[[], Optional[Dict[str, Any]]],
    interval: float,
    *,
    error_sleep: float = 10.0,
    max_error_sleep: float = 120.0,
) -> None:
    """Run cycle() forever with heartbeats and exponential backoff on errors."""
    write_heartbeat(name, {"phase": "started"})
    err_streak = 0
    while True:
        try:
            write_heartbeat(name, {"phase": "cycle_start"})
            meta = cycle() or {}
            err_streak = 0
            write_heartbeat(name, {"phase": "cycle_done", **meta})
            time.sleep(max(1.0, float(interval)))
        except KeyboardInterrupt:
            write_heartbeat(name, {"phase": "stopped"})
            logger.info("%s stopped", name)
            break
        except Exception as e:
            err_streak += 1
            sleep_for = min(max_error_sleep, error_sleep * (2 ** min(err_streak - 1, 4)))
            logger.exception("%s cycle error (streak=%s): %s", name, err_streak, e)
            write_heartbeat(
                name,
                {
                    "phase": "error",
                    "error": str(e)[:200],
                    "err_streak": err_streak,
                    "backoff_s": sleep_for,
                },
            )
            time.sleep(sleep_for)
