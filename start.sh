#!/usr/bin/env bash
# CyberFortress — start everything
# Usage: bash start.sh [local|docker|status]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
PID_DIR="$ROOT/logs/pids"
mkdir -p "$PID_DIR" logs evidence secrets telemetry/sentinel telemetry/mirage logs/whatsapp_pending logs/heartbeats logs/ir_cases evidence/ir_reports

chmod +x "$ROOT/start.sh" "$ROOT/stop.sh" "$ROOT/install.sh" 2>/dev/null || true

MODE="${1:-auto}"

live_flag() {
  if [[ -f .env ]]; then
    # shellcheck disable=SC1091
    set -a; source .env 2>/dev/null || true; set +a
  fi
  echo "${CF_CONTAINMENT_LIVE:-false}"
}

print_urls() {
  echo
  echo "  Dashboard : http://127.0.0.1:8091"
  echo "  Health    : http://127.0.0.1:8090"
  echo "  Webhook   : http://127.0.0.1:8089  (put TLS in front for Meta)"
  echo
  echo "  Firewall: agent starts with platform (CF_BLOCK chain)"
  echo "  Containment LIVE=$(live_flag) (DROP rules only when armed)"
  echo "  Logs:   tail -f logs/*.out"
  echo "  Stop:   bash stop.sh"
  echo "  Status: bash start.sh status"
}

status_local() {
  echo "CyberFortress local process status:"
  if [[ -d "$PID_DIR" ]]; then
    for f in "$PID_DIR"/*.pid; do
      [[ -e "$f" ]] || continue
      name=$(basename "$f" .pid)
      pid=$(cat "$f" 2>/dev/null || true)
      if [[ -n "${pid:-}" ]] && kill -0 "$pid" 2>/dev/null; then
        echo "  [UP]   $name  pid=$pid"
      else
        echo "  [DOWN] $name  (stale pid ${pid:-none})"
      fi
    done
  fi
  if command -v docker >/dev/null 2>&1; then
    if docker info >/dev/null 2>&1; then
      echo "Docker daemon is up."
    else
      echo "Docker CLI present but daemon is down."
    fi
  fi
}

start_local() {
  echo "[+] Starting CyberFortress locally (no Docker)..."
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
  if [[ -f .env ]]; then
    set -a; source .env 2>/dev/null || true; set +a
  fi

  start_bg() {
    local name="$1"; shift
    local log="$ROOT/logs/${name}.out"
    nohup "$@" >"$log" 2>&1 &
    local pid=$!
    echo "$pid" >"$PID_DIR/${name}.pid"
    echo "  · $name started (pid $pid)"
  }

  start_bg threat_agent   python3 -m agents.threat_hunting_agent
  start_bg fusion_agent   python3 -m agents.telemetry_fusion_agent
  start_bg compliance     python3 -m agents.compliance_logger
  start_bg watchdog       python3 -m agents.watchdog_agent
  start_bg firewall       python3 -m agents.firewall_agent
  start_bg whatsapp       python3 -m agents.whatsapp_webhook
  start_bg health         python3 -m agents.healthcheck --serve
  start_bg dashboard      python3 -m agents.dashboard
  start_bg daily_report   python3 -m agents.daily_report_agent
  start_bg weekly_evidence python3 -m agents.weekly_evidence_agent
  start_bg ir_detect       python3 -m agents.ir_detect_agent
  start_bg ir_investigate  python3 -m agents.ir_investigate_agent
  start_bg ir_respond      python3 -m agents.ir_respond_agent
  start_bg ir_report       python3 -m agents.ir_report_agent
  start_bg tenant_orch     python3 -m agents.tenant_orchestrator_agent

  local up=0 down=0
  sleep 1
  for f in "$PID_DIR"/*.pid; do
    [[ -e "$f" ]] || continue
    pid=$(cat "$f" 2>/dev/null || true)
    if [[ -n "${pid:-}" ]] && kill -0 "$pid" 2>/dev/null; then
      up=$((up+1))
    else
      down=$((down+1))
    fi
  done
  echo
  echo "[+] Local start complete: $up up, $down down"
  print_urls
}

start_docker() {
  echo "[+] Starting CyberFortress via Docker Compose..."
  if docker compose version >/dev/null 2>&1; then
    docker compose -f docker/docker-compose.yml up -d
  else
    docker-compose -f docker/docker-compose.yml up -d
  fi
  print_urls
}

case "$MODE" in
  status)
    status_local
    ;;
  local)
    start_local
    ;;
  docker)
    start_docker
    ;;
  auto|*)
    if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
      start_docker
    else
      if command -v docker >/dev/null 2>&1; then
        echo "[i] Docker CLI found but daemon is not running — using local mode"
        echo "    (start Docker later, or use: bash start.sh docker)"
      fi
      start_local
    fi
    ;;
esac
