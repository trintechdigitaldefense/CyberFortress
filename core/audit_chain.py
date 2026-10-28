#!/usr/bin/env python3
"""Tamper-evident append-only CMA audit chain (SHA-256 linked).

Process-safe appends use an exclusive file lock on a sidecar ``.lock`` file.
Malformed lines, missing hashes and broken links fail verification (fail closed).
Callers that need high-impact actions must treat append failures as authorization
failures — this module raises rather than writing an unchained fallback.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("cf_audit_chain")

GENESIS = "0" * 64


class AuditChainError(Exception):
    """Raised when the chain cannot be read or extended safely."""


def _canonical(entry: Dict[str, Any]) -> str:
    payload = {k: v for k, v in entry.items() if k != "entry_hash"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def hash_entry(entry: Dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(entry).encode("utf-8")).hexdigest()


def _lock_path(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".lock")


def _acquire_lock(path: Path):
    """Return an open lock file object holding an exclusive flock (caller closes)."""
    import fcntl

    lock_file = _lock_path(path)
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    fh = open(lock_file, "a+", encoding="utf-8")
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
    except Exception:
        fh.close()
        raise
    return fh


def last_hash(path: Path, *, strict: bool = True) -> str:
    """Return the last entry_hash in the chain.

    If *strict* is True (default), malformed JSON or missing entry_hash raises
    AuditChainError instead of skipping the line.
    """
    if not path.exists():
        return GENESIS
    prev = GENESIS
    with open(path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                if strict:
                    raise AuditChainError(f"invalid JSON at index {idx}: {e}") from e
                continue
            h = obj.get("entry_hash")
            if not h or not isinstance(h, str) or len(h) != 64:
                if strict:
                    raise AuditChainError(f"missing/invalid entry_hash at index {idx}")
                h = hash_entry(obj)
            prev = h
    return prev


def append_chained(path: Path, entry: Dict[str, Any]) -> Dict[str, Any]:
    """Append one hashed entry under an exclusive inter-process lock.

    Raises AuditChainError if the existing chain is corrupt or the write fails.
    Does **not** write an unchained fallback record.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_fh = _acquire_lock(path)
    try:
        entry = dict(entry)
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        if "clock_source" not in entry:
            entry["clock_source"] = "host_utc"
        try:
            entry["prev_hash"] = last_hash(path, strict=True)
        except AuditChainError:
            raise
        entry["entry_hash"] = hash_entry(entry)
        line = json.dumps(entry, default=str) + "\n"
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                pass
        try:
            os.chmod(path, 0o640)
        except OSError:
            pass
        return entry
    finally:
        try:
            import fcntl

            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
        lock_fh.close()


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


def load_entries(path: Path, *, skip_corrupt: bool = False) -> List[Dict[str, Any]]:
    """Load entries. By default raises on first corrupt line; set skip_corrupt for salvage."""
    out: List[Dict[str, Any]] = []
    if not path.exists():
        return out
    with open(path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                if skip_corrupt:
                    logger.warning("audit load skipping corrupt line index=%s", idx)
                    continue
                raise AuditChainError(f"invalid JSON at index {idx}")
    return out
