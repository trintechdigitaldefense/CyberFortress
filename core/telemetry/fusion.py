#!/usr/bin/env python3
"""
CyberFortress Telemetry Fusion Engine
Collects, normalizes, and correlates events from multiple sources
(Sentinel, Mirage, local logs, live APIs) and feeds them into the
Escalation Engine + Autonomy decision path.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from core.telemetry.adapters import SentinelAdapter, MirageAdapter, LocalLogAdapter, BaseAdapter
from core.telemetry.api_connectors import SentinelAPIConnector, MirageAPIConnector
from core.escalation import ingest_event, recommend_playbook, AlertLevel
from core.autonomy import execute_with_autonomy

logger = logging.getLogger("cf_telemetry.fusion")


class TelemetryFusion:
    def __init__(self, auto_respond: bool = False):
        self.adapters: List[BaseAdapter] = []
        self.auto_respond = auto_respond
        self._seen_ids = set()

    def register(self, adapter: BaseAdapter):
        self.adapters.append(adapter)
        logger.info(f"Registered adapter: {adapter.source_name}")

    def register_defaults(self):
        """Register file-based + live API connectors."""
        self.register(SentinelAdapter())
        self.register(MirageAdapter())
        self.register(LocalLogAdapter())
        # Live API connectors (no-op if env vars not set)
        self.register(SentinelAPIConnector())
        self.register(MirageAPIConnector())

    def collect(self) -> List[Dict[str, Any]]:
        all_events = []
        for adapter in self.adapters:
            try:
                events = adapter.fetch_events()
                all_events.extend(events)
                logger.debug(f"{adapter.source_name}: {len(events)} events")
            except Exception as e:
                logger.error(f"Adapter {adapter.source_name} failed: {e}")
        return all_events

    def process(self, events: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        if events is None:
            events = self.collect()

        results = []

        for event in events:
            eid = f"{event['source']}:{event['indicator']}:{event['target']}:{event.get('timestamp', '')}"
            if eid in self._seen_ids:
                continue
            self._seen_ids.add(eid)

            level = ingest_event(
                source=event["source"],
                indicator=event["indicator"],
                target=event["target"],
                raw=event.get("raw"),
            )

            recommended = recommend_playbook(level, event["indicator"])

            result = {
                "event": event,
                "escalated_level": level.value,
                "recommended_playbook": recommended,
                "auto_executed": False,
            }

            logger.info(
                f"[{level.value}] {event['source']} → {event['indicator']} on {event['target']} "
                f"| recommend: {recommended}"
            )

            if self.auto_respond and level in (AlertLevel.HIGH, AlertLevel.CRITICAL):
                logger.info(f"Auto-responding with playbook: {recommended}")
                allowed = execute_with_autonomy(
                    action=recommended,
                    target=event["target"],
                    scope="single" if level != AlertLevel.CRITICAL else "subnet",
                    force=False,
                    severity=level.value,
                )
                result["auto_executed"] = allowed

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
