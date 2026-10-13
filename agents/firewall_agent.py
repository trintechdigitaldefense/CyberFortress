#!/usr/bin/env python3
"""
CyberFortress Firewall Agent

Starts with the platform (start.sh). Ensures CF_BLOCK chain exists and
heartbeats so the dashboard shows the firewall as a live service.

Empty chain does not block traffic. DROP rules are only added when
containment is armed (CF_CONTAINMENT_LIVE=true) via autonomy/playbooks.
"""

from __future__ import annotations

import logging
import os
import time

from core.containment.firewall import ensure_chain, firewall_status
from core.watchdog import write_heartbeat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [FIREWALL] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_firewall_agent")

INTERVAL = int(os.getenv("CF_FIREWALL_INTERVAL", "30"))


def bootstrap() -> None:
    logger.info(
        "Firewall agent starting (auto_start=%s live=%s)",
        os.getenv("CF_FIREWALL_AUTO_START", "true"),
        os.getenv("CF_CONTAINMENT_LIVE", "false"),
    )
    result = ensure_chain(dry_run=False)
    if result.get("ok"):
        logger.info("%s", result.get("message") or "chain ready")
        for step in result.get("steps") or []:
            logger.debug("step: %s", step)
    else:
        logger.warning("ensure_chain: %s", result.get("error") or result)

    st = firewall_status()
    write_heartbeat(
        "firewall",
        {
            "phase": "started",
            "chain": st.get("chain"),
            "chain_exists": st.get("chain_exists"),
            "rule_count": st.get("rule_count"),
            "live_mode": st.get("live_mode"),
            "mode_label": st.get("mode_label"),
            "message": st.get("message"),
        },
    )


def main() -> None:
    bootstrap()
    while True:
        st = firewall_status()
        write_heartbeat(
            "firewall",
            {
                "phase": "alive",
                "chain": st.get("chain"),
                "chain_exists": st.get("chain_exists"),
                "rule_count": st.get("rule_count"),
                "live_mode": st.get("live_mode"),
                "mode_label": st.get("mode_label"),
                "message": st.get("message"),
            },
        )
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
