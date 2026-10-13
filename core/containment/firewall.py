#!/usr/bin/env python3
"""
CyberFortress active firewall helper (iptables).

Uses a dedicated chain CF_BLOCK so rules are visible, countable, and removable
without touching unrelated host policy.

Safety:
  - Mutations only when dry_run=False AND CF_CONTAINMENT_LIVE=true
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


def _iptables_bin() -> Optional[str]:
    return shutil.which("iptables")


def _run(cmd: List[str], dry_run: bool) -> subprocess.CompletedProcess:
    if dry_run or not LIVE_MODE:
        logger.info("[DRY-RUN/SAFE] Would execute: %s", " ".join(cmd))
        return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")
    logger.info("Executing: %s", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, check=False)


def _run_read(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, check=False)


def ensure_chain(dry_run: bool = True) -> Dict[str, Any]:
    ipt = _iptables_bin()
    if not ipt:
        return {"ok": False, "error": "iptables not found on PATH"}

    steps = []
    r = _run([ipt, "-N", CHAIN], dry_run=dry_run)
    steps.append({"cmd": f"iptables -N {CHAIN}", "rc": r.returncode})

    for parent in ("INPUT", "OUTPUT"):
        chk = _run_read([ipt, "-C", parent, "-j", CHAIN])
        if chk.returncode != 0:
            r = _run([ipt, "-I", parent, "1", "-j", CHAIN], dry_run=dry_run)
            steps.append({"cmd": f"iptables -I {parent} -j {CHAIN}", "rc": r.returncode})
        else:
            steps.append({"cmd": f"jump {parent}->{CHAIN}", "rc": 0, "already": True})

    return {
        "ok": True,
        "chain": CHAIN,
        "dry_run": dry_run or (not LIVE_MODE),
        "live_mode": LIVE_MODE,
        "steps": steps,
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
            f"[DRY-RUN] Would ensure chain {CHAIN} and DROP src/dst {target} "
            f"(iptables={'yes' if ipt else 'not on PATH'})"
        )
        return result

    if not ipt:
        result["details"] = "iptables binary not found"
        return result

    ensure_chain(dry_run=False)
    cmt = re.sub(r"[^A-Za-z0-9_.:-]", "_", comment)[:40]
    cmds = [
        [ipt, "-A", CHAIN, "-s", target, "-j", "DROP", "-m", "comment", "--comment", cmt],
        [ipt, "-A", CHAIN, "-d", target, "-j", "DROP", "-m", "comment", "--comment", cmt],
    ]
    details = []
    ok = True
    for cmd in cmds:
        r = _run(cmd, dry_run=False)
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
        result["details"] = f"[DRY-RUN] Would remove DROP rules for {target} from {CHAIN}"
        return result

    if not ipt:
        result["details"] = "iptables binary not found"
        return result

    removed = 0
    for _ in range(8):
        for flag in ("-s", "-d"):
            cmd = [ipt, "-D", CHAIN, flag, target, "-j", "DROP"]
            r = _run(cmd, dry_run=False)
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
                rules.append({"num": parts[0], "raw": line[:120], "target": parts[3] if len(parts) > 3 else ""})
        except Exception:
            rules.append({"raw": line[:120]})
    return rules[:50]


def firewall_status() -> Dict[str, Any]:
    ipt = _iptables_bin()
    live = os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "true"
    status: Dict[str, Any] = {
        "backend": "iptables",
        "chain": CHAIN,
        "iptables_present": bool(ipt),
        "live_mode": live,
        "mode_label": "LIVE FIREWALL" if live else "PRACTICE (no rules applied)",
        "chain_exists": False,
        "rule_count": 0,
        "rules": [],
        "message": "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if not ipt:
        status["message"] = "iptables not installed or not on PATH"
        return status

    r = _run_read([ipt, "-L", CHAIN, "-n"])
    if r.returncode == 0:
        status["chain_exists"] = True
        rules = list_cf_rules()
        status["rules"] = rules
        status["rule_count"] = len(rules)
        status["message"] = (
            f"Chain {CHAIN} present with {status['rule_count']} rule(s)"
            if status["rule_count"]
            else f"Chain {CHAIN} present (empty)"
        )
    else:
        status["message"] = f"Chain {CHAIN} not created yet (will be created on first live block)"
        err = (r.stderr or b"").decode(errors="replace").strip()
        if err:
            status["iptables_error"] = err[:200]

    who = _run_read(["id", "-u"])
    try:
        status["running_as_uid"] = int((who.stdout or b"0").decode().strip() or "0")
    except Exception:
        status["running_as_uid"] = None
    if live and status.get("running_as_uid") not in (0, None):
        status["warning"] = "Live mode is on but process is not root — iptables may fail"

    return status
