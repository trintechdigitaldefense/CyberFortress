#!/usr/bin/env python3
"""
Telemetry Adapters for CyberFortress
Normalize events from Sentinel, Mirage, CyberGuardian, and local sources
into a common schema that the fusion engine and escalation can consume.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import json
import logging
from pathlib import Path

logger = logging.getLogger("cf_telemetry.adapters")


class BaseAdapter(ABC):
    """Base class for all telemetry source adapters."""

    source_name: str = "unknown"

    @abstractmethod
    def fetch_events(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Return a list of normalized events."""
        pass

    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a raw event into the CyberFortress common schema."""
        return {
            "source": self.source_name,
            "indicator": raw.get("indicator") or raw.get("type") or raw.get("event") or "unknown",
            "target": raw.get("target") or raw.get("host") or raw.get("ip") or raw.get("asset") or "unknown",
            "severity": raw.get("severity") or raw.get("level") or "MEDIUM",
            "timestamp": raw.get("timestamp") or datetime.now(timezone.utc).isoformat(),
            "raw": raw,
        }


class SentinelAdapter(BaseAdapter):
    """
    Adapter for TrinTech Sentinel (Line of Defense Engine).
    Expects either:
      - JSON log files / API endpoint
      - or a simple file drop in /var/log/sentinel/ or ./telemetry/sentinel/
    """

    source_name = "sentinel"

    def __init__(self, log_path: str = "./telemetry/sentinel"):
        self.log_path = Path(log_path)
        self.log_path.mkdir(parents=True, exist_ok=True)

    def fetch_events(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        events = []
        for f in sorted(self.log_path.glob("*.json")):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                    if isinstance(data, list):
                        for item in data:
                            events.append(self.normalize(item))
                    else:
                        events.append(self.normalize(data))
            except Exception as e:
                logger.warning(f"Failed to read Sentinel file {f}: {e}")
        return events


class MirageAdapter(BaseAdapter):
    """
    Adapter for TrinTech Mirage (Active Deception Platform).
    Captures canary / honey-token / fake-service triggers.
    """

    source_name = "mirage"

    def __init__(self, log_path: str = "./telemetry/mirage"):
        self.log_path = Path(log_path)
        self.log_path.mkdir(parents=True, exist_ok=True)

    def fetch_events(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        events = []
        for f in sorted(self.log_path.glob("*.json")):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                    if isinstance(data, list):
                        for item in data:
                            # Force indicator to highlight deception
                            item.setdefault("indicator", "decoy_trigger")
                            events.append(self.normalize(item))
                    else:
                        data.setdefault("indicator", "decoy_trigger")
                        events.append(self.normalize(data))
            except Exception as e:
                logger.warning(f"Failed to read Mirage file {f}: {e}")
        return events


class LocalLogAdapter(BaseAdapter):
    """
    Simple adapter that tails a JSONL or text log for local / custom sources.
    Useful for CyberGuardian, custom agents, or syslog-style feeds.
    """

    source_name = "local"

    def __init__(self, log_file: str = "./telemetry/local/events.jsonl"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_file.exists():
            self.log_file.touch()

    def fetch_events(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        events = []
        try:
            with open(self.log_file, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw = json.loads(line)
                        events.append(self.normalize(raw))
                    except json.JSONDecodeError:
                        # Treat plain text as a generic event
                        events.append(self.normalize({
                            "indicator": "local_log",
                            "target": "unknown",
                            "message": line,
                        }))
        except Exception as e:
            logger.warning(f"Failed to read local log {self.log_file}: {e}")
        return events
