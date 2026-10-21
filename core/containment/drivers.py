#!/usr/bin/env python3
"""CyberFortress containment drivers — iptables, session, decoy."""
from __future__ import annotations

import logging
import os
import subprocess
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger("cf_containment")


class ContainmentDriver(ABC):
    name = "base"

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def _run(self, cmd, check: bool = False):
        if self.dry_run:
            logger.info("[DRY-RUN] would run: %s", " ".join(cmd))
            return subprocess.CompletedProcess(cmd, 0, b"", b"")
        return subprocess.run(cmd, capture_output=True, check=check)

    @abstractmethod
    def execute(self, target: str, action: str = "", **kwargs) -> Dict[str, Any]:
        raise NotImplementedError


class IPTablesDriver(ContainmentDriver):
    name = "iptables"

    def execute(self, target: str, action: str = "block_ip", **kwargs) -> Dict[str, Any]:
        from core.containment import firewall as fw

        dry = self.dry_run
        action = (action or "block_ip").lower()
        if action in ("block_ip", "isolate_endpoint", "subnet_isolation"):
            return fw.block_ip(target, dry_run=dry)
        if action in ("unblock_ip", "restore_endpoint", "restore_subnet"):
            return fw.unblock_ip(target, dry_run=dry)
        return fw.block_ip(target, dry_run=dry)


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


class DecoyDeployer(ContainmentDriver):
    name = "decoy_deployer"

    def execute(self, target: str, action: str = "deploy_decoy", **kwargs) -> Dict[str, Any]:
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
            msg = f"Decoy deploy requested for {target}"
            if self.dry_run:
                msg = f"[DRY-RUN] {msg}"
            result["details"] = msg
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
    if action in ("deploy_decoy",):
        return DecoyDeployer(dry_run=dry_run)
    return IPTablesDriver(dry_run=dry_run)
