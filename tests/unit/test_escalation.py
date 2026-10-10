from core import escalation as esc
from core.escalation import ingest_event, recommend_playbook, AlertLevel


def setup_function():
    esc._recent_events.clear()


def test_reverse_shell_is_high():
    level = ingest_event("sentinel", "reverse_shell_detected", "SEC-WEB-01")
    assert level == AlertLevel.HIGH
    assert recommend_playbook(level, "reverse_shell_detected") == "block_ip"


def test_exfil_is_critical():
    level = ingest_event("sentinel", "data_exfil_attempt", "DB-01")
    assert level == AlertLevel.CRITICAL


def test_decoy_is_high():
    level = ingest_event("mirage", "decoy_trigger", "10.0.5.12")
    assert level == AlertLevel.HIGH


def test_low_default():
    level = ingest_event("local", "policy_notice", "host-1")
    assert level == AlertLevel.LOW
