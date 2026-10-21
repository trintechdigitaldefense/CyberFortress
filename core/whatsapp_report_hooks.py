"""Patches send_report / adds send_live_alert using dashboard notify settings.

Meta token stays in env. Dashboard stores only the client report number + toggles.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("cf_whatsapp_report_hooks")


def apply_hooks() -> None:
    import core.whatsapp_gateway as gw

    if getattr(gw, "_cf_notify_hooks", False):
        return

    _orig_notify = gw.notify_tier1

    def send_report(message: str, level: str = "REPORT") -> bool:
        try:
            from core.notify_settings import report_recipients
            targets = report_recipients() or gw.REPORT_NUMBERS or gw.ADMIN_NUMBERS
        except Exception:
            targets = gw.REPORT_NUMBERS or gw.ADMIN_NUMBERS
        if not targets:
            logger.info("[report/%s] no recipients: %s", level, message[:120])
            return False
        ok = True
        body = message if message.startswith("[") or message.startswith("*") else f"[{level}] {message}"
        for num in targets:
            if not gw._send_text(num, body):
                ok = False
        return ok

    def send_live_alert(
        title: str,
        detail: str = "",
        severity: str = "HIGH",
        action: str = "",
        target: str = "",
    ) -> bool:
        try:
            from core.notify_settings import severity_meets_live, report_recipients
            if not severity_meets_live(severity):
                return False
            targets = report_recipients() or gw.REPORT_NUMBERS or gw.ADMIN_NUMBERS
        except Exception:
            targets = gw.REPORT_NUMBERS or gw.ADMIN_NUMBERS
            if (severity or "").upper() not in ("HIGH", "CRITICAL"):
                return False
        if not targets:
            return False
        lines = [
            "*CyberFortress alert*",
            f"Severity: {(severity or 'HIGH').upper()}",
            f"{title}",
        ]
        if action:
            lines.append(f"Action: {action}")
        if target:
            lines.append(f"Target: {target}")
        if detail:
            lines.append(detail[:400])
        body = "\n".join(lines)
        ok = True
        for num in targets:
            if not gw._send_text(num, body):
                ok = False
        return ok

    def notify_tier1(action: str, target: str, justification: str) -> None:
        _orig_notify(action, target, justification)
        try:
            send_live_alert(
                title="Tier-1 action executed",
                detail=justification,
                severity="INFO",
                action=action,
                target=target,
            )
        except Exception:
            pass

    gw.send_report = send_report
    gw.send_live_alert = send_live_alert
    gw.notify_tier1 = notify_tier1
    gw._cf_notify_hooks = True
    logger.info("WhatsApp report/live-alert hooks applied")


try:
    apply_hooks()
except Exception as e:
    logger.warning("hooks not applied: %s", e)
