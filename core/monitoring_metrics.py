#!/usr/bin/env python3
"""Lightweight monitoring metrics for dashboard / reports.

Concurrency model:
- In-memory state is guarded by a non-reentrant threading.Lock.
- Snapshots are built under the lock; filesystem writes happen outside it
  so writers never re-enter the lock (avoids deadlock).
- Persistence uses atomic replace; a failed write does not corrupt a prior
  good file and is reported via a bounded logger (no recursive metrics calls).
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
from collections import Counter, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("cf_metrics")

_LOCK = threading.Lock()
_PATH = Path(os.getenv("CF_METRICS_PATH", "./logs/monitoring_metrics.json"))
_RECENT: deque = deque(maxlen=100)
_COUNTS: Counter = Counter()
_ADAPTER_STATS: Dict[str, Dict[str, Any]] = {}
_LAST_DETECTION: Optional[str] = None
_STARTED = datetime.now(timezone.utc).isoformat()
_LAST_PERSIST_ERROR: Optional[str] = None
_PERSIST_FAILS = 0


def _snapshot_unlocked() -> Dict[str, Any]:
    """Build snapshot. Caller must hold _LOCK (or accept a race for read-only use)."""
    return {
        "started_at": _STARTED,
        "total_events": int(_COUNTS.get("total", 0)),
        "last_detection": _LAST_DETECTION,
        "by_source": {k[4:]: v for k, v in _COUNTS.items() if k.startswith("src:")},
        "by_indicator": {k[4:]: v for k, v in _COUNTS.items() if k.startswith("ind:")},
        "adapters": {k: dict(v) for k, v in _ADAPTER_STATS.items()},
        "recent": list(_RECENT)[:20],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "persist_fails": _PERSIST_FAILS,
        "last_persist_error": _LAST_PERSIST_ERROR,
    }


def snapshot() -> Dict[str, Any]:
    with _LOCK:
        return _snapshot_unlocked()


_PERSIST_LOCK = threading.Lock()


def _persist_latest() -> None:
    """Snapshot under metrics lock, then atomic write under persist lock.

    Taking a fresh snapshot at write time prevents an older concurrent writer
    from overwriting a newer on-disk state.
    """
    global _LAST_PERSIST_ERROR, _PERSIST_FAILS
    with _PERSIST_LOCK:
        with _LOCK:
            data = _snapshot_unlocked()
        path = _PATH
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            raw = json.dumps(data, indent=2, default=str)
            fd, tmp_name = tempfile.mkstemp(
                dir=str(path.parent),
                prefix=".metrics_",
                suffix=".tmp",
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(raw)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_name, path)
            except Exception:
                try:
                    os.unlink(tmp_name)
                except OSError:
                    pass
                raise
            with _LOCK:
                _LAST_PERSIST_ERROR = None
        except Exception as e:
            with _LOCK:
                _PERSIST_FAILS += 1
                _LAST_PERSIST_ERROR = str(e)[:200]
            logger.warning("metrics persist failed path=%s err=%s", path, e)


def record_events(events: List[Dict[str, Any]]) -> None:
    global _LAST_DETECTION
    if not events:
        return
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
            st["events"] = int(st.get("events") or 0) + 1
            st["last"] = _LAST_DETECTION
    _persist_latest()


def record_adapter_error(source: str, error: str) -> None:
    with _LOCK:
        st = _ADAPTER_STATS.setdefault(source, {"events": 0, "last": None, "errors": 0})
        st["errors"] = int(st.get("errors") or 0) + 1
        st["last_error"] = (error or "")[:200]
        st["last_error_at"] = datetime.now(timezone.utc).isoformat()
    _persist_latest()


def load_persisted() -> Dict[str, Any]:
    if _PATH.exists():
        try:
            return json.loads(_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("metrics load_persisted failed: %s", e)
    return snapshot()
