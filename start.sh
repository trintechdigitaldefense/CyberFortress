#!/usr/bin/env bash
# CyberFortress — one command to start everything
# Usage:
#   ./start.sh          # start all services
#   ./start.sh status   # show status
#   ./start.sh docker   # force Docker mode
#   ./start.sh local    # force local (no Docker) mode
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

# Load .env if present
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

MODE="${1:-start}"
PID_DIR="$ROOT/logs/pids"
mkdir -p "$PID_DIR" logs evidence secrets telemetry/sentinel telemetry/mirage

has_docker() {
  command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1
}

start_docker() {
  echo "[+] Starting CyberFortress via Docker Compose..."
  docker compose -f docker/docker-compose.yml up -d --build
  echo
  echo "[+] All services started (Docker)."
  print_urls
  echo "  Logs:  docker compose -f docker/docker-compose.yml logs -f"
  echo "  Stop:  ./stop.sh"
}

start_local() {
  echo "[+] Starting CyberFortress locally (no Docker)..."

  start_bg() {
    local name="$1"
    shift
    local pidfile="$PID_DIR/${name}.pid"
    if [[ -f "$pidfile" ]] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
      echo "  · $name already running (pid $(cat "$pidfile"))"
      return
    fi
    nohup "$@" >>"logs/${name}.out" 2>&1 &
    echo $! >"$pidfile"
    echo "  · $name started (pid $!)"
  }

  start_bg threat_agent   python3 -m agents.threat_hunting_agent
  start_bg fusion_agent   python3 -m agents.telemetry_fusion_agent
  start_bg compliance     python3 -m agents.compliance_logger
  start_bg watchdog       python3 -m agents.watchdog_agent
  start_bg whatsapp       python3 -m agents.whatsapp_webhook
  start_bg health         python3 -m agents.healthcheck --serve
  start_bg dashboard      python3 -m agents.dashboard

  echo
  echo "[+] All local services started."
  print_urls
  echo "  Logs:  tail -f logs/*.out"
  echo "  Stop:  ./stop.sh"
}

print_urls() {
  echo
  echo "  Dashboard : http://127.0.0.1:8091"
  echo "  Health    : http://127.0.0.1:8090"
  echo "  Webhook   : http://127.0.0.1:8089  (put TLS in front for Meta)"
  echo
  echo "  Mode: containment LIVE=${CF_CONTAINMENT_LIVE:-false} (dry-run unless signed off)"
}

status_local() {
  echo "CyberFortress local process status:"
  for f in "$PID_DIR"/*.pid; do
    [[ -f "$f" ]] || continue
    name=$(basename "$f" .pid)
    pid=$(cat "$f")
    if kill -0 "$pid" 2>/dev/null; then
      echo "  [UP]   $name  pid=$pid"
    else
      echo "  [DOWN] $name  (stale pid $pid)"
    fi
  done
  if has_docker; then
    echo
    echo "Docker services (if any):"
    docker compose -f docker/docker-compose.yml ps 2>/dev/null || true
  fi
}

case "$MODE" in
  start|"")
    if has_docker; then
      start_docker
    else
      echo "[i] Docker not found — starting local Python processes"
      start_local
    fi
    ;;
  docker)
    if ! has_docker; then
      echo "[!] Docker Compose not available"
      exit 1
    fi
    start_docker
    ;;
  local)
    start_local
    ;;
  status)
    status_local
    ;;
  *)
    echo "Usage: $0 [start|status|docker|local]"
    exit 2
    ;;
esac
