import os
from core.rules import load_pack, match_rule, resolve_playbook, pack_summary, list_available_packs


def test_default_pack_loads():
    os.environ.pop("CF_RULE_PACK", None)
    os.environ["CF_RULE_PACK_NAME"] = "default"
    pack = load_pack(force=True)
    assert pack.get("pack_id")
    assert len(pack.get("rules") or []) >= 3


def test_retail_pack():
    os.environ["CF_RULE_PACK_NAME"] = "retail"
    pack = load_pack(force=True)
    assert pack.get("pack_id") == "retail_v1"
    rule = match_rule("pos_malware_skimmer")
    assert rule is not None


def test_finance_pack():
    os.environ["CF_RULE_PACK_NAME"] = "finance"
    pack = load_pack(force=True)
    assert pack.get("pack_id") == "finance_v1"
    pb, rid, _ = resolve_playbook("business_email_compromise", "block_ip")
    assert pb == "halt_operations"


def test_smb_pack():
    os.environ["CF_RULE_PACK_NAME"] = "smb"
    pack = load_pack(force=True)
    assert pack.get("pack_id") == "smb_v1"


def test_list_packs():
    names = list_available_packs()
    assert any("retail" in n for n in names)


def test_match_decoy_default():
    os.environ["CF_RULE_PACK_NAME"] = "default"
    load_pack(force=True)
    rule = match_rule("mirage_decoy_trip")
    assert rule is not None
