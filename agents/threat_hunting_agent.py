#!/usr/bin/env python3
"""CyberFortress Threat Hunting Agent — continuous rules-driven telemetry cycles."""

from __future__ import annotations

from typing import Optional
import logging
import os
from datetime import datetime, timezone

from core.agent_runtime import run_forever
from core.rules import load_pack, pack_summary
from core.telemetry.fusion import TelemetryFusion
from core.tenant import apply_tenant_env

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [THREAT_AGENT] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_threat_agent")

INTERVAL = int(os.getenv("CF_THREAT_INTERVAL", "30"))
_fusion: Optional[TelemetryFusion] = None


def _get_fusion() -> TelemetryFusion:
    global _fusion
    if _fusion is None:
        auto = os.getenv("CF_AUTO_RESPOND", "true").lower() == "true"
        _fusion = TelemetryFusion(auto_respond=auto)
        _fusion.register_defaults()
        logger.info("Fusion registered | auto_respond=%s | adapters=%s", auto, len(_fusion.adapters))
    return _fusion


def _cycle():
    fusion = _get_fusion()
    ts = datetime.now(timezone.utc).isoformat()
    logger.info("Hunting cycle at %s", ts)
    results = fusion.process()
    high = sum(1 for r in results if r.get("escalated_level") in ("HIGH", "CRITICAL"))
    logger.info("Cycle complete: %s event(s), %s high/critical", len(results), high)
    return {
        "events": len(results),
        "high_or_critical": high,
        **pack_summary(),
    }


def main():
    logger.info("CyberFortress Threat Hunting Agent starting...")
    apply_tenant_env()
    load_pack(force=True)
    summary = pack_summary()
    logger.info("Rule pack: %s (%s rules)", summary.get("pack_id"), summary.get("rule_count"))
    _get_fusion()
    run_forever("threat_agent", _cycle, INTERVAL, error_sleep=10.0)


if __name__ == "__main__":
    main()
