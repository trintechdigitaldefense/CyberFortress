#!/usr/bin/env bash
# Layered readiness: software → monitoring → pilot → live containment.
# Exit 1 if software/monitoring fail, or if --require-pilot/--require-live not met.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
export CF_ROOT="$ROOT"

REQUIRE_PILOT=0
REQUIRE_LIVE=0
for arg in "$@"; do
  case "$arg" in
    --require-pilot) REQUIRE_PILOT=1 ;;
    --require-live) REQUIRE_LIVE=1 ;;
  esac
done
export REQUIRE_PILOT REQUIRE_LIVE

python3 - <<'PY'
import os, sys
from core.readiness import readiness_report

rep = readiness_report()
print("==============================================")
print(" CyberFortress readiness")
print("==============================================")
for name, layer in rep["layers"].items():
    mark = "OK " if layer["ok"] else "NO "
    print(f"  [{mark}] {name}")
    for n in layer["notes"]:
        print(f"         - {n}")
print(f"  env CF_CONTAINMENT_LIVE={rep['containment_live_env']}")
print(f"  recommended_mode={rep['recommended_mode']}")
print("==============================================")
print(" Docs: docs/PILOT_SOAK.md · docs/GO_LIVE.md · docs/LEGAL_GATE.md")

layers = rep["layers"]
if not layers["software"]["ok"] or not layers["monitoring"]["ok"]:
    sys.exit(1)
if os.environ.get("REQUIRE_PILOT") == "1" and not layers["pilot"]["ok"]:
    print("[!] --require-pilot not satisfied")
    sys.exit(1)
if os.environ.get("REQUIRE_LIVE") == "1" and not layers["live_containment"]["ok"]:
    print("[!] --require-live not satisfied")
    sys.exit(1)
sys.exit(0)
PY
