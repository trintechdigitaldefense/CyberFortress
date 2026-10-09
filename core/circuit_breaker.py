#!/usr/bin/env python3
"""
CyberFortress Fail-Safe / Circuit Breaker

Protects the environment from runaway autonomous actions.

Rules (configurable):
- If too many Tier-2 / high-impact actions occur in a short window → TRIP
- When tripped, all new autonomous actions are blocked until manually reset
- Force overrides still work but are heavily logged
- State is persisted so a restart does not clear a tripped breaker
"""

import json
import logging
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from enum import Enum

logger = logging.getLogger("cf_circuit_breaker")

STATE_FILE = Path(os.getenv("CF_BREAKER_STATE", "./logs/circuit_breaker_state.json"))
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

# Defaults – can be overridden by environment variables
WINDOW_MINUTES = int(os.getenv("CF_BREAKER_WINDOW_MINUTES", "15"))
MAX_ACTIONS = int(os.getenv("CF_BREAKER_MAX_ACTIONS", "8"))          # total high-impact actions
MAX_TIER2 = int(os.getenv("CF_BREAKER_MAX_TIER2", "4"))              # Tier-2 specifically
MAX_CRITICAL = int(os.getenv("CF_BREAKER_MAX_CRITICAL", "2"))        # CRITICAL severity


class BreakerState(Enum):
    CLOSED = "CLOSED"       # Normal operation
    OPEN = "OPEN"           # Tripped – blocking new autonomous actions
    HALF_OPEN = "HALF_OPEN" # Optional future: limited testing after timeout


class CircuitBreaker:
    def __init__(self):
        self.state = BreakerState.CLOSED
        self.tripped_at: Optional[datetime] = None
        self.reason: str = ""
        self.recent_actions: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        if not STATE_FILE.exists():
            return
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            self.state = BreakerState(data.get("state", "CLOSED"))
            self.reason = data.get("reason", "")
            if data.get("tripped_at"):
                self.tripped_at = datetime.fromisoformat(data["tripped_at"])
            self.recent_actions = data.get("recent_actions", [])
            logger.info(f"Circuit breaker loaded: state={self.state.value}")
        except Exception as e:
            logger.warning(f"Could not load breaker state: {e}")

    def _save(self):
        data = {
            "state": self.state.value,
            "reason": self.reason,
            "tripped_at": self.tripped_at.isoformat() if self.tripped_at else None,
            "recent_actions": self.recent_actions[-50:],  # keep last 50
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _prune(self):
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=WINDOW_MINUTES)
        self.recent_actions = [
            a for a in self.recent_actions
            if datetime.fromisoformat(a["timestamp"]) > cutoff
        ]

    def record(self, action: str, target: str, severity: str = "HIGH", tier: int = 2):
        """Record an action and evaluate whether to trip."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "target": target,
            "severity": severity,
            "tier": tier,
        }
        self.recent_actions.append(entry)
        self._prune()

        total = len(self.recent_actions)
        tier2_count = sum(1 for a in self.recent_actions if a.get("tier") == 2)
        critical_count = sum(1 for a in self.recent_actions if a.get("severity") == "CRITICAL")

        should_trip = False
        reason = ""

        if critical_count >= MAX_CRITICAL:
            should_trip = True
            reason = f"Too many CRITICAL actions ({critical_count}) in {WINDOW_MINUTES} min window"
        elif tier2_count >= MAX_TIER2:
            should_trip = True
            reason = f"Too many Tier-2 actions ({tier2_count}) in {WINDOW_MINUTES} min window"
        elif total >= MAX_ACTIONS:
            should_trip = True
            reason = f"Too many high-impact actions ({total}) in {WINDOW_MINUTES} min window"

        if should_trip and self.state != BreakerState.OPEN:
            self.trip(reason)

        self._save()
        return self.state

    def trip(self, reason: str):
        """Force the breaker into OPEN state."""
        self.state = BreakerState.OPEN
        self.tripped_at = datetime.now(timezone.utc)
        self.reason = reason
        self._save()
        logger.critical(f"CIRCUIT BREAKER TRIPPED: {reason}")
        # TODO: send WhatsApp emergency notification here

    def reset(self, by: str = "operator"):
        """Manually reset the breaker to CLOSED."""
        previous = self.state.value
        self.state = BreakerState.CLOSED
        self.tripped_at = None
        self.reason = ""
        self.recent_actions = []
        self._save()
        logger.warning(f"Circuit breaker RESET by {by} (was {previous})")

    def allow(self, force: bool = False) -> bool:
        """
        Return True if a new autonomous action is allowed.
        Force overrides are permitted but still logged.
        """
        if self.state == BreakerState.CLOSED:
            return True

        if force:
            logger.warning("Circuit breaker is OPEN but FORCE override requested — allowing")
            return True

        logger.error(f"Circuit breaker is OPEN — action blocked. Reason: {self.reason}")
        return False

    def status(self) -> Dict[str, Any]:
        self._prune()
        return {
            "state": self.state.value,
            "reason": self.reason,
            "tripped_at": self.tripped_at.isoformat() if self.tripped_at else None,
            "window_minutes": WINDOW_MINUTES,
            "recent_actions_in_window": len(self.recent_actions),
            "max_actions": MAX_ACTIONS,
            "max_tier2": MAX_TIER2,
            "max_critical": MAX_CRITICAL,
        }


# Singleton used by the rest of the platform
breaker = CircuitBreaker()
