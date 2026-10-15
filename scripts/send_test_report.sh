#!/usr/bin/env bash
# Send one WhatsApp daily report now (for testing)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi
python3 -c "
from agents.daily_report_agent import send_once, build_report
print('--- preview ---')
print(build_report())
print('--- sending ---')
ok = send_once()
print('ok=', ok)
"
