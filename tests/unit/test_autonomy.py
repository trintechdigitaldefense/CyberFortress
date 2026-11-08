from core.autonomy import classify_action, AutonomyTier, TIER_1_ACTIONS, TIER_2_ACTIONS


def test_tier1_block_ip():
    assert classify_action("block_ip", "single") == AutonomyTier.TIER_1_FULL


def test_tier2_isolate():
    assert classify_action("isolate_endpoint", "single") == AutonomyTier.TIER_2_GUARDED


def test_subnet_scope_forces_tier2():
    assert classify_action("block_ip", "subnet") == AutonomyTier.TIER_2_GUARDED


def test_tier_sets_disjoint():
    assert TIER_1_ACTIONS.isdisjoint(TIER_2_ACTIONS)


def test_tier1_returns_false_when_driver_fails(monkeypatch):
    import core.autonomy as autonomy

    monkeypatch.setattr(autonomy, "is_action_authorized", lambda action: True)
    monkeypatch.setattr(autonomy.breaker, "allow", lambda force=False: True)
    monkeypatch.setattr(autonomy, "get_justification", lambda action: {"section": "test", "justification": "test"})
    monkeypatch.setattr(autonomy, "write_cma_entry", lambda *a, **k: None)
    monkeypatch.setattr(autonomy, "notify_tier1", lambda *a, **k: None)
    monkeypatch.setattr(autonomy, "_perform_containment", lambda *a, **k: {"success": False, "details": "driver error"})
    assert autonomy.execute_with_autonomy("block_ip", "192.0.2.1") is False


def test_tier1_returns_true_only_after_driver_success(monkeypatch):
    import core.autonomy as autonomy

    monkeypatch.setattr(autonomy, "is_action_authorized", lambda action: True)
    monkeypatch.setattr(autonomy.breaker, "allow", lambda force=False: True)
    monkeypatch.setattr(autonomy, "get_justification", lambda action: {"section": "test", "justification": "test"})
    monkeypatch.setattr(autonomy, "write_cma_entry", lambda *a, **k: None)
    monkeypatch.setattr(autonomy, "notify_tier1", lambda *a, **k: None)
    monkeypatch.setattr(autonomy, "_perform_containment", lambda *a, **k: {"success": True, "details": "verified"})
    monkeypatch.setattr(autonomy.breaker, "record", lambda *a, **k: None)
    assert autonomy.execute_with_autonomy("block_ip", "192.0.2.1") is True
