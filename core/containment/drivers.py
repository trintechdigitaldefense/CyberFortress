#!/usr/bin/env python3
"""
CyberFortress Real Containment Drivers
Containment + rollback. All support dry_run.
"""

import os
import subprocess
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime, timezone
from pathlib import Path

from core.identity.providers import get_identity_provider

logger = logging.getLogger("cf_containment")

LIVE_MODE = os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "true"


class ContainmentDriver(ABC):
    name: str = "base"

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run or (not LIVE_MODE)

    @abstractmethod
    def execute(self, target: str, **kwargs) -> Dict[str, Any]:
        pass

    def _run(self, cmd: list, check: bool = True) -> subprocess.CompletedProcess:
        cmd_str = " ".join(cmd)
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would execute: {cmd_str}")
            return subprocess.CompletedProcess(cmd, 0, stdout=b"dry-run", stderr=b"")
        logger.info(f"Executing: {cmd_str}")
        return subprocess.run(cmd, capture_output=True, check=check)


class IPTablesDriver(ContainmentDriver):
    name = "iptables"

    def execute(self, target: str, action: str = "block_ip", **kwargs) -> Dict[str, Any]:
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
            if action in ("block_ip", "isolate_endpoint"):
                for direction, chain in [("INPUT", "src"), ("OUTPUT", "dst")]:
                    cmd = ["iptables", "-I", direction, "1", "-s" if chain == "src" else "-d", target, "-j", "DROP"]
                    self._run(cmd)
                result["details"] = f"iptables DROP rules inserted for {target}"
                result["success"] = True

            elif action == "subnet_isolation":
                for direction, flag in [("INPUT", "-s"), ("OUTPUT", "-d"), ("FORWARD", "-s")]:
                    cmd = ["iptables", "-I", direction, "1", flag, target, "-j", "DROP"]
                    self._run(cmd)
                result["details"] = f"Subnet isolation rules applied for {target}"
                result["success"] = True

            elif action in ("unblock_ip", "restore_endpoint"):
                # Best-effort delete matching DROP rules (may need multiple passes in production)
                for direction, flag in [("INPUT", "-s"), ("OUTPUT", "-d")]:
                    cmd = ["iptables", "-D", direction, flag, target, "-j", "DROP"]
                    self._run(cmd, check=False)
                result["details"] = f"iptables DROP rules removed (best-effort) for {target}"
                result["success"] = True

            elif action == "restore_subnet":
                for direction, flag in [("INPUT", "-s"), ("OUTPUT", "-d"), ("FORWARD", "-s")]:
                    cmd = ["iptables", "-D", direction, flag, target, "-j", "DROP"]
                    self._run(cmd, check=False)
                result["details"] = f"Subnet isolation rules removed (best-effort) for {target}"
                result["success"] = True

            else:
                result["details"] = f"Unsupported action for IPTablesDriver: {action}"

        except subprocess.CalledProcessError as e:
            result["details"] = f"iptables failed: {e.stderr.decode() if e.stderr else str(e)}"
            logger.error(result["details"])
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
            logger.exception("SessionKiller error")
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
        decoy_content = kwargs.get(
            "content",
            "# CANARY TOKEN - DO NOT USE\n"
            "DB_PASSWORD=SuperSecretCanary123!\n"
            "API_KEY=cf-canary-" + datetime.now().strftime("%Y%m%d%H%M%S") + "\n",
        )
        decoy_path = kwargs.get("path", f"/tmp/.cf_decoy_{target.replace('.', '_')}.env")
        try:
            if self.dry_run:
                logger.info(f"[DRY-RUN] Would write decoy to {decoy_path}")
                result["details"] = f"Dry-run: decoy would be placed at {decoy_path}"
                result["success"] = True
            else:
                with open(decoy_path, "w", encoding="utf-8") as f:
                    f.write(decoy_content)
                os.chmod(decoy_path, 0o644)
                result["details"] = f"Decoy deployed at {decoy_path}"
                result["success"] = True
        except Exception as e:
            result["details"] = str(e)
            logger.exception("DecoyDeployer error")
        return result


class CredentialRotator(ContainmentDriver):
    name = "credential_rotator"

    def execute(self, target: str, action: str = "credential_rotation", **kwargs) -> Dict[str, Any]:
        provider_name = kwargs.get("provider") or os.getenv("CF_IDENTITY_PROVIDER", "local_linux")
        idp = get_identity_provider(provider_name)
        result = {
            "driver": self.name,
            "action": action,
            "target": target,
            "provider": idp.name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dry_run": self.dry_run,
            "success": False,
            "details": "",
            "rotated": [],
        }
        if target.lower() in ("all", "fleet", "*"):
            users = idp.list_users() or ["(fleet-wide — no users returned by provider)"]
        else:
            users = [u.strip() for u in target.split(",") if u.strip()]
        try:
            rotation_log = []
            all_ok = True
            for user in users:
                rot = idp.rotate_password(user, dry_run=self.dry_run)
                rotation_log.append(rot)
                if not rot.get("success"):
                    all_ok = False
            result["rotated"] = rotation_log
            result["success"] = all_ok
            result["details"] = f"Credential rotation via {idp.name} for {len(users)} target(s)"
        except Exception as e:
            result["details"] = str(e)
            logger.exception("CredentialRotator error")
        return result


class HaltOperations(ContainmentDriver):
    name = "halt_operations"

    def execute(self, target: str, action: str = "halt_operations", **kwargs) -> Dict[str, Any]:
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
            steps = []
            ipt = IPTablesDriver(dry_run=self.dry_run)
            iso = ipt.execute(target=target if "/" in target else "0.0.0.0/0", action="subnet_isolation")
            steps.append(f"network_isolation: {iso.get('details')}")
            for svc in kwargs.get("services", ["nginx", "apache2", "mysql", "postgresql"]):
                self._run(["systemctl", "stop", svc], check=False)
                steps.append(f"stopped_service: {svc}")
            result["details"] = " | ".join(steps)
            result["success"] = True
        except Exception as e:
            result["details"] = str(e)
            logger.exception("HaltOperations error")
        return result


def get_driver(action: str, dry_run: bool = True) -> ContainmentDriver:
    mapping = {
        "block_ip": IPTablesDriver,
        "isolate_endpoint": IPTablesDriver,
        "subnet_isolation": IPTablesDriver,
        "unblock_ip": IPTablesDriver,
        "restore_endpoint": IPTablesDriver,
        "restore_subnet": IPTablesDriver,
        "terminate_session": SessionKiller,
        "deploy_decoy": DecoyDeployer,
        "credential_rotation": CredentialRotator,
        "halt_operations": HaltOperations,
    }
    cls = mapping.get(action, IPTablesDriver)
    return cls(dry_run=dry_run)
