#!/usr/bin/env python3
"""IR Team — DETECT: open/correlate cases with windowed intelligence scoring."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from core.agent_runtime import run_forever
from core.capacity import limits, should_shed
from core.intelligence import get_engine
from core.ir.cases import CaseStore
from core.ir.scoring import score_event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [IR-DETECT] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_ir_detect")

INTERVAL = int(os.getenv("CF_IR_DETECT_INTERVAL", "30"))
AUDIT = Path(os.getenv("CF_AUDIT_PATH", "./logs/cma_audit.jsonl"))
STATE = Path(os.getenv("CF_LOG_DIR", "./logs")) / "ir_detect_offset"
STORE = CaseStore()
SEV_OK = {"HIGH", "CRITICAL"}
MIN_SCORE = int(os.getenv("CF_IR_MIN_SCORE", "55"))
ENGINE = get_engine()


def _load_assets():
    raw = os.getenv("CF_ASSET_CRITICALITY_JSON", "")
    if raw:
        try:
            ENGINE.set_asset_criticality(json.loads(raw))
        except Exception:
            pass


def _offset() -> int:
    if STATE.exists():
        try:
            return int(STATE.read_text().strip() or "0")
        except Exception:
            return 0
    return 0


def _set_offset(n: int) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(str(n), encoding="utf-8")


def _cycle():
    _load_assets()
    if not AUDIT.exists():
        return {"opened": 0, "correlated": 0, "note": "no audit yet", **ENGINE.summary()}
    lines = AUDIT.read_text(encoding="utf-8").splitlines()
    start = _offset()
    if start > len(lines):
        start = 0
    batch = lines[start:]
    max_ev = limits()["max_events_per_cycle"]
    load_ratio = max(1.0, len(batch) / max(1, max_ev))
    if should_shed(len(batch)):
        batch = batch[-max_ev:]
        logger.warning("Load shed: processing last %s audit lines", len(batch))

    opened = correlated = skipped = 0
    open_cap = limits()["max_open_ir_cases"]
    open_now = STORE.summary().get("open_total", 0)

    for line in batch:
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        sev = str(e.get("severity", "")).upper()
        if sev not in SEV_OK:
            continue
        action = str(e.get("action", ""))
        if not (
            action.startswith("detection:")
            or "detection" in action
            or action in ("block_ip", "isolate_endpoint", "terminate_session")
        ):
            continue
        indicator = str(e.get("indicator") or action.replace("detection:", "") or "unknown")
        target = str(e.get("target", "unknown"))
        source = str(e.get("source", "audit"))
        base_score, conf = score_event(indicator, sev, 0)
        intel = ENGINE.observe(
            indicator=indicator, target=target, severity=sev, source=source, score=base_score
        )
        score = int(intel["priority"])
        conf = intel["confidence"]
        if score < MIN_SCORE:
            skipped += 1
            continue
        related = {
            "timestamp": e.get("timestamp"),
            "action": action,
            "severity": sev,
            "indicator": indicator,
            "source": source,
            "intel": {
                k: intel[k]
                for k in ("priority", "burst", "multi_signal", "target_hits_in_window")
            },
        }
        match = STORE.find_open_match(indicator, target)
        if match:
            STORE.append_related(match, related)
            if score > match.score:
                match.score = score
                match.confidence = conf
                STORE.update(match)
            correlated += 1
            continue
        if open_now >= open_cap:
            skipped += 1
            continue
        tags = []
        if intel.get("burst"):
            tags.append("burst")
        if intel.get("multi_signal"):
            tags.append("multi_signal")
        if intel.get("recommend_escalate"):
            tags.append("escalate")
        if "brute" in indicator.lower():
            tags.append("auth")
        if sev == "CRITICAL":
            tags.append("critical")
        case = STORE.create(
            indicator=indicator,
            target=target,
            source=source,
            severity=sev,
            related=related,
            score=score,
            confidence=conf,
            tags=tags,
        )
        opened += 1
        open_now += 1
        logger.info(
            "Opened %s score=%s conf=%s burst=%s target=%s",
            case.case_id,
            score,
            conf,
            intel.get("burst"),
            target,
        )
    _set_offset(len(lines))
    return {
        "opened": opened,
        "correlated": correlated,
        "skipped_low_score": skipped,
        "audit_lines": len(lines),
        "load_ratio": load_ratio,
        **STORE.summary(),
        **ENGINE.summary(),
    }


def main():
    logger.info("IR Detect (intel window) interval=%ss min_score=%s", INTERVAL, MIN_SCORE)
    run_forever("ir_detect", _cycle, INTERVAL, error_sleep=15.0)


if __name__ == "__main__":
    main()
