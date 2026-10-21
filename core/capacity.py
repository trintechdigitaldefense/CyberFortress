#!/usr/bin/env python3
"""Honest capacity limits and load shedding for enterprise-leaning deployments."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional


def limits() -> Dict[str, Any]:
    return {
        "max_events_per_cycle": int(os.getenv("CF_CAP_EVENTS_PER_CYCLE", "500")),
        "max_open_ir_cases": int(os.getenv("CF_CAP_OPEN_IR_CASES", "200")),
        "max_firewall_rules": int(os.getenv("CF_FIREWALL_MAX_RULES", "200")),
        "max_tenants_per_host": int(os.getenv("CF_CAP_TENANTS_PER_HOST", "25")),
        "agent_interval_floor_s": float(os.getenv("CF_CAP_INTERVAL_FLOOR", "5")),
        "recommended_sites": "single-site to multi-site SMB/mid-market (≤25 tenants/host)",
        "not_designed_for": "global multi-region SOC with 10k+ EPS without external SIEM",
    }


def should_shed(queue_depth: int, max_depth: Optional[int] = None) -> bool:
    cap = max_depth if max_depth is not None else limits()["max_events_per_cycle"]
    return queue_depth > int(cap)


def adaptive_interval(base: float, load_ratio: float) -> float:
    floor = float(limits()["agent_interval_floor_s"])
    if load_ratio <= 1.0:
        return max(floor, base)
    return max(floor, base * min(4.0, load_ratio))
