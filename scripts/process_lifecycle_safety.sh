#!/usr/bin/env bash
# Regression test: stop.sh must not kill an unrelated process from a stale/reused PID.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
PID=""

cleanup() {
  if [[ -n "$PID" ]] && kill -0 "$PID" 2>/dev/null; then
    kill "$PID" 2>/dev/null || true
    wait "$PID" 2>/dev/null || true
  fi
  rm -rf -- "$TMP"
}
trap cleanup EXIT

mkdir -p "$TMP/logs/pids"
cp "$ROOT/stop.sh" "$TMP/stop.sh"

python3 -c 'import time; time.sleep(60)' &
PID=$!
printf '%s\n' "$PID" > "$TMP/logs/pids/dashboard.pid"

bash "$TMP/stop.sh"

if ! kill -0 "$PID" 2>/dev/null; then
  echo "FAIL: stop.sh signalled an unrelated process"
  exit 1
fi

if [[ -e "$TMP/logs/pids/dashboard.pid" ]]; then
  echo "FAIL: mismatched PID record was not safely discarded"
  exit 1
fi

if grep -nE 'pkill|fuser -k|free_port|lsof -t -iTCP|ss -lptn' "$ROOT/stop.sh"; then
  echo "FAIL: broad process/port termination found in stop.sh"
  exit 1
fi

echo "PASS: stop.sh leaves unrelated processes and listener ports untouched"
