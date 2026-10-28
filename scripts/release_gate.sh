#!/usr/bin/env bash
# Local release gate — mirrors CI blocking checks (no silent ignore).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
export CF_CONTAINMENT_LIVE=false
export CF_ALLOW_FORCE=false
export CF_ROOT="$ROOT"

echo "=============================================="
echo " CyberFortress release gate"
echo "=============================================="

echo "[1] Unit + integration tests"
python3 -m pytest tests/ -q --tb=line

echo "[2] Audit chain module self-test"
python3 - <<'PY'
from pathlib import Path
import tempfile
from core.audit_chain import append_chained, verify_chain
d = Path(tempfile.mkdtemp())
p = d / "a.jsonl"
append_chained(p, {"action": "test", "target": "1.1.1.1"})
ok, _, msg = verify_chain(p)
assert ok, msg
print("  audit chain OK")
PY

echo "[3] Readiness software/monitoring"
bash scripts/readiness_check.sh

echo "[4] Defense posture"
bash scripts/defense_check.sh

echo "[5] Version present"
test -f VERSION && echo "  VERSION=$(cat VERSION)"

echo
echo "=============================================="
echo " Release gate: PASSED (code quality)"
echo " Live containment still requires VM soak + legal sign-off"
echo "=============================================="
