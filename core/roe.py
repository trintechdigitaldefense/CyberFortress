#!/usr/bin/env python3
"""
Fail-closed rules-of-engagement enforcement.

Live actions are authorised only by an explicit, valid client sign-off.
Missing, malformed or incomplete sign-off grants no live actions.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import List, Optional, Set

logger = logging.getLogger("cf_roe")

SIGNOFF_PATH = Path(os.getenv("CF_PILOT_SIGNOFF", "./config/pilot_signoff.json"))


def _load_authorized() -> Optional[List[str]]:
    """Return explicitly authorised actions, or None when sign-off is unusable."""
    if not SIGNOFF_PATH.is_file():
        return None
    try:
        data = json.loads(SIGNOFF_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None
        actions = data.get("authorized_actions")
        if not isinstance(actions, list) or not actions:
            return None
        cleaned = [str(action).strip() for action in actions if str(action).strip()]
        return cleaned or None
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.warning("Could not read ROE sign-off: %s", exc)
        return None


def allowed_actions() -> Set[str]:
    """Return the client-approved action set; empty means deny all live actions."""
    loaded = _load_authorized()
    return set(loaded) if loaded is not None else set()


def is_action_authorized(action: str) -> bool:
    allowed = allowed_actions()
    ok = bool(action) and action in allowed
    if not ok:
        logger.error("Action '%s' denied: no valid explicit ROE authorisation", action)
    return ok


def roe_status() -> dict:
    loaded = _load_authorized()
    valid = loaded is not None
    return {
        "signoff_file": str(SIGNOFF_PATH),
        "signoff_present": SIGNOFF_PATH.is_file(),
        "signoff_valid": valid,
        "source": "pilot_signoff" if valid else "deny_all",
        "authorized_actions": sorted(loaded or []),
    }
