#!/usr/bin/env python3
"""
CyberFortress Identity Provider Hooks

Pluggable backends for credential rotation and account management.
Designed so Caribbean SMB environments can start with local Linux
and later connect to Active Directory, LDAP, or Azure AD without
changing the playbook layer.
"""

import os
import logging
import subprocess
import secrets
import string
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("cf_identity")


def _generate_password(length: int = 20) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    return "".join(secrets.choice(alphabet) for _ in range(length))


class IdentityProvider(ABC):
    """Base interface every identity backend must implement."""

    name: str = "base"

    @abstractmethod
    def rotate_password(self, username: str, dry_run: bool = True) -> Dict[str, Any]:
        """Rotate the password for a single user. Return result dict."""
        pass

    @abstractmethod
    def disable_account(self, username: str, dry_run: bool = True) -> Dict[str, Any]:
        """Disable / lock an account."""
        pass

    @abstractmethod
    def list_users(self) -> List[str]:
        """Return a list of manageable usernames (best-effort)."""
        pass


class LocalLinuxProvider(IdentityProvider):
    """
    Local Linux accounts via chpasswd / usermod / passwd.
    Suitable for single-host or small Ubuntu/Debian deployments.
    """

    name = "local_linux"

    def rotate_password(self, username: str, dry_run: bool = True) -> Dict[str, Any]:
        new_pass = _generate_password()
        result = {
            "provider": self.name,
            "username": username,
            "action": "rotate_password",
            "dry_run": dry_run,
            "success": False,
            "details": "",
            "secret_ref": None,
        }

        if dry_run:
            result["details"] = f"[DRY-RUN] Would rotate local password for {username}"
            result["success"] = True
            logger.info(result["details"])
            return result

        try:
            # Use chpasswd for non-interactive password change
            proc = subprocess.run(
                ["chpasswd"],
                input=f"{username}:{new_pass}".encode(),
                capture_output=True,
                check=True,
            )
            # Store the secret securely for the operator
            secrets_dir = Path("./secrets/rotated")
            secrets_dir.mkdir(parents=True, exist_ok=True)
            secret_file = secrets_dir / f"local_{username}_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
            secret_file.write_text(
                f"provider=local_linux\nuser={username}\npassword={new_pass}\n"
                f"generated={datetime.now(timezone.utc).isoformat()}\n",
                encoding="utf-8",
            )
            os.chmod(secret_file, 0o600)

            result["success"] = True
            result["secret_ref"] = str(secret_file)
            result["details"] = f"Local password rotated for {username}; secret at {secret_file}"
            logger.info(result["details"])

        except subprocess.CalledProcessError as e:
            result["details"] = f"chpasswd failed: {e.stderr.decode() if e.stderr else str(e)}"
            logger.error(result["details"])
        except Exception as e:
            result["details"] = str(e)
            logger.exception("LocalLinuxProvider.rotate_password error")

        return result

    def disable_account(self, username: str, dry_run: bool = True) -> Dict[str, Any]:
        result = {
            "provider": self.name,
            "username": username,
            "action": "disable_account",
            "dry_run": dry_run,
            "success": False,
            "details": "",
        }
        if dry_run:
            result["details"] = f"[DRY-RUN] Would lock account {username}"
            result["success"] = True
            return result

        try:
            subprocess.run(["usermod", "-L", username], check=True, capture_output=True)
            result["success"] = True
            result["details"] = f"Account {username} locked (usermod -L)"
            logger.info(result["details"])
        except Exception as e:
            result["details"] = str(e)
            logger.exception("LocalLinuxProvider.disable_account error")
        return result

    def list_users(self) -> List[str]:
        try:
            # Simple approach: users with UID >= 1000
            out = subprocess.check_output(["getent", "passwd"], text=True)
            users = []
            for line in out.splitlines():
                parts = line.split(":")
                if len(parts) >= 3 and parts[2].isdigit() and int(parts[2]) >= 1000:
                    users.append(parts[0])
            return users
        except Exception:
            return []


