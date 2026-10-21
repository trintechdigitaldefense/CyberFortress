#!/usr/bin/env python3
"""Tenant orchestrator — multi-site scan on one host (lightweight)."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from core.agent_runtime import run_forever
from core.capacity import limits
from core.tenant import apply_tenant_env, list_tenants, load_tenant_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [TENANT-ORCH] %(levelname)s %(message)s",
    force=True,
)
logger = logging.getLogger("cf_tenant_orch")

INTERVAL = int(os.getenv("CF_TENANT_ORCH_INTERVAL", "60"))


def _cycle():
    tenants = list_tenants()
    max_t = limits()["max_tenants_per_host"]
    if len(tenants) > max_t:
        logger.warning("Tenant count %s exceeds host cap %s — truncating", len(tenants), max_t)
        tenants = tenants[:max_t]
    report = []
    for tid in tenants:
        settings = load_tenant_settings(tid)
        prev = os.environ.get("CF_TENANT_ID")
        try:
            apply_tenant_env(tid)
            audit = Path(os.environ.get("CF_AUDIT_PATH", ""))
            report.append(
                {
                    "tenant_id": tid,
                    "client": settings.get("client_name", tid),
                    "audit_exists": audit.exists(),
                    "audit_bytes": audit.stat().st_size if audit.exists() else 0,
                    "rule_pack": settings.get("rule_pack") or os.getenv("CF_RULE_PACK_NAME", ""),
                }
            )
        finally:
            if prev is not None:
                os.environ["CF_TENANT_ID"] = prev
    logger.info("Tenants scanned: %s", len(report))
    return {"tenants": len(report), "detail": report[:25], "cap": max_t}


def main():
    if os.getenv("CF_TENANT_ORCH", "true").lower() not in ("1", "true", "yes"):
        logger.info("Tenant orchestrator disabled (CF_TENANT_ORCH=false)")
        return
    logger.info("Tenant orchestrator interval=%ss", INTERVAL)
    run_forever("tenant_orch", _cycle, INTERVAL, error_sleep=20.0)


if __name__ == "__main__":
    main()
