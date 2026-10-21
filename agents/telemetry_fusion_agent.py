#!/usr/bin/env python3
"""Telemetry fusion agent — collection loop with metrics in heartbeat."""

from __future__ import annotations

from typing import Optional
import logging
import os

from core.agent_runtime import run_forever
from core.monitoring_metrics import load_persisted
from core.telemetry.fusion import TelemetryFusion
from core.tenant import apply_tenant_env

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [FUSION_AGENT] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_fusion_agent")

INTERVAL = int(os.getenv("CF_FUSION_INTERVAL", "30"))
_fusion: Optional[TelemetryFusion] = None


def _get_fusion() -> TelemetryFusion:
    global _fusion
    if _fusion is None:
        auto = os.getenv("CF_AUTO_RESPOND", "true").lower() == "true"
        _fusion = TelemetryFusion(auto_respond=auto)
        _fusion.register_defaults()
    return _fusion


def _cycle():
    results = _get_fusion().process()
    mon = {}
    try:
        mon = load_persisted()
    except Exception:
        pass
    return {
        "events": len(results),
        "metrics_total": mon.get("total_events"),
        "last_detection": mon.get("last_detection"),
        "adapters": len(_get_fusion().adapters),
    }


def main():
    apply_tenant_env()
    logger.info("Fusion agent interval=%ss", INTERVAL)
    _get_fusion()
    run_forever("fusion_agent", _cycle, INTERVAL, error_sleep=10.0)


if __name__ == "__main__":
    main()