class LDAPProvider(IdentityProvider):
    """
    LDAP / Active Directory style backend.
    Requires python-ldap or ldap3 in production.
    This is a safe stub that logs intent and can be completed later.
    """

    name = "ldap"

    def __init__(self):
        self.server = os.getenv("CF_LDAP_SERVER", "")
        self.bind_dn = os.getenv("CF_LDAP_BIND_DN", "")
        self.bind_password = os.getenv("CF_LDAP_BIND_PASSWORD", "")
        self.user_base = os.getenv("CF_LDAP_USER_BASE", "")

    def rotate_password(self, username: str, dry_run: bool = True) -> Dict[str, Any]:
        result = {
            "provider": self.name,
            "username": username,
            "action": "rotate_password",
            "dry_run": dry_run,
            "success": False,
            "details": "",
            "secret_ref": None,
        }

        if not self.server:
            result["details"] = "LDAP provider not configured (set CF_LDAP_SERVER etc.)"
            logger.warning(result["details"])
            return result

        new_pass = _generate_password()
        if dry_run:
            result["details"] = f"[DRY-RUN] Would rotate LDAP password for {username} on {self.server}"
            result["success"] = True
            return result

        # TODO: implement real ldap3 / python-ldap password modify extended operation
        result["details"] = (
            f"LDAP password rotation for {username} is stubbed. "
            f"Configure CF_LDAP_* variables and install ldap3 to enable."
        )
        logger.warning(result["details"])
        return result

    def disable_account(self, username: str, dry_run: bool = True) -> Dict[str, Any]:
        result = {
            "provider": self.name,
            "username": username,
            "action": "disable_account",
            "dry_run": dry_run,
            "success": False,
            "details": "LDAP disable is stubbed — configure CF_LDAP_* to enable",
        }
        return result

    def list_users(self) -> List[str]:
        return []


class AzureADProvider(IdentityProvider):
    """
    Microsoft Entra ID (Azure AD) backend via Microsoft Graph.
    Requires MSAL + Graph permissions in production.
    Currently a safe configuration-aware stub.
    """

    name = "azure_ad"

    def __init__(self):
        self.tenant_id = os.getenv("CF_AZURE_TENANT_ID", "")
        self.client_id = os.getenv("CF_AZURE_CLIENT_ID", "")
        self.client_secret = os.getenv("CF_AZURE_CLIENT_SECRET", "")

    def rotate_password(self, username: str, dry_run: bool = True) -> Dict[str, Any]:
        result = {
            "provider": self.name,
            "username": username,
            "action": "rotate_password",
            "dry_run": dry_run,
            "success": False,
            "details": "",
            "secret_ref": None,
        }

        if not all([self.tenant_id, self.client_id, self.client_secret]):
            result["details"] = "Azure AD provider not configured (set CF_AZURE_* variables)"
            logger.warning(result["details"])
            return result

        if dry_run:
            result["details"] = f"[DRY-RUN] Would rotate Azure AD password for {username}"
            result["success"] = True
            return result

        # TODO: implement MSAL client-credentials flow + Graph password profile update
        result["details"] = (
            f"Azure AD password rotation for {username} is stubbed. "
            f"Install msal + configure CF_AZURE_* to enable."
        )
        logger.warning(result["details"])
        return result

    def disable_account(self, username: str, dry_run: bool = True) -> Dict[str, Any]:
        result = {
            "provider": self.name,
            "username": username,
            "action": "disable_account",
            "dry_run": dry_run,
            "success": False,
            "details": "Azure AD disable is stubbed — configure CF_AZURE_* to enable",
        }
        return result

    def list_users(self) -> List[str]:
        return []


def get_identity_provider(name: Optional[str] = None) -> IdentityProvider:
    """
    Factory. Selection order:
    1. Explicit name argument
    2. CF_IDENTITY_PROVIDER environment variable
    3. Default to local_linux
    """
    chosen = (name or os.getenv("CF_IDENTITY_PROVIDER", "local_linux")).lower()

    mapping = {
        "local_linux": LocalLinuxProvider,
        "local": LocalLinuxProvider,
        "linux": LocalLinuxProvider,
        "ldap": LDAPProvider,
        "ad": LDAPProvider,
        "active_directory": LDAPProvider,
        "azure_ad": AzureADProvider,
        "azure": AzureADProvider,
        "entra": AzureADProvider,
    }

    cls = mapping.get(chosen, LocalLinuxProvider)
    logger.info(f"Using identity provider: {cls.name if hasattr(cls, 'name') else chosen}")
    return cls()
