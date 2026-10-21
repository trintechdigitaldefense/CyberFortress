#!/usr/bin/env python3
"""Post-action verification for CF_BLOCK rules."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional


def verify_block(
    target: str,
    chain: str = "CF_BLOCK",
    list_rules_fn: Optional[Callable[[], List[Dict[str, str]]]] = None,
) -> Dict[str, Any]:
    """Return verified=True if target appears as source or destination DROP in chain."""
    if list_rules_fn is None:
        from core.containment.firewall import list_cf_rules

        list_rules_fn = list_cf_rules

    host = (target or "").strip().split("/")[0]
    rules = list_rules_fn() or []
    hits = []
    for r in rules:
        src = str(r.get("source") or "")
        dst = str(r.get("destination") or "")
        raw = str(r.get("raw") or "")
        if host and (host == src or host == dst or host in raw):
            hits.append(r)

    ok = len(hits) > 0
    both = any(h.get("source") == host for h in hits) and any(
        h.get("destination") == host for h in hits
    )
    return {
        "verified": ok,
        "target": host,
        "chain": chain,
        "bidirectional": both,
        "matching_rules": hits[:10],
        "rule_count_seen": len(rules),
        "message": (
            f"Verified {len(hits)} rule(s) matching {host} in {chain}"
            + (" (src+dst)" if both else "")
            if ok
            else f"FAIL: no {chain} rule matched {host} after block_ip"
        ),
    }
