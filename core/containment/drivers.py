#!/usr/bin/env python3
"""CyberFortress containment drivers — iptables, session, decoy."""
from __future__ import annotations

import logging
import os
import re
import signal
import subprocess
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict

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
        if action in ("block_ip", "isolate_endpoint"):
            return fw.block_ip(target, dry_run=dry, roe_action=action)
        if action in ("unblock_ip", "restore_endpoint"):
            return fw.unblock_ip(target, dry_run=dry, roe_action=action, comment=kwargs.get("comment", "CyberFortress"))
        return {"success": False, "dry_run": dry, "details": f"unsupported firewall action: {action}"}


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
            if self.dry_run:
                result["details"] = f"[DRY-RUN] Would terminate session/process {target}"
                result["success"] = True
                return result
            if target.isdigit():
                pid = int(target)
                if pid <= 1 or pid == os.getpid():
                    result["details"] = "Refusing to terminate PID 0, PID 1, or the CyberFortress process"
                    return result
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    result["verification"] = {"verified": True, "method": "pid_absent"}
                    result["success"] = True
                    result["details"] = f"Process {pid} was already absent"
                else:
                    try:
                        os.kill(pid, 0)
                    except ProcessLookupError:
                        result["verification"] = {"verified": True, "method": "pid_absent"}
                        result["success"] = True
                        result["details"] = f"Process {pid} is no longer present"
                    except PermissionError as exc:
                        result["details"] = f"Cannot verify process termination: {exc}"
                    else:
                        result["verification"] = {"verified": False, "method": "pid_still_present"}
                        result["details"] = f"Process {pid} remains present after termination request"
            else:
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]{0,31}", target):
                    result["details"] = "Invalid session username"
                    return result
                completed = self._run(["loginctl", "terminate-user", target])
                if completed.returncode != 0:
                    detail = (completed.stderr or b"").decode(errors="replace")[:200]
                    raise RuntimeError(detail or f"loginctl exited {completed.returncode}")
                listing = self._run(["loginctl", "list-sessions", "--no-legend"])
                if listing.returncode != 0:
                    raise RuntimeError("unable to verify remaining login sessions")
                rows = (listing.stdout or b"").decode(errors="replace").splitlines()
                remains = any(len(row.split()) >= 3 and row.split()[2] == target for row in rows)
                result["verification"] = {"verified": not remains, "method": "loginctl_list_sessions"}
                result["success"] = not remains
                result["details"] = (
                    f"No login sessions remain for {target}"
                    if not remains else f"Login sessions remain for {target}"
                )
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
            if not self.dry_run:
                result["details"] = "No decoy deployment backend is configured; refusing to claim deployment success"
                return result
            result["details"] = f"[DRY-RUN] Would deploy decoy for {target}"
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
    ):
        return IPTablesDriver(dry_run=dry_run)
    if action in ("terminate_session",):
        return SessionKiller(dry_run=dry_run)
    if action in ("deploy_decoy",):
        return DecoyDeployer(dry_run=dry_run)
    raise ValueError(f"unsupported containment action: {action}")
