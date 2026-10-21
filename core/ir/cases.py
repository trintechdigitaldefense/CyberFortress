#!/usr/bin/env python3
"""Incident case store for the IR response team — strengthened lifecycle."""

from __future__ import annotations

import json
import os
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

_LOCK = threading.Lock()
CASE_DIR = Path(os.getenv("CF_IR_CASE_DIR", "./logs/ir_cases"))
CASE_DIR.mkdir(parents=True, exist_ok=True)
INDEX = CASE_DIR / "index.jsonl"

OPENISH = ("open", "investigating", "awaiting_approval", "contained")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class IncidentCase:
    case_id: str
    status: str
    severity: str
    indicator: str
    target: str
    source: str
    detected_at: str
    title: str = ""
    findings: List[str] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    related_events: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    confidence: str = "medium"
    score: int = 50
    report_path: Optional[str] = None
    updated_at: str = ""
    closed_at: Optional[str] = None
    close_reason: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        if not d.get("updated_at"):
            d["updated_at"] = _now()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "IncidentCase":
        fields = cls.__dataclass_fields__
        return cls(**{k: data[k] for k in fields if k in data})


class CaseStore:
    def create(
        self,
        *,
        indicator: str,
        target: str,
        source: str,
        severity: str,
        title: str = "",
        related: Optional[Dict[str, Any]] = None,
        score: int = 50,
        confidence: str = "medium",
        tags: Optional[List[str]] = None,
    ) -> IncidentCase:
        case = IncidentCase(
            case_id=f"IR-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}",
            status="open",
            severity=severity,
            indicator=indicator,
            target=target,
            source=source,
            detected_at=_now(),
            title=title or f"{indicator} on {target}",
            related_events=[related] if related else [],
            score=score,
            confidence=confidence,
            tags=tags or [],
            updated_at=_now(),
        )
        self._write(case)
        return case

    def get(self, case_id: str) -> Optional[IncidentCase]:
        path = CASE_DIR / f"{case_id}.json"
        if not path.exists():
            return None
        return IncidentCase.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def find_open_match(self, indicator: str, target: str) -> Optional[IncidentCase]:
        for c in self.list_by_status(OPENISH, 80):
            if c.indicator == indicator and c.target == target:
                return c
        return None

    def list_open(self, limit: int = 50) -> List[IncidentCase]:
        return self.list_by_status(OPENISH, limit)

    def list_by_status(self, statuses: Sequence[str], limit: int = 50) -> List[IncidentCase]:
        wanted = set(statuses)
        cases: List[IncidentCase] = []
        for path in sorted(CASE_DIR.glob("IR-*.json"), reverse=True)[:400]:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if data.get("status") in wanted:
                    cases.append(IncidentCase.from_dict(data))
            except Exception:
                continue
            if len(cases) >= limit:
                break
        return cases

    def summary(self) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        for path in CASE_DIR.glob("IR-*.json"):
            try:
                st = json.loads(path.read_text(encoding="utf-8")).get("status", "unknown")
                counts[st] = counts.get(st, 0) + 1
            except Exception:
                continue
        return {
            "by_status": counts,
            "open_total": sum(counts.get(s, 0) for s in OPENISH),
            "case_dir": str(CASE_DIR),
        }

    def update(self, case: IncidentCase) -> IncidentCase:
        case.updated_at = _now()
        self._write(case)
        return case

    def append_related(self, case: IncidentCase, event: Dict[str, Any]) -> IncidentCase:
        case.related_events.append(event)
        if len(case.related_events) > 40:
            case.related_events = case.related_events[-40:]
        case.score = min(100, int(case.score) + 5)
        if case.score >= 80:
            case.confidence = "high"
        return self.update(case)

    def close(self, case: IncidentCase, reason: str) -> IncidentCase:
        case.status = "closed"
        case.closed_at = _now()
        case.close_reason = reason
        return self.update(case)

    def _write(self, case: IncidentCase) -> None:
        with _LOCK:
            path = CASE_DIR / f"{case.case_id}.json"
            path.write_text(json.dumps(case.to_dict(), indent=2), encoding="utf-8")
            with open(INDEX, "a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {
                            "case_id": case.case_id,
                            "status": case.status,
                            "severity": case.severity,
                            "score": case.score,
                            "at": _now(),
                        }
                    )
                    + "\n"
                )
