#!/usr/bin/env python3
"""Multi-tenant path helpers for CyberFortress — enterprise isolation."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.tenant_guard import TenantError, assert_single_tenant_runtime, validate_tenant_id

_ROOT = Path(os.getenv("CF_ROOT", ".")).resolve()


def tenant_id() -> str:
    return (os.getenv("CF_TENANT_ID") or "").strip()


def tenant_dir() -> Optional[Path]:
    tid = validate_tenant_id(tenant_id())
    if not tid:
        return None
    raw_root = _ROOT / "config" / "tenants"
    if raw_root.is_symlink():
        raise TenantError("tenant root must not be a symlink")
    root = raw_root.resolve()
    candidate = root / tid
    if candidate.is_symlink() or candidate.resolve().parent != root:
        raise TenantError("tenant path escapes configured tenant root")
    return candidate.resolve()


def list_tenants() -> List[str]:
    root = _ROOT / "config" / "tenants"
    if root.is_symlink() or not root.is_dir():
        return []
    out: List[str] = []
    for p in sorted(root.iterdir()):
        if p.is_symlink() or not p.is_dir() or p.name.startswith(".") or p.name == "example_client":
            continue
        try:
            tid = validate_tenant_id(p.name)
        except TenantError:
            continue
        if (p / "settings.yaml").exists() or (p / "rule_pack.yaml").exists():
            out.append(tid)
    seen = set()
    ordered = []
    for t in out:
        if t not in seen:
            seen.add(t)
            ordered.append(t)
    return ordered


def load_tenant_settings(tid: Optional[str] = None) -> Dict[str, Any]:
    tid = validate_tenant_id(tid or tenant_id())
    if not tid:
        return {}
    raw_root = _ROOT / "config" / "tenants"
    if raw_root.is_symlink():
        raise TenantError("tenant root must not be a symlink")
    root = raw_root.resolve()
    d = root / tid
    if d.is_symlink() or d.resolve().parent != root:
        raise TenantError("tenant path escapes configured tenant root")
    path = d / "settings.yaml"
    if path.is_symlink():
        raise TenantError("tenant settings must not be a symlink")
    if not path.exists():
        return {"tenant_id": tid}
    try:
        import yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ValueError("tenant settings must be a YAML mapping")
        data.setdefault("tenant_id", tid)
        return data
    except Exception as exc:
        raise TenantError("tenant settings are invalid") from exc


def apply_tenant_env(tid: Optional[str] = None) -> Dict[str, Any]:
    previous = os.environ.get("CF_TENANT_ID")
    if tid:
        os.environ["CF_TENANT_ID"] = validate_tenant_id(tid)
    try:
        assert_single_tenant_runtime()
    except TenantError:
        if previous is None:
            os.environ.pop("CF_TENANT_ID", None)
        else:
            os.environ["CF_TENANT_ID"] = previous
        raise
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
