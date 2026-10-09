#!/usr/bin/env python3
"""
CyberFortress Real Containment Drivers
Actual enforcement actions for approved playbooks.

Designed for Linux hosts (Ubuntu / Debian) commonly used in Caribbean SMB environments.
All drivers support a dry_run mode for safe testing.
"""

import os
import subprocess
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger("cf_containment")

# Safety: require explicit enablement for live actions
LIVE_MODE = os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "true"


class ContainmentDriver(ABC):
    """Base class for all containment drivers."""

    name: str = "base"

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run or (not LIVE_MODE)

    @abstractmethod
    def execute(self, target: str, **kwargs) -> Dict[str, Any]:
        """Perform the containment action. Returns result dict."""
        pass

    def _run(self, cmd: list, check: bool = True) -> subprocess.CompletedProcess:
        """Helper to run shell commands with logging."""
        cmd_str = " ".join(cmd)
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would execute: {cmd_str}")
            return subprocess.CompletedProcess(cmd, 0, stdout=b"dry-run", stderr=b"")
        logger.info(f"Executing: {cmd_str}")
        return subprocess.run(cmd, capture_output=True, check=check)


class IPTablesDriver(ContainmentDriver):
    """
    Block or isolate using iptables / ip6tables.
    Supports:
      - block_ip
      - isolate_endpoint (drop all traffic to/from host)
      - subnet_isolation (broader drop)
    """

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
                # Drop inbound + outbound for the target IP
                for direction, chain in [("INPUT", "src"), ("OUTPUT", "dst")]:
                    cmd = ["iptables", "-I", direction, "1", "-s" if chain == "src" else "-d", target, "-j", "DROP"]
                    self._run(cmd)
                result["details"] = f"iptables DROP rules inserted for {target}"
                result["success"] = True

            elif action == "subnet_isolation":
                # Broader isolation – treat target as CIDR
                for direction, flag in [("INPUT", "-s"), ("OUTPUT", "-d"), ("FORWARD", "-s")]:
                    cmd = ["iptables", "-I", direction, "1", flag, target, "-j", "DROP"]
                    self._run(cmd)
                result["details"] = f"Subnet isolation rules applied for {target}"
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
    """
    Terminate user sessions or processes.
    Uses loginctl / pkill / kill where appropriate.
    """

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
            # target can be a username, PID, or session ID
            if target.isdigit():
                cmd = ["kill", "-9", target]
            else:
                # Try loginctl first (systemd), fall back to pkill
                cmd = ["loginctl", "terminate-user", target]

            self._run(cmd)
            result["details"] = f"Session/process termination requested for {target}"
            result["success"] = True

        except Exception as e:
            result["details"] = str(e)
            logger.exception("SessionKiller error")

        return result


class DecoyDeployer(ContainmentDriver):
    """
    Deploy a simple canary / decoy file.
    Integrates conceptually with Mirage-style deception.
    """

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
                logger.info(result["details"])

        except Exception as e:
            result["details"] = str(e)
            logger.exception("DecoyDeployer error")

        return result


def get_driver(action: str, dry_run: bool = True) -> ContainmentDriver:
    """
    Factory: return the appropriate driver for a given playbook action.
    """
    mapping = {
        "block_ip": IPTablesDriver,
        "isolate_endpoint": IPTablesDriver,
        "subnet_isolation": IPTablesDriver,
        "terminate_session": SessionKiller,
        "deploy_decoy": DecoyDeployer,
        # credential_rotation and halt_operations need higher-level orchestration
        # and are left as stubs for now
    }
    cls = mapping.get(action, IPTablesDriver)
    return cls(dry_run=dry_run)
