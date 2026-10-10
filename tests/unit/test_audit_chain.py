import json
from core.audit_chain import append_chained, verify_chain


def test_chain_valid_after_appends(tmp_path):
    p = tmp_path / "a.jsonl"
    append_chained(p, {"action": "block_ip", "target": "1.1.1.1"})
    append_chained(p, {"action": "unblock_ip", "target": "1.1.1.1"})
    ok, idx, msg = verify_chain(p)
    assert ok is True
    assert idx is None


def test_tamper_detected(tmp_path):
    p = tmp_path / "b.jsonl"
    append_chained(p, {"action": "block_ip", "target": "1.1.1.1"})
    append_chained(p, {"action": "unblock_ip", "target": "1.1.1.1"})
    lines = p.read_text().splitlines()
    o = json.loads(lines[0])
    o["target"] = "EVIL"
    lines[0] = json.dumps(o)
    p.write_text("\n".join(lines) + "\n")
    ok, idx, msg = verify_chain(p)
    assert ok is False
    assert idx == 0
