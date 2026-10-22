#!/usr/bin/env bash
# Install CyberFortress systemd units for 24/7 operation (survives reboot).
# Usage:  sudo ./deploy/systemd/install_systemd.sh
#         sudo ./deploy/systemd/install_systemd.sh --enable
#         sudo ./deploy/systemd/install_systemd.sh --status
#         sudo ./deploy/systemd/install_systemd.sh --uninstall
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
UNIT_DIR="${UNIT_DIR:-/etc/systemd/system}"
INSTALL_ROOT="${CF_INSTALL_ROOT:-$ROOT}"
ACTION="${1:-install}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "[!] Run as root: sudo $0 $*"
  exit 1
fi

status_all() {
  echo "=== cyberfortress.target ==="
  systemctl status cyberfortress.target --no-pager -l 2>/dev/null || true
  echo
  echo "=== units (active/failed) ==="
  systemctl list-units 'cyberfortress*' --all --no-pager 2>/dev/null || true
  echo
  echo "=== enabled on boot? ==="
  systemctl is-enabled cyberfortress.target 2>/dev/null || echo "not enabled"
}

uninstall() {
  systemctl stop cyberfortress.target 2>/dev/null || true
  systemctl disable cyberfortress.target 2>/dev/null || true
  rm -f "$UNIT_DIR/cyberfortress.target"
  rm -f "$UNIT_DIR/cyberfortress-agent@.service"
  rm -f "$UNIT_DIR/cyberfortress-firewall.service"
  rm -rf "$UNIT_DIR/cyberfortress-agent@healthcheck.service.d"
  systemctl daemon-reload
  echo "[+] systemd units removed (app files under $INSTALL_ROOT left intact)"
}

if [[ "$ACTION" == "--status" || "$ACTION" == "status" ]]; then
  status_all
  exit 0
fi

if [[ "$ACTION" == "--uninstall" || "$ACTION" == "uninstall" ]]; then
  uninstall
  exit 0
fi

echo "[+] Install root: $INSTALL_ROOT"
if [[ ! -d "$INSTALL_ROOT/agents" ]]; then
  echo "[!] $INSTALL_ROOT/agents missing — set CF_INSTALL_ROOT or run from repo"
  exit 1
fi

if [[ -f "$INSTALL_ROOT/.env" ]]; then
  cp -n "$INSTALL_ROOT/.env" /etc/cyberfortress.env 2>/dev/null || true
  chmod 600 /etc/cyberfortress.env 2>/dev/null || true
elif [[ -f "$INSTALL_ROOT/.env.example" ]]; then
  cp -n "$INSTALL_ROOT/.env.example" /etc/cyberfortress.env
  chmod 600 /etc/cyberfortress.env
  echo "[i] Seeded /etc/cyberfortress.env from .env.example — edit secrets before go-live"
fi

ensure_env() {
  local key="$1" val="$2"
  if [[ -f /etc/cyberfortress.env ]] && ! grep -q "^${key}=" /etc/cyberfortress.env 2>/dev/null; then
    echo "${key}=${val}" >> /etc/cyberfortress.env
  fi
}
ensure_env CF_CONTAINMENT_LIVE false
ensure_env CF_ALLOW_FORCE false
ensure_env CF_ROOT "$INSTALL_ROOT"

render() {
  sed "s|/opt/CyberFortress|$INSTALL_ROOT|g" "$1" >"$2"
  echo "  wrote $2"
}

render "$ROOT/deploy/systemd/cyberfortress.target" "$UNIT_DIR/cyberfortress.target"
render "$ROOT/deploy/systemd/cyberfortress-agent@.service" "$UNIT_DIR/cyberfortress-agent@.service"
render "$ROOT/deploy/systemd/cyberfortress-firewall.service" "$UNIT_DIR/cyberfortress-firewall.service"

mkdir -p "$UNIT_DIR/cyberfortress-agent@healthcheck.service.d"
cat >"$UNIT_DIR/cyberfortress-agent@healthcheck.service.d/override.conf" <<OV
[Service]
ExecStart=
ExecStart=/usr/bin/python3 -m agents.healthcheck --serve
OV
echo "  wrote healthcheck override (--serve)"

systemctl daemon-reload
echo "[+] Units installed (daemon-reload done)"
echo
echo "Next:"
echo "  sudo systemctl enable --now cyberfortress.target"
echo "  sudo systemctl status cyberfortress.target"
echo "  sudo ./deploy/systemd/install_systemd.sh --status"
echo
echo "Notes:"
echo "  - Default remains MONITORING (CF_CONTAINMENT_LIVE=false)"
echo "  - Arm only after ROE + pilot_signoff + ./scripts/enable_live_mode.sh"
echo "  - Prefer systemd OR ./start.sh — not both at once"

if [[ "$ACTION" == "--enable" || "$ACTION" == "enable" ]]; then
  systemctl enable --now cyberfortress.target
  status_all
fi
