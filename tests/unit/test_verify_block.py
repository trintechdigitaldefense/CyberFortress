from core.containment.firewall import block_ip, verify_block


def test_block_ip_dry_run_skips_verify():
    r = block_ip("8.8.8.8", dry_run=True)
    assert r["success"] is True
    assert r.get("verify", {}).get("skipped") is True


def test_verify_block_returns_dict():
    v = verify_block("8.8.8.8")
    assert "verified" in v
    assert "message" in v
