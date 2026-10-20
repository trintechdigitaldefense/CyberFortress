from core.tenant import tenant_id, load_tenant_settings


def test_tenant_id_empty_by_default(monkeypatch):
    monkeypatch.delenv("CF_TENANT_ID", raising=False)
    assert tenant_id() == ""


def test_example_tenant_settings(monkeypatch):
    monkeypatch.setenv("CF_TENANT_ID", "example_client")
    s = load_tenant_settings()
    assert s.get("tenant_id") == "example_client" or s.get("client_name")
