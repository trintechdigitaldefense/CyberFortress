#!/usr/bin/env bash
# CyberFortress — stop everything
# Usage: bash stop.sh   (or ./stop.sh after chmod)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
PID_DIR="$ROOT/logs/pids"

chmod +x "$ROOT/start.sh" "$ROOT/stop.sh" "$ROOT/install.sh" 2>/dev/null || true

echo "[+] Stopping CyberFortress..."

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  if docker compose version >/dev/null 2>&1; then
    docker compose -f docker/docker-compose.yml down 2>/dev/null || true
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f docker/docker-compose.yml down 2>/dev/null || true
  fi
  echo "  · Docker services stopped (if any)"
fi

if [[ -d "$PID_DIR" ]]; then
  for f in "$PID_DIR"/*.pid; do
    [[ -f "$f" ]] || continue
    name=$(basename "$f" .pid)
    pid=$(cat "$f" 2>/dev/null || true)
    if [[ -n "${pid:-}" ]] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      sleep 0.2
      kill -9 "$pid" 2>/dev/null || true
      echo "  · stopped $name (pid $pid)"
    fi
    rm -f "$f"
  done
fi

# Free HTTP ports in case orphans remain
free_port() {
  local port="$1"
  if command -v fuser >/dev/null 2>&1; then
    fuser -k "${port}/tcp" >/dev/null 2>&1 || true
  elif command -v lsof >/dev/null 2>&1; then
    local pids
    pids=$(lsof -t -iTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
    if [[ -n "${pids:-}" ]]; then
      # shellcheck disable=SC2086
      kill $pids 2>/dev/null || true
      sleep 0.1
      # shellcheck disable=SC2086
      kill -9 $pids 2>/dev/null || true
      echo "  · freed port $port"
    fi
  fi
}
free_port 8089
free_port 8090
free_port 8091

rm -f logs/platform_started_at 2>/dev/null || true
echo "[+] Stopped."
