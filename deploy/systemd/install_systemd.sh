#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
UNIT_DIR="${UNIT_DIR:-/etc/systemd/system}"
if [[ "$(id -u)" -ne 0 ]]; then
  echo "[!] Run as root: sudo $0"
  exit 1
fi
INSTALL_ROOT="${CF_INSTALL_ROOT:-$ROOT}"
echo "[+] Install root: $INSTALL_ROOT"
if [[ -f "$INSTALL_ROOT/.env" ]]; then
  cp -n "$INSTALL_ROOT/.env" /etc/cyberfortress.env 2>/dev/null || true
  chmod 600 /etc/cyberfortress.env 2>/dev/null || true
elif [[ -f "$INSTALL_ROOT/.env.example" ]]; then
  cp -n "$INSTALL_ROOT/.env.example" /etc/cyberfortress.env
  chmod 600 /etc/cyberfortress.env
fi
render() { sed "s|/opt/CyberFortress|$INSTALL_ROOT|g" "$1" >"$2"; echo "  wrote $2"; }
render "$ROOT/deploy/systemd/cyberfortress.target" "$UNIT_DIR/cyberfortress.target"
render "$ROOT/deploy/systemd/cyberfortress-agent@.service" "$UNIT_DIR/cyberfortress-agent@.service"
render "$ROOT/deploy/systemd/cyberfortress-firewall.service" "$UNIT_DIR/cyberfortress-firewall.service"
mkdir -p "$UNIT_DIR/cyberfortress-agent@healthcheck.service.d"
cat >"$UNIT_DIR/cyberfortress-agent@healthcheck.service.d/override.conf" <<OV
[Service]
ExecStart=
ExecStart=/usr/bin/python3 -m agents.healthcheck --serve
OV
systemctl daemon-reload
echo "[+] Enable: systemctl enable --now cyberfortress.target"
