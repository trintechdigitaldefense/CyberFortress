#!/usr/bin/env python3
"""Lightweight monitoring metrics for dashboard / reports."""

from __future__ import annotations

import json
import os
import threading
from collections import Counter, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_LOCK = threading.Lock()
_PATH = Path(os.getenv("CF_METRICS_PATH", "./logs/monitoring_metrics.json"))
_RECENT = deque(maxlen=100)
_COUNTS: Counter = Counter()
_ADAPTER_STATS: Dict[str, Dict[str, Any]] = {}
_LAST_DETECTION: Optional[str] = None
_STARTED = datetime.now(timezone.utc).isoformat()


def record_events(events: List[Dict[str, Any]]) -> None:
    global _LAST_DETECTION
    with _LOCK:
        for ev in events:
            src = ev.get("source", "unknown")
            ind = ev.get("indicator", "unknown")
            _COUNTS[f"src:{src}"] += 1
            _COUNTS[f"ind:{ind}"] += 1
            _COUNTS["total"] += 1
            _RECENT.appendleft(
                {
                    "ts": ev.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                    "source": src,
                    "indicator": ind,
                    "target": ev.get("target"),
                    "severity": ev.get("severity") or ev.get("escalated_level"),
                }
            )
            _LAST_DETECTION = datetime.now(timezone.utc).isoformat()
            st = _ADAPTER_STATS.setdefault(src, {"events": 0, "last": None})
            st["events"] += 1
            st["last"] = _LAST_DETECTION
        _flush()


def record_adapter_error(source: str, error: str) -> None:
    with _LOCK:
        st = _ADAPTER_STATS.setdefault(source, {"events": 0, "last": None, "errors": 0})
        st["errors"] = int(st.get("errors") or 0) + 1
        st["last_error"] = error[:200]
        st["last_error_at"] = datetime.now(timezone.utc).isoformat()
        _flush()


def snapshot() -> Dict[str, Any]:
    with _LOCK:
        return {
            "started_at": _STARTED,
            "total_events": int(_COUNTS.get("total", 0)),
            "last_detection": _LAST_DETECTION,
            "by_source": {k[4:]: v for k, v in _COUNTS.items() if k.startswith("src:")},
            "by_indicator": {k[4:]: v for k, v in _COUNTS.items() if k.startswith("ind:")},
            "adapters": dict(_ADAPTER_STATS),
            "recent": list(_RECENT)[:20],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def _flush() -> None:
    try:
        _PATH.parent.mkdir(parents=True, exist_ok=True)
        _PATH.write_text(json.dumps(snapshot(), indent=2), encoding="utf-8")
    except Exception:
        pass


def load_persisted() -> Dict[str, Any]:
    if _PATH.exists():
        try:
            return json.loads(_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return snapshot()
