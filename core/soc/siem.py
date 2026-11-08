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

logger = logging.getLogger("cf_siem")


def sanitize_ingest_event(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Remove caller-supplied tenant identity and stamp the authenticated local tenant."""
    if not isinstance(raw, dict):
        raise ValueError("SIEM event must be an object")
    clean = dict(raw)
    tenant = os.getenv("CF_TENANT_ID", "").strip()
    clean.pop("tenant_id", None)
    if tenant:
        clean["tenant_id"] = tenant
    return clean


def require_ingest_token(token: Optional[str]) -> bool:
    expected = os.getenv("CF_SIEM_INGEST_TOKEN", "")
    required = os.getenv("CF_SIEM_REQUIRE_TOKEN", "true").lower() in ("1", "true", "yes")
    if not expected:
        return not required
    return bool(token) and secrets.compare_digest(str(token), expected)


def normalize_event(raw: Dict[str, Any]) -> Dict[str, Any]:
    raw = sanitize_ingest_event(raw)
    return {
        "timestamp": raw.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        "source": raw.get("source") or raw.get("vendor") or "siem_ingest",
        "severity": str(raw.get("severity") or raw.get("sev") or "MEDIUM").upper(),
        "indicator": str(raw.get("indicator") or raw.get("signature") or raw.get("name") or "event"),
        "target": str(raw.get("target") or raw.get("src_ip") or raw.get("host") or "unknown"),
        "action": str(raw.get("action") or f"detection:{raw.get('indicator') or 'event'}"),
        "raw": raw,
    }


def ingest_batch(events: List[Dict[str, Any]], token: Optional[str] = None) -> int:
    if not require_ingest_token(token):
        raise PermissionError("valid SIEM ingest token required")
    bus = get_bus()
    n = 0
    for e in events:
        if bus.publish(normalize_event(e)):
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
