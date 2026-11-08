#!/usr/bin/env python3
"""
CyberFortress active firewall helper (iptables).

Uses a dedicated chain CF_BLOCK so rules are visible, countable, and removable
without touching unrelated host policy.

Safety:
  - Chain setup (ensure_chain) runs when the firewall agent starts (empty chain = no blocks)
  - DROP rules only when CF_CONTAINMENT_LIVE=true (armed containment)
  - status() is always read-only
  - Private/loopback/multicast blocked from DROP by default
  - Operator allowlist never blocked
  - Max rule count + dedupe before insert
  - Post-action verify after live DROP
"""

from __future__ import annotations

import ipaddress
import json
import logging
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("cf_firewall")

CHAIN = os.getenv("CF_IPTABLES_CHAIN", "CF_BLOCK")
STATUS_PATH = Path(os.getenv("CF_FIREWALL_STATUS", "./logs/firewall_status.json"))
MAX_RULES = int(os.getenv("CF_FIREWALL_MAX_RULES", "200"))
ALLOW_PRIVATE = os.getenv("CF_FIREWALL_ALLOW_PRIVATE", "false").lower() in ("1", "true", "yes")


def _live() -> bool:
    return os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "true"


def _auto_start() -> bool:
    return os.getenv("CF_FIREWALL_AUTO_START", "false").lower() == "true"


def _iptables_bin() -> Optional[str]:
    return shutil.which("iptables")


def _run_real(cmd: List[str]) -> subprocess.CompletedProcess:
    logger.info("Executing: %s", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, check=False)


def _run_block(cmd: List[str], dry_run: bool) -> subprocess.CompletedProcess:
    if dry_run or not _live():
        logger.info("[STANDBY] Would execute: %s", " ".join(cmd))
        return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")
    return _run_real(cmd)


def _run_read(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, check=False)


def load_allowlist() -> Set[str]:
    """IPs/CIDRs that must never be DROP'd (operators, gateways, DNS)."""
    raw = os.getenv("CF_FIREWALL_ALLOWLIST", "")
    items: Set[str] = set()
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if part:
            items.add(part)
    items.update({"127.0.0.1", "::1", "localhost"})
    path = Path(os.getenv("CF_FIREWALL_ALLOWLIST_FILE", "./config/firewall_allowlist.txt"))
    if path.is_file():
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    items.add(line)
        except Exception as e:
            logger.warning("allowlist file: %s", e)
    return items


def _ip_in_networks(ip: str, networks: Set[str]) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    for n in networks:
        try:
            if "/" in n:
                if addr in ipaddress.ip_network(n, strict=False):
                    return True
            else:
                if addr == ipaddress.ip_address(n):
                    return True
        except ValueError:
            continue
    return False


def validate_block_target(target: str) -> Dict[str, Any]:
    """Reject malformed, localhost, and (by default) private ranges."""
    t = (target or "").strip()
    if not t:
        return {"ok": False, "error": "empty target"}
    if "/" in t:
        return {"ok": False, "error": "CIDR targets are not supported; supply one IP address"}
    host = t.split("/")[0].strip()
    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        return {"ok": False, "error": f"invalid IP: {target}"}

    if addr.is_loopback:
        return {"ok": False, "error": "refusing to block loopback"}
    if addr.is_multicast or addr.is_unspecified:
        return {"ok": False, "error": "refusing to block multicast/unspecified"}
    if addr.is_link_local:
        return {"ok": False, "error": "refusing to block link-local"}
    if not ALLOW_PRIVATE and addr.is_private:
        return {
            "ok": False,
            "error": (
                "refusing to block private/reserved address "
                "(set CF_FIREWALL_ALLOW_PRIVATE=true to override)"
            ),
        }

    if _ip_in_networks(host, load_allowlist()):
        return {"ok": False, "error": f"target {host} is on firewall allowlist — never block"}

    return {"ok": True, "ip": host}


