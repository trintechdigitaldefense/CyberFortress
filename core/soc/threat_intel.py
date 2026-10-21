#!/usr/bin/env python3
"""Threat intel feed loader — local file + optional URL."""

from __future__ import annotations

import logging
import os
import urllib.request
from pathlib import Path
from typing import Dict, Set

logger = logging.getLogger("cf_ti")
TI_DIR = Path(os.getenv("CF_TI_DIR", "./config/threat_intel"))
_CACHE: Set[str] = set()
_META: Dict[str, str] = {}


def load_local() -> Set[str]:
    global _CACHE
    indicators: Set[str] = set()
    TI_DIR.mkdir(parents=True, exist_ok=True)
    sample = TI_DIR / "block_ips.txt"
    if not sample.exists():
        sample.write_text("# one IP or domain per line\n", encoding="utf-8")
    for path in TI_DIR.glob("*.txt"):
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    indicators.add(line.lower())
        except Exception as e:
            logger.warning("TI file %s: %s", path, e)
    _CACHE = indicators
    _META["count"] = str(len(indicators))
    return indicators


def refresh_url() -> int:
    url = os.getenv("CF_TI_URL", "")
    if not url:
        return 0
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            text = resp.read().decode("utf-8", errors="replace")
        dest = TI_DIR / "feed_url.txt"
        dest.write_text(text, encoding="utf-8")
        load_local()
        return len(_CACHE)
    except Exception as e:
        logger.warning("TI URL refresh failed: %s", e)
        return 0


def match(target: str) -> bool:
    if not _CACHE:
        load_local()
    return (target or "").lower() in _CACHE


def status() -> Dict[str, str]:
    if not _CACHE:
        load_local()
    return {"indicators": str(len(_CACHE)), **_META}
