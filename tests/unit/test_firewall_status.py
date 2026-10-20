from core.containment.firewall import firewall_status


def test_firewall_status_returns_dict():
    st = firewall_status()
    assert "mode_label" in st
    assert "chain" in st
    assert "message" in st
