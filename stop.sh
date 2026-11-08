#!/usr/bin/env bash
# CyberFortress — stop only processes started and recorded by this checkout.
# Usage: bash stop.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
PID_DIR="$ROOT/logs/pids"

echo "[+] Stopping CyberFortress processes recorded by this checkout..."

# A PID file is not sufficient authority to kill a process: PIDs can be reused.
# Verify the live process command line still identifies the expected module.
process_matches_module() {
  local pid="$1"
  local module="$2"
  local command_line=""

  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
  [[ "$pid" -gt 1 ]] || return 1
  [[ "$pid" != "$$" ]] || return 1

  if [[ -r "/proc/$pid/cmdline" ]]; then
    command_line="$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || true)"
  elif command -v ps >/dev/null 2>&1; then
    command_line="$(ps -p "$pid" -o args= 2>/dev/null || true)"
  fi

  [[ -n "$command_line" ]] || return 1
  [[ "$command_line" == *"$module"* ]] || return 1
  [[ "$command_line" == *"python"* ]]
}

stop_recorded_process() {
  local pid_file="$1"
  local module="$2"
  local name pid attempt

  name="$(basename "$pid_file" .pid)"
  pid="$(cat "$pid_file" 2>/dev/null || true)"

  if [[ ! "$pid" =~ ^[0-9]+$ ]] || [[ "$pid" -le 1 ]]; then
    echo "  [!] $name has an invalid PID record; removing stale file"
    rm -f -- "$pid_file"
    return 0
  fi

  if ! kill -0 "$pid" 2>/dev/null; then
    echo "  [i] $name is already stopped"
    rm -f -- "$pid_file"
    return 0
  fi

  if ! process_matches_module "$pid" "$module"; then
    echo "  [!] $name PID $pid no longer matches $module; refusing to signal it"
    rm -f -- "$pid_file"
    return 0
  fi

  kill -TERM "$pid" 2>/dev/null || true
  for attempt in {1..30}; do
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "  [+] stopped $name (pid $pid)"
      rm -f -- "$pid_file"
      return 0
    fi
    # Re-check identity before any further signal in case the PID was reused.
    if ! process_matches_module "$pid" "$module"; then
      echo "  [+] $name process exited or PID identity changed"
      rm -f -- "$pid_file"
      return 0
    fi
    sleep 0.2
  done

  if process_matches_module "$pid" "$module"; then
    echo "  [!] $name did not stop after SIGTERM; sending SIGKILL to verified PID"
    kill -KILL "$pid" 2>/dev/null || true
  else
    echo "  [!] $name PID identity changed; refusing SIGKILL"
  fi
  rm -f -- "$pid_file"
}

# Docker shutdown is limited to this repository's compose project.
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  if docker compose version >/dev/null 2>&1; then
    docker compose -f docker/docker-compose.yml down
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f docker/docker-compose.yml down
  fi
fi

if [[ -d "$PID_DIR" ]]; then
  # Stop only the modules that start.sh records in this checkout.
  declare -A MODULES=(
    [threat_agent]="agents.threat_hunting_agent"
    [fusion_agent]="agents.telemetry_fusion_agent"
    [compliance]="agents.compliance_logger"
    [watchdog]="agents.watchdog_agent"
    [firewall]="agents.firewall_agent"
    [whatsapp]="agents.whatsapp_webhook"
    [health]="agents.healthcheck"
    [dashboard]="agents.dashboard"
    [daily_report]="agents.daily_report_agent"
    [weekly_evidence]="agents.weekly_evidence_agent"
    [ir_detect]="agents.ir_detect_agent"
    [ir_investigate]="agents.ir_investigate_agent"
    [ir_respond]="agents.ir_respond_agent"
    [ir_report]="agents.ir_report_agent"
    [tenant_orch]="agents.tenant_orchestrator_agent"
    [soc_api]="agents.soc_api_agent"
    [siem_bridge]="agents.siem_bridge_agent"
    [playbook]="agents.playbook_agent"
    [threat_intel]="agents.threat_intel_agent"
    [auto_defense]="agents.auto_defense_agent"
  )

  for name in "${!MODULES[@]}"; do
    pid_file="$PID_DIR/$name.pid"
    [[ -f "$pid_file" ]] || continue
    stop_recorded_process "$pid_file" "${MODULES[$name]}"
  done

  # Remove only empty/stale PID files for unknown names; never signal their PIDs.
  for pid_file in "$PID_DIR"/*.pid; do
    [[ -f "$pid_file" ]] || continue
    echo "  [!] Unknown PID record $(basename "$pid_file"); leaving it untouched"
  done
fi

rm -f -- "$ROOT/logs/platform_started_at"
echo "[+] Stop sequence complete. No unrelated listener ports were targeted."
