#!/usr/bin/env python3
"""
Rules-driven intelligence layer — correlation, burst detection, priority.

Not ML. Deterministic windowed scoring so agents act less noisy and more precise.
"""

from __future__ import annotations

import json
import os
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Set

_LOCK = threading.Lock()
WINDOW_S = int(os.getenv("CF_INTEL_WINDOW_S", "900"))
BURST_THRESHOLD = int(os.getenv("CF_INTEL_BURST_THRESHOLD", "8"))
STATE_PATH = Path(os.getenv("CF_INTEL_STATE", "./logs/intelligence_state.json"))


@dataclass
class Signal:
    at: float
    indicator: str
    target: str
    severity: str
    source: str
    score: int = 50


class IntelligenceEngine:
    def __init__(self) -> None:
        self._by_target: Dict[str, Deque[Signal]] = defaultdict(deque)
        self._by_indicator: Dict[str, Deque[Signal]] = defaultdict(deque)
        self._by_source: Dict[str, Deque[Signal]] = defaultdict(deque)
        self._asset_criticality: Dict[str, int] = {}

    def set_asset_criticality(self, mapping: Dict[str, int]) -> None:
        self._asset_criticality = {str(k): int(v) for k, v in (mapping or {}).items()}

    def _prune(self, q: Deque[Signal], now: float) -> None:
        while q and now - q[0].at > WINDOW_S:
            q.popleft()

    def observe(
        self,
        *,
        indicator: str,
        target: str,
        severity: str,
        source: str,
        score: int = 50,
    ) -> Dict[str, Any]:
        now = time.time()
        sig = Signal(now, indicator, target, severity.upper(), source, score)
        with _LOCK:
            self._by_target[target].append(sig)
            self._by_indicator[indicator].append(sig)
            self._by_source[source].append(sig)
            self._prune(self._by_target[target], now)
            self._prune(self._by_indicator[indicator], now)
            self._prune(self._by_source[source], now)

            t_count = len(self._by_target[target])
            i_count = len(self._by_indicator[indicator])
            s_count = len(self._by_source[source])
            unique_inds = len({x.indicator for x in self._by_target[target]})

            burst = t_count >= BURST_THRESHOLD or s_count >= BURST_THRESHOLD * 2
            multi_signal = unique_inds >= 3

            prio = score
            prio += min(25, (t_count - 1) * 4)
            if multi_signal:
                prio += 15
            if burst:
                prio += 20
            prio += min(20, self._asset_criticality.get(target, 0))
            if severity.upper() == "CRITICAL":
                prio = max(prio, 90)
            prio = min(100, prio)

            confidence = "low"
            if prio >= 85 or (multi_signal and t_count >= 3):
                confidence = "high"
            elif prio >= 55:
                confidence = "medium"

            result = {
                "priority": prio,
                "confidence": confidence,
                "burst": burst,
                "multi_signal": multi_signal,
                "target_hits_in_window": t_count,
                "indicator_hits_in_window": i_count,
                "source_hits_in_window": s_count,
                "unique_indicators_on_target": unique_inds,
                "window_s": WINDOW_S,
                "recommend_escalate": prio >= 75 or burst,
            }
            self._persist_unlocked()
            return result

    def top_targets(self, limit: int = 10) -> List[Dict[str, Any]]:
        now = time.time()
        rows = []
        with _LOCK:
            for target, q in self._by_target.items():
                self._prune(q, now)
                if not q:
                    continue
                rows.append(
                    {
                        "target": target,
                        "hits": len(q),
                        "indicators": sorted({x.indicator for x in q}),
                        "max_sev": max(
                            (x.severity for x in q),
                            key=lambda s: {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(s, 0),
                        ),
                    }
                )
        rows.sort(key=lambda r: r["hits"], reverse=True)
        return rows[:limit]

    def summary(self) -> Dict[str, Any]:
        with _LOCK:
            return {
                "targets_tracked": len(self._by_target),
                "indicators_tracked": len(self._by_indicator),
                "window_s": WINDOW_S,
                "burst_threshold": BURST_THRESHOLD,
                "top_targets": self.top_targets(5),
            }

    def _persist_unlocked(self) -> None:
        try:
            STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "at": datetime.now(timezone.utc).isoformat(),
                "summary": {
                    "targets_tracked": len(self._by_target),
                    "indicators_tracked": len(self._by_indicator),
                    "window_s": WINDOW_S,
                },
                "top_targets": [
                    {
                        "target": t,
                        "hits": len(q),
                        "indicators": sorted({x.indicator for x in q})[:8],
                    }
                    for t, q in sorted(
                        self._by_target.items(), key=lambda kv: len(kv[1]), reverse=True
                    )[:10]
                    if q
                ],
            }
            STATE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            pass


_ENGINE: Optional[IntelligenceEngine] = None


def get_engine() -> IntelligenceEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = IntelligenceEngine()
    return _ENGINE
