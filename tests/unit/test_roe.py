import json

from core import roe


def test_missing_signoff_denies_all_actions(tmp_path, monkeypatch):
    monkeypatch.setattr(roe, "SIGNOFF_PATH", tmp_path / "missing.json")
    assert roe.allowed_actions() == set()
    assert roe.is_action_authorized("block_ip") is False
    status = roe.roe_status()
    assert status["signoff_valid"] is False
    assert status["source"] == "deny_all"


def test_valid_signoff_allows_only_explicit_actions(tmp_path, monkeypatch):
    signoff = tmp_path / "pilot_signoff.json"
    signoff.write_text(json.dumps({"authorized_actions": ["block_ip"]}), encoding="utf-8")
    monkeypatch.setattr(roe, "SIGNOFF_PATH", signoff)
    assert roe.is_action_authorized("block_ip") is True
    assert roe.is_action_authorized("isolate_endpoint") is False


def test_invalid_signoff_denies_all_actions(tmp_path, monkeypatch):
    signoff = tmp_path / "pilot_signoff.json"
    signoff.write_text("{invalid", encoding="utf-8")
    monkeypatch.setattr(roe, "SIGNOFF_PATH", signoff)
    assert roe.allowed_actions() == set()
    assert roe.is_action_authorized("block_ip") is False


def test_empty_or_wrong_type_allowlist_denies_all(tmp_path, monkeypatch):
    signoff = tmp_path / "pilot_signoff.json"
    for payload in ({"authorized_actions": []}, {"authorized_actions": "block_ip"}, []):
        signoff.write_text(json.dumps(payload), encoding="utf-8")
        monkeypatch.setattr(roe, "SIGNOFF_PATH", signoff)
        assert roe.allowed_actions() == set()
