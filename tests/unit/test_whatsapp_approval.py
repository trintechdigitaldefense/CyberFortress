import json
import importlib
import time

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
        "request_id": rid, "nonce": nonce, "action": "isolate_endpoint", "target": "10.0.0.1", "expires_at": time.time() + 60
    }))
    wh.record_decision(rid, "APPROVE", "+18680000001", nonce)
    dec = json.loads((d / f"{rid}.decision").read_text())
    assert dec["decision"] == "APPROVE"
    assert dec["nonce_ok"] is True


def test_unknown_sender_denied(pending):
    d, gw, wh = pending
    rid = "CF-TEST-2"
    nonce = "DDEEFF"
    (d / f"{rid}.json").write_text(json.dumps({"request_id": rid, "nonce": nonce, "expires_at": time.time() + 60}))
    assert wh.record_decision(rid, "APPROVE", "+19999999999", nonce) is False
    assert not (d / f"{rid}.decision").exists()


def test_bad_nonce_denied(pending):
    d, gw, wh = pending
    rid = "CF-TEST-3"
    nonce = "112233"
    (d / f"{rid}.json").write_text(json.dumps({"request_id": rid, "nonce": nonce, "expires_at": time.time() + 60}))
    wh.record_decision(rid, "APPROVE", "+18680000001", "000000")
    dec = json.loads((d / f"{rid}.decision").read_text())
    assert dec["decision"] == "DENY-BAD-NONCE"
    assert dec["nonce_ok"] is False


def test_timeout_deny(pending, monkeypatch):
    d, gw, wh = pending
    monkeypatch.setenv("CF_APPROVAL_TIMEOUT", "1")
    importlib.reload(gw)
    ok = gw.request_approval("isolate_endpoint", "10.0.0.9", "HIGH", "test")
    assert ok is False


def test_signature_required_when_enabled(monkeypatch):
    monkeypatch.setenv("CF_WHATSAPP_ENABLED", "true")
    monkeypatch.delenv("CF_WHATSAPP_REQUIRE_SIGNATURE", raising=False)
    import importlib
    import core.defense as defense
    importlib.reload(defense)
    assert defense.whatsapp_signature_required() is True
    assert defense.verify_meta_signature("", b"{}", "") is False
    assert defense.verify_meta_signature("", b"{}", "sha256=abc") is False


def test_signature_valid(monkeypatch):
    monkeypatch.setenv("CF_WHATSAPP_ENABLED", "true")
    import importlib
    import hmac
    import hashlib
    import core.defense as defense
    importlib.reload(defense)
    secret = "app-secret"
    body = b'{"entry":[]}'
    dig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert defense.verify_meta_signature(secret, body, f"sha256={dig}") is True
    assert defense.verify_meta_signature(secret, body, "sha256=00") is False
    assert defense.verify_meta_signature(secret, body, "") is False


def test_default_verify_token_rejected_at_start(monkeypatch):
    monkeypatch.setenv("CF_WHATSAPP_ENABLED", "true")
    monkeypatch.setenv("CF_WHATSAPP_VERIFY_TOKEN", "cf_verify_token_change_me")
    monkeypatch.setenv("CF_WHATSAPP_APP_SECRET", "x")
    import importlib
    import agents.whatsapp_webhook as wh
    importlib.reload(wh)
    assert wh.VERIFY_TOKEN == "cf_verify_token_change_me"
    with pytest.raises(RuntimeError, match="VERIFY_TOKEN"):
        wh.validate_startup_config()


def test_expired_nonce_is_rejected(pending):
    d, gw, wh = pending
    rid = "CF-EXPIRED"
    (d / f"{rid}.json").write_text(json.dumps({
        "request_id": rid, "nonce": "AABBCC", "expires_at": time.time() - 1
    }))
    assert wh.record_decision(rid, "APPROVE", "+18680000001", "AABBCC") is False
    expired = json.loads((d / f"{rid}.decision").read_text())
    assert expired["decision"] == "DENY-EXPIRED"


def test_nonce_can_be_consumed_only_once(pending):
    d, gw, wh = pending
    rid = "CF-ONCE"
    (d / f"{rid}.json").write_text(json.dumps({
        "request_id": rid, "nonce": "AABBCC", "expires_at": time.time() + 60
    }))
    assert wh.record_decision(rid, "APPROVE", "+18680000001", "AABBCC") is True
    assert wh.record_decision(rid, "DENY", "+18680000001", "AABBCC") is False
    dec = json.loads((d / f"{rid}.decision").read_text())
    assert dec["decision"] == "APPROVE"
