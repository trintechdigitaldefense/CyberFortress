#!/usr/bin/env python3
"""Host signal collection for stronger local monitoring (no external SIEM required)."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.telemetry.adapters import BaseAdapter

_PATTERNS = [
    (re.compile(r"Failed password for (?:invalid user )?(\S+) from (\d+\.\d+\.\d+\.\d+)", re.I),
     "bruteforce_ssh", "source_ip"),
    (re.compile(r"authentication failure.*rhost=(\d+\.\d+\.\d+\.\d+)", re.I),
     "failed_login_flood", "source_ip"),
    (re.compile(r"Invalid user (\S+) from (\d+\.\d+\.\d+\.\d+)", re.I),
     "bruteforce_ssh", "source_ip"),
    (re.compile(r"sudo:.*authentication failure", re.I),
     "sudo_auth_failure", "local"),
    (re.compile(r"session opened for user root", re.I),
     "root_session", "local"),
    (re.compile(r"Accepted publickey for (\S+) from (\d+\.\d+\.\d+\.\d+)", re.I),
     "ssh_login_success", "source_ip"),
]


class HostLogAdapter(BaseAdapter):
    source_name = "host_log"

    def __init__(self):
        self.paths = [
            Path(p)
            for p in os.getenv(
                "CF_HOST_LOG_PATHS",
                "/var/log/auth.log,/var/log/secure,/var/log/syslog,/var/log/messages",
            ).split(",")
            if p.strip()
        ]
        self.state_file = Path(os.getenv("CF_HOST_LOG_STATE", "./logs/host_log_state.json"))
        self.max_lines = int(os.getenv("CF_HOST_LOG_MAX_LINES", "500"))
        self._offsets: Dict[str, int] = {}
        self._load_state()

    def _load_state(self) -> None:
        import json
        if self.state_file.exists():
            try:
                self._offsets = json.loads(self.state_file.read_text(encoding="utf-8"))
            except Exception:
                self._offsets = {}

    def _save_state(self) -> None:
        import json
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            self.state_file.write_text(json.dumps(self._offsets), encoding="utf-8")
        except Exception:
            pass

    def fetch_events(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        for path in self.paths:
            if not path.exists() or not path.is_file():
                continue
            try:
                events.extend(self._scan_file(path))
            except Exception:
                continue
        self._save_state()
        return events

    def _scan_file(self, path: Path) -> List[Dict[str, Any]]:
        key = str(path)
        size = path.stat().st_size
        offset = int(self._offsets.get(key, 0))
        if offset > size:
            offset = 0
        events: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            fh.seek(offset)
            lines = fh.readlines()[-self.max_lines :]
            self._offsets[key] = fh.tell()
        for line in lines:
            for rx, indicator, kind in _PATTERNS:
                m = rx.search(line)
                if not m:
                    continue
                if kind == "source_ip":
                    target = m.group(m.lastindex or 1)
                    for g in m.groups():
                        if g and re.match(r"^\d+\.\d+\.\d+\.\d+$", g):
                            target = g
                            break
                else:
                    target = "localhost"
                events.append(
                    self.normalize(
                        {
                            "indicator": indicator,
                            "target": target,
                            "severity": "HIGH" if "brute" in indicator or "sudo" in indicator else "MEDIUM",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "raw": {"line": line.strip()[:300], "log": key},
                        }
                    )
                )
                break
        return events


class HostResourceAdapter(BaseAdapter):
    source_name = "host_resource"

    def fetch_events(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        min_free = float(os.getenv("CF_WATCHDOG_MIN_FREE_MB", "200"))
        try:
            st = os.statvfs(".")
            free_mb = (st.f_bavail * st.f_frsize) / (1024 * 1024)
            if free_mb < min_free:
                events.append(
                    self.normalize(
                        {
                            "indicator": "disk_pressure",
                            "target": "localhost",
                            "severity": "CRITICAL" if free_mb < min_free / 2 else "HIGH",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "raw": {"free_mb": round(free_mb, 1), "threshold_mb": min_free},
                        }
                    )
                )
        except Exception:
            pass
        try:
            load1 = os.getloadavg()[0]
            cpus = max(1, os.cpu_count() or 1)
            if load1 > cpus * float(os.getenv("CF_LOAD_THRESHOLD_MULT", "2.0")):
                events.append(
                    self.normalize(
                        {
                            "indicator": "high_load",
                            "target": "localhost",
                            "severity": "MEDIUM",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "raw": {"load1": load1, "cpus": cpus},
                        }
                    )
                )
        except Exception:
            pass
        return events
