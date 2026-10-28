"""Secrets rotation helpers + SIEM ingest auth / tenant strip."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from core.secrets_mgmt import (
    check_env_permissions,
    generate_token,
    redact,
    rotate_env_keys,
    write_secret_file,
)
from core.soc.siem import ingest_batch, require_ingest_token, sanitize_ingest_event


def test_generate_and_redact():
    t = generate_token(16)
    assert len(t) > 10
    assert "***" in redact(t) or "…" in redact(t)


def test_rotate_env(tmp_path):
    env = tmp_path / ".env"
    env.write_text("CF_DASHBOARD_PASS=oldpass\nCF_OTHER=keep\n")
    updated = rotate_env_keys(env, ["CF_DASHBOARD_PASS"])
    assert "CF_DASHBOARD_PASS" in updated
    assert updated["CF_DASHBOARD_PASS"] != "oldpass"
    text = env.read_text()
    assert "CF_OTHER=keep" in text
    assert "oldpass" not in text
    assert (tmp_path / ".env.bak").exists()


def test_secret_file_perms(tmp_path, monkeypatch):
    monkeypatch.setenv("CF_SECRETS_DIR", str(tmp_path / "sec"))
    path = write_secret_file("dash_pass", "super-secret-value")
    assert path.is_file()
    assert "super-secret-value" in path.read_text()


def test_siem_token_required(monkeypatch):
    monkeypatch.setenv("CF_SIEM_INGEST_TOKEN", "ingest-secret")
    assert require_ingest_token("ingest-secret") is True
    assert require_ingest_token("wrong") is False
    with pytest.raises(PermissionError):
        ingest_batch([{"indicator": "x", "target": "1.1.1.1"}], token="wrong")


def test_siem_strips_spoofed_tenant(monkeypatch):
    monkeypatch.setenv("CF_TENANT_ID", "alpha")
    monkeypatch.delenv("CF_SIEM_INGEST_TOKEN", raising=False)
    monkeypatch.setenv("CF_SIEM_REQUIRE_TOKEN", "false")
    clean = sanitize_ingest_event({"indicator": "x", "target": "1.1.1.1", "tenant_id": "evil"})
    assert clean.get("tenant_id") == "alpha"
    assert clean.get("tenant_id") != "evil"


def test_env_perms(tmp_path):
    env = tmp_path / ".env"
    env.write_text("X=1\n")
    os.chmod(env, 0o600)
    ok, msg = check_env_permissions(env)
    assert ok is True
