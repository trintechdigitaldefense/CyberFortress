from core.intelligence import IntelligenceEngine
from core.capacity import limits, adaptive_interval, should_shed


def test_observe_boosts_on_repeat():
    eng = IntelligenceEngine()
    a = eng.observe(indicator="bruteforce_ssh", target="1.2.3.4", severity="HIGH", source="t", score=70)
    b = eng.observe(indicator="bruteforce_ssh", target="1.2.3.4", severity="HIGH", source="t", score=70)
    assert b["priority"] >= a["priority"]
    assert b["target_hits_in_window"] >= 2


def test_multi_signal():
    eng = IntelligenceEngine()
    for ind in ("a", "b", "c"):
        eng.observe(indicator=ind, target="9.9.9.9", severity="HIGH", source="s", score=60)
    s = eng.observe(indicator="d", target="9.9.9.9", severity="HIGH", source="s", score=60)
    assert s["multi_signal"] is True
    assert s["priority"] >= 60


def test_capacity_limits():
    L = limits()
    assert L["max_tenants_per_host"] >= 1
    assert adaptive_interval(10, 2.0) >= 10
    assert should_shed(9999, max_depth=10) is True
