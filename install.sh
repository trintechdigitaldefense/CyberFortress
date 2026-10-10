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

# Python
if ! command -v python3 >/dev/null 2>&1; then
  echo "[!] python3 is required"
  exit 1
fi
echo "[+] Python: $(python3 --version)"

# Dependencies
echo "[+] Installing Python packages..."
python3 -m pip install --user -q -r requirements.txt 2>/dev/null \
  || python3 -m pip install -q -r requirements.txt

# Env file
if [[ ! -f .env ]]; then
  cp .env.example .env
  chmod 600 .env
  echo "[+] Created .env from .env.example (edit secrets later)"
else
  echo "[+] .env already exists — left unchanged"
fi

# Runtime dirs
mkdir -p logs evidence secrets telemetry/sentinel telemetry/mirage
chmod 700 secrets 2>/dev/null || true
echo "[+] Runtime dirs ready (logs, evidence, secrets, telemetry)"

# Scripts executable
chmod +x install.sh start.sh stop.sh 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true

echo
echo "[+] Install complete."
echo
echo "  Start everything:  ./start.sh"
echo "  Stop everything:   ./stop.sh"
echo "  Status:            ./start.sh status"
echo
echo "  Dashboard:  http://127.0.0.1:8091"
echo "  Health:     http://127.0.0.1:8090"
echo
echo "  Safety defaults: LIVE=off  FORCE=off  (dry-run)"
echo "=============================================="
