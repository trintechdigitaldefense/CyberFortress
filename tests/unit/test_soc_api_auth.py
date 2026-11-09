"""SOC API authentication, authorization and request-boundary tests."""

from __future__ import annotations


def test_soc_api_rejects_anonymous_by_default(monkeypatch):
    from agents.soc_api_agent import Handler

    monkeypatch.delenv("CF_SOC_USERS", raising=False)
    monkeypatch.delenv("CF_DASHBOARD_PASS", raising=False)
    monkeypatch.setenv("CF_SOC_REQUIRE_AUTH", "false")
    handler = Handler.__new__(Handler)
    handler.headers = {}
    assert handler._auth() is None


def test_soc_api_bearer_requires_configured_user(monkeypatch):
    from agents.soc_api_agent import Handler

    monkeypatch.setenv("CF_DASHBOARD_PASS", "dashboard-secret")
    monkeypatch.setenv("CF_SOC_USERS", "analyst:analyst:secret-token")
    handler = Handler.__new__(Handler)
    handler.headers = {"Authorization": "Bearer secret-token"}
    assert handler._auth() == "analyst"
    handler.headers = {"Authorization": "Bearer unknown-token"}
    assert handler._auth() is None
    handler.headers = {"Authorization": "Bearer dashboard-secret"}
    assert handler._auth() is None


def test_soc_api_route_permissions_are_explicit():
    from agents.soc_api_agent import required_permission

    assert required_permission("GET", "/api/soc/health") == "read:status"
    assert required_permission("GET", "/api/soc/playbooks") == "read:status"
    assert required_permission("GET", "/api/soc/tier2") == "read:status"
    assert required_permission("POST", "/api/soc/ingest") == "write:ingest"
    assert required_permission("POST", "/api/soc/ingest/cef") == "write:ingest"
    assert required_permission("POST", "/api/soc/unknown") is None


def test_ingest_permission_not_granted_to_viewer():
    from core.soc.rbac import authorize

    assert authorize("viewer", "write:ingest") is False
    assert authorize("analyst", "write:ingest") is True
    assert authorize("operator", "write:ingest") is True
