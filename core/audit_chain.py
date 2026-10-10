#!/usr/bin/env python3
"""Tamper-evident append-only CMA audit chain (SHA-256 linked)."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

GENESIS = "0" * 64


def _canonical(entry: Dict[str, Any]) -> str:
    payload = {k: v for k, v in entry.items() if k != "entry_hash"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def hash_entry(entry: Dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(entry).encode("utf-8")).hexdigest()


def last_hash(path: Path) -> str:
    if not path.exists():
        return GENESIS
    prev = GENESIS
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                prev = obj.get("entry_hash") or hash_entry(obj)
            except json.JSONDecodeError:
                continue
    return prev


def append_chained(path: Path, entry: Dict[str, Any]) -> Dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = dict(entry)
    if "timestamp" not in entry:
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
    if "clock_source" not in entry:
        entry["clock_source"] = "host_utc"
    entry["prev_hash"] = last_hash(path)
    entry["entry_hash"] = hash_entry(entry)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")
    return entry


def verify_chain(path: Path) -> Tuple[bool, Optional[int], str]:
    if not path.exists():
        return True, None, "no log file (empty chain ok)"
    prev = GENESIS
    with open(path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                return False, idx, f"invalid JSON at index {idx}"
            if obj.get("prev_hash") != prev:
                return False, idx, f"prev_hash mismatch at index {idx}"
            expected = hash_entry(obj)
            if obj.get("entry_hash") != expected:
                return False, idx, f"entry_hash mismatch at index {idx}"
            prev = obj["entry_hash"]
    return True, None, "chain intact"


def load_entries(path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not path.exists():
        return out
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out
