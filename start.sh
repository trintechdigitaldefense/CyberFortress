#!/usr/bin/env bash
# CyberFortress — start everything
# Usage: bash start.sh [local|docker|status]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
PID_DIR="$ROOT/logs/pids"
mkdir -p "$PID_DIR" logs evidence secrets telemetry/sentinel telemetry/mirage logs/whatsapp_pending logs/heartbeats logs/ir_cases evidence/ir_reports config/playbooks config/threat_intel

chmod +x "$ROOT/start.sh" "$ROOT/stop.sh" "$ROOT/install.sh" 2>/dev/null || true

source "$ROOT/scripts/load_env.sh"

MODE="${1:-auto}"

live_flag() {
  load_cyberfortress_env "$ROOT/.env"
  echo "${CF_CONTAINMENT_LIVE:-false}"
}

print_urls() {
  echo
  echo "  Dashboard : http://127.0.0.1:8091"
  echo "  Health    : http://127.0.0.1:8090"
  echo "  Webhook   : http://127.0.0.1:8089  (put TLS in front for Meta)"
  echo "  SOC API   : http://127.0.0.1:8092  (/metrics, /api/soc/ingest)"
  echo
  echo "  Firewall: agent starts with platform (CF_BLOCK chain)"
  echo "  Auto-defense: policy-gated Tier-1 (LIVE=$(live_flag))"
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
}

start_local() {
  echo "[+] Starting CyberFortress locally (no Docker)..."
  export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
  load_cyberfortress_env "$ROOT/.env"

  # Termux and proot do not provide a dependable host firewall control plane.
  # Force monitoring-only for this runtime even if a stale .env says LIVE=true.
  if [[ -n "${TERMUX_VERSION:-}" ||
        "${PREFIX:-}" == /data/data/com.termux* ||
        -n "${PROOT_TMP_DIR:-}" ||
        -n "${PROOT_LOADER:-}" ]]; then
    export CF_CONTAINMENT_LIVE=false
    export CF_FIREWALL_AUTO_START=false
    echo "[!] Restricted Termux/proot runtime detected — forcing MONITORING ONLY."
  fi

  start_bg() {
    local name="$1"; shift
    local pid_file="$PID_DIR/${name}.pid"
    local log="$ROOT/logs/${name}.out"
    local expected_module=""
    local recorded_pid=""
    local command_line=""

    if [[ "${1:-}" == "python" || "${1:-}" == "python3" ]] && [[ "${2:-}" == "-m" ]]; then
      expected_module="${3:-}"
    fi

    # Avoid duplicate launches, and never trust a PID file without checking identity.
    if [[ -f "$pid_file" ]]; then
      recorded_pid="$(cat "$pid_file" 2>/dev/null || true)"
      if [[ "$recorded_pid" =~ ^[0-9]+$ ]] && [[ "$recorded_pid" -gt 1 ]] && kill -0 "$recorded_pid" 2>/dev/null; then
        if [[ -r "/proc/$recorded_pid/cmdline" ]]; then
          command_line="$(tr '\\0' ' ' < "/proc/$recorded_pid/cmdline" 2>/dev/null || true)"
        elif command -v ps >/dev/null 2>&1; then
          command_line="$(ps -p "$recorded_pid" -o args= 2>/dev/null || true)"
        fi
        if [[ -n "$expected_module" && "$command_line" == *python* && "$command_line" == *"$expected_module"* ]]; then
          echo "  · $name already running (pid $recorded_pid); skipping duplicate"
          return 0
        fi
      fi
      # Stale or mismatched PID record: discard the record, never signal its PID.
      rm -f -- "$pid_file"
    fi

    nohup "$@" >"$log" 2>&1 &
    local pid=$!
    echo "$pid" >"$pid_file"
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
  start_bg soc_api         python3 -m agents.soc_api_agent
  start_bg siem_bridge     python3 -m agents.siem_bridge_agent
  start_bg playbook        python3 -m agents.playbook_agent
  start_bg threat_intel    python3 -m agents.threat_intel_agent
  start_bg auto_defense    python3 -m agents.auto_defense_agent

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
  status) status_local ;;
  local) start_local ;;
  docker) start_docker ;;
  auto|*)
    if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
      start_docker
    else
      if command -v docker >/dev/null 2>&1; then
        echo "[i] Docker CLI found but daemon is not running — using local mode"
      fi
      start_local
    fi
    ;;
esac
