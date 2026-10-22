from core.tier2 import risk_card, status_summary
from core.autonomy import classify_action, AutonomyTier


def test_classify_tier2():
    assert classify_action("isolate_endpoint") == AutonomyTier.TIER_2_GUARDED
    assert classify_action("subnet_isolation", "subnet") == AutonomyTier.TIER_2_GUARDED


def test_risk_card():
    c = risk_card("isolate_endpoint")
    assert c["risk"] == "HIGH"
    assert "rollback" in c


def test_status_summary_shape():
    s = status_summary()
    assert s["tier"] == 2
    assert "pending_count" in s
    assert s["require_whatsapp_approve"] is True
