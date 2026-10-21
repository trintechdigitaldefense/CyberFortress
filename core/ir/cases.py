#!/usr/bin/env python3
"""Lightweight incident case store for the IR response team agents."""

from __future__ import annotations

import json
import os
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_LOCK = threading.Lock()
CASE_DIR = Path(os.getenv("CF_IR_CASE_DIR", "./logs/ir_cases"))
CASE_DIR.mkdir(parents=True, exist_ok=True)
INDEX = CASE_DIR / "index.jsonl"


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
    report_path: Optional[str] = None
    updated_at: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        if not d.get("updated_at"):
            d["updated_at"] = _now()
        return d


class CaseStore:
    def create(
        self,
        *,
        indicator: str,
        target: str,
        source: str,
        severity: str,
        title: str = "",
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
            updated_at=_now(),
        )
        self._write(case)
        return case

    def get(self, case_id: str) -> Optional[IncidentCase]:
        path = CASE_DIR / f"{case_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return IncidentCase(**{k: data[k] for k in IncidentCase.__dataclass_fields__ if k in data})

    def list_open(self, limit: int = 50) -> List[IncidentCase]:
        return self.list_by_status(("open", "investigating", "contained"), limit)

    def list_by_status(self, statuses, limit: int = 50):
        wanted = set(statuses)
        cases = []
        for path in sorted(CASE_DIR.glob("IR-*.json"), reverse=True)[:300]:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if data.get("status") in wanted:
                    cases.append(
                        IncidentCase(**{k: data[k] for k in IncidentCase.__dataclass_fields__ if k in data})
                    )
            except Exception:
                continue
            if len(cases) >= limit:
                break
        return cases

    def update(self, case: IncidentCase) -> IncidentCase:
        case.updated_at = _now()
        self._write(case)
        return case

    def _write(self, case: IncidentCase) -> None:
        with _LOCK:
            path = CASE_DIR / f"{case.case_id}.json"
            path.write_text(json.dumps(case.to_dict(), indent=2), encoding="utf-8")
            with open(INDEX, "a", encoding="utf-8") as f:
                f.write(json.dumps({"case_id": case.case_id, "status": case.status, "at": _now()}) + "\n")
