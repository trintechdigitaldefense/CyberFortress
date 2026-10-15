#!/usr/bin/env python3
"""
CyberFortress Daily WhatsApp Report Agent

Sends an automatic status summary to CF_WHATSAPP_REPORT_TO (or CF_WHATSAPP_ADMINS)
every CF_REPORT_INTERVAL_SECONDS (default 86400 = 24 hours).

Env:
  CF_REPORT_ENABLED=true
  CF_REPORT_INTERVAL_SECONDS=86400
  CF_REPORT_ON_START=true
  CF_CLIENT_NAME=...
  CF_WHATSAPP_REPORT_TO=+18683620679
  CF_WHATSAPP_ADMINS=+18683620679
  CF_WHATSAPP_ENABLED=true
  CF_WHATSAPP_TOKEN=...
  CF_WHATSAPP_PHONE_NUMBER_ID=...
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from core.watchdog import write_heartbeat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [DAILY_REPORT] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_daily_report")

INTERVAL = int(os.getenv("CF_REPORT_INTERVAL_SECONDS", "86400"))
ON_START = os.getenv("CF_REPORT_ON_START", "true").lower() == "true"
CLIENT = os.getenv("CF_CLIENT_NAME", "Client")
AUDIT_PATH = Path(os.getenv("CF_AUDIT_PATH", "./logs/cma_audit.jsonl"))
WATCHDOG_STATUS = Path(os.getenv("CF_WATCHDOG_STATUS", "./logs/watchdog_status.json"))


def _enabled() -> bool:
    flag = os.getenv("CF_REPORT_ENABLED", "").lower()
    if flag in ("true", "1", "yes"):
        return True
    if flag in ("false", "0", "no"):
        return False
    return os.getenv("CF_WHATSAPP_ENABLED", "false").lower() == "true"


def _audit_counts(hours: int = 24) -> dict:
    by_sev = {"CRITICAL": 0, "HIGH": 0, "INFO": 0, "MEDIUM": 0, "LOW": 0}
    total = 0
    if not AUDIT_PATH.exists():
        return {"total": 0, "by_severity": by_sev}
    cutoff = time.time() - hours * 3600
    try:
        for line in AUDIT_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = e.get("timestamp") or ""
            try:
                from datetime import datetime as dt

                t = dt.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
                if t < cutoff:
                    continue
            except Exception:
                pass
            total += 1
            sev = e.get("severity", "INFO")
            by_sev[sev] = by_sev.get(sev, 0) + 1
    except Exception as ex:
        logger.warning("audit read: %s", ex)
    return {"total": total, "by_severity": by_sev}


def build_report() -> str:
    live = os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "true"
    mode = "ACTIVE CONTAINMENT" if live else "MONITORING"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    wd = {"overall": "UNKNOWN"}
    if WATCHDOG_STATUS.exists():
        try:
            wd = json.loads(WATCHDOG_STATUS.read_text(encoding="utf-8"))
        except Exception:
            pass

    counts = _audit_counts(24)
    sev = counts["by_severity"]

    fw_msg = "—"
    try:
        from core.containment.firewall import firewall_status

        fw = firewall_status()
        fw_msg = f"{fw.get('mode_label', '—')} · rules={fw.get('rule_count', 0)}"
    except Exception as e:
        fw_msg = str(e)[:80]

    breaker_state = "—"
    try:
        from core.circuit_breaker import breaker

        breaker_state = breaker.status().get("state", "—")
    except Exception:
        pass

    lines = [
        f"*CyberFortress daily report*",
        f"Client: {CLIENT}",
        f"Time: {now}",
        f"",
        f"Mode: {mode}",
        f"Platform: {wd.get('overall', 'UNKNOWN')}",
        f"Circuit breaker: {breaker_state}",
        f"Firewall: {fw_msg}",
        f"",
        f"Last 24h actions: {counts['total']}",
        f"  Critical: {sev.get('CRITICAL', 0)}",
        f"  High: {sev.get('HIGH', 0)}",
        f"  Info: {sev.get('INFO', 0)}",
        f"",
        f"Dashboard: http://127.0.0.1:8091 (operator host)",
        f"— TrinTech Digital Defense",
    ]
    return "\n".join(lines)


def send_once() -> bool:
    if not _enabled():
        logger.info("Daily report skipped (CF_REPORT_ENABLED / WhatsApp not enabled)")
        return False
    try:
        from core.whatsapp_gateway import send_report

        msg = build_report()
        ok = send_report(msg, level="DAILY")
        logger.info("Daily report sent ok=%s", ok)
        write_heartbeat(
            "daily_report",
            {"phase": "sent" if ok else "failed", "ok": ok},
        )
        return ok
    except Exception as e:
        logger.exception("Daily report failed: %s", e)
        write_heartbeat("daily_report", {"phase": "error", "error": str(e)[:200]})
        return False


def main() -> None:
    logger.info(
        "Daily report agent starting (interval=%ss on_start=%s enabled=%s)",
        INTERVAL,
        ON_START,
        _enabled(),
    )
    write_heartbeat("daily_report", {"phase": "started", "interval": INTERVAL})

    if ON_START:
        time.sleep(15)
        send_once()

    while True:
        time.sleep(max(60, INTERVAL))
        send_once()


if __name__ == "__main__":
    main()
