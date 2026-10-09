#!/usr/bin/env python3
"""
CyberFortress Identity Provider Hooks

Pluggable backends for credential rotation and account management.
- LocalLinuxProvider  : fully working
- LDAPProvider        : real implementation via ldap3
- AzureADProvider     : real implementation via MSAL + Microsoft Graph
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


def _store_secret(provider: str, username: str, password: str) -> str:
    """Write a one-time secret file (mode 600) and return its path."""
    secrets_dir = Path("./secrets/rotated")
    secrets_dir.mkdir(parents=True, exist_ok=True)
    secret_file = secrets_dir / f"{provider}_{username}_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
    secret_file.write_text(
        f"provider={provider}\nuser={username}\npassword={password}\n"
        f"generated={datetime.now(timezone.utc).isoformat()}\n",
        encoding="utf-8",
    )
    os.chmod(secret_file, 0o600)
    return str(secret_file)


class IdentityProvider(ABC):
    name: str = "base"

    @abstractmethod
    def rotate_password(self, username: str, dry_run: bool = True) -> Dict[str, Any]:
        pass

    @abstractmethod
    def disable_account(self, username: str, dry_run: bool = True) -> Dict[str, Any]:
        pass

    @abstractmethod
    def list_users(self) -> List[str]:
        pass


# ---------------------------------------------------------------------------
# Local Linux
# ---------------------------------------------------------------------------
class LocalLinuxProvider(IdentityProvider):
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
            subprocess.run(
                ["chpasswd"],
                input=f"{username}:{new_pass}".encode(),
                capture_output=True,
                check=True,
            )
            secret_ref = _store_secret(self.name, username, new_pass)
            result["success"] = True
            result["secret_ref"] = secret_ref
            result["details"] = f"Local password rotated for {username}; secret at {secret_ref}"
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
            out = subprocess.check_output(["getent", "passwd"], text=True)
            users = []
            for line in out.splitlines():
                parts = line.split(":")
                if len(parts) >= 3 and parts[2].isdigit() and int(parts[2]) >= 1000:
                    users.append(parts[0])
            return users
        except Exception:
            return []


# ---------------------------------------------------------------------------
# LDAP / Active Directory (real implementation via ldap3)
# ---------------------------------------------------------------------------
class LDAPProvider(IdentityProvider):
    """
    Real LDAP / AD provider using the ldap3 library.

    Required environment variables:
      CF_LDAP_SERVER          e.g. ldap://dc.example.tt or ldaps://dc.example.tt
      CF_LDAP_BIND_DN         e.g. cn=admin,dc=example,dc=tt
      CF_LDAP_BIND_PASSWORD
      CF_LDAP_USER_BASE       e.g. ou=users,dc=example,dc=tt
      CF_LDAP_USER_FILTER     optional, default (uid={username}) or sAMAccountName for AD
    """

    name = "ldap"

    def __init__(self):
        self.server = os.getenv("CF_LDAP_SERVER", "")
        self.bind_dn = os.getenv("CF_LDAP_BIND_DN", "")
        self.bind_password = os.getenv("CF_LDAP_BIND_PASSWORD", "")
        self.user_base = os.getenv("CF_LDAP_USER_BASE", "")
        self.user_filter = os.getenv("CF_LDAP_USER_FILTER", "(uid={username})")
        # For Active Directory many people prefer:
        # CF_LDAP_USER_FILTER=(sAMAccountName={username})

    def _connect(self):
        try:
            from ldap3 import Server, Connection, ALL, Tls
            import ssl
        except ImportError:
            raise RuntimeError("ldap3 is not installed. Run: pip install ldap3")

        use_ssl = self.server.lower().startswith("ldaps://")
        tls = None
        if use_ssl:
            tls = Tls(validate=ssl.CERT_NONE)  # tighten in production if you have proper CA

        server = Server(self.server, get_info=ALL, use_ssl=use_ssl, tls=tls)
        conn = Connection(
            server,
            user=self.bind_dn,
            password=self.bind_password,
            auto_bind=True,
        )
        return conn

    def _find_user_dn(self, conn, username: str) -> Optional[str]:
        search_filter = self.user_filter.format(username=username)
        conn.search(self.user_base, search_filter, attributes=["dn"])
        if conn.entries:
            return str(conn.entries[0].entry_dn)
        return None

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

        if not all([self.server, self.bind_dn, self.bind_password, self.user_base]):
            result["details"] = "LDAP provider not fully configured (need CF_LDAP_SERVER, BIND_DN, BIND_PASSWORD, USER_BASE)"
            logger.warning(result["details"])
            return result

        new_pass = _generate_password()

        if dry_run:
            result["details"] = f"[DRY-RUN] Would rotate LDAP password for {username} on {self.server}"
            result["success"] = True
            return result

        try:
            conn = self._connect()
            user_dn = self._find_user_dn(conn, username)
            if not user_dn:
                result["details"] = f"User '{username}' not found under {self.user_base}"
                conn.unbind()
                return result

            # Prefer the Password Modify extended operation when available
            # Fall back to direct unicodePwd / userPassword attribute replace
            from ldap3 import MODIFY_REPLACE

            # Try extended operation first (RFC 3062)
            try:
                if conn.extend.standard.modify_password(user_dn, new_password=new_pass):
                    secret_ref = _store_secret(self.name, username, new_pass)
                    result["success"] = True
                    result["secret_ref"] = secret_ref
                    result["details"] = f"LDAP password rotated for {username} via extend.modify_password; secret at {secret_ref}"
                else:
                    raise RuntimeError(conn.result)
            except Exception:
                # Fallback for many AD / OpenLDAP setups
                changes = {"userPassword": [(MODIFY_REPLACE, [new_pass])]}
                # Active Directory often wants unicodePwd as UTF-16-LE quoted
                if "sAMAccountName" in self.user_filter or "ad" in self.server.lower():
                    encoded = f'"{new_pass}"'.encode("utf-16-le")
                    changes = {"unicodePwd": [(MODIFY_REPLACE, [encoded])]}

                success = conn.modify(user_dn, changes)
                if success:
                    secret_ref = _store_secret(self.name, username, new_pass)
                    result["success"] = True
                    result["secret_ref"] = secret_ref
                    result["details"] = f"LDAP password rotated for {username} via attribute replace; secret at {secret_ref}"
                else:
                    result["details"] = f"LDAP modify failed: {conn.result}"

            conn.unbind()
            logger.info(result["details"])

        except Exception as e:
            result["details"] = str(e)
            logger.exception("LDAPProvider.rotate_password error")

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

        if not all([self.server, self.bind_dn, self.bind_password, self.user_base]):
            result["details"] = "LDAP provider not fully configured"
            return result

        if dry_run:
            result["details"] = f"[DRY-RUN] Would disable LDAP account {username}"
            result["success"] = True
            return result

        try:
            from ldap3 import MODIFY_REPLACE
            conn = self._connect()
            user_dn = self._find_user_dn(conn, username)
            if not user_dn:
                result["details"] = f"User '{username}' not found"
                conn.unbind()
                return result

            # Generic approach: set a disabled flag if the attribute exists
            # For AD the common method is userAccountControl bit
            changes = {"userAccountControl": [(MODIFY_REPLACE, ["514"])] }  # 512=normal, 514=disabled
            success = conn.modify(user_dn, changes)
            if not success:
                # Fallback for non-AD directories – just log
                result["details"] = f"Could not set disabled flag (may need directory-specific attribute): {conn.result}"
            else:
                result["success"] = True
                result["details"] = f"LDAP account {username} disabled"

            conn.unbind()
            logger.info(result["details"])

        except Exception as e:
            result["details"] = str(e)
            logger.exception("LDAPProvider.disable_account error")

        return result

    def list_users(self) -> List[str]:
        if not all([self.server, self.bind_dn, self.bind_password, self.user_base]):
            return []
        try:
            conn = self._connect()
            conn.search(self.user_base, "(objectClass=person)", attributes=["uid", "sAMAccountName", "cn"])
            users = []
            for entry in conn.entries:
                if hasattr(entry, "sAMAccountName") and entry.sAMAccountName:
                    users.append(str(entry.sAMAccountName))
                elif hasattr(entry, "uid") and entry.uid:
                    users.append(str(entry.uid))
                elif hasattr(entry, "cn") and entry.cn:
                    users.append(str(entry.cn))
            conn.unbind()
            return users
        except Exception as e:
            logger.warning(f"LDAP list_users failed: {e}")
            return []


# ---------------------------------------------------------------------------
# Microsoft Entra ID / Azure AD (real implementation via MSAL + Graph)
# ---------------------------------------------------------------------------
class AzureADProvider(IdentityProvider):
    """
    Real Microsoft Entra ID (Azure AD) provider.

    Required environment variables:
      CF_AZURE_TENANT_ID
      CF_AZURE_CLIENT_ID
      CF_AZURE_CLIENT_SECRET

    The App Registration needs Application permissions:
      User.ReadWrite.All  (or Directory.ReadWrite.All)
    and admin consent.
    """

    name = "azure_ad"
    GRAPH = "https://graph.microsoft.com/v1.0"

    def __init__(self):
        self.tenant_id = os.getenv("CF_AZURE_TENANT_ID", "")
        self.client_id = os.getenv("CF_AZURE_CLIENT_ID", "")
        self.client_secret = os.getenv("CF_AZURE_CLIENT_SECRET", "")

    def _get_token(self) -> str:
        try:
            from msal import ConfidentialClientApplication
        except ImportError:
            raise RuntimeError("msal is not installed. Run: pip install msal")

        app = ConfidentialClientApplication(
            self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            client_credential=self.client_secret,
        )
        result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        if "access_token" not in result:
            raise RuntimeError(f"Failed to obtain Graph token: {result.get('error_description', result)}")
        return result["access_token"]

    def _headers(self, token: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _resolve_user_id(self, token: str, username: str) -> Optional[str]:
        """Accept UPN, email or display name and return the Graph user id."""
        import requests

        # Try direct UPN lookup first
        url = f"{self.GRAPH}/users/{username}"
        r = requests.get(url, headers=self._headers(token), timeout=30)
        if r.status_code == 200:
            return r.json().get("id")

        # Fallback search
        url = f"{self.GRAPH}/users?$filter=userPrincipalName eq '{username}' or mail eq '{username}'"
        r = requests.get(url, headers=self._headers(token), timeout=30)
        if r.status_code == 200 and r.json().get("value"):
            return r.json()["value"][0]["id"]
        return None

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
            result["details"] = "Azure AD provider not configured (set CF_AZURE_TENANT_ID, CLIENT_ID, CLIENT_SECRET)"
            logger.warning(result["details"])
            return result

        new_pass = _generate_password()

        if dry_run:
            result["details"] = f"[DRY-RUN] Would rotate Azure AD password for {username}"
            result["success"] = True
            return result

        try:
            import requests

            token = self._get_token()
            user_id = self._resolve_user_id(token, username)
            if not user_id:
                result["details"] = f"User '{username}' not found in Azure AD"
                return result

            url = f"{self.GRAPH}/users/{user_id}"
            payload = {
                "passwordProfile": {
                    "password": new_pass,
                    "forceChangePasswordNextSignIn": True,
                }
            }
            r = requests.patch(url, headers=self._headers(token), json=payload, timeout=30)

            if r.status_code in (200, 204):
                secret_ref = _store_secret(self.name, username, new_pass)
                result["success"] = True
                result["secret_ref"] = secret_ref
                result["details"] = f"Azure AD password rotated for {username}; secret at {secret_ref}"
                logger.info(result["details"])
            else:
                result["details"] = f"Graph API error {r.status_code}: {r.text}"
                logger.error(result["details"])

        except Exception as e:
            result["details"] = str(e)
            logger.exception("AzureADProvider.rotate_password error")

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

        if not all([self.tenant_id, self.client_id, self.client_secret]):
            result["details"] = "Azure AD provider not configured"
            return result

        if dry_run:
            result["details"] = f"[DRY-RUN] Would disable Azure AD account {username}"
            result["success"] = True
            return result

        try:
            import requests

            token = self._get_token()
            user_id = self._resolve_user_id(token, username)
            if not user_id:
                result["details"] = f"User '{username}' not found in Azure AD"
                return result

            url = f"{self.GRAPH}/users/{user_id}"
            payload = {"accountEnabled": False}
            r = requests.patch(url, headers=self._headers(token), json=payload, timeout=30)

            if r.status_code in (200, 204):
                result["success"] = True
                result["details"] = f"Azure AD account {username} disabled"
                logger.info(result["details"])
            else:
                result["details"] = f"Graph API error {r.status_code}: {r.text}"

        except Exception as e:
            result["details"] = str(e)
            logger.exception("AzureADProvider.disable_account error")

        return result

    def list_users(self) -> List[str]:
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            return []
        try:
            import requests

            token = self._get_token()
            url = f"{self.GRAPH}/users?$select=userPrincipalName&$top=999"
            r = requests.get(url, headers=self._headers(token), timeout=30)
            if r.status_code == 200:
                return [u["userPrincipalName"] for u in r.json().get("value", [])]
            return []
        except Exception as e:
            logger.warning(f"Azure AD list_users failed: {e}")
            return []


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
def get_identity_provider(name: Optional[str] = None) -> IdentityProvider:
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
    logger.info(f"Using identity provider: {getattr(cls, 'name', chosen)}")
    return cls()
