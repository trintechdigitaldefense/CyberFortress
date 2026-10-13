#!/usr/bin/env python3
"""
CyberFortress — one-command pilot dry-run

  bash scripts/pilot_dry_run.sh
  # or:  python3 scripts/pilot_dry_run.py

Seeds realistic Sentinel + Mirage events → fusion → autonomy (dry-run) →
CMA audit entries → evidence pack → prints pilot review summary.

Always forces CF_CONTAINMENT_LIVE=false for this process.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

os.environ["CF_CONTAINMENT_LIVE"] = "false"
os.environ.setdefault("CF_ALLOW_FORCE", "false")
os.environ.setdefault("CF_CLIENT_NAME", os.environ.get("CF_CLIENT_NAME", "Pilot Demo Client"))

CLIENT = os.environ["CF_CLIENT_NAME"]

# Isolated audit log for this drill (avoids mixing with old/broken chains)
PILOT_AUDIT = ROOT / "logs" / "pilot_dry_run_cma_audit.jsonl"
os.environ["CF_AUDIT_PATH"] = str(PILOT_AUDIT)
if PILOT_AUDIT.exists():
    PILOT_AUDIT.unlink()


def _banner(msg: str) -> None:
    print()
    print("=" * 60)
    print(f" {msg}")
    print("=" * 60)


def _step(n: int, title: str) -> None:
    print()
    print(f"[Step {n}] {title}")


def _ok(msg: str) -> None:
    print(f"  [OK]  {msg}")


def _info(msg: str) -> None:
    print(f"  [..]  {msg}")


def _fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")


def seed_events() -> list:
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%S")
    ts = now.isoformat()

    sentinel_dir = ROOT / "telemetry" / "sentinel"
    mirage_dir = ROOT / "telemetry" / "mirage"
    sentinel_dir.mkdir(parents=True, exist_ok=True)
    mirage_dir.mkdir(parents=True, exist_ok=True)

    sentinel_event = {
        "indicator": "reverse_shell_detected",
        "target": "SEC-WEB-01",
        "severity": "HIGH",
        "host": "SEC-WEB-01",
        "ip": "10.0.5.12",
        "timestamp": ts,
        "details": (
            "Pilot dry-run: outbound connection to 203.0.113.88:4444 "
            "matched reverse-shell pattern (synthetic event)"
        ),
        "pilot_run_id": stamp,
    }
    mirage_event = {
        "indicator": "decoy_trigger",
        "target": "203.0.113.45",
        "severity": "HIGH",
        "decoy_type": "fake_ssh_credentials",
        "attacker_ip": "203.0.113.45",
        "timestamp": ts,
        "details": (
            "Pilot dry-run: attacker attempted login to decoy SSH with "
            "canary credentials (synthetic event)"
        ),
        "pilot_run_id": stamp,
    }

    s_path = sentinel_dir / f"pilot_{stamp}_alert.json"
    m_path = mirage_dir / f"pilot_{stamp}_decoy.json"
    s_path.write_text(json.dumps(sentinel_event, indent=2), encoding="utf-8")
    m_path.write_text(json.dumps(mirage_event, indent=2), encoding="utf-8")
    _ok(f"Seeded Sentinel event → {s_path.relative_to(ROOT)}")
    _ok(f"Seeded Mirage event   → {m_path.relative_to(ROOT)}")

    return [
        {
            "source": "sentinel",
            "indicator": sentinel_event["indicator"],
            "target": sentinel_event["target"],
            "severity": "HIGH",
            "timestamp": ts,
            "raw": sentinel_event,
        },
        {
            "source": "mirage",
            "indicator": mirage_event["indicator"],
            "target": mirage_event["target"],
            "severity": "HIGH",
            "timestamp": ts,
            "raw": mirage_event,
        },
    ]


def run_fusion(events: list) -> list:
    from core.telemetry.fusion import TelemetryFusion

    fusion = TelemetryFusion(auto_respond=True)
    results = fusion.process(events)
    for r in results:
        ev = r.get("event") or {}
        _ok(
            "{src} / {ind} on {tgt} → {lvl} → playbook={pb} executed={ex}".format(
                src=ev.get("source"),
                ind=ev.get("indicator"),
                tgt=ev.get("target"),
                lvl=r.get("escalated_level"),
                pb=r.get("recommended_playbook"),
                ex=r.get("auto_executed"),
            )
        )
    return results


def verify_audit() -> tuple:
    from core.audit_chain import verify_chain

    path = Path(os.getenv("CF_AUDIT_PATH", "./logs/cma_audit.jsonl"))
    ok, idx, msg = verify_chain(path)
    if ok:
        _ok(f"Audit chain: {msg}")
    else:
        _fail(f"Audit chain broken at {idx}: {msg}")
    entries = 0
    if path.exists():
        entries = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    _info(f"Audit log entries: {entries} ({path})")
    return ok, entries


def make_evidence() -> dict:
    from core.evidence.pack import generate_evidence_pack_with_meta

    result = generate_evidence_pack_with_meta(client_name=CLIENT, create_zip=True)
    if result.get("ok"):
        _ok(f"Evidence ZIP: {result.get('path')}")
        _ok(f"Actions in pack: {result.get('actions_loaded')}")
        _info(f"Files: {', '.join(result.get('files') or [])}")
    else:
        _fail(f"Evidence pack failed: {result}")
    return result


def print_pilot_review(fusion_results: list, audit_ok: bool, entries: int, evidence: dict) -> int:
    from core.roe import roe_status
    from core.circuit_breaker import breaker

    live = os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "true"
    roe = roe_status()
    cb = breaker.status()

    _banner("PILOT DRY-RUN SUMMARY")
    print(f"  Client name     : {CLIENT}")
    print(f"  Mode            : {'LIVE' if live else 'PRACTICE (dry-run)'}  [forced dry-run for this script]")
    print(f"  Events fused    : {len(fusion_results)}")
    print(f"  Audit entries   : {entries}")
    print(f"  Audit integrity : {'OK' if audit_ok else 'FAILED'}")
    print(f"  Circuit breaker : {cb.get('state')}")
    print(f"  ROE source      : {roe.get('source')} (sign-off file: {'yes' if roe.get('signoff_present') else 'no'})")
    print(f"  Evidence pack   : {evidence.get('path')}")
    print()
    print("  What this proved:")
    print("    1. Synthetic Sentinel + Mirage alerts were ingested")
    print("    2. Fusion escalated and recommended playbooks")
    print("    3. Autonomy ran in dry-run (no live firewall changes)")
    print("    4. CMA audit chain accepted new entries")
    print("    5. Client-ready evidence pack was generated")
    print()

    ready = (
        not live
        and audit_ok
        and entries > 0
        and bool(evidence.get("ok"))
        and len(fusion_results) >= 1
    )

    if ready:
        print("*" * 60)
        print("  READY FOR PILOT REVIEW")
        print("*" * 60)
        print()
        print("  Next human steps:")
        print("    • Open the evidence ZIP / 01_Executive_Report.html with the client")
        print("    • Walk docs/PILOT_DEPLOYMENT.md on their agreed scope")
        print("    • Keep CF_CONTAINMENT_LIVE=false until signed pilot_signoff.json")
        print("    • Optional: wire WhatsApp + TLS before any live week")
        print()
        return 0

    print("!" * 60)
    print("  NOT READY — fix failures above before pilot review")
    print("!" * 60)
    print()
    return 1


def main() -> int:
    _banner("CyberFortress Pilot Dry-Run")
    print(f"  Repo   : {ROOT}")
    print(f"  Client : {CLIENT}")
    print(f"  Safety : CF_CONTAINMENT_LIVE=false (enforced for this run)")

    _step(1, "Preflight")
    try:
        from core.telemetry.fusion import TelemetryFusion  # noqa: F401
        from core.autonomy import DRY_RUN
        from core.roe import roe_status

        _ok(f"Imports OK — autonomy DRY_RUN={DRY_RUN}")
        roe = roe_status()
        _info(f"ROE: source={roe.get('source')} actions={len(roe.get('authorized_actions') or [])}")
        if not DRY_RUN:
            _fail("DRY_RUN is False — refusing to continue")
            return 2
    except Exception as e:
        _fail(f"Preflight import error: {e}")
        return 2

    _step(2, "Seed realistic telemetry events")
    events = seed_events()

    _step(3, "Fusion path (escalate + recommend + dry-run autonomy)")
    try:
        results = run_fusion(events)
    except Exception as e:
        _fail(f"Fusion failed: {e}")
        import traceback

        traceback.print_exc()
        return 3

    _step(4, "Verify CMA audit chain")
    audit_ok, entries = verify_audit()

    _step(5, "Generate evidence pack")
    try:
        evidence = make_evidence()
    except Exception as e:
        _fail(f"Evidence pack error: {e}")
        import traceback

        traceback.print_exc()
        return 5

    return print_pilot_review(results, audit_ok, entries, evidence)


if __name__ == "__main__":
    sys.exit(main())
