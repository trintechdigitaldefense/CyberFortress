"""Audit chain integrity and fail-closed behaviour."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest

from core.audit_chain import (
    AuditChainError,
    append_chained,
    hash_entry,
    load_entries,
    verify_chain,
)


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


def test_malformed_line_fails_verify(tmp_path):
    p = tmp_path / "c.jsonl"
    append_chained(p, {"action": "block_ip", "target": "1.1.1.1"})
    with open(p, "a", encoding="utf-8") as f:
        f.write("{not-json\n")
    ok, idx, msg = verify_chain(p)
    assert ok is False
    assert "invalid JSON" in msg


def test_malformed_line_blocks_append(tmp_path):
    p = tmp_path / "d.jsonl"
    append_chained(p, {"action": "block_ip", "target": "1.1.1.1"})
    with open(p, "a", encoding="utf-8") as f:
        f.write("CORRUPT\n")
    with pytest.raises(AuditChainError):
        append_chained(p, {"action": "unblock_ip", "target": "1.1.1.1"})


def test_deleted_middle_entry_breaks_chain(tmp_path):
    p = tmp_path / "e.jsonl"
    append_chained(p, {"action": "a", "target": "1"})
    append_chained(p, {"action": "b", "target": "2"})
    append_chained(p, {"action": "c", "target": "3"})
    lines = p.read_text().splitlines()
    p.write_text(lines[0] + "\n" + lines[2] + "\n")
    ok, idx, msg = verify_chain(p)
    assert ok is False


def test_concurrent_appends_remain_valid(tmp_path):
    p = tmp_path / "f.jsonl"

    def worker(i: int):
        append_chained(p, {"action": "block_ip", "target": f"10.0.0.{i}", "n": i})

    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = [ex.submit(worker, i) for i in range(24)]
        for f in as_completed(futs, timeout=20):
            f.result(timeout=10)

    ok, idx, msg = verify_chain(p)
    assert ok is True, msg
    entries = load_entries(p)
    assert len(entries) == 24


def test_prev_hash_links(tmp_path):
    p = tmp_path / "g.jsonl"
    e1 = append_chained(p, {"action": "x", "target": "1"})
    e2 = append_chained(p, {"action": "y", "target": "2"})
    assert e1["prev_hash"] == "0" * 64
    assert e2["prev_hash"] == e1["entry_hash"]
    assert e2["entry_hash"] == hash_entry(e2)
