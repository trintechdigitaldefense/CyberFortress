#!/usr/bin/env python3
"""
CyberFortress active firewall helper (iptables).

Uses a dedicated chain CF_BLOCK so rules are visible, countable, and removable
without touching unrelated host policy.

Safety:
  - Chain setup (ensure_chain) runs when the firewall agent starts (empty chain = no blocks)
  - DROP rules only when CF_CONTAINMENT_LIVE=true (armed containment)
  - status() is always read-only
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("cf_firewall")

CHAIN = os.getenv("CF_IPTABLES_CHAIN", "CF_BLOCK")
LIVE_MODE = os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "true"
AUTO_START = os.getenv("CF_FIREWALL_AUTO_START", "true").lower() == "true"


def _iptables_bin() -> Optional[str]:
    return shutil.which("iptables")


def _run_real(cmd: List[str]) -> subprocess.CompletedProcess:
    logger.info("Executing: %s", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, check=False)


def _run_block(cmd: List[str], dry_run: bool) -> subprocess.CompletedProcess:
    if dry_run or not LIVE_MODE:
        logger.info("[STANDBY] Would execute: %s", " ".join(cmd))
        return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")
    return _run_real(cmd)


def _run_read(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, check=False)


def ensure_chain(dry_run: bool = False, force_infra: bool = False) -> Dict[str, Any]:
    ipt = _iptables_bin()
    if not ipt:
        return {"ok": False, "error": "iptables not found on PATH", "chain": CHAIN}

    do_real = (not dry_run) and (LIVE_MODE or AUTO_START or force_infra)

    steps = []
    if do_real:
        r = _run_real([ipt, "-N", CHAIN])
        steps.append({"cmd": f"iptables -N {CHAIN}", "rc": r.returncode})
    else:
        logger.info("[STANDBY] Would create chain %s", CHAIN)
        steps.append({"cmd": f"iptables -N {CHAIN}", "rc": 0, "simulated": True})

    for parent in ("INPUT", "OUTPUT"):
        chk = _run_read([ipt, "-C", parent, "-j", CHAIN]) if do_real or ipt else None
        if do_real:
            if chk is not None and chk.returncode != 0:
                r = _run_real([ipt, "-I", parent, "1", "-j", CHAIN])
                steps.append({"cmd": f"iptables -I {parent} -j {CHAIN}", "rc": r.returncode})
            else:
                steps.append({"cmd": f"jump {parent}->{CHAIN}", "rc": 0, "already": True})
        else:
            steps.append({"cmd": f"jump {parent}->{CHAIN}", "rc": 0, "simulated": True})

    return {
        "ok": True,
        "chain": CHAIN,
        "infrastructure": do_real,
        "live_mode": LIVE_MODE,
        "auto_start": AUTO_START,
        "steps": steps,
        "message": (
            f"Chain {CHAIN} ready (empty until containment actions add DROP rules)"
            if do_real
            else f"Chain {CHAIN} setup simulated (set CF_FIREWALL_AUTO_START=true and install iptables)"
        ),
    }


def block_ip(target: str, dry_run: bool = True, comment: str = "CyberFortress") -> Dict[str, Any]:
    ipt = _iptables_bin()
    result: Dict[str, Any] = {
        "action": "block_ip",
        "target": target,
        "chain": CHAIN,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run or (not LIVE_MODE),
        "live_mode": LIVE_MODE,
        "success": False,
        "details": "",
    }

    if result["dry_run"]:
        result["success"] = True
        result["details"] = (
            f"[MONITORING] Would DROP src/dst {target} in {CHAIN} "
            f"(arm containment with CF_CONTAINMENT_LIVE=true to apply)"
        )
        return result

    if not ipt:
        result["details"] = "iptables binary not found"
        return result

    ensure_chain(dry_run=False, force_infra=True)
    cmt = re.sub(r"[^A-Za-z0-9_.:-]", "_", comment)[:40]
    cmds = [
        [ipt, "-A", CHAIN, "-s", target, "-j", "DROP", "-m", "comment", "--comment", cmt],
        [ipt, "-A", CHAIN, "-d", target, "-j", "DROP", "-m", "comment", "--comment", cmt],
    ]
    details = []
    ok = True
    for cmd in cmds:
        r = _run_block(cmd, dry_run=False)
        details.append(" ".join(cmd[1:]))
        if r.returncode != 0:
            ok = False
            if r.stderr:
                details.append(r.stderr.decode(errors="replace")[:200])

    result["success"] = ok
    result["details"] = f"Inserted DROP in {CHAIN} for {target}: " + "; ".join(details)
    return result


def unblock_ip(target: str, dry_run: bool = True) -> Dict[str, Any]:
    ipt = _iptables_bin()
    result: Dict[str, Any] = {
        "action": "unblock_ip",
        "target": target,
        "chain": CHAIN,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run or (not LIVE_MODE),
        "live_mode": LIVE_MODE,
        "success": False,
        "details": "",
    }

    if result["dry_run"]:
        result["success"] = True
        result["details"] = f"[MONITORING] Would remove DROP rules for {target} from {CHAIN}"
        return result

    if not ipt:
        result["details"] = "iptables binary not found"
        return result

    removed = 0
    for _ in range(8):
        for flag in ("-s", "-d"):
            cmd = [ipt, "-D", CHAIN, flag, target, "-j", "DROP"]
            r = _run_block(cmd, dry_run=False)
            if r.returncode == 0:
                removed += 1
    result["success"] = True
    result["details"] = f"Removed rules for {target} in {CHAIN} (deleted={removed})"
    return result


def list_cf_rules() -> List[Dict[str, str]]:
    ipt = _iptables_bin()
    if not ipt:
        return []
    r = _run_read([ipt, "-L", CHAIN, "-n", "-v", "--line-numbers"])
    if r.returncode != 0:
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
                        "raw": line[:120],
                    }
                )
            else:
                rules.append(
                    {
                        "num": parts[0],
                        "raw": line[:120],
                        "target": parts[3] if len(parts) > 3 else "",
                    }
                )
        except Exception:
            rules.append({"raw": line[:120]})
    return rules[:50]


def firewall_status() -> Dict[str, Any]:
    ipt = _iptables_bin()
    live = os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "true"
    auto = os.getenv("CF_FIREWALL_AUTO_START", "true").lower() == "true"
    status: Dict[str, Any] = {
        "backend": "iptables",
        "chain": CHAIN,
        "iptables_present": bool(ipt),
        "live_mode": live,
        "auto_start": auto,
        "service": "running",
        "mode_label": "ARMED" if live else "RUNNING (standby for DROP rules)",
        "chain_exists": False,
        "rule_count": 0,
        "rules": [],
        "message": "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if not ipt:
        status["message"] = "iptables not installed or not on PATH"
        status["mode_label"] = "UNAVAILABLE"
        return status

    r = _run_read([ipt, "-L", CHAIN, "-n"])
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
    else:
        status["message"] = (
            f"Chain {CHAIN} not present yet — firewall agent will create it on start "
            f"(needs root + iptables)"
        )

    who = _run_read(["id", "-u"])
    try:
        status["running_as_uid"] = int((who.stdout or b"0").decode().strip() or "0")
    except Exception:
        status["running_as_uid"] = None
    if status.get("running_as_uid") not in (0, None) and auto:
        status["warning"] = "Not root — cannot create/manage iptables rules (start with sudo for full firewall)"

    return status
