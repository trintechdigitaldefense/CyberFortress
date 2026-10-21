#!/usr/bin/env python3
"""Refresh local/URL threat intel indicators."""

from __future__ import annotations

import logging
import os

from core.agent_runtime import run_forever
from core.soc.threat_intel import load_local, refresh_url, status

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [TI] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_ti_agent")
INTERVAL = int(os.getenv("CF_TI_INTERVAL", "3600"))


def _cycle():
    n = load_local()
    url_n = refresh_url()
    st = status()
    logger.info("TI indicators=%s url_refresh=%s", len(n), url_n)
    return {"indicators": len(n), "url_count": url_n, **st}


def main():
    logger.info("Threat intel agent interval=%ss", INTERVAL)
    run_forever("threat_intel", _cycle, INTERVAL, error_sleep=60.0)


if __name__ == "__main__":
    main()
