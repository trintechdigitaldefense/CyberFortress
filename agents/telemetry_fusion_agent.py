#!/usr/bin/env python3
"""
Telemetry fusion agent.

By default does NOT re-run full fusion.process() (threat_hunting_agent already does).
Set CF_FUSION_PROCESS=true only if you intentionally want a second collector loop.
"""

from __future__ import annotations

import logging
import os

from core.agent_runtime import run_forever
from core.monitoring_metrics import load_persisted
from core.tenant import apply_tenant_env

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [FUSION_AGENT] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_fusion_agent")

INTERVAL = int(os.getenv("CF_FUSION_INTERVAL", "30"))
DO_PROCESS = os.getenv("CF_FUSION_PROCESS", "false").lower() in ("1", "true", "yes")
_fusion = None


def _get_fusion():
    global _fusion
    if _fusion is None:
        from core.telemetry.fusion import TelemetryFusion

        auto = os.getenv("CF_AUTO_RESPOND", "true").lower() == "true"
        _fusion = TelemetryFusion(auto_respond=auto)
        _fusion.register_defaults()
    return _fusion


def _cycle():
    mon = {}
    try:
        mon = load_persisted()
    except Exception:
        pass
    events = 0
    if DO_PROCESS:
        results = _get_fusion().process()
        events = len(results)
    return {
        "events": events,
        "process_enabled": DO_PROCESS,
        "metrics_total": mon.get("total_events"),
        "last_detection": mon.get("last_detection"),
        "adapters": len(_get_fusion().adapters) if DO_PROCESS else 0,
    }


def main():
    apply_tenant_env()
    logger.info(
        "Fusion agent interval=%ss process=%s (threat agent is primary collector)",
        INTERVAL,
        DO_PROCESS,
    )
    if DO_PROCESS:
        _get_fusion()
    run_forever("fusion_agent", _cycle, INTERVAL, error_sleep=10.0)


if __name__ == "__main__":
    main()