def ensure_chain(dry_run: bool = False, force_infra: bool = False) -> Dict[str, Any]:
    ipt = _iptables_bin()
    live = _live()
    auto = _auto_start()
    if not ipt:
        return {"ok": False, "error": "iptables not found on PATH", "chain": CHAIN}

    do_real = (not dry_run) and (live or auto or force_infra)

    steps = []
    if do_real:
        r = _run_real([ipt, "-N", CHAIN])
        steps.append({"cmd": f"iptables -N {CHAIN}", "rc": r.returncode})
    else:
        logger.info("[STANDBY] Would create chain %s", CHAIN)
        steps.append({"cmd": f"iptables -N {CHAIN}", "rc": 0, "simulated": True})

    for parent in ("INPUT", "OUTPUT", "FORWARD"):
        if do_real:
            chk = _run_read([ipt, "-C", parent, "-j", CHAIN])
            if chk.returncode != 0:
                r = _run_real([ipt, "-I", parent, "1", "-j", CHAIN])
                steps.append({"cmd": f"iptables -I {parent} -j {CHAIN}", "rc": r.returncode})
            else:
                steps.append({"cmd": f"iptables -C {parent} -j {CHAIN}", "rc": 0, "exists": True})
        else:
            steps.append({"cmd": f"iptables -I {parent} -j {CHAIN}", "rc": 0, "simulated": True})

    if do_real:
        probe = _run_read([ipt, "-L", CHAIN, "-n"])
        err = (probe.stderr or b"").decode(errors="replace").lower()
        if probe.returncode != 0 and ("permission denied" in err or "operation not permitted" in err):
            return {
                "ok": False,
                "error": "Permission denied — host lacks netfilter capability (CAP_NET_ADMIN)",
                "chain": CHAIN,
                "infrastructure": False,
                "live_mode": live,
                "auto_start": auto,
                "steps": steps,
                "message": "UNAVAILABLE: cannot manage iptables on this host",
            }

    return {
        "ok": True,
        "chain": CHAIN,
        "infrastructure": do_real,
        "live_mode": live,
        "auto_start": auto,
        "steps": steps,
        "message": (
            f"Chain {CHAIN} ready (empty until containment actions add DROP rules)"
            if do_real
            else f"Chain {CHAIN} setup simulated (set CF_FIREWALL_AUTO_START=true and install iptables)"
        ),
    }


def _already_blocked(target: str) -> bool:
    for r in list_cf_rules(strict=True):
        if r.get("source") == target or r.get("destination") == target:
            return True
    return False


def block_ip(
    target: str,
    dry_run: bool = True,
    comment: str = "CyberFortress",
    roe_action: str = "block_ip",
) -> Dict[str, Any]:
    ipt = _iptables_bin()
    live = _live()
    result: Dict[str, Any] = {
        "action": roe_action,
        "target": target,
        "chain": CHAIN,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run or (not live),
        "live_mode": live,
        "success": False,
        "details": "",
    }

    if not result["dry_run"]:
        from core.roe import is_action_authorized
        if not is_action_authorized(roe_action):
            result["details"] = f"action {roe_action} not authorized by client ROE"
            result["rejected"] = True
            result["roe_denied"] = True
            return result

    v = validate_block_target(target)
    if not v.get("ok"):
        result["details"] = v.get("error", "invalid target")
        result["rejected"] = True
        return result
    target = v["ip"]
    result["target"] = target

    if result["dry_run"]:
        result["success"] = True
        result["details"] = (
            f"[MONITORING] Would DROP src/dst {target} in {CHAIN} "
            f"(arm containment with CF_CONTAINMENT_LIVE=true to apply)"
        )
        result["verify"] = {"skipped": True, "verified": False, "message": "dry-run / monitoring"}
        return result

    if not ipt:
        result["details"] = "iptables binary not found"
        return result

    try:
        rules = list_cf_rules(strict=True)
    except Exception as exc:
        result["details"] = f"Unable to read firewall state safely: {exc}"
        return result
    if len(rules) >= MAX_RULES:
        result["details"] = f"max rules reached ({MAX_RULES}) — refuse new DROP for {target}"
        result["circuit"] = True
        return result

    try:
        already_blocked = _already_blocked(target)
    except Exception as exc:
        result["details"] = f"Unable to inspect existing firewall rules: {exc}"
        return result

    if already_blocked:
        try:
            result["verify"] = verify_block(target)
        except Exception as exc:
            result["details"] = f"Unable to verify existing firewall rules: {exc}"
            return result
        result["success"] = bool(result["verify"].get("verified") and result["verify"].get("bidirectional"))
        result["details"] = (
            f"already present and verified in {CHAIN} for {target}"
            if result["success"] else f"existing rules failed bidirectional verification for {target}"
        )
        return result

    chain_status = ensure_chain(dry_run=False, force_infra=True)
    if not chain_status.get("ok"):
        result["details"] = chain_status.get("error") or "firewall chain is not ready"
        result["infrastructure"] = False
        return result
    cmt = re.sub(r"[^A-Za-z0-9_.:-]", "_", comment)[:48]
    cmds = [
        [ipt, "-A", CHAIN, "-s", target, "-j", "DROP", "-m", "comment", "--comment", cmt],
        [ipt, "-A", CHAIN, "-d", target, "-j", "DROP", "-m", "comment", "--comment", cmt],
    ]
    details = []
    inserted = []
    for cmd in cmds:
        completed = _run_block(cmd, dry_run=False)
        details.append(" ".join(cmd[1:]))
        if completed.returncode != 0:
            error = (completed.stderr or b"").decode(errors="replace")[:200]
            for prior in reversed(inserted):
                rollback = [ipt, "-D", *prior[2:]]
                _run_block(rollback, dry_run=False)
            result["details"] = f"DROP insertion failed; partial changes rolled back where possible: {error}"
            result["rollback_attempted"] = bool(inserted)
            return result
        inserted.append(cmd)

    try:
        verification = verify_block(target)
    except Exception as exc:
        result["details"] = f"Firewall insertion completed but read-back failed: {exc}"
        result["verify"] = {"verified": False, "bidirectional": False, "message": "read-back failed"}
        return result
    result["verify"] = verification
    result["success"] = bool(verification.get("verified") and verification.get("bidirectional"))
    result["details"] = f"Inserted and verified bidirectional DROP in {CHAIN} for {target}"
    if not result["success"]:
        result["details"] += " | VERIFY FAILED: both source and destination rules were not confirmed"
        logger.error("Post-action bidirectional verification failed for %s", target)
    return result


