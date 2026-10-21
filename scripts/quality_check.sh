#!/usr/bin/env bash
# Fast posture + unit test gate for operators
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

echo "=============================================="
echo " CyberFortress quality check"
echo "=============================================="

bash scripts/defense_check.sh || true

echo
echo "[+] Unit tests"
python3 -m pytest tests/unit/ -q --tb=line

echo
echo "[+] Core imports"
python3 - <<'PY'
import importlib
for m in [
  "core.defense","core.ir.cases","core.ir.scoring","core.telemetry.fusion",
  "core.monitoring_metrics","core.agent_runtime","agents.ir_detect_agent",
]:
    importlib.import_module(m)
    print("  OK", m)
print("  LIVE default:", __import__("os").getenv("CF_CONTAINMENT_LIVE","false"))
PY

echo
echo "=============================================="
echo " Quality gate: unit tests green + defense posture printed above"
echo " Pilot path: docs/FIRST_PILOT.md · docs/GO_LIVE.md"
echo "=============================================="
