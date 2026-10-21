#!/usr/bin/env python3
"""Drain SOC event bus → audit/intelligence + optional SIEM syslog export."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from core.agent_runtime import run_forever
from core.audit_chain import append_chained
from core.intelligence import get_engine
from core.soc.event_bus import get_bus
from core.soc.siem import export_syslog, format_cef
from core.soc.threat_intel import match as ti_match

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SIEM-BRIDGE] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_siem_bridge")
INTERVAL = int(os.getenv("CF_SIEM_BRIDGE_INTERVAL", "10"))
AUDIT = Path(os.getenv("CF_AUDIT_PATH", "./logs/cma_audit.jsonl"))
ENGINE = get_engine()


def _cycle():
    bus = get_bus()
    batch = bus.consume(int(os.getenv("CF_SIEM_BRIDGE_BATCH", "200")))
    written = 0
    ti_hits = 0
    for ev in batch:
        target = str(ev.get("target", ""))
        if ti_match(target):
            ev["tags"] = list(set((ev.get("tags") or []) + ["threat_intel"]))
            ev["severity"] = "HIGH"
            ti_hits += 1
        intel = ENGINE.observe(
            indicator=str(ev.get("indicator", "event")),
            target=target,
            severity=str(ev.get("severity", "MEDIUM")),
            source=str(ev.get("source", "siem")),
            score=70 if ti_hits else 55,
        )
        try:
            entry = {
                "timestamp": ev.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                "action": ev.get("action") or f"detection:{ev.get('indicator')}",
                "target": target,
                "severity": ev.get("severity"),
                "indicator": ev.get("indicator"),
                "source": ev.get("source"),
                "priority": intel["priority"],
                "tags": ev.get("tags") or [],
            }
            try:
                append_chained(AUDIT, entry)
            except Exception:
                AUDIT.parent.mkdir(parents=True, exist_ok=True)
                with open(AUDIT, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")
            written += 1
        except Exception as e:
            logger.warning("audit write: %s", e)
        if os.getenv("CF_SIEM_SYSLOG_HOST"):
            export_syslog(format_cef(ev))
    return {"consumed": len(batch), "written": written, "ti_hits": ti_hits, **bus.stats()}


def main():
    logger.info("SIEM bridge interval=%ss", INTERVAL)
    run_forever("siem_bridge", _cycle, INTERVAL, error_sleep=10.0)


if __name__ == "__main__":
    main()