def unblock_ip(target: str, dry_run: bool = True, roe_action: str = "unblock_ip") -> Dict[str, Any]:
    ipt = _iptables_bin()
    live = _live()
    result: Dict[str, Any] = {
        "action": roe_action,
        "target": target,
        "chain": CHAIN,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run or (not live),
        "live_mode": live,
        "success": False,
        "details": "",
    }

    host = (target or "").strip().split("/")[0]
    try:
        ipaddress.ip_address(host)
        target = host
        result["target"] = target
    except ValueError:
        result["details"] = f"invalid IP: {target}"
        return result

    if not result["dry_run"]:
        from core.roe import is_action_authorized
        if not is_action_authorized(roe_action):
            result["details"] = f"action {roe_action} not authorized by client ROE"
            result["rejected"] = True
            result["roe_denied"] = True
            return result

    if result["dry_run"]:
        result["success"] = True
        result["details"] = f"[MONITORING] Would remove DROP rules for {target} from {CHAIN}"
        return result

    if not ipt:
        result["details"] = "iptables binary not found"
        return result

    removed = 0
    for _ in range(12):
        for flag in ("-s", "-d"):
            cmd = [ipt, "-D", CHAIN, flag, target, "-j", "DROP"]
            r = _run_block(cmd, dry_run=False)
            if r.returncode == 0:
                removed += 1
    probe = _run_read([ipt, "-L", CHAIN, "-n"])
    if probe.returncode != 0:
        detail = (probe.stderr or b"").decode(errors="replace")[:200]
        result["details"] = f"Unable to verify rollback from {CHAIN}: {detail}"
        result["verify"] = {"cleared": False, "message": "firewall read-back failed"}
        return result
    try:
        remaining = _already_blocked(target)
    except Exception as exc:
        result["details"] = f"Firewall rollback read-back failed: {exc}"
        result["verify"] = {"cleared": False, "message": "firewall state unreadable"}
        return result
    result["success"] = not remaining
    result["details"] = f"Removed rules for {target} in {CHAIN} (deleted={removed})"
    result["verify"] = {
        "cleared": not remaining,
        "message": "gone from chain" if not remaining else "still present",
    }
    if remaining:
        result["details"] += " | ROLLBACK VERIFY FAILED: matching rule remains"
    return result


