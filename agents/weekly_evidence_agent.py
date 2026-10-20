#!/usr/bin/env python3
"""Weekly evidence pack job — pairs with daily WhatsApp summary."""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from core.watchdog import write_heartbeat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WEEKLY_EVIDENCE] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_weekly_evidence")

INTERVAL = int(os.getenv("CF_WEEKLY_EVIDENCE_SECONDS", str(7 * 24 * 3600)))
ON_START = os.getenv("CF_WEEKLY_EVIDENCE_ON_START", "false").lower() == "true"


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
    logger.info("Weekly evidence pack ready: %s", path)
    try:
        marker = Path(os.getenv("CF_EVIDENCE_DIR", "./evidence")) / "last_weekly_pack.txt"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(f"{out['generated_at']} {path}\n", encoding="utf-8")
    except Exception as e:
        logger.warning("Could not write marker: %s", e)
    return out


def main():
    logger.info(
        "Weekly evidence agent starting | interval=%ss on_start=%s",
        INTERVAL,
        ON_START,
    )
    if ON_START:
        try:
            write_heartbeat("weekly_evidence", {"phase": "start_pack"})
            generate_once()
            write_heartbeat("weekly_evidence", {"phase": "start_pack_done"})
        except Exception as e:
            logger.exception("Initial pack failed: %s", e)

    while True:
        try:
            time.sleep(INTERVAL)
            write_heartbeat("weekly_evidence", {"phase": "cycle"})
            generate_once()
            write_heartbeat("weekly_evidence", {"phase": "done"})
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.exception("Weekly pack error: %s", e)
            write_heartbeat("weekly_evidence", {"phase": "error", "error": str(e)[:200]})
            time.sleep(60)


if __name__ == "__main__":
    main()
