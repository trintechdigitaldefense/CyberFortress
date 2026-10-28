#!/usr/bin/env bash
# Phase 9 — compliance / legal readiness check (operational, not legal advice).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
export CF_ROOT="$ROOT"

python3 - <<'PY'
import sys
from core.compliance_pack import build_compliance_report, write_compliance_report

rep = build_compliance_report()
path = write_compliance_report()
print("==============================================")
print(" CyberFortress compliance readiness")
print(" NOT LEGAL ADVICE — counsel must review")
print("==============================================")
print(f" Report: {path}")
ch = rep["checklist"]
for k, v in ch["items"].items():
    print(f"  [{'OK' if v else 'NO'}] {k}")
if ch["missing"]:
    print(" Missing:", ", ".join(ch["missing"]))
print(f" ready_for_live_consideration={ch['ready_for_live_consideration']}")
print(f" containment_default_safe={ch['items'].get('containment_live_env_false')}")
print(" Templates: docs/LEGAL_GATE.md · NDA/ROE under docs/templates/")
print("==============================================")
if not rep["readiness"]["layers"]["software"]["ok"]:
    sys.exit(1)
sys.exit(0)
PY
