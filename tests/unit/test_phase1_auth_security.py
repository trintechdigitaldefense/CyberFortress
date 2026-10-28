"""Phase 1 authorization and security regression tests."""

from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path


def test_whatsapp_signature_required_when_enabled(monkeypatch):
    from core import defense

    monkeypatch.delenv("CF_WHATSAPP_REQUIRE_SIGNATURE", raising=False)
    monkeypatch.setenv("CF_WHATSAPP_ENABLED", "true")
    assert defense.whatsapp_signature_required() is True
    assert defense.verify_meta_signature("", b"{}", "") is False


def test_whatsapp_signature_valid_hmac(monkeypatch):
    from core import defense

    monkeypatch.setenv("CF_WHATSAPP_ENABLED", "true")
    secret = "app-secret"
    body = b'{"entry":[]}'
    dig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert defense.verify_meta_signature(secret, body, f"sha256={dig}") is True
    assert defense.verify_meta_signature(secret, body, "sha256=dead") is False


def test_safe_under_dir_blocks_traversal(tmp_path):
    from core.defense import safe_under_dir

    (tmp_path / "ok.txt").write_text("x")
    assert safe_under_dir(tmp_path, "ok.txt") is not None
    assert safe_under_dir(tmp_path, "../outside") is None
    assert safe_under_dir(tmp_path, "subdir/../../etc/passwd") is None


def test_dashboard_auth_required_without_anon(monkeypatch):
    monkeypatch.setenv("CF_DASHBOARD_PASS", "")
    monkeypatch.setenv("CF_DASHBOARD_ALLOW_ANON", "false")
    monkeypatch.setenv("CF_DASHBOARD_BIND", "127.0.0.1")
    import importlib
    import agents.dashboard as dash

    importlib.reload(dash)
    assert dash._auth_required() is True
    assert dash._auth_ok(type("H", (), {"headers": {}})()) is False


def test_dashboard_anon_only_with_flag(monkeypatch):
    monkeypatch.setenv("CF_DASHBOARD_PASS", "")
    monkeypatch.setenv("CF_DASHBOARD_ALLOW_ANON", "true")
    monkeypatch.setenv("CF_DASHBOARD_BIND", "127.0.0.1")
    import importlib
    import agents.dashboard as dash

    importlib.reload(dash)
    assert dash._auth_required() is False


def test_firewall_roe_denies_live_block(monkeypatch, tmp_path):
    from core.containment import firewall as fw
    import core.roe as roe

    signoff = tmp_path / "pilot_signoff.json"
    signoff.write_text(json.dumps({"authorized_actions": ["deploy_decoy"]}))
    monkeypatch.setattr(roe, "SIGNOFF_PATH", signoff)
    monkeypatch.setenv("CF_CONTAINMENT_LIVE", "true")
    r = fw.block_ip("8.8.8.8", dry_run=False)
    assert r.get("rejected") is True
    assert r.get("roe_denied") is True
    assert "not authorized" in (r.get("details") or "").lower()


def test_firewall_rejects_hostname():
    from core.containment.firewall import validate_block_target

    assert validate_block_target("evil.example.com")["ok"] is False


def test_firewall_rejects_cidr_by_default():
    from core.containment.firewall import validate_block_target

    assert validate_block_target("8.8.8.0/24")["ok"] is False


def test_decision_idempotent_and_expired(tmp_path, monkeypatch):
    import agents.whatsapp_webhook as wh

    monkeypatch.setattr(wh, "PENDING_DIR", tmp_path)
    rid = "CF-EXP"
    nonce = "AABBCC"
    (tmp_path / f"{rid}.json").write_text(
        json.dumps({"request_id": rid, "nonce": nonce, "expires_at": 1})
    )
    monkeypatch.setattr(wh, "is_allowed_approver", lambda s: True)
    wh.record_decision(rid, "APPROVE", "+18680000000", nonce)
    dec = json.loads((tmp_path / f"{rid}.decision").read_text())
    assert dec["decision"] == "DENY-EXPIRED"
    (tmp_path / f"{rid}.decision").write_text(json.dumps({"decision": "DENY-EXPIRED"}))
    wh.record_decision(rid, "APPROVE", "+18680000000", nonce)
    assert json.loads((tmp_path / f"{rid}.decision").read_text())["decision"] == "DENY-EXPIRED"
