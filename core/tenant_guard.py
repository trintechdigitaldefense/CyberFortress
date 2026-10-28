#!/usr/bin/env python3
"""Tenant context validation for API and file-scoped operations."""

from __future__ import annotations

import os
import re
from typing import Any, Dict, Optional, Tuple

_TENANT_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$")


class TenantError(Exception):
    """Invalid or mismatched tenant context."""


def active_tenant() -> str:
    return (os.getenv("CF_TENANT_ID") or "").strip()


def validate_tenant_id(tid: str) -> str:
    t = (tid or "").strip()
    if not t:
        return ""
    if not _TENANT_RE.match(t):
        raise TenantError("invalid tenant_id format")
    if ".." in t or "/" in t or "\\" in t:
        raise TenantError("invalid tenant_id path characters")
    return t


def resolve_request_tenant(
    header_tenant: Optional[str] = None,
    body_tenant: Optional[str] = None,
) -> str:
    """
    Derive tenant for a request.

    Policy:
    - Active process tenant (CF_TENANT_ID) is authoritative when set.
    - Client-supplied tenant must match active tenant or be empty.
    - Never allow request body/header alone to switch tenant when CF_TENANT_ID is set.
    """
    active = validate_tenant_id(active_tenant()) if active_tenant() else ""
    hdr = validate_tenant_id(header_tenant or "") if header_tenant else ""
    body = validate_tenant_id(body_tenant or "") if body_tenant else ""

    claimed = hdr or body
    if active:
        if claimed and claimed != active:
            raise TenantError("cross-tenant request denied")
        return active
    return claimed


def assert_tenant_owns(resource_tenant: str, *, allow_empty_resource: bool = True) -> None:
    active = active_tenant()
    if not active:
        return
    rt = (resource_tenant or "").strip()
    if not rt and allow_empty_resource:
        return
    if rt != active:
        raise TenantError("resource belongs to another tenant")


def strip_client_tenant_fields(payload: Dict[str, Any]) -> Dict[str, Any]:
    data = dict(payload or {})
    data.pop("tenant_id", None)
    data.pop("tenant", None)
    tid = active_tenant()
    if tid:
        data["tenant_id"] = tid
    return data


def tenant_match_ok(resource_tenant: str) -> bool:
    try:
        assert_tenant_owns(resource_tenant)
        return True
    except TenantError:
        return False
