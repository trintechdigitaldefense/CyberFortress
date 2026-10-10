#!/usr/bin/env bash
# CyberFortress — one-command install (run after git clone)
# Usage:  ./install.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "=============================================="
echo " CyberFortress Install"
echo " TrinTech Digital Defense"
echo "=============================================="

if ! command -v python3 >/dev/null 2>&1; then
  echo "[!] python3 is required"
  exit 1
fi
echo "[+] Python: $(python3 --version)"

echo "[+] Installing core Python packages..."
if python3 -m pip install --user -q -r requirements.txt; then
  echo "[+] Core packages installed"
elif python3 -m pip install -q -r requirements.txt; then
  echo "[+] Core packages installed (system pip)"
else
  echo "[!] Failed to install core requirements"
  exit 1
fi

# Optional identity backends (do not fail install if network/PyPI issues)
echo "[+] Optional identity packages (ldap3, msal) — best effort..."
python3 -m pip install --user -q ldap3 msal 2>/dev/null \
  || python3 -m pip install -q ldap3 msal 2>/dev/null \
  || echo "[i] Optional ldap3/msal skipped (install later if using LDAP/Azure AD)"

if [[ ! -f .env ]]; then
  cp .env.example .env
  chmod 600 .env
  echo "[+] Created .env from .env.example (edit secrets later)"
else
  echo "[+] .env already exists — left unchanged"
fi

mkdir -p logs evidence secrets telemetry/sentinel telemetry/mirage logs/pids logs/whatsapp_pending
chmod 700 secrets 2>/dev/null || true
echo "[+] Runtime dirs ready"

chmod +x install.sh start.sh stop.sh 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true

echo
echo "[+] Install complete."
echo "  Start: ./start.sh"
echo "  Stop:  ./stop.sh"
echo "  Dashboard: http://127.0.0.1:8091"
echo "  Safety: LIVE=off FORCE=off (dry-run)"
echo "=============================================="
