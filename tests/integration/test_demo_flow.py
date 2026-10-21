"""End-to-end demo flow checks."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def demo_env(tmp_path, monkeypatch):
    work = tmp_path
    (work / "logs").mkdir()
    (work / "evidence").mkdir()
    env = {
        "CF_CONTAINMENT_LIVE": "false",
        "CF_ALLOW_FORCE": "false",
        "CF_CMA_AUDIT_LOG": str(work / "logs" / "cma_audit.jsonl"),
        "CF_EVIDENCE_DIR": str(work / "evidence"),
        "CF_WHATSAPP_MOCK": "true",
        "CF_WHATSAPP_ADMINS": "+18683620679",
        "CF_APPROVAL_TIMEOUT": "3",
    }
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    return work, env


def test_escalation_from_samples(demo_env):
    work, env = demo_env
    sys.path.insert(0, str(ROOT))
    from core.telemetry.fusion import TelemetryFusion

    f = TelemetryFusion(auto_respond=False)
    results = f.process(
        [
            {
                "source": "sentinel",
                "indicator": "reverse_shell_detected",
                "target": "SEC-WEB-01",
                "timestamp": "2026-10-10T00:00:00Z",
                "raw": {},
            },
            {
                "source": "mirage",
                "indicator": "decoy_trigger",
                "target": "10.0.5.12",
                "timestamp": "2026-10-10T00:00:01Z",
                "raw": {},
            },
        ]
    )
    levels = {r["escalated_level"] for r in results}
    assert levels & {"HIGH", "CRITICAL"}, levels


def test_tier1_dry_run_writes_cma(demo_env):
    work, env = demo_env
    os.environ.update(env)
    from agents.compliance_logger import write_cma_entry
    from core.audit_chain import verify_chain

    e = write_cma_entry("block_ip", "203.0.113.50", "test justification", severity="HIGH")
    assert e.get("entry_hash")
    ok, msg, _ = verify_chain(env["CF_CMA_AUDIT_LOG"])
    assert ok, msg


def test_evidence_pack_builds(demo_env):
    work, env = demo_env
    os.environ.update(env)
    from agents.compliance_logger import write_cma_entry
    from core.evidence.pack import generate_evidence_pack

    write_cma_entry("block_ip", "203.0.113.50", "CMA test", severity="HIGH")
    result = generate_evidence_pack(client_name="Demo", engagement_id="ENG-TEST")
    assert result.get("ok") is True or result.get("path") or Path(result.get("zip", "")).exists()


def test_mock_tier2_approve_and_timeout(demo_env):
    work, env = demo_env
    os.environ.update(env)
    from core import whatsapp_gateway as gw

    ok = gw.request_approval("isolate_endpoint", "10.0.0.8", "HIGH", "timeout path")
    assert ok is False
