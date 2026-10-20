#!/usr/bin/env python3
"""CyberFortress rule packs — versioned indicator → severity/playbook mapping."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("cf_rules")

_PACK: Optional[Dict[str, Any]] = None


def _pack_path() -> Path:
    root = Path(os.getenv("CF_ROOT", ".")).resolve()
    custom = os.getenv("CF_RULE_PACK", "")
    if custom:
        return Path(custom)
    return root / "config" / "rule_packs" / "default.yaml"


def load_pack(force: bool = False) -> Dict[str, Any]:
    global _PACK
    if _PACK is not None and not force:
        return _PACK
    path = _pack_path()
    if not path.exists():
        logger.warning("Rule pack not found at %s — using empty pack", path)
        _PACK = {"pack_id": "none", "version": "0", "rules": []}
        return _PACK
    try:
        import yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        _PACK = data
        logger.info(
            "Loaded rule pack %s v%s (%s rules)",
            data.get("pack_id"),
            data.get("version"),
            len(data.get("rules") or []),
        )
        return _PACK
    except Exception as e:
        logger.exception("Failed to load rule pack: %s", e)
        _PACK = {"pack_id": "error", "version": "0", "rules": []}
        return _PACK


def match_rule(indicator: str) -> Optional[Dict[str, Any]]:
    pack = load_pack()
    ind = (indicator or "").lower()
    for rule in pack.get("rules") or []:
        for token in rule.get("match_indicators") or []:
            if token.lower() in ind:
                out = dict(rule)
                out["pack_id"] = pack.get("pack_id", "unknown")
                return out
    return None


def resolve_playbook(indicator: str, fallback: str) -> Tuple[str, Optional[str], Optional[str]]:
    rule = match_rule(indicator)
    if not rule:
        pack = load_pack()
        return fallback, None, pack.get("pack_id")
    return (
        rule.get("playbook") or fallback,
        rule.get("id"),
        rule.get("pack_id"),
    )


def pack_summary() -> Dict[str, Any]:
    pack = load_pack()
    return {
        "pack_id": pack.get("pack_id"),
        "version": pack.get("version"),
        "rule_count": len(pack.get("rules") or []),
    }
