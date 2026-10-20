#!/usr/bin/env python3
"""Telemetry adapters — normalize Sentinel / Mirage / local file drops."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger("cf_telemetry.adapters")


class BaseAdapter(ABC):
    source_name: str = "unknown"

    @abstractmethod
    def fetch_events(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        pass

    def normalize(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source": self.source_name,
            "indicator": raw.get("indicator") or raw.get("type") or raw.get("event") or "unknown",
            "target": raw.get("target") or raw.get("host") or raw.get("ip") or raw.get("asset") or "unknown",
            "severity": raw.get("severity") or raw.get("level") or "MEDIUM",
            "timestamp": raw.get("timestamp") or datetime.now(timezone.utc).isoformat(),
            "raw": raw,
        }


def _archive_file(path: Path) -> None:
    try:
        dest_dir = path.parent / "processed"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / path.name
        if dest.exists():
            dest = dest_dir / f"{path.stem}_{int(datetime.now().timestamp())}{path.suffix}"
        path.rename(dest)
    except Exception as e:
        logger.warning("Could not archive %s: %s", path, e)


class _JsonDirAdapter(BaseAdapter):
    def __init__(self, log_path: str, source_name: str):
        self.source_name = source_name
        self.log_path = Path(log_path)
        self.log_path.mkdir(parents=True, exist_ok=True)
        self.archive = os.getenv("CF_TELEMETRY_ARCHIVE", "true").lower() == "true"

    def fetch_events(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        for f in sorted(self.log_path.glob("*.json")):
            if f.name.startswith("."):
                continue
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    ev = self.normalize(item)
                    ev["_source_file"] = str(f)
                    events.append(ev)
                if self.archive:
                    _archive_file(f)
            except json.JSONDecodeError as e:
                logger.warning("Malformed JSON in %s: %s", f, e)
                try:
                    bad = self.log_path / "quarantine"
                    bad.mkdir(exist_ok=True)
                    f.rename(bad / f.name)
                except Exception:
                    pass
            except Exception as e:
                logger.warning("Failed to read %s: %s", f, e)
        return events


class SentinelAdapter(_JsonDirAdapter):
    def __init__(self, log_path: str = "./telemetry/sentinel"):
        super().__init__(log_path, "sentinel")


class MirageAdapter(_JsonDirAdapter):
    def __init__(self, log_path: str = "./telemetry/mirage"):
        super().__init__(log_path, "mirage")


class LocalLogAdapter(BaseAdapter):
    source_name = "local"

    def __init__(self, log_path: str = "./telemetry/local"):
        self.log_path = Path(log_path)
        self.log_path.mkdir(parents=True, exist_ok=True)

    def fetch_events(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        events = []
        for f in sorted(self.log_path.glob("*.jsonl")):
            try:
                for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        events.append(self.normalize(json.loads(line)))
                    except json.JSONDecodeError:
                        continue
                dest = self.log_path / "processed"
                dest.mkdir(exist_ok=True)
                f.rename(dest / f.name)
            except Exception as e:
                logger.warning("Local log %s failed: %s", f, e)
        return events
