#!/usr/bin/env python3
"""Simple file-based leader election for active/standby pairs."""

from __future__ import annotations

import os
import socket
import time
from pathlib import Path
from typing import Any, Dict

LOCK = Path(os.getenv("CF_HA_LOCK", "./logs/ha_leader.lock"))
TTL = int(os.getenv("CF_HA_TTL_S", "30"))
NODE = os.getenv("CF_HA_NODE_ID") or socket.gethostname()


def try_become_leader() -> Dict[str, Any]:
    now = time.time()
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        try:
            data = LOCK.read_text(encoding="utf-8").strip().split("|")
            node, ts = data[0], float(data[1])
            if node != NODE and now - ts < TTL:
                return {"leader": False, "leader_node": node, "node": NODE}
        except Exception:
            pass
    LOCK.write_text(f"{NODE}|{now}", encoding="utf-8")
    return {"leader": True, "leader_node": NODE, "node": NODE}


def is_leader() -> bool:
    return bool(try_become_leader().get("leader"))


def status() -> Dict[str, Any]:
    st = try_become_leader()
    st["ttl_s"] = TTL
    st["lock"] = str(LOCK)
    return st
