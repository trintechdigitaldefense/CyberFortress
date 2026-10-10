from core.autonomy import classify_action, AutonomyTier, TIER_1_ACTIONS, TIER_2_ACTIONS


def test_tier1_block_ip():
    assert classify_action("block_ip", "single") == AutonomyTier.TIER_1_FULL


def test_tier2_isolate():
    assert classify_action("isolate_endpoint", "single") == AutonomyTier.TIER_2_GUARDED


def test_subnet_scope_forces_tier2():
    assert classify_action("block_ip", "subnet") == AutonomyTier.TIER_2_GUARDED


def test_tier_sets_disjoint():
    assert TIER_1_ACTIONS.isdisjoint(TIER_2_ACTIONS)
