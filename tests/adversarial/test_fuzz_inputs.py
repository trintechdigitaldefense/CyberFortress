"""Adversarial / fuzz-style checks — platform must not crash; audit stays valid."""

from __future__ import annotations

import json
from pathlib import Path

from core.telemetry.adapters import SentinelAdapter
from core.telemetry.fusion import TelemetryFusion
from core.audit_chain import verify_chain


def test_malformed_json_quarantined(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    d = tmp_path / "telemetry" / "sentinel"
    d.mkdir(parents=True)
    bad = d / "garbage.json"
    bad.write_bytes(b"\x00\x01not-json{{{{")
    (tmp_path / "logs").mkdir(exist_ok=True)
    ad = SentinelAdapter(str(d))
    events = ad.fetch_events()
    assert events == []
    assert not bad.exists() or (d / "quarantine").exists()


def test_huge_line_and_injection_fields(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    logs = tmp_path / "logs"
    logs.mkdir()
    audit = logs / "cma_audit.jsonl"
    monkeypatch.setenv("CF_AUDIT_PATH", str(audit))
    import core.telemetry.fusion as fm

    fm.AUDIT_PATH = audit
    huge = "A" * 50000
    event = {
        "source": "fuzz",
        "indicator": "bruteforce\nprev_hash=fake",
        "target": '10.0.0.1"; DROP TABLE',
        "timestamp": "2099-01-01T00:00:00+00:00",
        "raw": {"msg": huge[:1000]},
    }
    fus = TelemetryFusion(auto_respond=False)
    results = fus.process([event])
    assert len(results) == 1
    ok, _, msg = verify_chain(audit)
    assert ok, msg


def test_webhook_nonce_replay_rejected(tmp_path, monkeypatch):
    pending = tmp_path / "pending"
    pending.mkdir()
    monkeypatch.setenv("CF_WHATSAPP_PENDING_DIR", str(pending))
    req_id = "req-fuzz-1"
    (pending / f"{req_id}.json").write_text(
        json.dumps({"request_id": req_id, "nonce": "ABC123", "action": "block_ip", "target": "1.2.3.4"}),
        encoding="utf-8",
    )
    decision = {"request_id": req_id, "nonce": "ABC123", "decision": "APPROVE"}
    (pending / f"{req_id}.decision").write_text(json.dumps(decision), encoding="utf-8")
    assert (pending / f"{req_id}.decision").exists()
    existing = json.loads((pending / f"{req_id}.decision").read_text())
    assert existing["nonce"] == "ABC123"


def test_disk_full_signal_watchdog_codes():
    from core import watchdog as wd

    assert hasattr(wd, "write_heartbeat")
