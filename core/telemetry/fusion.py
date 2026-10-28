#!/usr/bin/env python3
"""Telemetry fusion — collect, correlate, audit, optional auto-respond."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from core.telemetry.adapters import SentinelAdapter, MirageAdapter, LocalLogAdapter, BaseAdapter
from core.telemetry.api_connectors import SentinelAPIConnector, MirageAPIConnector
from core.telemetry.host_signals import HostLogAdapter, HostResourceAdapter
from core.escalation import ingest_event, recommend_playbook, AlertLevel
from core.autonomy import execute_with_autonomy
from core.rules import resolve_playbook, pack_summary
from core.monitoring_metrics import record_events, record_adapter_error

logger = logging.getLogger("cf_telemetry.fusion")

AUDIT_PATH = Path(os.getenv("CF_AUDIT_PATH", "./logs/cma_audit.jsonl"))


class TelemetryFusion:
    def __init__(self, auto_respond: bool = False):
        self.adapters: List[BaseAdapter] = []
        self.auto_respond = auto_respond
        self._seen_ids: set = set()

    def register(self, adapter: BaseAdapter):
        self.adapters.append(adapter)
        logger.info("Registered adapter: %s", adapter.source_name)

    def register_defaults(self):
        self.register(SentinelAdapter())
        self.register(MirageAdapter())
        self.register(LocalLogAdapter())
        self.register(SentinelAPIConnector())
        self.register(MirageAPIConnector())
        self.register(HostLogAdapter())
        self.register(HostResourceAdapter())

    def collect(self) -> List[Dict[str, Any]]:
        all_events = []
        for adapter in self.adapters:
            try:
                events = adapter.fetch_events()
                all_events.extend(events)
                if events:
                    logger.info("%s: %s events", adapter.source_name, len(events))
            except Exception as e:
                logger.error("Adapter %s failed: %s", adapter.source_name, e)
                try:
                    record_adapter_error(adapter.source_name, str(e))
                except Exception:
                    pass
        return all_events

    def _audit_detection(self, event, level, playbook, rule_id, pack_id, executed):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tag": "TT_CMA_TAG",
            "action": f"detection:{event.get('indicator', 'unknown')}",
            "target": event.get("target", "unknown"),
            "severity": level,
            "legislative_justification": (
                f"Rules-driven detection from {event.get('source')} | "
                f"playbook={playbook} | rule={rule_id or 'escalation_default'} | "
                f"pack={pack_id or 'n/a'} | auto_executed={executed}"
            ),
            "source": event.get("source", "fusion"),
            "indicator": event.get("indicator"),
            "recommended_playbook": playbook,
            "rule_id": rule_id,
            "pack_id": pack_id,
            "auto_executed": executed,
        }
        try:
            from core.audit_chain import append_chained, AuditChainError

            append_chained(AUDIT_PATH, entry)
        except Exception as e:
            # Fail closed: never write an unchained record to the same audit log.
            # High-impact callers must treat this as an authorization / evidence failure.
            logger.error("Audit chain write failed (no unchained fallback): %s", e)
            raise

    def process(self, events: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        if events is None:
            events = self.collect()

        try:
            if events:
                record_events(events)
        except Exception:
            pass

        results = []
        for event in events:
            eid = f"{event.get('source')}:{event.get('indicator')}:{event.get('target')}:{event.get('timestamp', '')}"
            if eid in self._seen_ids:
                continue
            self._seen_ids.add(eid)
            if len(self._seen_ids) > 5000:
                self._seen_ids = set(list(self._seen_ids)[-2000:])

            level = ingest_event(
                source=event["source"],
                indicator=event["indicator"],
                target=event["target"],
                raw=event.get("raw"),
            )

            recommended = recommend_playbook(level, event["indicator"])
            playbook, rule_id, pack_id = resolve_playbook(event["indicator"], recommended)

            result = {
                "event": event,
                "escalated_level": level.value,
                "recommended_playbook": playbook,
                "rule_id": rule_id,
                "pack_id": pack_id,
                "auto_executed": False,
            }

            logger.info(
                "[%s] %s → %s on %s | playbook=%s rule=%s",
                level.value,
                event["source"],
                event["indicator"],
                event["target"],
                playbook,
                rule_id or "-",
            )

            executed = False
            if self.auto_respond and level in (AlertLevel.HIGH, AlertLevel.CRITICAL):
                logger.info("Auto-responding with playbook: %s", playbook)
                executed = bool(
                    execute_with_autonomy(
                        action=playbook,
                        target=event["target"],
                        scope="single" if level != AlertLevel.CRITICAL else "subnet",
                        force=False,
                        severity=level.value,
                    )
                )
                result["auto_executed"] = executed

            self._audit_detection(event, level.value, playbook, rule_id, pack_id, executed)
            results.append(result)

        return results


def ingest_from_source(source: str, indicator: str, target: str, raw: dict = None) -> Dict[str, Any]:
    fusion = TelemetryFusion(auto_respond=False)
    event = {
        "source": source,
        "indicator": indicator,
        "target": target,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "raw": raw or {},
    }
    results = fusion.process([event])
    return results[0] if results else {}
