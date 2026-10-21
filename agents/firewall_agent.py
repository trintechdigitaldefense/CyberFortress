#!/usr/bin/env python3
"""CyberFortress Firewall Agent — CF_BLOCK chain + continuous status heartbeats."""

from __future__ import annotations

import logging
import os

from core.agent_runtime import run_forever
from core.containment.firewall import ensure_chain, firewall_status, load_allowlist

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [FIREWALL] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_firewall_agent")

INTERVAL = int(os.getenv("CF_FIREWALL_INTERVAL", "20"))


def bootstrap() -> dict:
    logger.info(
        "Firewall agent starting (auto_start=%s live=%s allowlist=%s)",
        os.getenv("CF_FIREWALL_AUTO_START", "true"),
        os.getenv("CF_CONTAINMENT_LIVE", "false"),
        len(load_allowlist()),
    )
    result = ensure_chain(dry_run=False, force_infra=True)
    if result.get("ok"):
        logger.info("%s", result.get("message") or "chain ready")
    else:
        logger.warning("ensure_chain: %s", result.get("error") or result)
    return result


def _cycle():
    ensure_chain(dry_run=False, force_infra=True)
    st = firewall_status()
    if st.get("mode_label") == "UNAVAILABLE":
        logger.warning("Firewall UNAVAILABLE: %s", st.get("message"))
    elif st.get("rule_count", 0) >= st.get("max_rules", 200):
        logger.warning("Firewall at max rules: %s", st.get("rule_count"))
    return {
        "chain": st.get("chain"),
        "chain_exists": st.get("chain_exists"),
        "rule_count": st.get("rule_count"),
        "max_rules": st.get("max_rules"),
        "live_mode": st.get("live_mode"),
        "mode_label": st.get("mode_label"),
        "allowlist_count": st.get("allowlist_count"),
        "message": (st.get("message") or "")[:160],
    }


def main() -> None:
    bootstrap()
    run_forever("firewall", _cycle, INTERVAL, error_sleep=15.0)


if __name__ == "__main__":
    main()
