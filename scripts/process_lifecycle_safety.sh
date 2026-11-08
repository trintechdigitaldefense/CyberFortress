#!/usr/bin/env bash
# Regression test: stop.sh must not kill an unrelated process from a stale/reused PID.
set -euo pipefail

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

# Preserve stop.sh's expected checkout layout: its PID directory is relative
# to the parent of the script's directory.
CHECKOUT="$TMP/repo"
mkdir -p "$CHECKOUT/logs/pids"
cp "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/stop.sh" "$CHECKOUT/stop.sh"

python3 -c 'import time; time.sleep(60)' &
PID=$!
printf '%s\n' "$PID" > "$CHECKOUT/logs/pids/dashboard.pid"

bash "$CHECKOUT/stop.sh"

if ! kill -0 "$PID" 2>/dev/null; then
  echo "FAIL: stop.sh signalled an unrelated process"
  exit 1
fi

if [[ -e "$CHECKOUT/logs/pids/dashboard.pid" ]]; then
  echo "FAIL: mismatched PID record was not safely discarded"
  exit 1
fi

if grep -nE 'pkill|fuser -k|free_port|lsof -t -iTCP|ss -lptn' "$CHECKOUT/stop.sh"; then
  echo "FAIL: broad process/port termination found in stop.sh"
  exit 1
fi

echo "PASS: stop.sh leaves unrelated processes and listener ports untouched"
