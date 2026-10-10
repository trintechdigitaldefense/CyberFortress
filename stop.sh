#!/usr/bin/env bash
# CyberFortress — stop everything
# Usage: ./stop.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
PID_DIR="$ROOT/logs/pids"

echo "[+] Stopping CyberFortress..."

# Docker
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  docker compose -f docker/docker-compose.yml down 2>/dev/null || true
  echo "  · Docker services stopped"
fi

# Local PIDs
if [[ -d "$PID_DIR" ]]; then
  for f in "$PID_DIR"/*.pid; do
    [[ -f "$f" ]] || continue
    name=$(basename "$f" .pid)
    pid=$(cat "$f" 2>/dev/null || true)
    if [[ -n "${pid:-}" ]] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      echo "  · stopped $name (pid $pid)"
    fi
    rm -f "$f"
  done
fi

echo "[+] Stopped."
