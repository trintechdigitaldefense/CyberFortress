#!/usr/bin/env python3
"""Prometheus-style metrics exposition."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Dict

from core.capacity import limits
from core.soc.event_bus import get_bus


def collect() -> Dict[str, float]:
    m: Dict[str, float] = {
        "cf_up": 1.0,
        "cf_containment_live": 1.0
        if os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "true"
        else 0.0,
        "cf_bus_depth": float(get_bus().stats()["depth"]),
        "cf_bus_dropped": float(get_bus().stats()["dropped"]),
        "cf_cap_events_per_cycle": float(limits()["max_events_per_cycle"]),
        "cf_cap_tenants": float(limits()["max_tenants_per_host"]),
        "cf_scrape_ts": float(time.time()),
    }
    audit = Path(os.getenv("CF_AUDIT_PATH", "./logs/cma_audit.jsonl"))
    if audit.exists():
        m["cf_audit_bytes"] = float(audit.stat().st_size)
    cases = Path(os.getenv("CF_IR_CASE_DIR", "./logs/ir_cases"))
    if cases.is_dir():
        m["cf_ir_case_files"] = float(len(list(cases.glob("IR-*.json"))))
    hb = Path(os.getenv("CF_LOG_DIR", "./logs")) / "heartbeats"
    if hb.is_dir():
        m["cf_agent_heartbeats"] = float(len(list(hb.glob("*.json"))))
    return m


def prometheus_text() -> str:
    lines = ["# HELP cf_up CyberFortress process up", "# TYPE cf_up gauge"]
    for k, v in sorted(collect().items()):
        lines.append(f"{k} {v}")
    return "\n".join(lines) + "\n"
