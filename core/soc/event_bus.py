#!/usr/bin/env python3
"""Buffered event bus for higher EPS before fusion/IR."""

from __future__ import annotations

import json
import os
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

_LOCK = threading.Lock()
MAX = int(os.getenv("CF_SOC_BUS_MAX", "10000"))
SPILL = Path(os.getenv("CF_SOC_BUS_SPILL", "./logs/soc_event_spill.jsonl"))


class EventBus:
    def __init__(self, maxsize: int = MAX) -> None:
        self._q: Deque[Dict[str, Any]] = deque(maxlen=maxsize)
        self._dropped = 0
        self._in = 0
        self._out = 0

    def publish(self, event: Dict[str, Any]) -> bool:
        with _LOCK:
            if len(self._q) >= (self._q.maxlen or MAX):
                self._dropped += 1
                try:
                    SPILL.parent.mkdir(parents=True, exist_ok=True)
                    with open(SPILL, "a", encoding="utf-8") as f:
                        f.write(json.dumps(event, default=str) + "\n")
                except Exception:
                    pass
                return False
            event.setdefault("bus_ts", time.time())
            self._q.append(event)
            self._in += 1
            return True

    def consume(self, n: int = 100) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        with _LOCK:
            for _ in range(min(n, len(self._q))):
                out.append(self._q.popleft())
                self._out += 1
        return out

    def stats(self) -> Dict[str, Any]:
        with _LOCK:
            return {
                "depth": len(self._q),
                "max": self._q.maxlen,
                "in": self._in,
                "out": self._out,
                "dropped": self._dropped,
            }


_BUS: Optional[EventBus] = None


def get_bus() -> EventBus:
    global _BUS
    if _BUS is None:
        _BUS = EventBus()
    return _BUS
