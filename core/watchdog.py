#!/usr/bin/env python3
"""
CyberFortress 24/7 Self-Monitoring Watchdog

Continuously verifies that CyberFortress is operating as intended:
- Component heartbeats (fusion, threat agent, compliance)
- Circuit breaker state
- Audit log freshness
- Pending approval backlog
- Disk / path health
- Optional auto-recovery / fail-closed hooks

Writes structured status to logs/watchdog_status.json and can notify via WhatsApp.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("cf_watchdog")

LOG_DIR = Path(os.getenv("CF_LOG_DIR", "./logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

STATUS_FILE = LOG_DIR / "watchdog_status.json"
HEARTBEAT_DIR = LOG_DIR / "heartbeats"
HEARTBEAT_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_LOG = Path(os.getenv("CF_AUDIT_PATH", str(LOG_DIR / "cma_audit.jsonl")))
PENDING_DIR = Path(os.getenv("CF_WHATSAPP_PENDING_DIR", str(LOG_DIR / "whatsapp_pending")))

HEARTBEAT_STALE_SECONDS = int(os.getenv("CF_WATCHDOG_HEARTBEAT_STALE", "180"))
AUDIT_STALE_HOURS = float(os.getenv("CF_WATCHDOG_AUDIT_STALE_HOURS", "24"))
MAX_PENDING_APPROVALS = int(os.getenv("CF_WATCHDOG_MAX_PENDING", "10"))
MIN_FREE_MB = int(os.getenv("CF_WATCHDOG_MIN_FREE_MB", "200"))
CHECK_INTERVAL = int(os.getenv("CF_WATCHDOG_INTERVAL", "60"))


def write_heartbeat(component: str, meta: Optional[Dict[str, Any]] = None) -> None:
    """Other agents call this to prove they are alive."""
    payload = {
        "component": component,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "meta": meta or {},
    }
    path = HEARTBEAT_DIR / f"{component}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _read_heartbeat(component: str) -> Optional[Dict[str, Any]]:
    path = HEARTBEAT_DIR / f"{component}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _heartbeat_age_seconds(component: str) -> Optional[float]:
    hb = _read_heartbeat(component)
    if not hb or "timestamp" not in hb:
        return None
    try:
        ts = datetime.fromisoformat(hb["timestamp"])
        return (datetime.now(timezone.utc) - ts).total_seconds()
    except Exception:
        return None


def _audit_age_hours() -> Optional[float]:
    if not AUDIT_LOG.exists():
        return None
    try:
        mtime = datetime.fromtimestamp(AUDIT_LOG.stat().st_mtime, tz=timezone.utc)
        return (datetime.now(timezone.utc) - mtime).total_seconds() / 3600.0
    except Exception:
        return None


def _count_pending() -> int:
    if not PENDING_DIR.exists():
        return 0
    count = 0
    for f in PENDING_DIR.glob("*.json"):
        if not (PENDING_DIR / f"{f.stem}.decision").exists():
            count += 1
    return count


def _free_disk_mb(path: Path = Path(".")) -> Optional[float]:
    try:
        st = os.statvfs(path)
        return (st.f_bavail * st.f_frsize) / (1024 * 1024)
    except Exception:
        return None


def run_checks() -> Dict[str, Any]:
    """Run one full self-check cycle. Returns structured status."""
    from core.circuit_breaker import breaker

    issues: List[Dict[str, str]] = []
    components = ["threat_agent", "fusion_agent", "compliance_logger", "watchdog"]

    write_heartbeat("watchdog", {"role": "self_monitor"})

    hb_status = {}
    for comp in components:
        age = _heartbeat_age_seconds(comp)
        if age is None:
            if comp == "watchdog":
                hb_status[comp] = {"ok": True, "age_s": 0}
            else:
                hb_status[comp] = {"ok": False, "age_s": None, "note": "no heartbeat yet"}
                issues.append({
                    "severity": "WARNING",
                    "code": "HEARTBEAT_MISSING",
                    "message": f"No heartbeat from {comp}",
                })
        elif age > HEARTBEAT_STALE_SECONDS:
            hb_status[comp] = {"ok": False, "age_s": round(age, 1)}
            issues.append({
                "severity": "CRITICAL" if comp in ("fusion_agent", "threat_agent") else "WARNING",
                "code": "HEARTBEAT_STALE",
                "message": f"{comp} heartbeat stale ({int(age)}s > {HEARTBEAT_STALE_SECONDS}s)",
            })
        else:
            hb_status[comp] = {"ok": True, "age_s": round(age, 1)}

    cb = breaker.status()
    if cb.get("state") == "OPEN":
        issues.append({
            "severity": "CRITICAL",
            "code": "BREAKER_OPEN",
            "message": f"Circuit breaker OPEN: {cb.get('reason', 'unknown')}",
        })

    audit_age = _audit_age_hours()
    if audit_age is not None and audit_age > AUDIT_STALE_HOURS:
        issues.append({
            "severity": "WARNING",
            "code": "AUDIT_STALE",
            "message": f"Audit log not updated in {audit_age:.1f} hours",
        })

    pending = _count_pending()
    if pending > MAX_PENDING_APPROVALS:
        issues.append({
            "severity": "WARNING",
            "code": "PENDING_BACKLOG",
            "message": f"{pending} pending WhatsApp approvals (max {MAX_PENDING_APPROVALS})",
        })

    free_mb = _free_disk_mb()
    if free_mb is not None and free_mb < MIN_FREE_MB:
        issues.append({
            "severity": "CRITICAL",
            "code": "DISK_LOW",
            "message": f"Free disk {free_mb:.0f} MB below minimum {MIN_FREE_MB} MB",
        })

    critical = [i for i in issues if i["severity"] == "CRITICAL"]
    warnings = [i for i in issues if i["severity"] == "WARNING"]

    overall = "HEALTHY"
    if critical:
        overall = "UNHEALTHY"
    elif warnings:
        overall = "DEGRADED"

    status = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall": overall,
        "containment_live": os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "true",
        "whatsapp_enabled": os.getenv("CF_WHATSAPP_ENABLED", "false").lower() == "true",
        "circuit_breaker": cb,
        "heartbeats": hb_status,
        "audit_age_hours": round(audit_age, 2) if audit_age is not None else None,
        "pending_approvals": pending,
        "free_disk_mb": round(free_mb, 1) if free_mb is not None else None,
        "issues": issues,
        "critical_count": len(critical),
        "warning_count": len(warnings),
    }

    STATUS_FILE.write_text(json.dumps(status, indent=2), encoding="utf-8")
    return status


def notify_if_needed(status: Dict[str, Any], last_notified_overall: Optional[str]) -> Optional[str]:
    """Send WhatsApp alert on state change to UNHEALTHY / DEGRADED."""
    overall = status["overall"]
    if overall == last_notified_overall:
        return last_notified_overall
    if overall == "HEALTHY":
        if last_notified_overall in ("UNHEALTHY", "DEGRADED"):
            try:
                from core.whatsapp_gateway import send_notification
                send_notification(
                    f"✅ *CyberFortress Watchdog*\nStatus restored to HEALTHY\nTime: {status['timestamp']}"
                )
            except Exception as e:
                logger.warning(f"Could not send recovery notification: {e}")
        return overall

    try:
        from core.whatsapp_gateway import send_notification
        lines = [f"🚨 *CyberFortress Watchdog — {overall}*", f"Time: {status['timestamp']}", ""]
        for issue in status.get("issues", []):
            lines.append(f"• [{issue['severity']}] {issue['message']}")
        send_notification("\n".join(lines))
    except Exception as e:
        logger.warning(f"Could not send watchdog alert: {e}")

    return overall


def maybe_auto_safe_mode(status: Dict[str, Any]) -> None:
    """If critically unhealthy, fail closed: trip breaker (CF_WATCHDOG_FAIL_CLOSED=true)."""
    if os.getenv("CF_WATCHDOG_FAIL_CLOSED", "false").lower() != "true":
        return
    if status["overall"] != "UNHEALTHY":
        return

    try:
        from core.circuit_breaker import breaker
        if breaker.status().get("state") != "OPEN":
            breaker.trip("Watchdog fail-closed: platform UNHEALTHY")
            logger.critical("Watchdog tripped circuit breaker (fail-closed)")
    except Exception as e:
        logger.exception(f"Fail-closed breaker trip failed: {e}")
