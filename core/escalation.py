#!/usr/bin/env python3
"""
CyberFortress Smart Escalation Engine
Automatically promotes alerts based on velocity, lateral movement, and impact signals.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
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


# Simple in-memory window for MVP (replace with Redis / DB later)
_recent_events: List[AlertEvent] = []
WINDOW_MINUTES = 15


def _prune_old_events():
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=WINDOW_MINUTES)
    global _recent_events
    _recent_events = [e for e in _recent_events if e.timestamp > cutoff]


def ingest_event(source: str, indicator: str, target: str, raw: dict = None) -> AlertLevel:
    """
    Ingest a new detection event and return the recommended alert level.
    """
    event = AlertEvent(source=source, indicator=indicator, target=target, raw=raw)
    _recent_events.append(event)
    _prune_old_events()

    level = _calculate_level(event)
    logger.info(f"Ingested {indicator} on {target} from {source} → {level.value}")
    return level


def _calculate_level(event: AlertEvent) -> AlertLevel:
    """
    Basic rules (expand with ML / more signals later):
    - Single decoy trigger or failed login spike → HIGH
    - Multiple hosts in short window or data-exfil indicators → CRITICAL
    - Everything else starts at LOW and can be promoted
    """
    indicator = event.indicator.lower()

    # Immediate CRITICAL signals
    critical_keywords = ["exfil", "ransomware", "encryption", "mass_credential", "lateral"]
    if any(k in indicator for k in critical_keywords):
        return AlertLevel.CRITICAL

    # Count related events in the window
    same_target = sum(1 for e in _recent_events if e.target == event.target)
    unique_targets = len({e.target for e in _recent_events})

    if unique_targets >= 3 or same_target >= 4:
        return AlertLevel.CRITICAL

    if "decoy" in indicator or "credential" in indicator or "bruteforce" in indicator:
        return AlertLevel.HIGH

    if same_target >= 2:
        return AlertLevel.HIGH

    return AlertLevel.LOW


def recommend_playbook(level: AlertLevel, indicator: str) -> str:
    """Suggest the most appropriate playbook for the current level + indicator."""
    if level == AlertLevel.CRITICAL:
        if "exfil" in indicator.lower() or "encryption" in indicator.lower():
            return "halt_operations"
        return "subnet_isolation"

    if level == AlertLevel.HIGH:
        if "credential" in indicator.lower():
            return "credential_rotation"
        if "decoy" in indicator.lower():
            return "isolate_endpoint"
        return "isolate_endpoint"

    return "block_ip"  # conservative default for LOW
