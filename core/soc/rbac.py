#!/usr/bin/env python3
"""Simple RBAC for SOC API / dashboard."""

from __future__ import annotations

import hmac
import os
from typing import Dict, Optional, Set

ROLES: Dict[str, Set[str]] = {
    "viewer": {"read:status", "read:cases", "read:metrics"},
    "analyst": {"read:status", "read:cases", "read:metrics", "write:cases", "write:evidence"},
    "operator": {
        "read:status",
        "read:cases",
        "read:metrics",
        "write:cases",
        "write:evidence",
        "write:containment",
        "approve:tier2",
    },
    "admin": {"*"},
}


def _users() -> Dict[str, Dict[str, str]]:
    raw = os.getenv("CF_SOC_USERS", "")
    users: Dict[str, Dict[str, str]] = {}
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        bits = part.split(":")
        if len(bits) >= 3:
            user, role, token = bits[0], bits[1], ":".join(bits[2:])
            users[user] = {"role": role, "token": token}
    if not users and os.getenv("CF_DASHBOARD_PASS"):
        users["operator"] = {"role": "operator", "token": os.getenv("CF_DASHBOARD_PASS", "")}
    return users


def authenticate(user: str, token: str) -> Optional[str]:
    users = _users()
    rec = users.get(user)
    if not rec:
        if not users and not os.getenv("CF_SOC_REQUIRE_AUTH", "false").lower() in ("1", "true", "yes"):
            return "viewer"
        return None
    if hmac.compare_digest(rec["token"], token):
        return rec["role"]
    return None


def authorize(role: Optional[str], permission: str) -> bool:
    if role is None:
        return not (os.getenv("CF_SOC_REQUIRE_AUTH", "false").lower() in ("1", "true", "yes"))
    perms = ROLES.get(role, set())
    return "*" in perms or permission in perms
