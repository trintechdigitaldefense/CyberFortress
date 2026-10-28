"""Regression tests for metrics lock + persistence (P0 deadlock fix)."""

from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import core.monitoring_metrics as metrics


def _reset(tmp_path: Path) -> None:
    metrics._PATH = tmp_path / "monitoring_metrics.json"
    metrics._COUNTS.clear()
    metrics._ADAPTER_STATS.clear()
    metrics._RECENT.clear()
    metrics._LAST_DETECTION = None
    metrics._PERSIST_FAILS = 0
    metrics._LAST_PERSIST_ERROR = None


def test_record_events_completes_bounded(tmp_path):
    _reset(tmp_path)
    done = threading.Event()

    def run():
        metrics.record_events(
            [{"source": "t", "indicator": "bruteforce", "target": "1.2.3.4", "severity": "HIGH"}]
        )
        done.set()

    t = threading.Thread(target=run)
    t.start()
    t.join(timeout=3.0)
    assert not t.is_alive(), "record_events deadlocked (did not finish within 3s)"
    assert done.is_set()
    snap = metrics.snapshot()
    assert snap["total_events"] == 1
    assert metrics._PATH.exists()
    data = json.loads(metrics._PATH.read_text())
    assert data["total_events"] == 1


def test_adapter_error_persists(tmp_path):
    _reset(tmp_path)
    metrics.record_adapter_error("syslog", "connection refused")
    snap = metrics.snapshot()
    assert snap["adapters"]["syslog"]["errors"] == 1
    disk = json.loads(metrics._PATH.read_text())
    assert disk["adapters"]["syslog"]["errors"] == 1


def test_concurrent_writes_valid_json(tmp_path):
    _reset(tmp_path)

    def worker(i: int):
        metrics.record_events(
            [{"source": f"s{i % 3}", "indicator": f"ind{i}", "target": f"10.0.0.{i % 250}"}]
        )

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(worker, i) for i in range(40)]
        for f in as_completed(futs, timeout=15):
            f.result(timeout=5)

    raw = metrics._PATH.read_text()
    data = json.loads(raw)
    assert data["total_events"] == 40
    snap = metrics.snapshot()
    assert snap["total_events"] == 40


def test_failed_disk_write_no_deadlock(tmp_path, monkeypatch):
    _reset(tmp_path)

    def boom(*_a, **_k):
        raise OSError("disk full")

    monkeypatch.setattr(metrics.os, "replace", boom)
    t0 = time.monotonic()
    metrics.record_events([{"source": "x", "indicator": "y"}])
    assert time.monotonic() - t0 < 3.0
    assert metrics.snapshot()["total_events"] == 1
    assert metrics.snapshot()["persist_fails"] >= 1
