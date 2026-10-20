#!/usr/bin/env python3
"""Post-action verification for CF_BLOCK rules."""

from __future__ import annotations

from typing import Any, Dict, List


def verify_block(target: str, chain: str, list_rules_fn) -> Dict[str, Any]:
    rules = list_rules_fn()
    hits = []
    for r in rules:
        raw = " ".join(
            [
                str(r.get("raw") or ""),
                str(r.get("source") or ""),
                str(r.get("destination") or ""),
            ]
        )
        if target in raw:
            hits.append(r)
    ok = len(hits) >= 1
    return {
        "verified": ok,
        "target": target,
        "matching_rules": hits[:10],
        "rule_count_seen": len(rules),
        "message": (
            f"Verified {len(hits)} rule(s) matching {target} in {chain}"
            if ok
            else f"FAIL: no {chain} rule matched {target} after block_ip"
        ),
    }
