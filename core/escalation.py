#!/usr/bin/env python3
"""
CyberFortress Smart Escalation Engine
Rules-based promotion by indicator, velocity, and impact signals.
(No ML model in this MVP.)
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import logging

logger = logging.getLogger("cf_escalation")


class AlertLevel(Enum):
    LOW = "LOW"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class AlertEvent:
    source: str
    indicator: str
    target: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    raw: Optional[dict] = None


_recent_events: List[AlertEvent] = []
WINDOW_MINUTES = 15


def _prune_old_events():
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=WINDOW_MINUTES)
    global _recent_events
    _recent_events = [e for e in _recent_events if e.timestamp > cutoff]


def ingest_event(source: str, indicator: str, target: str, raw: dict = None) -> AlertLevel:
    event = AlertEvent(source=source, indicator=indicator, target=target, raw=raw)
    _recent_events.append(event)
    _prune_old_events()
    level = _calculate_level(event)
    logger.info(f"Ingested {indicator} on {target} from {source} → {level.value}")
    return level


def _calculate_level(event: AlertEvent) -> AlertLevel:
    indicator = event.indicator.lower()

    critical_keywords = [
        "exfil", "ransomware", "encryption", "mass_credential", "lateral",
    ]
    if any(k in indicator for k in critical_keywords):
        return AlertLevel.CRITICAL

    same_target = sum(1 for e in _recent_events if e.target == event.target)
    unique_targets = len({e.target for e in _recent_events})

    if unique_targets >= 3 or same_target >= 4:
        return AlertLevel.CRITICAL

    high_keywords = [
        "decoy", "credential", "bruteforce", "reverse_shell", "shell",
        "c2", "beacon", "malware",
    ]
    if any(k in indicator for k in high_keywords):
        return AlertLevel.HIGH

    if same_target >= 2:
        return AlertLevel.HIGH

    return AlertLevel.LOW


def recommend_playbook(level: AlertLevel, indicator: str) -> str:
    ind = indicator.lower()
    if level == AlertLevel.CRITICAL:
        if "exfil" in ind or "encryption" in ind:
            return "halt_operations"
        return "subnet_isolation"

    if level == AlertLevel.HIGH:
        if "credential" in ind:
            return "credential_rotation"
        if "decoy" in ind:
            return "isolate_endpoint"
        if "reverse_shell" in ind or "shell" in ind:
            return "block_ip"
        return "isolate_endpoint"

    return "block_ip"
