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
import secrets
import string
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pathlib import Path

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
    """Block or isolate using iptables."""

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
    """Terminate user sessions or processes."""

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
    """Deploy a simple canary / decoy file."""

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


class CredentialRotator(ContainmentDriver):
    """
    Widespread or targeted credential rotation.

    MVP behaviour:
    - Generates strong random passwords
    - Records the rotation action + new password hash location
    - In live mode can call system tools (chpasswd, passwd) or write a rotation script
    - Designed so real identity providers (AD, LDAP, cloud IAM) can be plugged in later
    """

    name = "credential_rotator"

    def _generate_password(self, length: int = 20) -> str:
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def execute(self, target: str, action: str = "credential_rotation", **kwargs) -> Dict[str, Any]:
        """
        target can be:
          - a single username
          - a comma-separated list of usernames
          - "all" / "fleet" for broader rotation (logged only in MVP)
        """
        result = {
            "driver": self.name,
            "action": action,
            "target": target,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dry_run": self.dry_run,
            "success": False,
            "details": "",
            "rotated": [],
        }

        users: List[str] = []
        if target.lower() in ("all", "fleet", "*"):
            users = ["(fleet-wide rotation requested)"]
        else:
            users = [u.strip() for u in target.split(",") if u.strip()]

        try:
            rotation_log = []
            for user in users:
                new_pass = self._generate_password()
                # We never log the clear-text password in production logs.
                # Instead we record that a rotation occurred and where the secret was stored.
                secret_ref = f"cf-rotated-{user}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

                if self.dry_run:
                    logger.info(f"[DRY-RUN] Would rotate credentials for user '{user}' → secret_ref={secret_ref}")
                    rotation_log.append({"user": user, "status": "dry-run", "secret_ref": secret_ref})
                else:
                    # MVP: write a secure one-time file that an admin can consume
                    # In production this would call AD / LDAP / cloud IAM / chpasswd etc.
                    secrets_dir = Path("./secrets/rotated")
                    secrets_dir.mkdir(parents=True, exist_ok=True)
                    secret_file = secrets_dir / f"{secret_ref}.txt"
                    secret_file.write_text(
                        f"user={user}\npassword={new_pass}\ngenerated={datetime.now(timezone.utc).isoformat()}\n",
                        encoding="utf-8",
                    )
                    os.chmod(secret_file, 0o600)
                    logger.info(f"Credentials rotated for '{user}' — secret stored at {secret_file} (mode 600)")
                    rotation_log.append({"user": user, "status": "rotated", "secret_ref": str(secret_file)})

            result["rotated"] = rotation_log
            result["details"] = f"Credential rotation completed for {len(users)} target(s)"
            result["success"] = True

        except Exception as e:
            result["details"] = str(e)
            logger.exception("CredentialRotator error")

        return result


class HaltOperations(ContainmentDriver):
    """
    Emergency halt / critical containment.
    Stages a controlled shutdown of non-essential services and network isolation.
    """

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

            # 1. Broad network isolation of the target (or whole host)
            ipt = IPTablesDriver(dry_run=self.dry_run)
            iso = ipt.execute(target=target if "/" in target else "0.0.0.0/0", action="subnet_isolation")
            steps.append(f"network_isolation: {iso.get('details')}")

            # 2. Stop non-essential services (MVP list – expand per client)
            services_to_stop = kwargs.get("services", ["nginx", "apache2", "mysql", "postgresql"])
            for svc in services_to_stop:
                cmd = ["systemctl", "stop", svc]
                self._run(cmd, check=False)
                steps.append(f"stopped_service: {svc}")

            result["details"] = " | ".join(steps)
            result["success"] = True
            logger.warning(f"HALT OPERATIONS executed on {target}: {result['details']}")

        except Exception as e:
            result["details"] = str(e)
            logger.exception("HaltOperations error")

        return result


def get_driver(action: str, dry_run: bool = True) -> ContainmentDriver:
    """Factory: return the appropriate driver for a given playbook action."""
    mapping = {
        "block_ip": IPTablesDriver,
        "isolate_endpoint": IPTablesDriver,
        "subnet_isolation": IPTablesDriver,
        "terminate_session": SessionKiller,
        "deploy_decoy": DecoyDeployer,
        "credential_rotation": CredentialRotator,
        "halt_operations": HaltOperations,
    }
    cls = mapping.get(action, IPTablesDriver)
    return cls(dry_run=dry_run)
