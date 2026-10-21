#!/usr/bin/env python3
"""Multi-tenant path helpers for CyberFortress — enterprise isolation."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

_ROOT = Path(os.getenv("CF_ROOT", ".")).resolve()


def tenant_id() -> str:
    return (os.getenv("CF_TENANT_ID") or "").strip()


def tenant_dir() -> Optional[Path]:
    tid = tenant_id()
    if not tid:
        return None
    return _ROOT / "config" / "tenants" / tid


def list_tenants() -> List[str]:
    root = _ROOT / "config" / "tenants"
    if not root.is_dir():
        return []
    out: List[str] = []
    for p in sorted(root.iterdir()):
        if p.is_dir() and not p.name.startswith("."):
            if (p / "settings.yaml").exists() or (p / "rule_pack.yaml").exists():
                out.append(p.name)
    seen = set()
    ordered = []
    for t in out:
        if t not in seen:
            seen.add(t)
            ordered.append(t)
    return ordered


def load_tenant_settings(tid: Optional[str] = None) -> Dict[str, Any]:
    tid = tid or tenant_id()
    if not tid:
        return {}
    d = _ROOT / "config" / "tenants" / tid
    path = d / "settings.yaml"
    if not path.exists():
        return {"tenant_id": tid}
    try:
        import yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        data.setdefault("tenant_id", tid)
        return data
    except Exception:
        return {"tenant_id": tid}


def apply_tenant_env(tid: Optional[str] = None) -> Dict[str, Any]:
    if tid:
        os.environ["CF_TENANT_ID"] = tid
    settings = load_tenant_settings()
    active = tenant_id()
    if not active:
        return settings
    logs = _ROOT / "logs" / "tenants" / active
    evidence = _ROOT / "evidence" / "tenants" / active
    cases = logs / "ir_cases"
    for p in (logs, evidence, cases, logs / "heartbeats"):
        p.mkdir(parents=True, exist_ok=True)
    os.environ["CF_AUDIT_PATH"] = str(logs / "cma_audit.jsonl")
    os.environ["CF_EVIDENCE_DIR"] = str(evidence)
    os.environ["CF_IR_CASE_DIR"] = str(cases)
    os.environ["CF_LOG_DIR"] = str(logs)
    os.environ.setdefault("CF_WHATSAPP_PENDING_DIR", str(logs / "whatsapp_pending"))
    if settings.get("client_name"):
        os.environ["CF_CLIENT_NAME"] = str(settings["client_name"])
    if settings.get("whatsapp_report_to") and not os.getenv("CF_WHATSAPP_REPORT_TO"):
        os.environ["CF_WHATSAPP_REPORT_TO"] = str(settings["whatsapp_report_to"])
    if settings.get("rule_pack") and not os.getenv("CF_RULE_PACK_NAME"):
        os.environ["CF_RULE_PACK_NAME"] = str(settings["rule_pack"])
    assets = settings.get("asset_criticality") or {}
    if assets:
        os.environ["CF_ASSET_CRITICALITY_JSON"] = json.dumps(assets)
    return settings
