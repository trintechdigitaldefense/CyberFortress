#!/usr/bin/env bash
# CyberFortress — stop everything
# Usage: bash stop.sh
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
      sleep 0.15
      kill -9 "$pid" 2>/dev/null || true
      echo "  · stopped $name (pid $pid)"
    fi
    rm -f "$f"
  done
fi

kill_module() {
  local mod="$1"
  if command -v pkill >/dev/null 2>&1; then
    if pkill -f "python3? -m ${mod}" 2>/dev/null; then
      echo "  · pkill ${mod}"
    fi
  elif command -v pgrep >/dev/null 2>&1; then
    local pids
    pids=$(pgrep -f "python3? -m ${mod}" 2>/dev/null || true)
    if [[ -n "${pids:-}" ]]; then
      # shellcheck disable=SC2086
      kill $pids 2>/dev/null || true
      sleep 0.15
      # shellcheck disable=SC2086
      kill -9 $pids 2>/dev/null || true
      echo "  · killed orphan ${mod}"
    fi
  fi
}

kill_module "agents.dashboard"
kill_module "agents.healthcheck"
kill_module "agents.whatsapp_webhook"
kill_module "agents.threat_hunting_agent"
kill_module "agents.telemetry_fusion_agent"
kill_module "agents.compliance_logger"
kill_module "agents.watchdog_agent"
kill_module "agents.firewall_agent"
kill_module "agents.daily_report_agent"
kill_module "agents.weekly_evidence_agent"
sleep 0.3

free_port() {
  local port="$1"
  if command -v fuser >/dev/null 2>&1; then
    if fuser "${port}/tcp" >/dev/null 2>&1; then
      fuser -k "${port}/tcp" >/dev/null 2>&1 || true
      echo "  · freed port $port (fuser)"
    fi
  fi
  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids=$(lsof -t -iTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
    if [[ -n "${pids:-}" ]]; then
      # shellcheck disable=SC2086
      kill $pids 2>/dev/null || true
      sleep 0.1
      # shellcheck disable=SC2086
      kill -9 $pids 2>/dev/null || true
      echo "  · freed port $port (lsof)"
    fi
  fi
  if command -v ss >/dev/null 2>&1; then
    local pids
    pids=$(ss -lptn "sport = :$port" 2>/dev/null | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | sort -u)
    if [[ -n "${pids:-}" ]]; then
      # shellcheck disable=SC2086
      kill $pids 2>/dev/null || true
      sleep 0.1
      # shellcheck disable=SC2086
      kill -9 $pids 2>/dev/null || true
      echo "  · freed port $port (ss)"
    fi
  fi
}
free_port 8089
free_port 8090
free_port 8091

rm -f logs/platform_started_at 2>/dev/null || true
echo "[+] Stopped."
