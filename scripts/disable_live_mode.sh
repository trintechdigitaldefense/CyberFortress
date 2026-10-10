#!/usr/bin/env bash
# Immediately disable live containment (fail safe).
# Usage: ./scripts/disable_live_mode.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"

echo "[!] Disabling live containment..."

if [[ -f "$ENV_FILE" ]]; then
  if grep -q '^CF_CONTAINMENT_LIVE=' "$ENV_FILE"; then
    sed -i.bak 's/^CF_CONTAINMENT_LIVE=.*/CF_CONTAINMENT_LIVE=false/' "$ENV_FILE"
    rm -f "$ENV_FILE.bak"
  else
    echo "CF_CONTAINMENT_LIVE=false" >> "$ENV_FILE"
  fi
  chmod 600 "$ENV_FILE"
else
  echo "CF_CONTAINMENT_LIVE=false" > "$ENV_FILE"
  chmod 600 "$ENV_FILE"
fi

export CF_CONTAINMENT_LIVE=false

echo "[+] CF_CONTAINMENT_LIVE=false"
echo "[+] Restart services to apply:"
echo "    docker compose -f docker/docker-compose.yml up -d"
echo "[+] Optional emergency breaker trip:"
echo "    python3 playbooks/breaker.py trip --reason 'Live mode disabled by operator'"
echo "[+] See docs/OPERATOR_RUNBOOK.md"
