from core.ir.cases import CaseStore
from core.ir.scoring import score_event
from core.ir.playbooks_text import investigate, recommend_action, build_incident_report


def test_score_bruteforce():
    s, c = score_event("bruteforce_ssh", "HIGH")
    assert s >= 70
    assert c in ("medium", "high")


def test_case_correlate(tmp_path, monkeypatch):
    import core.ir.cases as cases

    cases.CASE_DIR = tmp_path
    store = CaseStore()
    c = store.create(
        indicator="bruteforce_ssh", target="1.2.3.4", source="t", severity="HIGH", score=70
    )
    store.append_related(
        c, {"timestamp": "x", "action": "detection:bruteforce_ssh", "severity": "HIGH"}
    )
    c2 = store.get(c.case_id)
    assert len(c2.related_events) == 1
    assert c2.score >= 70


def test_investigate_and_report():
    findings = investigate("bruteforce_ssh", "1.2.3.4", "HIGH", "host_log", related_count=2)
    assert any("brute" in f.lower() or "auth" in f.lower() for f in findings)
    assert recommend_action("bruteforce_ssh", "HIGH") == "block_ip"
    md = build_incident_report(
        {
            "case_id": "IR-TEST",
            "title": "t",
            "status": "investigating",
            "severity": "HIGH",
            "score": 75,
            "confidence": "high",
            "detected_at": "now",
            "updated_at": "now",
            "target": "1.2.3.4",
            "indicator": "bruteforce_ssh",
            "source": "t",
            "tags": ["auth"],
            "findings": findings,
            "related_events": [],
            "actions": [],
        }
    )
    assert "IR-TEST" in md
