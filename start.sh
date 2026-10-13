#!/usr/bin/env bash
# CyberFortress — one command to start everything
# Usage:
#   ./start.sh          # start all services (Docker if daemon up, else local)
#   ./start.sh status   # show status
#   ./start.sh docker   # force Docker mode (fails if daemon down)
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
mkdir -p "$PID_DIR" logs evidence secrets telemetry/sentinel telemetry/mirage logs/whatsapp_pending

# CLI present AND compose plugin/binary works
has_docker_cli() {
  command -v docker >/dev/null 2>&1 || return 1
  docker compose version >/dev/null 2>&1 || docker-compose version >/dev/null 2>&1
}

# Daemon actually reachable (fixes: CLI installed but dockerd not running)
docker_daemon_up() {
  has_docker_cli || return 1
  docker info >/dev/null 2>&1
}

compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    echo "docker compose"
  else
    echo "docker-compose"
  fi
}

start_docker() {
  if ! docker_daemon_up; then
    echo "[!] Docker CLI found but daemon is not running (no /var/run/docker.sock)."
    echo "    Start Docker, or use: ./start.sh local"
    exit 1
  fi
  echo "[+] Starting CyberFortress via Docker Compose..."
  # shellcheck disable=SC2046
  $(compose_cmd) -f docker/docker-compose.yml up -d --build
  echo
  echo "[+] All services started (Docker)."
  print_urls
  echo "  Logs:  $(compose_cmd) -f docker/docker-compose.yml logs -f"
  echo "  Stop:  ./stop.sh"
}

start_local() {
  echo "[+] Starting CyberFortress locally (no Docker)..."

  if ! command -v python3 >/dev/null 2>&1; then
    echo "[!] python3 is required for local mode"
    exit 1
  fi

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

  sleep 1
  echo
  echo "[+] All local services started."
  print_urls
  echo "  Logs:  tail -f logs/*.out"
  echo "  Stop:  ./stop.sh"
  echo "  Status: ./start.sh status"
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
  local any=0
  for f in "$PID_DIR"/*.pid; do
    [[ -f "$f" ]] || continue
    any=1
    name=$(basename "$f" .pid)
    pid=$(cat "$f" 2>/dev/null || echo "?")
    if [[ "$pid" != "?" ]] && kill -0 "$pid" 2>/dev/null; then
      echo "  [UP]   $name  pid=$pid"
    else
      echo "  [DOWN] $name  (stale pid $pid)"
    fi
  done
  if [[ "$any" -eq 0 ]]; then
    echo "  (no local pid files — not started in local mode?)"
  fi
  if has_docker_cli; then
    echo
    if docker_daemon_up; then
      echo "Docker services:"
      $(compose_cmd) -f docker/docker-compose.yml ps 2>/dev/null || true
    else
      echo "Docker CLI present but daemon is down."
    fi
  fi
}

case "$MODE" in
  start|"")
    if docker_daemon_up; then
      start_docker
    else
      if has_docker_cli; then
        echo "[i] Docker CLI found but daemon is not running — using local mode"
        echo "    (start Docker later, or use ./start.sh docker when ready)"
      else
        echo "[i] Docker not found — starting local Python processes"
      fi
      start_local
    fi
    ;;
  docker)
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
