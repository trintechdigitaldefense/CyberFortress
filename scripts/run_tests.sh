#!/usr/bin/env bash
# CyberFortress test runner
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
export CF_CONTAINMENT_LIVE=false
export CF_ALLOW_FORCE=false

echo "[+] Installing test deps if needed..."
python3 -m pip install -q -r requirements.txt 2>/dev/null || python3 -m pip install --user -q -r requirements.txt

echo "[+] Running pytest..."
python3 -m pytest tests/ -v --tb=short
echo "[+] All tests passed."
