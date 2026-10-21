#!/usr/bin/env python3
"""Shared agent runtime — heartbeats, backoff, metrics, adaptive intervals."""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Callable, Dict, Optional

from core.capacity import adaptive_interval
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
    tenant = os.getenv("CF_TENANT_ID", "")
    write_heartbeat(name, {"phase": "started", "tenant": tenant})
    err_streak = 0
    cycles = 0
    while True:
        t0 = time.time()
        try:
            write_heartbeat(name, {"phase": "cycle_start", "tenant": tenant, "cycles": cycles})
            meta = cycle() or {}
            err_streak = 0
            cycles += 1
            elapsed = time.time() - t0
            load = float(meta.get("load_ratio") or 1.0)
            sleep_for = adaptive_interval(float(interval), load)
            write_heartbeat(
                name,
                {
                    "phase": "cycle_done",
                    "tenant": tenant,
                    "cycles": cycles,
                    "elapsed_ms": int(elapsed * 1000),
                    "next_sleep_s": sleep_for,
                    **meta,
                },
            )
            time.sleep(max(1.0, sleep_for))
        except KeyboardInterrupt:
            write_heartbeat(name, {"phase": "stopped", "cycles": cycles})
            logger.info("%s stopped after %s cycles", name, cycles)
            break
        except Exception as e:
            err_streak += 1
            sleep_for = min(max_error_sleep, error_sleep * (2 ** min(err_streak - 1, 4)))
            logger.exception("%s cycle error (streak=%s): %s", name, err_streak, e)
            write_heartbeat(
                name,
                {
                    "phase": "error",
                    "tenant": tenant,
                    "error": str(e)[:200],
                    "err_streak": err_streak,
                    "backoff_s": sleep_for,
                },
            )
            time.sleep(sleep_for)
