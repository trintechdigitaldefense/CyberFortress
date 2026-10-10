import json
import importlib

import pytest


@pytest.fixture
def pending(tmp_path, monkeypatch):
    d = tmp_path / "pending"
    d.mkdir()
    monkeypatch.setenv("CF_WHATSAPP_PENDING_DIR", str(d))
    monkeypatch.setenv("CF_WHATSAPP_ADMINS", "+18680000001")
    monkeypatch.setenv("CF_WHATSAPP_MOCK", "true")
    monkeypatch.setenv("CF_WHATSAPP_ENABLED", "false")
    monkeypatch.setenv("CF_APPROVAL_TIMEOUT", "5")
    monkeypatch.setenv("CF_AUDIT_PATH", str(tmp_path / "audit.jsonl"))
    import core.whatsapp_gateway as gw
    import agents.whatsapp_webhook as wh
    importlib.reload(gw)
    importlib.reload(wh)
    return d, gw, wh


def test_valid_admin_nonce_approves(pending):
    d, gw, wh = pending
    rid = "CF-TEST-1"
    nonce = "AABBCC"
    (d / f"{rid}.json").write_text(json.dumps({
        "request_id": rid, "nonce": nonce, "action": "isolate_endpoint", "target": "10.0.0.1"
    }))
    wh.record_decision(rid, "APPROVE", "+18680000001", nonce)
    dec = json.loads((d / f"{rid}.decision").read_text())
    assert dec["decision"] == "APPROVE"
    assert dec["nonce_ok"] is True


def test_unknown_sender_denied(pending):
    d, gw, wh = pending
    rid = "CF-TEST-2"
    nonce = "DDEEFF"
    (d / f"{rid}.json").write_text(json.dumps({"request_id": rid, "nonce": nonce}))
    wh.record_decision(rid, "APPROVE", "+19999999999", nonce)
    dec = json.loads((d / f"{rid}.decision").read_text())
    assert dec["decision"] == "DENY-UNKNOWN-SENDER"


def test_bad_nonce_denied(pending):
    d, gw, wh = pending
    rid = "CF-TEST-3"
    nonce = "112233"
    (d / f"{rid}.json").write_text(json.dumps({"request_id": rid, "nonce": nonce}))
    wh.record_decision(rid, "APPROVE", "+18680000001", "000000")
    dec = json.loads((d / f"{rid}.decision").read_text())
    assert dec["decision"] == "DENY-BAD-NONCE"
    assert dec["nonce_ok"] is False


def test_timeout_deny(pending, monkeypatch):
    d, gw, wh = pending
    monkeypatch.setenv("CF_APPROVAL_TIMEOUT", "1")
    import core.whatsapp_gateway as gw
    importlib.reload(gw)
    ok = gw.request_approval("isolate_endpoint", "10.0.0.9", "HIGH", "test")
    assert ok is False
