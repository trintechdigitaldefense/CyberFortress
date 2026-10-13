#!/usr/bin/env bash
# CyberFortress — stop everything
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
PID_DIR="$ROOT/logs/pids"

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

rm -f logs/platform_started_at 2>/dev/null || true
echo "[+] Stopped."
