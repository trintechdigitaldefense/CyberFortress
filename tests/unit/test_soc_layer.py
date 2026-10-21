from core.soc.event_bus import EventBus
from core.soc.siem import normalize_event, parse_cef
from core.soc.playbooks import match_playbook
from core.soc.rbac import authorize
from core.soc.metrics import prometheus_text
from core.soc.ha import try_become_leader


def test_bus_publish_consume():
    bus = EventBus(maxsize=10)
    assert bus.publish({"a": 1})
    assert len(bus.consume(5)) == 1


def test_normalize_and_cef():
    e = normalize_event({"src_ip": "1.2.3.4", "indicator": "scan", "severity": "high"})
    assert e["target"] == "1.2.3.4"
    assert e["severity"] == "HIGH"
    p = parse_cef("CEF:0|Vendor|Prod|1.0|100|PortScan|7|src=9.9.9.9 dst=1.1.1.1")
    assert p is not None


def test_playbook_match():
    pbs = [
        {
            "name": "t",
            "when": {"severity_in": ["HIGH"], "indicator_contains": ["brute"]},
            "actions": [{"action": "block_ip"}],
        }
    ]
    assert len(match_playbook({"severity": "HIGH", "indicator": "bruteforce_ssh", "score": 70}, pbs)) == 1


def test_rbac_metrics_ha():
    assert authorize("viewer", "read:status")
    assert not authorize("viewer", "write:containment")
    assert "cf_up" in prometheus_text()
    assert "leader" in try_become_leader()
