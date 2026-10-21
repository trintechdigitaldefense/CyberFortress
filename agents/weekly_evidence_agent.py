#!/usr/bin/env python3
"""Weekly evidence pack job — pairs with daily WhatsApp summary."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from core.agent_runtime import run_forever

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WEEKLY_EVIDENCE] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_weekly_evidence")

INTERVAL = int(os.getenv("CF_WEEKLY_EVIDENCE_SECONDS", str(7 * 24 * 3600)))
ON_START = os.getenv("CF_WEEKLY_EVIDENCE_ON_START", "false").lower() == "true"
_first = True


def generate_once() -> dict:
    from core.evidence.pack import generate_evidence_pack
    from core.tenant import apply_tenant_env, load_tenant_settings

    apply_tenant_env()
    settings = load_tenant_settings()
    client = settings.get("client_name") or os.getenv("CF_CLIENT_NAME", "Client")
    eng = settings.get("engagement_id") or os.getenv("CF_ENGAGEMENT_ID")
    path = generate_evidence_pack(client_name=str(client), engagement_id=eng, create_zip=True)
    out = {
        "ok": True,
        "path": str(path),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "client": client,
        "engagement_id": eng,
    }
    stamp = Path(os.getenv("CF_LOG_DIR", "./logs")) / "last_weekly_evidence.json"
    try:
        stamp.parent.mkdir(parents=True, exist_ok=True)
        stamp.write_text(json.dumps(out, indent=2), encoding="utf-8")
    except Exception:
        pass
    logger.info("Evidence pack generated: %s", path)
    return out


def _cycle():
    global _first
    if _first and not ON_START:
        _first = False
        logger.info("Skipping pack on start (CF_WEEKLY_EVIDENCE_ON_START=false)")
        return {"phase": "skipped_start"}
    _first = False
    try:
        return generate_once()
    except Exception as e:
        logger.exception("Weekly evidence failed: %s", e)
        return {"ok": False, "error": str(e)[:200]}


def main():
    logger.info("Weekly evidence agent interval=%ss on_start=%s", INTERVAL, ON_START)
    run_forever("weekly_evidence", _cycle, INTERVAL, error_sleep=60.0, max_error_sleep=600.0)


if __name__ == "__main__":
    main()
