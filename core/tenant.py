#!/usr/bin/env python3
"""Multi-tenant path helpers for CyberFortress."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

_ROOT = Path(os.getenv("CF_ROOT", ".")).resolve()


def tenant_id() -> str:
    return (os.getenv("CF_TENANT_ID") or "").strip()


def tenant_dir() -> Optional[Path]:
    tid = tenant_id()
    if not tid:
        return None
    return _ROOT / "config" / "tenants" / tid


def load_tenant_settings() -> Dict[str, Any]:
    d = tenant_dir()
    if not d:
        return {}
    path = d / "settings.yaml"
    if not path.exists():
        return {"tenant_id": tenant_id()}
    try:
        import yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        data.setdefault("tenant_id", tenant_id())
        return data
    except Exception:
        return {"tenant_id": tenant_id()}


def apply_tenant_env() -> Dict[str, Any]:
    settings = load_tenant_settings()
    tid = tenant_id()
    if not tid:
        return settings
    logs = _ROOT / "logs" / "tenants" / tid
    evidence = _ROOT / "evidence" / "tenants" / tid
    logs.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("CF_AUDIT_PATH", str(logs / "cma_audit.jsonl"))
    os.environ.setdefault("CF_EVIDENCE_DIR", str(evidence))
    if settings.get("whatsapp_report_to") and not os.getenv("CF_WHATSAPP_REPORT_TO"):
        os.environ["CF_WHATSAPP_REPORT_TO"] = str(settings["whatsapp_report_to"])
    if settings.get("rule_pack") and not os.getenv("CF_RULE_PACK_NAME"):
        os.environ["CF_RULE_PACK_NAME"] = str(settings["rule_pack"])
    return settings
