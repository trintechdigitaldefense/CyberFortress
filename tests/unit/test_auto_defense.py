from core.soc.auto_defense import _choose_action


def test_choose_brute():
    assert _choose_action("bruteforce_ssh", []) == "block_ip"


def test_choose_ti():
    assert _choose_action("unknown_sig", ["threat_intel"]) == "block_ip"


def test_choose_none():
    assert _choose_action("info_heartbeat", []) is None
