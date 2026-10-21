#!/usr/bin/env python3
"""Threat hunting agent — primary fusion collector + intelligence observe."""

from __future__ import annotations

import json
import logging
import os

from core.agent_runtime import run_forever
from core.capacity import limits
from core.intelligence import get_engine
from core.tenant import apply_tenant_env

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [THREAT] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_threat")

INTERVAL = int(os.getenv("CF_THREAT_INTERVAL", "25"))
_fusion = None
ENGINE = get_engine()


def _get_fusion():
    global _fusion
    if _fusion is None:
        from core.telemetry.fusion import TelemetryFusion

        auto = os.getenv("CF_AUTO_RESPOND", "true").lower() == "true"
        _fusion = TelemetryFusion(auto_respond=auto)
        _fusion.register_defaults()
    return _fusion


def _cycle():
    raw = os.getenv("CF_ASSET_CRITICALITY_JSON", "")
    if raw:
        try:
            ENGINE.set_asset_criticality(json.loads(raw))
        except Exception:
            pass
    fusion = _get_fusion()
    results = fusion.process() or []
    max_ev = limits()["max_events_per_cycle"]
    load_ratio = max(1.0, len(results) / max(1, max_ev))
    high = 0
    for r in results:
        try:
            if isinstance(r, dict):
                ind = str(r.get("indicator") or r.get("rule") or "event")
                tgt = str(r.get("target") or r.get("src") or "unknown")
                sev = str(r.get("severity") or "MEDIUM")
                src = str(r.get("source") or "fusion")
                score = int(r.get("score") or 50)
            else:
                ind = str(getattr(r, "indicator", "event"))
                tgt = str(getattr(r, "target", "unknown"))
                sev = str(getattr(r, "severity", "MEDIUM"))
                src = str(getattr(r, "source", "fusion"))
                score = 50
            intel = ENGINE.observe(
                indicator=ind, target=tgt, severity=sev, source=src, score=score
            )
            if intel["priority"] >= 70:
                high += 1
        except Exception:
            continue
    return {
        "events": len(results),
        "high_priority": high,
        "load_ratio": load_ratio,
        **ENGINE.summary(),
    }


def main():
    apply_tenant_env()
    logger.info("Threat hunting agent interval=%ss", INTERVAL)
    run_forever("threat_agent", _cycle, INTERVAL, error_sleep=12.0)


if __name__ == "__main__":
    main()
