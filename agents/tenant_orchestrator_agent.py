#!/usr/bin/env python3
"""Tenant orchestrator — multi-site scan on one host (lightweight)."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from core.agent_runtime import run_forever
from core.capacity import limits
from core.tenant import list_tenants, load_tenant_settings

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
        logger.error("Tenant count %s exceeds isolated-runtime cap %s — refusing shared processing", len(tenants), max_t)
        return {"tenants": len(tenants), "detail": [], "cap": max_t, "blocked": True}
    report = []
    for tid in tenants:
        settings = load_tenant_settings(tid)
        audit = Path("logs") / "tenants" / tid / "cma_audit.jsonl"
        report.append(
            {
                "tenant_id": tid,
                "client": settings.get("client_name", tid),
                "audit_exists": audit.exists(),
                "audit_bytes": audit.stat().st_size if audit.exists() else 0,
                "rule_pack": settings.get("rule_pack") or "",
            }
        )
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
