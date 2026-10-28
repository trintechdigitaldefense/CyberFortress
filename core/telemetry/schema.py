#!/usr/bin/env python3
"""Versioned canonical telemetry event schema for CyberFortress."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

SCHEMA_VERSION = "1.0"

REQUIRED_FIELDS = ("source", "indicator", "target")
OPTIONAL_FIELDS = (
    "timestamp",
    "severity",
    "tenant_id",
    "event_id",
    "raw",
    "confidence",
    "tags",
)

_SEVERITIES = frozenset({"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO", "UNKNOWN"})


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_timestamp(value: Any) -> Tuple[Optional[str], Optional[str]]:
    """Return (utc_iso, error). Invalid values are flagged, not silently accepted as now."""
    if value is None or value == "":
        return _utc_now(), None
    s = str(value).strip()
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat(), None
    except ValueError:
        return None, f"invalid timestamp: {value!r}"


def validate_event(raw: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Validate and normalize a raw event into canonical form."""
    errors: List[str] = []
    if not isinstance(raw, dict):
        return False, ["event must be an object"], {}

    source = str(raw.get("source") or "").strip()
    indicator = str(raw.get("indicator") or "").strip()
    target = str(raw.get("target") or "").strip()
    if not source:
        errors.append("missing source")
    if not indicator:
        errors.append("missing indicator")
    if not target:
        errors.append("missing target")

    ts, ts_err = parse_timestamp(raw.get("timestamp"))
    if ts_err:
        errors.append(ts_err)
        ts = _utc_now()

    sev = str(raw.get("severity") or raw.get("escalated_level") or "MEDIUM").upper()
    if sev not in _SEVERITIES:
        errors.append(f"invalid severity: {sev}")
        sev = "UNKNOWN"

    event_id = str(raw.get("event_id") or "").strip()
    if not event_id:
        event_id = f"{source}:{indicator}:{target}:{ts}"

    tenant_id = str(raw.get("tenant_id") or "").strip() or None
    conf = str(raw.get("confidence") or "").strip().lower() or None
    tags = raw.get("tags")
    if tags is not None and not isinstance(tags, list):
        errors.append("tags must be a list")
        tags = None

    normalized: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "source": source or "unknown",
        "indicator": indicator or "unknown",
        "target": target or "unknown",
        "timestamp": ts,
        "severity": sev,
        "event_id": event_id,
        "tenant_id": tenant_id,
        "confidence": conf,
        "tags": tags or [],
        "raw": raw.get("raw") if isinstance(raw.get("raw"), dict) else {},
    }
    return (len(errors) == 0), errors, normalized


def normalize_event(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize for pipeline use; attaches validation errors under _schema_errors if any."""
    ok, errors, norm = validate_event(raw)
    if not ok:
        norm["_schema_errors"] = errors
        norm["_schema_ok"] = False
    else:
        norm["_schema_ok"] = True
    return norm
