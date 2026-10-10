from core.roe import is_action_authorized, DEFAULT_ALLOW


def test_default_allows_block_ip():
    assert is_action_authorized("block_ip") is True


def test_unknown_action_rejected():
    assert is_action_authorized("format_disk") is False
    assert is_action_authorized("not_a_real_action") is False


def test_default_allow_nonempty():
    assert "block_ip" in DEFAULT_ALLOW
