"""Dashboard auth, role and CSRF gates (Phase 1)."""

from __future__ import annotations

import base64
import importlib
import os

import pytest


@pytest.fixture
def dash(monkeypatch):
    monkeypatch.setenv("CF_DASHBOARD_USER", "operator")
    monkeypatch.setenv("CF_DASHBOARD_PASS", "s3cret-pass")
    monkeypatch.setenv("CF_DASHBOARD_ROLE", "operator")
    monkeypatch.setenv("CF_DASHBOARD_BIND", "127.0.0.1")
    monkeypatch.delenv("CF_DASHBOARD_ALLOW_ANON", raising=False)
    import agents.dashboard as d

    importlib.reload(d)
    return d


class _H:
    def __init__(self, auth=None, csrf=None):
        self.headers = {}
        if auth:
            self.headers["Authorization"] = auth
        if csrf:
            self.headers["X-CF-Requested-With"] = csrf


def _basic(user, password):
    tok = base64.b64encode(f"{user}:{password}".encode()).decode()
    return f"Basic {tok}"


def test_auth_required_with_password(dash):
    assert dash._auth_required() is True
    assert dash._auth_ok(_H()) is False
    assert dash._auth_ok(_H(auth=_basic("operator", "wrong"))) is False
    assert dash._auth_ok(_H(auth=_basic("operator", "s3cret-pass"))) is True


def test_auditor_cannot_write(monkeypatch):
    monkeypatch.setenv("CF_DASHBOARD_PASS", "x")
    monkeypatch.setenv("CF_DASHBOARD_ROLE", "auditor")
    import agents.dashboard as d

    importlib.reload(d)
    assert d._can_write() is False


def test_operator_can_write(dash):
    assert dash._can_write() is True


def test_csrf_header_required_for_write_gate(dash):
    assert dash._csrf_ok(_H()) is False
    assert dash._csrf_ok(_H(csrf="CyberFortress")) is True


def test_empty_password_refuses_auth_ok(monkeypatch):
    monkeypatch.setenv("CF_DASHBOARD_PASS", "")
    monkeypatch.setenv("CF_DASHBOARD_REQUIRE_AUTH", "true")
    import agents.dashboard as d

    importlib.reload(d)
    assert d._auth_required() is True
    assert d._auth_ok(_H(auth=_basic("operator", ""))) is False
