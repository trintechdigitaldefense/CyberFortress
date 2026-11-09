"""Fail-closed tenant boundary and SOC authorization regression tests."""

from __future__ import annotations

import pytest


def test_missing_rbac_role_is_denied(monkeypatch):
    from core.soc.rbac import authorize

    monkeypatch.setenv("CF_SOC_REQUIRE_AUTH", "false")
    assert authorize(None, "read:status") is False
    assert authorize("unknown-role", "read:status") is False


def test_shared_tenant_runtime_is_rejected(tmp_path, monkeypatch):
    from core.tenant_guard import TenantError, assert_single_tenant_runtime

    root = tmp_path / "repo"
    tenants = root / "config" / "tenants"
    (tenants / "alpha").mkdir(parents=True)
    (tenants / "beta").mkdir()
    monkeypatch.setenv("CF_ROOT", str(root))
    monkeypatch.delenv("CF_TENANT_ID", raising=False)
    with pytest.raises(TenantError, match="multiple tenants"):
        assert_single_tenant_runtime()


def test_single_tenant_runtime_requires_matching_context(tmp_path, monkeypatch):
    from core.tenant_guard import TenantError, assert_single_tenant_runtime

    root = tmp_path / "repo"
    tenant = root / "config" / "tenants" / "alpha"
    tenant.mkdir(parents=True)
    monkeypatch.setenv("CF_ROOT", str(root))
    monkeypatch.delenv("CF_TENANT_ID", raising=False)
    with pytest.raises(TenantError, match="does not match"):
        assert_single_tenant_runtime()
    monkeypatch.setenv("CF_TENANT_ID", "alpha")
    assert assert_single_tenant_runtime() == "alpha"


def test_tenant_symlink_is_not_counted(tmp_path, monkeypatch):
    from core.tenant_guard import configured_tenants

    root = tmp_path / "repo"
    tenants = root / "config" / "tenants"
    tenants.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (tenants / "linked").symlink_to(outside, target_is_directory=True)
    monkeypatch.setenv("CF_ROOT", str(root))
    assert configured_tenants() == []
