#!/usr/bin/env python3
"""
Policy-gated automatic defense.

NOT unattended god-mode. Every action still goes through:
  ROE allow-list → circuit breaker → autonomy tiers → LIVE/dry-run.

Tier-1 can execute without WhatsApp when LIVE and authorized.
Tier-2 always needs APPROVE (unless force is explicitly allowed).
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("cf_auto_defense")

ENABLED = os.getenv("CF_AUTO_DEFENSE", "true").lower() in ("1", "true", "yes")
MAX_PER_CYCLE = int(os.getenv("CF_AUTO_DEFENSE_MAX", "10"))
MIN_PRIORITY = int(os.getenv("CF_AUTO_DEFENSE_MIN_PRIORITY", "70"))
AUDIT = Path(os.getenv("CF_AUDIT_PATH", "./logs/cma_audit.jsonl"))
STATE = Path(os.getenv("CF_LOG_DIR", "./logs")) / "auto_defense_offset"
SEEN = Path(os.getenv("CF_LOG_DIR", "./logs")) / "auto_defense_seen.json"

AUTO_MAP = [
    (("brute", "password_spray", "failed_login", "ssh_auth_fail"), "block_ip"),
    (("port_scan", "recon", "nmap", "masscan"), "block_ip"),
    (("c2", "beacon", "callback"), "block_ip"),
    (("malware", "trojan", "ransomware_drop"), "block_ip"),
    (("decoy", "honeypot_hit"), "deploy_decoy"),
]


def _load_seen() -> Set[str]:
    if not SEEN.exists():
        return set()
    try:
        data = json.loads(SEEN.read_text(encoding="utf-8"))
        return set(data if isinstance(data, list) else [])
    except Exception:
        return set()


def _save_seen(seen: Set[str]) -> None:
    SEEN.parent.mkdir(parents=True, exist_ok=True)
    SEEN.write_text(json.dumps(list(seen)[-5000:]), encoding="utf-8")


def _offset() -> int:
    if STATE.exists():
        try:
            return int(STATE.read_text().strip() or "0")
        except Exception:
            return 0
    return 0


def _choose_action(indicator: str, tags: List[str]) -> Optional[str]:
    blob = f"{indicator} {' '.join(tags)}".lower()
    for keys, action in AUTO_MAP:
        if any(k in blob for k in keys):
            return action
    if "threat_intel" in {t.lower() for t in tags}:
        return "block_ip"
    return None


def evaluate_cycle() -> Dict[str, Any]:
    if not ENABLED:
        return {"enabled": False, "executed": 0, "skipped": 0}

    from core.autonomy import execute_with_autonomy

    if not AUDIT.exists():
        return {"enabled": True, "executed": 0, "skipped": 0, "note": "no audit yet"}

    lines = AUDIT.read_text(encoding="utf-8").splitlines()
    start = _offset()
    if start > len(lines):
        start = 0

    seen = _load_seen()
    executed = 0
    skipped = 0
    results: List[Dict[str, Any]] = []

    for line in lines[start:]:
        if executed >= MAX_PER_CYCLE:
            break
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue

        sev = str(e.get("severity", "")).upper()
        if sev not in ("HIGH", "CRITICAL"):
            continue
        action_field = str(e.get("action") or "")
        if action_field.startswith("containment:"):
            continue

        priority = int(e.get("priority") or e.get("score") or (90 if sev == "CRITICAL" else 75))
        if priority < MIN_PRIORITY:
            skipped += 1
            continue

        target = str(e.get("target") or "").strip()
        if not target or target in ("unknown", "n/a", "-"):
            skipped += 1
            continue

        indicator = str(e.get("indicator") or e.get("action") or "")
        tags = e.get("tags") or []
        auto_action = _choose_action(indicator, tags if isinstance(tags, list) else [])
        if not auto_action:
            skipped += 1
            continue

        key = f"{auto_action}|{target}|{indicator[:40]}"
        if key in seen:
            skipped += 1
            continue

        ok = execute_with_autonomy(
            action=auto_action,
            target=target,
            scope="single",
            force=False,
            severity=sev,
        )
        seen.add(key)
        executed += 1
        results.append({"action": auto_action, "target": target, "ok": bool(ok), "severity": sev})
        logger.info("Auto-defense %s %s → ok=%s", auto_action, target, ok)

    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(str(len(lines)), encoding="utf-8")
    _save_seen(seen)

    return {
        "enabled": True,
        "executed": executed,
        "skipped": skipped,
        "results": results,
        "live": os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "true",
        "mode": "LIVE"
        if os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "true"
        else "DRY-RUN",
    }