def list_cf_rules(strict: bool = False) -> List[Dict[str, str]]:
    ipt = _iptables_bin()
    if not ipt:
        if strict:
            raise RuntimeError("iptables binary not found")
        return []
    r = _run_read([ipt, "-L", CHAIN, "-n", "-v", "--line-numbers"])
    if r.returncode != 0:
        if strict:
            detail = (r.stderr or b"").decode(errors="replace")[:200]
            raise RuntimeError(detail or f"iptables read exited {r.returncode}")
        return []
    text = r.stdout.decode(errors="replace")
    rules: List[Dict[str, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("Chain ") or line.startswith("num "):
            continue
        parts = line.split()
        if len(parts) < 6:
            continue
        try:
            if parts[0].isdigit() and len(parts) >= 10:
                rules.append(
                    {
                        "num": parts[0],
                        "pkts": parts[1],
                        "target": parts[3],
                        "source": parts[8],
                        "destination": parts[9],
                        "raw": line[:160],
                    }
                )
            else:
                rules.append(
                    {
                        "num": parts[0],
                        "raw": line[:160],
                        "target": parts[3] if len(parts) > 3 else "",
                        "source": "",
                        "destination": "",
                    }
                )
        except Exception:
            rules.append({"raw": line[:160]})
    return rules


def persist_status(st: Dict[str, Any]) -> None:
    try:
        STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATUS_PATH.write_text(json.dumps(st, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning("persist firewall status: %s", e)


def firewall_status() -> Dict[str, Any]:
    ipt = _iptables_bin()
    live = _live()
    auto = _auto_start()
    status: Dict[str, Any] = {
        "chain": CHAIN,
        "iptables_present": bool(ipt),
        "live_mode": live,
        "auto_start": auto,
        "service": "running",
        "mode_label": "ARMED" if live else "RUNNING (standby for DROP rules)",
        "chain_exists": False,
        "rule_count": 0,
        "max_rules": MAX_RULES,
        "allowlist_count": len(load_allowlist()),
        "allow_private": ALLOW_PRIVATE,
        "rules": [],
        "message": "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if not ipt:
        status["message"] = "iptables not installed or not on PATH"
        status["mode_label"] = "UNAVAILABLE"
        persist_status(status)
        return status

    r = _run_read([ipt, "-L", CHAIN, "-n"])
    err = (r.stderr or b"").decode(errors="replace").strip()
    if r.returncode == 0:
        status["chain_exists"] = True
        rules = list_cf_rules()
        status["rules"] = rules
        status["rule_count"] = len(rules)
        if live:
            status["mode_label"] = "ARMED"
            status["message"] = f"Chain {CHAIN} active · {status['rule_count']} DROP rule(s)"
        else:
            status["mode_label"] = "RUNNING"
            status["message"] = (
                f"Firewall service up · chain {CHAIN} ready · "
                f"{status['rule_count']} rule(s) · containment not armed (no new DROP from alerts)"
            )
        if status["rule_count"] >= MAX_RULES:
            status["warning"] = f"At max rules ({MAX_RULES})"
    else:
        denied = "permission denied" in err.lower() or "operation not permitted" in err.lower()
        if denied:
            status["mode_label"] = "UNAVAILABLE"
            status["message"] = (
                f"Host blocked netfilter (Permission denied). "
                f"Deploy on a VM/bare metal with CAP_NET_ADMIN, or privileged container. Detail: {err[:120]}"
            )
            status["host_blocked"] = True
        else:
            status["message"] = (
                f"Chain {CHAIN} not present yet — firewall agent will create it on start "
                f"(needs root + iptables). {err[:80]}"
            )

    who = _run_read(["id", "-u"])
    try:
        status["running_as_uid"] = int((who.stdout or b"0").decode().strip() or "0")
    except Exception:
        status["running_as_uid"] = None
    if status.get("running_as_uid") not in (0, None) and auto:
        status["warning"] = "Not root — cannot create/manage iptables rules (start with sudo for full firewall)"

    persist_status(status)
    return status


def verify_block(target: str) -> dict:
    """Post-action check that target appears in CF_BLOCK (or skipped in dry-run paths)."""
    from core.containment.verify import verify_block as _verify

    return _verify(target, chain=CHAIN, list_rules_fn=lambda: list_cf_rules(strict=True))
