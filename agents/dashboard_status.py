#!/usr/bin/env python3
"""Dashboard agent roster + live status helpers."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

HEARTBEAT_DIR = Path(os.getenv("CF_LOG_DIR", "./logs")) / "heartbeats"
STALE_S = int(os.getenv("CF_DASHBOARD_AGENT_STALE_S", "180"))

EXPECTED_AGENTS: List[Tuple[str, str]] = [
    ("threat_agent", "Threat detection"),
    ("fusion_agent", "Telemetry fusion"),
    ("compliance_logger", "Compliance audit"),
    ("watchdog", "Self-monitor"),
    ("firewall", "Firewall"),
    ("whatsapp", "WhatsApp gateway"),
    ("health", "Health API"),
    ("daily_report", "Daily reports"),
    ("weekly_evidence", "Weekly evidence"),
    ("ir_detect", "IR detect"),
    ("ir_investigate", "IR investigate"),
    ("ir_respond", "IR respond"),
    ("ir_report", "IR report"),
    ("tenant_orch", "Multi-tenant"),
    ("soc_api", "SOC API"),
    ("siem_bridge", "SIEM bridge"),
    ("playbook", "Playbooks"),
    ("threat_intel", "Threat intel"),
    ("auto_defense", "Auto-defense"),
]


def raw_heartbeats() -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if not HEARTBEAT_DIR.exists():
        return out
    for f in HEARTBEAT_DIR.glob("*.json"):
        try:
            out[f.stem] = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
    return out


def agent_status() -> Dict[str, Any]:
    raw = raw_heartbeats()
    now = datetime.now(timezone.utc)
    rows = []
    up = stale = down = 0
    for name, label in EXPECTED_AGENTS:
        hb = raw.get(name) or {}
        ts = hb.get("timestamp")
        age_s = None
        state = "down"
        if ts:
            try:
                age_s = (now - datetime.fromisoformat(ts)).total_seconds()
                state = "up" if age_s <= STALE_S else "stale"
            except Exception:
                state = "down"
        if state == "up":
            up += 1
        elif state == "stale":
            stale += 1
        else:
            down += 1
        meta = hb.get("meta") if isinstance(hb.get("meta"), dict) else {}
        rows.append({
            "id": name,
            "label": label,
            "state": state,
            "age_s": None if age_s is None else int(age_s),
            "phase": meta.get("phase") or hb.get("phase"),
            "timestamp": ts,
        })
    known = {n for n, _ in EXPECTED_AGENTS}
    for name, hb in raw.items():
        if name in known:
            continue
        rows.append({
            "id": name,
            "label": name,
            "state": "up",
            "age_s": None,
            "phase": (hb.get("meta") or {}).get("phase") if isinstance(hb.get("meta"), dict) else None,
            "timestamp": hb.get("timestamp"),
        })
    return {
        "agents": rows,
        "summary": {"up": up, "stale": stale, "down": down, "total": len(EXPECTED_AGENTS)},
    }
