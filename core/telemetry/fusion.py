#!/usr/bin/env python3
"""
CyberFortress Telemetry Fusion Engine
Collects, normalizes, and correlates events from multiple sources
(Sentinel, Mirage, local logs, etc.) and feeds them into the
Escalation Engine + Autonomy decision path.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from core.telemetry.adapters import SentinelAdapter, MirageAdapter, LocalLogAdapter, BaseAdapter
from core.escalation import ingest_event, recommend_playbook, AlertLevel
from core.autonomy import execute_with_autonomy

logger = logging.getLogger("cf_telemetry.fusion")


class TelemetryFusion:
    """
    Central fusion point.
    - Pulls events from registered adapters
    - Normalizes them
    - Runs them through the Smart Escalation Engine
    - Optionally auto-triggers recommended playbooks
    """

    def __init__(self, auto_respond: bool = False):
        self.adapters: List[BaseAdapter] = []
        self.auto_respond = auto_respond  # if True, automatically run recommended playbooks
        self._seen_ids = set()  # simple de-duplication for MVP

    def register(self, adapter: BaseAdapter):
        self.adapters.append(adapter)
        logger.info(f"Registered adapter: {adapter.source_name}")

    def register_defaults(self):
        """Convenience: register the standard TrinTech adapters."""
        self.register(SentinelAdapter())
        self.register(MirageAdapter())
        self.register(LocalLogAdapter())

    def collect(self) -> List[Dict[str, Any]]:
        """Pull fresh events from all adapters."""
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
        """
        Main fusion loop:
        1. Collect (if not provided)
        2. De-duplicate
        3. Feed into Escalation Engine
        4. Optionally auto-execute recommended playbook
        """
        if events is None:
            events = self.collect()

        results = []

        for event in events:
            # Simple de-dupe key
            eid = f"{event['source']}:{event['indicator']}:{event['target']}:{event.get('timestamp', '')}"
            if eid in self._seen_ids:
                continue
            self._seen_ids.add(eid)

            # Feed into Smart Escalation
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

            # Optional auto-response (still respects Tier 1 / Tier 2 HITL)
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
    """
    Convenience helper for other modules (or external tools)
    to push a single event directly into the fusion + escalation pipeline.
    """
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
