#!/usr/bin/env python3
"""
ROE allow-list enforcement.

Only actions listed in config/pilot_signoff.json → authorized_actions may run.
If no sign-off file exists, a safe built-in pilot allow-list is used.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import List, Optional, Set

logger = logging.getLogger("cf_roe")

SIGNOFF_PATH = Path(os.getenv("CF_PILOT_SIGNOFF", "./config/pilot_signoff.json"))

# Safe default when no client sign-off is present (supervised pilot)
DEFAULT_ALLOW = {
    "block_ip",
    "terminate_session",
    "deploy_decoy",
    "isolate_endpoint",
    "unblock_ip",
    "restore_endpoint",
}


def _load_authorized() -> Optional[List[str]]:
    if not SIGNOFF_PATH.exists():
        return None
    try:
        data = json.loads(SIGNOFF_PATH.read_text(encoding="utf-8"))
        actions = data.get("authorized_actions") or []
        if isinstance(actions, list) and actions:
            return [str(a).strip() for a in actions if str(a).strip()]
    except Exception as e:
        logger.warning(f"Could not read ROE sign-off: {e}")
    return None


def allowed_actions() -> Set[str]:
    loaded = _load_authorized()
    if loaded is None:
        logger.debug("No pilot sign-off — using default pilot allow-list")
        return set(DEFAULT_ALLOW)
    return set(loaded)


def is_action_authorized(action: str) -> bool:
    allowed = allowed_actions()
    ok = action in allowed
    if not ok:
        logger.error(f"Action '{action}' not in ROE allow-list: {sorted(allowed)}")
    return ok


def roe_status() -> dict:
    loaded = _load_authorized()
    return {
        "signoff_file": str(SIGNOFF_PATH),
        "signoff_present": SIGNOFF_PATH.exists(),
        "source": "pilot_signoff" if loaded is not None else "default_pilot",
        "authorized_actions": sorted(allowed_actions()),
    }
