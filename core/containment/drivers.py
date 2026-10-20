#!/usr/bin/env python3
"""Containment drivers — iptables, session, etc."""

from __future__ import annotations

import logging
import os
import subprocess
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("cf_drivers")


class ContainmentDriver(ABC):
    name = "base"

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def _run(self, cmd, check: bool = False):
        cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
        if self.dry_run:
            logger.info("[DRY-RUN] Would execute: %s", cmd_str)
            return subprocess.CompletedProcess(cmd if isinstance(cmd, list) else [cmd], 0, stdout=b"dry-run", stderr=b"")
        logger.info("Executing: %s", cmd_str)
        return subprocess.run(cmd, capture_output=True, check=check)

    @abstractmethod
    def execute(self, target: str, action: str = "", **kwargs) -> Dict[str, Any]:
        pass


class IPTablesDriver(ContainmentDriver):
    name = "iptables"

    def execute(self, target: str, action: str = "block_ip", **kwargs) -> Dict[str, Any]:
        from core.containment.firewall import block_ip, unblock_ip, ensure_chain

        result = {
            "driver": self.name,
            "action": action,
            "target": target,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dry_run": self.dry_run,
            "success": False,
            "details": "",
        }

        try:
            ensure_chain(dry_run=self.dry_run)
            if action in ("block_ip", "isolate_endpoint", "subnet_isolation"):
                fw = block_ip(target, dry_run=self.dry_run, comment=f"CF:{action}")
                result["success"] = fw.get("success", False)
                result["details"] = fw.get("details", "")
                result["firewall"] = fw
                if result["success"] and not self.dry_run and not fw.get("dry_run"):
                    try:
                        from core.containment.verify import verify_block
                        from core.containment.firewall import list_cf_rules, CHAIN

                        v = fw.get("verify") or verify_block(target, CHAIN, list_cf_rules)
                        result["verify"] = v
                        if v.get("verified") is False:
                            result["success"] = False
                            result["details"] += " | VERIFY_FAIL"
                    except Exception as ve:
                        result["verify"] = {"verified": False, "error": str(ve)}
                elif fw.get("verify"):
                    result["verify"] = fw["verify"]
            elif action in ("unblock_ip", "restore_endpoint", "restore_subnet"):
                fw = unblock_ip(target, dry_run=self.dry_run)
                result["success"] = fw.get("success", False)
                result["details"] = fw.get("details", "")
                result["firewall"] = fw
            else:
                result["details"] = f"Unsupported action for IPTablesDriver: {action}"
        except Exception as e:
            result["details"] = str(e)
            logger.exception("IPTablesDriver error")

        return result


class SessionKiller(ContainmentDriver):
    name = "session_killer"

    def execute(self, target: str, action: str = "terminate_session", **kwargs) -> Dict[str, Any]:
        result = {
            "driver": self.name,
            "action": action,
            "target": target,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dry_run": self.dry_run,
            "success": False,
            "details": "",
        }
        try:
            if target.isdigit():
                cmd = ["kill", "-9", target]
            else:
                cmd = ["loginctl", "terminate-user", target]
            self._run(cmd)
            result["details"] = f"Session/process termination requested for {target}"
            result["success"] = True
        except Exception as e:
            result["details"] = str(e)
        return result


def get_driver(action: str, dry_run: bool = True) -> ContainmentDriver:
    action = (action or "").lower()
    if action in (
        "block_ip",
        "unblock_ip",
        "isolate_endpoint",
        "restore_endpoint",
        "subnet_isolation",
        "restore_subnet",
    ):
        return IPTablesDriver(dry_run=dry_run)
    if action in ("terminate_session",):
        return SessionKiller(dry_run=dry_run)
    return IPTablesDriver(dry_run=dry_run)
