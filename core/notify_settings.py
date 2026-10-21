"""Dashboard-managed WhatsApp notify settings (report number + toggles).

Meta token stays in env / secrets manager — never stored here.
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("cf_notify_settings")

SETTINGS_PATH = Path(os.getenv("CF_NOTIFY_SETTINGS", "./config/whatsapp_notify.json"))
E164_RE = re.compile(r"^\+?[1-9]\d{7,14}$")


def _default() -> Dict[str, Any]:
    env_to = (
        os.getenv("CF_WHATSAPP_REPORT_TO", "").strip()
        or (os.getenv("CF_WHATSAPP_ADMINS", "").split(",")[0].strip() if os.getenv("CF_WHATSAPP_ADMINS") else "")
    )
    return {
        "report_to": env_to,
        "daily_enabled": True,
        "live_alerts_enabled": True,
        "min_live_severity": "HIGH",
        "updated_at": None,
        "source": "default",
    }


def load_settings() -> Dict[str, Any]:
    base = _default()
    if not SETTINGS_PATH.exists():
        return base
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return base
        out = {**base, **{k: data[k] for k in data if k in (
            "report_to", "daily_enabled", "live_alerts_enabled", "min_live_severity", "updated_at", "source"
        )}}
        out["daily_enabled"] = bool(out.get("daily_enabled", True))
        out["live_alerts_enabled"] = bool(out.get("live_alerts_enabled", True))
        sev = str(out.get("min_live_severity") or "HIGH").upper()
        out["min_live_severity"] = sev if sev in ("HIGH", "CRITICAL") else "HIGH"
        out["report_to"] = str(out.get("report_to") or "").strip()
        out["source"] = "file"
        return out
    except Exception as e:
        logger.warning("notify settings read failed: %s", e)
        return base


def normalize_e164(num: str) -> str:
    n = (num or "").strip().replace(" ", "").replace("-", "")
    if n and not n.startswith("+") and n.isdigit():
        n = "+" + n
    return n


def validate_number(num: str) -> Optional[str]:
    n = normalize_e164(num)
    if not n:
        return None
    if not E164_RE.match(n):
        return "Use E.164 format, e.g. +18683620679"
    return None


def save_settings(
    report_to: str,
    daily_enabled: bool = True,
    live_alerts_enabled: bool = True,
    min_live_severity: str = "HIGH",
) -> Dict[str, Any]:
    err = validate_number(report_to)
    if err:
        raise ValueError(err)
    sev = (min_live_severity or "HIGH").upper()
    if sev not in ("HIGH", "CRITICAL"):
        sev = "HIGH"
    data = {
        "report_to": normalize_e164(report_to),
        "daily_enabled": bool(daily_enabled),
        "live_alerts_enabled": bool(live_alerts_enabled),
        "min_live_severity": sev,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": "dashboard",
    }
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(SETTINGS_PATH, 0o600)
    except OSError:
        pass
    logger.info(
        "notify settings saved report_to=%s daily=%s live=%s",
        data["report_to"] or "(empty)",
        data["daily_enabled"],
        data["live_alerts_enabled"],
    )
    return data


def report_recipients() -> list:
    s = load_settings()
    if s.get("report_to"):
        return [s["report_to"]]
    env = os.getenv("CF_WHATSAPP_REPORT_TO", "").strip()
    if env:
        return [normalize_e164(env)]
    admins = [normalize_e164(x) for x in os.getenv("CF_WHATSAPP_ADMINS", "").split(",") if x.strip()]
    return [a for a in admins if a]


def daily_enabled() -> bool:
    return bool(load_settings().get("daily_enabled", True))


def live_alerts_enabled() -> bool:
    return bool(load_settings().get("live_alerts_enabled", True))


def severity_meets_live(severity: str) -> bool:
    s = load_settings()
    if not s.get("live_alerts_enabled", True):
        return False
    min_s = str(s.get("min_live_severity") or "HIGH").upper()
    sev = (severity or "INFO").upper()
    order = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    return order.get(sev, 0) >= order.get(min_s, 3)
