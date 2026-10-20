"""Drop alert JSON → fusion process → audit chain entry."""
import json
from pathlib import Path

from core.telemetry.fusion import TelemetryFusion
from core.audit_chain import verify_chain


def test_sentinel_file_drop_to_audit(tmp_path, monkeypatch):
    tele = tmp_path / "telemetry" / "sentinel"
    tele.mkdir(parents=True)
    logs = tmp_path / "logs"
    logs.mkdir()
    audit = logs / "cma_audit.jsonl"

    monkeypatch.setenv("CF_AUDIT_PATH", str(audit))
    monkeypatch.setenv("CF_TELEMETRY_ARCHIVE", "true")
    monkeypatch.setenv("CF_CONTAINMENT_LIVE", "false")
    monkeypatch.chdir(tmp_path)

    (tmp_path / "telemetry" / "sentinel").mkdir(parents=True, exist_ok=True)
    (tmp_path / "telemetry" / "mirage").mkdir(parents=True, exist_ok=True)
    (tmp_path / "telemetry" / "local").mkdir(parents=True, exist_ok=True)

    alert = {
        "indicator": "decoy_trip",
        "target": "10.0.0.50",
        "severity": "HIGH",
        "type": "decoy",
    }
    (tmp_path / "telemetry" / "sentinel" / "test_alert.json").write_text(
        json.dumps(alert), encoding="utf-8"
    )

    from core.telemetry.adapters import SentinelAdapter
    from core.telemetry import fusion as fusion_mod

    fusion_mod.AUDIT_PATH = audit

    fus = TelemetryFusion(auto_respond=False)
    fus.register(SentinelAdapter(str(tmp_path / "telemetry" / "sentinel")))
    results = fus.process()

    assert len(results) >= 1
    assert results[0]["event"]["target"] == "10.0.0.50"
    assert audit.exists()
    ok, idx, msg = verify_chain(audit)
    assert ok, msg
