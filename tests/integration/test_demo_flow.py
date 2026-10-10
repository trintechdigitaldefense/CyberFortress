"""Headless demo flow checks (FIXES_VERIFIED / Brief 2)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def demo_env(tmp_path_factory):
    work = tmp_path_factory.mktemp("demo")
    (work / "logs").mkdir()
    (work / "evidence").mkdir()
    env = {
        "CF_CONTAINMENT_LIVE": "false",
        "CF_ALLOW_FORCE": "false",
        "CF_WHATSAPP_MOCK": "true",
        "CF_WHATSAPP_ENABLED": "false",
        "CF_WHATSAPP_ADMINS": "+18680000000",
        "CF_AUDIT_PATH": str(work / "logs" / "cma_audit.jsonl"),
        "CF_LOG_DIR": str(work / "logs"),
        "CF_BREAKER_STATE": str(work / "logs" / "breaker.json"),
    }
    return work, env


def test_escalation_from_samples(demo_env):
    work, env = demo_env
    sys.path.insert(0, str(ROOT))
    from core.telemetry.fusion import TelemetryFusion
    f = TelemetryFusion(auto_respond=False)
    results = f.process([
        {"source": "sentinel", "indicator": "reverse_shell_detected", "target": "SEC-WEB-01", "timestamp": "2026-10-10T00:00:00Z", "raw": {}},
        {"source": "mirage", "indicator": "decoy_trigger", "target": "10.0.5.12", "timestamp": "2026-10-10T00:00:01Z", "raw": {}},
    ])
    levels = {r["escalated_level"] for r in results}
    assert "HIGH" in levels


def test_tier1_dry_run_writes_cma(demo_env):
    work, env = demo_env
    os.environ.update(env)
    from agents.compliance_logger import write_cma_entry
    from core.audit_chain import verify_chain
    e = write_cma_entry("block_ip", "203.0.113.50", "test justification", severity="HIGH")
    assert e.get("entry_hash")
    assert e.get("prev_hash")
    ok, _, _ = verify_chain(Path(env["CF_AUDIT_PATH"]))
    assert ok


def test_evidence_pack_builds(demo_env):
    work, env = demo_env
    os.environ["CF_AUDIT_PATH"] = env["CF_AUDIT_PATH"]
    from core.evidence.pack import EvidencePack
    from agents.compliance_logger import write_cma_entry
    import core.evidence.pack as ep
    write_cma_entry("block_ip", "203.0.113.50", "CMA test", severity="HIGH")
    pack = EvidencePack(client_name="Demo", engagement_id="ENG-ITEST")
    pack.load_from_audit_log(env["CF_AUDIT_PATH"])
    ep.EVIDENCE_ROOT = work / "evidence"
    d = pack.build()
    assert (d / "MANIFEST.sha256").exists()


def test_mock_tier2_approve_and_timeout(demo_env):
    work, env = demo_env
    os.environ.update(env)
    os.environ["CF_WHATSAPP_PENDING_DIR"] = str(work / "logs" / "whatsapp_pending")
    os.environ["CF_APPROVAL_TIMEOUT"] = "2"
    Path(os.environ["CF_WHATSAPP_PENDING_DIR"]).mkdir(parents=True, exist_ok=True)
    import importlib
    import core.whatsapp_gateway as gw
    importlib.reload(gw)
    ok = gw.request_approval("isolate_endpoint", "10.0.0.8", "HIGH", "timeout path")
    assert ok is False
