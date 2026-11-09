#!/usr/bin/env python3
"""SIEM bridge — ingest JSON/CEF-like events; optional syslog export."""

from __future__ import annotations

import logging
import os
import re
import socket
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.soc.event_bus import get_bus
from core.tenant_guard import assert_single_tenant_runtime, strip_client_tenant_fields

logger = logging.getLogger("cf_siem")


def sanitize_ingest_event(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Remove caller-supplied tenant identity and stamp the authenticated local tenant."""
    if not isinstance(raw, dict):
        raise ValueError("SIEM event must be an object")
    tenant = assert_single_tenant_runtime()
    clean = strip_client_tenant_fields(raw)
    if tenant:
        clean["tenant_id"] = tenant
    return clean


def require_ingest_token(token: Optional[str]) -> bool:
    expected = os.getenv("CF_SIEM_INGEST_TOKEN", "")
    required = os.getenv("CF_SIEM_REQUIRE_TOKEN", "true").lower() in ("1", "true", "yes")
    if not expected:
        return not required
    return bool(token) and secrets.compare_digest(str(token), expected)


def _bounded_text(value: Any, fallback: str, limit: int = 256) -> str:
    text = str(value if value is not None else fallback)
    return text[:limit]


def normalize_event(raw: Dict[str, Any]) -> Dict[str, Any]:
    raw = sanitize_ingest_event(raw)
    severity = _bounded_text(raw.get("severity") or raw.get("sev") or "MEDIUM", "MEDIUM", 16).upper()
    if severity not in {"INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"}:
        severity = "MEDIUM"
    safe_raw = {}
    for index, (key, value) in enumerate(raw.items()):
        if index >= 50:
            break
        safe_key = _bounded_text(key, "field", 64)
        if isinstance(value, (str, int, float, bool)) or value is None:
            safe_value = value if not isinstance(value, str) else value[:1024]
        else:
            safe_value = _bounded_text(value, "", 1024)
        safe_raw[safe_key] = safe_value
    return {
        "timestamp": _bounded_text(raw.get("timestamp") or datetime.now(timezone.utc).isoformat(), "", 64),
        "source": _bounded_text(raw.get("source") or raw.get("vendor") or "siem_ingest", "siem_ingest", 128),
        "severity": severity,
        "indicator": _bounded_text(raw.get("indicator") or raw.get("signature") or raw.get("name") or "event", "event"),
        "target": _bounded_text(raw.get("target") or raw.get("src_ip") or raw.get("host") or "unknown", "unknown"),
        "action": _bounded_text(raw.get("action") or f"detection:{raw.get('indicator') or 'event'}", "event"),
        "raw": safe_raw,
    }


def ingest_batch(events: List[Dict[str, Any]], token: Optional[str] = None) -> int:
    if not require_ingest_token(token):
        raise PermissionError("valid SIEM ingest token required")
    if not isinstance(events, list):
        raise ValueError("SIEM batch must be a list")
    max_events = max(1, int(os.getenv("CF_SIEM_MAX_EVENTS", "500")))
    if len(events) > max_events:
        raise ValueError(f"SIEM batch exceeds maximum of {max_events} events")
    if any(not isinstance(event, dict) for event in events):
        raise ValueError("each SIEM event must be an object")
    bus = get_bus()
    n = 0
    for event in events:
        if bus.publish(normalize_event(event)):
            n += 1
    return n


_CEF_RE = re.compile(
    r"CEF:\d+\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|(\d+)\|(.*)$"
)


def parse_cef(line: str) -> Optional[Dict[str, Any]]:
    m = _CEF_RE.search(line.strip())
    if not m:
        return None
    vendor, product, version, sig_id, name, severity, ext = m.groups()
    fields: Dict[str, str] = {}
    for part in re.findall(r"(\w+)=([^=]*?)(?=\s\w+=|$)", ext):
        fields[part[0]] = part[1].strip()
    sev_map = {
        "0": "INFO",
        "1": "INFO",
        "2": "LOW",
        "3": "LOW",
        "4": "MEDIUM",
        "5": "MEDIUM",
        "6": "HIGH",
        "7": "HIGH",
        "8": "CRITICAL",
        "9": "CRITICAL",
        "10": "CRITICAL",
    }
    return normalize_event(
        {
            "source": f"{vendor}/{product}",
            "indicator": name or sig_id,
            "severity": sev_map.get(str(severity), "MEDIUM"),
            "target": fields.get("src") or fields.get("dst") or fields.get("dhost") or "unknown",
            "signature_id": sig_id,
            "extension": fields,
        }
    )


def export_syslog(message: str) -> bool:
    host = os.getenv("CF_SIEM_SYSLOG_HOST", "")
    if not host:
        return False
    port = int(os.getenv("CF_SIEM_SYSLOG_PORT", "514"))
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(message.encode("utf-8", errors="replace")[:60000], (host, port))
        sock.close()
        return True
    except Exception as e:
        logger.warning("syslog export failed: %s", e)
        return False


def format_cef(event: Dict[str, Any]) -> str:
    sev = {"INFO": 1, "LOW": 3, "MEDIUM": 5, "HIGH": 7, "CRITICAL": 9}.get(
        str(event.get("severity", "MEDIUM")).upper(), 5
    )
    name = str(event.get("indicator", "event")).replace("|", "_")
    return (
        f"CEF:0|TrinTech|CyberFortress|1.0|{name}|{name}|{sev}|"
        f"src={event.get('target', '')} msg={str(event.get('action', ''))[:80]}"
    )
