"""IR case store: path safety, transitions, tenant isolation."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.ir.cases import CaseStore, validate_case_id


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.delenv("CF_TENANT_ID", raising=False)
    monkeypatch.setenv("CF_IR_CASE_DIR", str(tmp_path / "cases"))
    return CaseStore(tmp_path / "cases")


def test_create_and_get(store):
    c = store.create(indicator="bruteforce", target="8.8.8.8", source="lab", severity="HIGH")
    got = store.get(c.case_id)
    assert got is not None
    assert got.indicator == "bruteforce"
    assert got.status == "open"


def test_reject_path_traversal_case_id(store):
    with pytest.raises(ValueError):
        validate_case_id("../etc/passwd")
    with pytest.raises(ValueError):
        validate_case_id("IR-20260101-abc/../../x")


def test_transition_valid(store):
    c = store.create(indicator="x", target="1.2.3.4", source="t", severity="MEDIUM")
    c = store.transition(c, "investigating", changed_by="analyst")
    assert c.status == "investigating"
    c = store.transition(c, "closed", changed_by="analyst", reason="fp")
    assert c.status == "closed"
    assert c.closed_at


def test_transition_invalid(store):
    c = store.create(indicator="x", target="1.2.3.4", source="t", severity="LOW")
    with pytest.raises(ValueError):
        store.transition(c, "not_a_real_status")
    c = store.transition(c, "closed", reason="done")
    with pytest.raises(ValueError):
        store.transition(c, "open")  # closed is terminal


def test_cross_tenant_denied(tmp_path, monkeypatch):
    d = tmp_path / "cases"
    monkeypatch.setenv("CF_IR_CASE_DIR", str(d))
    monkeypatch.setenv("CF_TENANT_ID", "alpha")
    a = CaseStore(d)
    ca = a.create(indicator="phish", target="9.9.9.9", source="a", severity="HIGH")
    assert ca.tenant_id == "alpha"

    monkeypatch.setenv("CF_TENANT_ID", "beta")
    b = CaseStore(d)
    assert b.get(ca.case_id) is None
    assert all(x.case_id != ca.case_id for x in b.list_open())


def test_atomic_write_readable(store):
    c = store.create(indicator="scan", target="1.1.1.1", source="n", severity="INFO")
    path = Path(store._dir) / f"{c.case_id}.json"
    assert path.is_file()
    text = path.read_text()
    assert c.case_id in text
