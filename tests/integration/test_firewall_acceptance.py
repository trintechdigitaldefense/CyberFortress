"""Firewall containment acceptance tests using mocked host commands only."""

import json
import subprocess

from core.containment import firewall as fw
from core.roe import SIGNOFF_PATH


def _signoff(tmp_path, monkeypatch, actions):
    path = tmp_path / "pilot_signoff.json"
    path.write_text(json.dumps({"authorized_actions": actions}), encoding="utf-8")
    monkeypatch.setattr("core.roe.SIGNOFF_PATH", path)
    return path


def test_live_block_requires_exact_client_roe(tmp_path, monkeypatch):
    _signoff(tmp_path, monkeypatch, ["isolate_endpoint"])
    monkeypatch.setattr(fw, "_live", lambda: True)
    monkeypatch.setattr(fw, "_iptables_bin", lambda: "iptables")
    monkeypatch.setattr(fw, "ensure_chain", lambda **kwargs: {"ok": True})
    monkeypatch.setattr(fw, "_already_blocked", lambda target: False)
    monkeypatch.setattr(fw, "_run_block", lambda cmd, dry_run: subprocess.CompletedProcess(cmd, 0, b"", b""))
    monkeypatch.setattr(fw, "verify_block", lambda target: {
        "verified": True, "bidirectional": True, "matching_rules": []
    })

    allowed = fw.block_ip("8.8.8.8", dry_run=False, roe_action="isolate_endpoint")
    denied = fw.block_ip("8.8.4.4", dry_run=False, roe_action="block_ip")
    assert allowed["success"] is True
    assert allowed["verify"]["bidirectional"] is True
    assert denied["success"] is False
    assert denied["roe_denied"] is True


def test_live_block_rolls_back_partial_insert(tmp_path, monkeypatch):
    _signoff(tmp_path, monkeypatch, ["block_ip"])
    monkeypatch.setattr(fw, "_live", lambda: True)
    monkeypatch.setattr(fw, "_iptables_bin", lambda: "iptables")
    monkeypatch.setattr(fw, "ensure_chain", lambda **kwargs: {"ok": True})
    monkeypatch.setattr(fw, "_already_blocked", lambda target: False)
    calls = []

    def run(cmd, dry_run):
        calls.append(cmd)
        code = 0 if len(calls) == 1 else 1
        return subprocess.CompletedProcess(cmd, code, b"", b"simulated failure")

    monkeypatch.setattr(fw, "_run_block", run)
    result = fw.block_ip("8.8.8.8", dry_run=False)
    assert result["success"] is False
    assert result["rollback_attempted"] is True
    assert len(calls) == 3
    assert calls[2][1] == "-D"


def test_live_rollback_requires_roe_and_readback(tmp_path, monkeypatch):
    _signoff(tmp_path, monkeypatch, ["unblock_ip"])
    monkeypatch.setattr(fw, "_live", lambda: True)
    monkeypatch.setattr(fw, "_iptables_bin", lambda: "iptables")
    monkeypatch.setattr(fw, "_run_block", lambda cmd, dry_run: subprocess.CompletedProcess(cmd, 0, b"", b""))
    monkeypatch.setattr(fw, "_run_read", lambda cmd: subprocess.CompletedProcess(cmd, 0, b"Chain CF_BLOCK (0 references)\n", b""))
    monkeypatch.setattr(fw, "_already_blocked", lambda target: False)

    result = fw.unblock_ip("8.8.8.8", dry_run=False)
    assert result["success"] is True
    assert result["verify"]["cleared"] is True


def test_live_rollback_fails_if_firewall_readback_fails(tmp_path, monkeypatch):
    _signoff(tmp_path, monkeypatch, ["unblock_ip"])
    monkeypatch.setattr(fw, "_live", lambda: True)
    monkeypatch.setattr(fw, "_iptables_bin", lambda: "iptables")
    monkeypatch.setattr(fw, "_run_block", lambda cmd, dry_run: subprocess.CompletedProcess(cmd, 0, b"", b""))
    monkeypatch.setattr(fw, "_run_read", lambda cmd: subprocess.CompletedProcess(cmd, 1, b"", b"permission denied"))
    result = fw.unblock_ip("8.8.8.8", dry_run=False)
    assert result["success"] is False
    assert result["verify"]["cleared"] is False
