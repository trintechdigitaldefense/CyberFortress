#!/usr/bin/env python3
"""Rules-driven severity scoring for IR cases."""

from __future__ import annotations

from typing import Tuple

_CRITICAL_HINTS = ("ransomware", "exfil", "reverse_shell", "c2", "beacon", "disk_pressure")
_HIGH_HINTS = ("brute", "failed_login", "decoy", "honeypot", "port_scan", "sudo", "credential")


def score_event(indicator: str, severity: str, related_count: int = 0) -> Tuple[int, str]:
    ind = (indicator or "").lower()
    sev = (severity or "MEDIUM").upper()
    base = {"CRITICAL": 85, "HIGH": 70, "MEDIUM": 45, "LOW": 25, "INFO": 10}.get(sev, 40)
    if any(h in ind for h in _CRITICAL_HINTS):
        base = max(base, 90)
    elif any(h in ind for h in _HIGH_HINTS):
        base = max(base, 72)
    base = min(100, base + min(20, related_count * 5))
    if base >= 85:
        conf = "high"
    elif base >= 55:
        conf = "medium"
    else:
        conf = "low"
    return base, conf
