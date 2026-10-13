#!/usr/bin/env bash
# CyberFortress — one command to start everything
# Usage:
#   bash start.sh          # works even without +x
#   ./start.sh             # after chmod (install.sh does this)
#   bash start.sh status
#   bash start.sh local
#   bash start.sh docker
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

# Always make launcher scripts executable (fixes Permission denied on ./start.sh)
chmod +x "$ROOT/start.sh" "$ROOT/stop.sh" "$ROOT/install.sh" 2>/dev/null || true
chmod +x "$ROOT"/scripts/*.sh 2>/dev/null || true

# Load .env if present
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

MODE="${1:-start}"
PID_DIR="$ROOT/logs/pids"
mkdir -p "$PID_DIR" logs evidence secrets telemetry/sentinel telemetry/mirage logs/whatsapp_pending logs/heartbeats

has_docker_cli() {
  command -v docker >/dev/null 2>&1 || return 1
  docker compose version >/dev/null 2>&1 || docker-compose version >/dev/null 2>&1
}

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

# Free CF ports held by leftover processes (common cause of dashboard/health DOWN)
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
      sleep 0.2
      # shellcheck disable=SC2086
      kill -9 $pids 2>/dev/null || true
    fi
  fi
}

start_docker() {
  if ! docker_daemon_up; then
    echo "[!] Docker CLI found but daemon is not running (no /var/run/docker.sock)."
    echo "    Start Docker, or use: bash start.sh local"
    exit 1
  fi
  echo "[+] Starting CyberFortress via Docker Compose..."
  # shellcheck disable=SC2046
  $(compose_cmd) -f docker/docker-compose.yml up -d --build
  echo
  echo "[+] All services started (Docker)."
  print_urls
  echo "  Logs:  $(compose_cmd) -f docker/docker-compose.yml logs -f"
  echo "  Stop:  bash stop.sh"
}

start_local() {
  echo "[+] Starting CyberFortress locally (no Docker)..."

  if ! command -v python3 >/dev/null 2>&1; then
    echo "[!] python3 is required for local mode"
    exit 1
  fi

  # Clear stale pid tracking + free HTTP ports from previous runs
  if [[ -d "$PID_DIR" ]]; then
    for f in "$PID_DIR"/*.pid; do
      [[ -f "$f" ]] || continue
      pid=$(cat "$f" 2>/dev/null || true)
      if [[ -n "${pid:-}" ]] && kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null || true
        sleep 0.1
        kill -9 "$pid" 2>/dev/null || true
      fi
      rm -f "$f"
    done
  fi
  free_port 8089
  free_port 8090
  free_port 8091
  sleep 0.3

  start_bg() {
    local name="$1"
    shift
    local pidfile="$PID_DIR/${name}.pid"
    local logfile="logs/${name}.out"
    : >"$logfile"
    nohup "$@" >>"$logfile" 2>&1 &
    local pid=$!
    echo "$pid" >"$pidfile"
    sleep 0.4
    if kill -0 "$pid" 2>/dev/null; then
      echo "  · $name started (pid $pid)"
    else
      echo "  · $name FAILED to stay up — last log lines:"
      tail -n 12 "$logfile" 2>/dev/null | sed 's/^/      /' || true
      echo "      Full log: $logfile"
    fi
  }

  start_bg threat_agent   python3 -m agents.threat_hunting_agent
  start_bg fusion_agent   python3 -m agents.telemetry_fusion_agent
  start_bg compliance     python3 -m agents.compliance_logger
  start_bg watchdog       python3 -m agents.watchdog_agent
  start_bg whatsapp       python3 -m agents.whatsapp_webhook
  start_bg health         python3 -m agents.healthcheck --serve
  start_bg dashboard      python3 -m agents.dashboard

  sleep 0.5
  echo
  # Summary of UP/DOWN
  local up=0 down=0
  for f in "$PID_DIR"/*.pid; do
    [[ -f "$f" ]] || continue
    name=$(basename "$f" .pid)
    pid=$(cat "$f" 2>/dev/null || echo "")
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      up=$((up + 1))
    else
      down=$((down + 1))
      echo "  [!] $name is DOWN — see logs/${name}.out"
    fi
  done
  echo "[+] Local start complete: ${up} up, ${down} down"
  print_urls
  echo "  Logs:   tail -f logs/*.out"
  echo "  Stop:   bash stop.sh"
  echo "  Status: bash start.sh status"
  if [[ "$down" -gt 0 ]]; then
    echo
    echo "  Tip: if dashboard/health/whatsapp died, ports may still be busy:"
    echo "       bash stop.sh && sleep 1 && bash start.sh local"
  fi
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
      echo "  [DOWN] $name  (stale pid $pid) — see logs/${name}.out"
    fi
  done
  if [[ "$any" -eq 0 ]]; then
    echo "  (no local pid files — not started in local mode?)"
  fi
  # Quick port check
  for port in 8089 8090 8091; do
    if command -v ss >/dev/null 2>&1; then
      if ss -ltn 2>/dev/null | grep -q ":${port} "; then
        echo "  [port] $port LISTENING"
      fi
    fi
  done
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
        echo "    (start Docker later, or use: bash start.sh docker)"
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
    echo "Usage: bash start.sh [start|status|docker|local]"
    exit 2
    ;;
esac
