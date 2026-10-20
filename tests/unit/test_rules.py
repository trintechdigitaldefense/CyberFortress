from core.rules import load_pack, match_rule, resolve_playbook, pack_summary


def test_default_pack_loads():
    pack = load_pack(force=True)
    assert pack.get("pack_id")
    assert len(pack.get("rules") or []) >= 3


def test_match_decoy():
    rule = match_rule("mirage_decoy_trip")
    assert rule is not None
    assert rule["id"] == "CF-R001"


def test_resolve_playbook_ransomware():
    pb, rid, pid = resolve_playbook("ransomware_encryption", "block_ip")
    assert pb == "halt_operations"
    assert rid == "CF-R005"


def test_pack_summary():
    s = pack_summary()
    assert s["rule_count"] >= 1
