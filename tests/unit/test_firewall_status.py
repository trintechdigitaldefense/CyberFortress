from core.containment.firewall import firewall_status, validate_block_target, block_ip


def test_firewall_status_returns_dict():
    st = firewall_status()
    assert "mode_label" in st
    assert "chain" in st
    assert "message" in st
    assert "max_rules" in st


def test_validate_rejects_loopback():
    v = validate_block_target("127.0.0.1")
    assert v["ok"] is False


def test_validate_rejects_private_by_default():
    v = validate_block_target("192.168.1.50")
    assert v["ok"] is False


def test_validate_accepts_public():
    v = validate_block_target("8.8.8.8")
    assert v["ok"] is True
    assert v["ip"] == "8.8.8.8"


def test_block_ip_dry_run_public():
    r = block_ip("8.8.8.8", dry_run=True)
    assert r["success"] is True
    assert r.get("verify", {}).get("skipped") is True


def test_block_ip_rejects_loopback_even_live_looking():
    r = block_ip("127.0.0.1", dry_run=False)
    assert r.get("rejected") is True or r["success"] is False


def test_validate_rejects_hostname():
    v = validate_block_target("evil.example.com")
    assert v["ok"] is False


def test_validate_rejects_ipv6_loopback():
    v = validate_block_target("::1")
    assert v["ok"] is False


def test_validate_rejects_unspecified():
    v = validate_block_target("0.0.0.0")
    assert v["ok"] is False


def test_block_live_without_roe_denied(monkeypatch):
    monkeypatch.setenv("CF_CONTAINMENT_LIVE", "true")
    monkeypatch.setenv("CF_FIREWALL_ALLOW_PRIVATE", "true")
    import core.roe as roe
    monkeypatch.setattr(roe, "is_action_authorized", lambda action: False)
    r = block_ip("8.8.8.8", dry_run=False)
    assert r.get("rejected") is True or r.get("roe_denied") is True
    assert r["success"] is False


def test_block_cidr_disabled_by_default():
    v = validate_block_target("203.0.113.0/24")
    assert v["ok"] is False
