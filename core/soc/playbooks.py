#!/usr/bin/env python3
"""SOAR-lite playbook engine — YAML rules → autonomy actions."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("cf_playbooks")
PLAYBOOK_DIR = Path(os.getenv("CF_PLAYBOOK_DIR", "./config/playbooks"))


def load_playbooks() -> List[Dict[str, Any]]:
    if not PLAYBOOK_DIR.is_dir():
        return []
    out: List[Dict[str, Any]] = []
    try:
        import yaml
    except ImportError:
        logger.warning("PyYAML missing — playbooks disabled")
        return []
    for path in sorted(PLAYBOOK_DIR.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            if isinstance(data, list):
                for item in data:
                    item["_file"] = path.name
                    out.append(item)
            elif isinstance(data, dict):
                data["_file"] = path.name
                out.append(data)
        except Exception as e:
            logger.warning("playbook %s: %s", path, e)
    return out


def match_playbook(
    event: Dict[str, Any], playbooks: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    playbooks = playbooks if playbooks is not None else load_playbooks()
    hits = []
    ind = str(event.get("indicator", "")).lower()
    sev = str(event.get("severity", "")).upper()
    tags = {str(t).lower() for t in (event.get("tags") or [])}
    for pb in playbooks:
        if pb.get("enabled") is False:
            continue
        when = pb.get("when") or {}
        sev_ok = not when.get("severity_in") or sev in [s.upper() for s in when["severity_in"]]
        ind_ok = True
        if when.get("indicator_contains"):
            ind_ok = any(x.lower() in ind for x in when["indicator_contains"])
        tag_ok = True
        if when.get("tags_any"):
            tag_ok = bool(tags.intersection({t.lower() for t in when["tags_any"]}))
        min_score = when.get("min_score")
        score_ok = min_score is None or int(event.get("score") or event.get("priority") or 0) >= int(
            min_score
        )
        if sev_ok and ind_ok and tag_ok and score_ok:
            hits.append(pb)
    return hits


def run_playbook_actions(event: Dict[str, Any], playbook: Dict[str, Any]) -> List[Dict[str, Any]]:
    from core.autonomy import execute_with_autonomy

    results = []
    for step in playbook.get("actions") or []:
        action = step.get("action") or "block_ip"
        target = step.get("target") or event.get("target") or "unknown"
        force = bool(step.get("force", False))
        try:
            ok = execute_with_autonomy(
                action=action,
                target=str(target),
                scope=step.get("scope") or "single",
                force=force,
                severity=str(event.get("severity") or "HIGH"),
            )
            results.append(
                {
                    "action": action,
                    "target": target,
                    "ok": bool(ok),
                    "playbook": playbook.get("name"),
                }
            )
        except Exception as e:
            results.append(
                {"action": action, "target": target, "ok": False, "error": str(e)[:120]}
            )
    return results
