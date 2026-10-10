#!/usr/bin/env python3
"""Recompute CMA audit hash chain; exit 1 on first break."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.audit_chain import verify_chain


def main():
    p = argparse.ArgumentParser(description="Verify CyberFortress CMA audit chain")
    p.add_argument(
        "--path",
        default=str(Path(os.environ.get("CF_AUDIT_PATH", "./logs/cma_audit.jsonl"))),
        help="Path to cma_audit.jsonl",
    )
    args = p.parse_args()
    path = Path(args.path)
    ok, idx, msg = verify_chain(path)
    if ok:
        print(f"[OK] {msg} ({path})")
        return 0
    print(f"[FAIL] {msg} ({path})")
    if idx is not None:
        print(f"       first broken index: {idx}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
