from core.circuit_breaker import CircuitBreaker, BreakerState


def test_trip_and_reset(tmp_path, monkeypatch):
    state = tmp_path / "breaker.json"
    from core import circuit_breaker as cb_mod
    monkeypatch.setattr(cb_mod, "STATE_FILE", state)
    b = CircuitBreaker()
    assert b.allow() is True
    b.trip("test trip")
    assert b.state == BreakerState.OPEN
    assert b.allow() is False
    assert b.allow(force=True) is True
    b.reset(by="test")
    assert b.state == BreakerState.CLOSED
    assert b.allow() is True


def test_record_trips_on_max(tmp_path, monkeypatch):
    state = tmp_path / "breaker2.json"
    from core import circuit_breaker as cb_mod
    monkeypatch.setattr(cb_mod, "STATE_FILE", state)
    monkeypatch.setattr(cb_mod, "MAX_ACTIONS", 3)
    monkeypatch.setattr(cb_mod, "MAX_TIER2", 99)
    monkeypatch.setattr(cb_mod, "MAX_CRITICAL", 99)
    b = CircuitBreaker()
    for i in range(3):
        b.record("block_ip", f"1.1.1.{i}", severity="HIGH", tier=1)
    assert b.state == BreakerState.OPEN
