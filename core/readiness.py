#!/usr/bin/env python3
"""Layered readiness gates: software / monitoring / pilot / live-containment."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(os.getenv("CF_ROOT", ".")).resolve()


def _signoff_path() -> Path:
    return ROOT / "config" / "pilot_signoff.json"


def load_signoff() -> Dict[str, Any]:
    p = _signoff_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"_error": "invalid_json"}


def software_health() -> Tuple[bool, List[str]]:
    """Importable core modules and safe defaults."""
    notes: List[str] = []
    ok = True
    live = os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "true"
    if live:
        notes.append("CF_CONTAINMENT_LIVE is true (not a software-fault, note for operators)")
    try:
        import core.audit_chain  # noqa: F401
        import core.monitoring_metrics  # noqa: F401
        import core.defense  # noqa: F401
        notes.append("core modules import ok")
    except Exception as e:
        ok = False
        notes.append(f"core import failed: {e}")
    py = os.getenv("CF_REQUIRE_PYTHON", "3.12")
    import sys

    ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    if sys.version_info < (3, 10):
        ok = False
        notes.append(f"Python {ver} too old (need >= 3.10, recommended {py})")
    else:
        notes.append(f"Python {ver}")
    return ok, notes


def monitoring_ready() -> Tuple[bool, List[str]]:
    """MONITORING path can run without live or WhatsApp."""
    ok, notes = software_health()
    logs = ROOT / "logs"
    if not logs.exists():
        notes.append("logs/ missing — run install.sh or start.sh")
    else:
        notes.append("logs/ present")
    if os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "true":
        notes.append("warning: live flag set — monitoring-only ops should use false")
    return ok, notes


def pilot_ready() -> Tuple[bool, List[str]]:
    """Pilot VM preconditions (sign-off partial + capability)."""
    notes: List[str] = []
    data = load_signoff()
    if not data or data.get("_error"):
        return False, ["missing or invalid config/pilot_signoff.json"]
    need = ["nda_signed", "roe_signed", "host_netadmin_verified", "operator_runbook_acknowledged"]
    missing = [k for k in need if data.get(k) is not True]
    if missing:
        notes.append("pilot flags missing: " + ", ".join(missing))
        return False, notes
    notes.append("pilot legal/host flags present")
    cap = ROOT / "config" / "host_capability.json"
    if cap.exists():
        try:
            c = json.loads(cap.read_text(encoding="utf-8"))
            if not c.get("netadmin_ok"):
                notes.append("host_capability netadmin_ok is false")
                return False, notes
            notes.append("host_capability netadmin_ok")
        except Exception as e:
            notes.append(f"host_capability unreadable: {e}")
            return False, notes
    else:
        notes.append("no host_capability.json yet (run check_netadmin.sh)")
    return True, notes


def live_containment_ready() -> Tuple[bool, List[str]]:
    """Full gate including soak + attorney + E&O."""
    ok, notes = pilot_ready()
    if not ok:
        return False, notes
    data = load_signoff()
    need = [
        "checklist_complete",
        "attorney_review_completed",
        "eo_insurance_confirmed",
        "soak_completed",
    ]
    missing = [k for k in need if data.get(k) is not True]
    if missing:
        notes.append("live flags missing: " + ", ".join(missing))
        return False, notes
    actions = data.get("authorized_actions") or []
    if not isinstance(actions, list) or len(actions) < 1:
        notes.append("authorized_actions empty")
        return False, notes
    notes.append("live containment sign-off complete (still requires enable_live_mode.sh)")
    return True, notes


def readiness_report() -> Dict[str, Any]:
    layers = {
        "software": software_health(),
        "monitoring": monitoring_ready(),
        "pilot": pilot_ready(),
        "live_containment": live_containment_ready(),
    }
    return {
        "layers": {
            name: {"ok": ok, "notes": notes} for name, (ok, notes) in layers.items()
        },
        "containment_live_env": os.getenv("CF_CONTAINMENT_LIVE", "false"),
        "recommended_mode": (
            "LIVE"
            if layers["live_containment"][0]
            else "MONITORING"
            if layers["monitoring"][0]
            else "FIX_SOFTWARE"
        ),
    }
