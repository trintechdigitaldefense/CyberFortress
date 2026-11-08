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


def test_dry_run_is_not_reported_as_executed(monkeypatch):
    import core.autonomy as autonomy
    monkeypatch.setattr(autonomy, "DRY_RUN", True)
    monkeypatch.setattr(autonomy, "get_driver", lambda action, dry_run: type(
        "Driver", (), {"name": "test", "execute": lambda self, **kwargs: {
            "success": True, "dry_run": True, "details": "simulated"
        }}
    )())
    result = autonomy._perform_containment("block_ip", "192.0.2.1")
    assert result["success"] is False
    assert result["simulated"] is True


def test_unknown_containment_action_is_rejected():
    import pytest
    from core.containment.drivers import get_driver
    with pytest.raises(ValueError):
        get_driver("unknown_action", dry_run=False)


def test_force_cannot_bypass_tier2_human_approval(monkeypatch):
    import core.autonomy as autonomy
    monkeypatch.setattr(autonomy, "ALLOW_FORCE", True)
    monkeypatch.setattr(autonomy, "is_action_authorized", lambda action: True)
    monkeypatch.setattr(autonomy, "get_justification", lambda action: {"section": "test", "justification": "test"})
    monkeypatch.setattr(autonomy, "write_cma_entry", lambda *a, **k: None)
    monkeypatch.setattr(autonomy, "_perform_containment", lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not execute")))
    assert autonomy.execute_with_autonomy("isolate_endpoint", "192.0.2.2", force=True) is False
