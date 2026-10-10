#!/usr/bin/env bash
# CyberFortress — Live Meta WhatsApp + HTTPS webhook setup helper
# Usage: ./scripts/setup_whatsapp_live.sh
# Does NOT enable containment live mode. Only configures WhatsApp HITL.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
ENV_FILE="$ROOT/.env"

echo "=============================================="
echo " CyberFortress — Live WhatsApp Setup"
echo " Meta Cloud API + HTTPS webhook"
echo "=============================================="
echo
echo "This configures Tier-2 HITL only. Containment stays dry-run"
echo "until NDA + ROE + pilot_signoff + enable_live_mode.sh."
echo

if [[ ! -f "$ENV_FILE" ]]; then
  cp .env.example .env
  chmod 600 .env
  echo "[+] Created .env"
fi

set_env() {
  local key="$1" val="$2"
  if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
    # escape sed specials minimally
    local esc
    esc=$(printf '%s' "$val" | sed 's/[&|]/n/g')
    sed -i.bak "s|^${key}=.*|${key}=${esc}|" "$ENV_FILE"
    rm -f "$ENV_FILE.bak"
  else
    echo "${key}=${val}" >> "$ENV_FILE"
  fi
}

echo "--- Meta Developer Console values ---"
read -r -p "Phone Number ID: " PHONE_ID
read -r -p "Permanent access token: " TOKEN
read -r -p "Admin numbers (comma-separated, E.164 e.g. +1868...): " ADMINS
read -r -p "Webhook verify token (long random string): " VERIFY
read -r -p "Approval timeout seconds [900]: " TIMEOUT
TIMEOUT="${TIMEOUT:-900}"

set_env CF_WHATSAPP_PHONE_NUMBER_ID "$PHONE_ID"
set_env CF_WHATSAPP_TOKEN "$TOKEN"
set_env CF_WHATSAPP_ADMINS "$ADMINS"
set_env CF_WHATSAPP_VERIFY_TOKEN "$VERIFY"
set_env CF_APPROVAL_TIMEOUT "$TIMEOUT"
set_env CF_WHATSAPP_MOCK "false"
set_env CF_WHATSAPP_ENABLED "false"  # enable after HTTPS verified

chmod 600 "$ENV_FILE"
echo
echo "[+] Wrote Meta credentials to .env (WhatsApp still DISABLED until HTTPS OK)"
echo
echo "--- HTTPS in front of 127.0.0.1:8089 ---"
echo "Meta requires a public HTTPS callback. Choose one:"
echo "  A) Caddy + DNS  (production) — see docker/caddy.whatsapp.example"
echo "  B) Cloudflare Tunnel"
echo "  C) ngrok        (short pilot only)"
echo
read -r -p "Public HTTPS webhook base URL (e.g. https://webhook.example.tt): " HOOK_URL
HOOK_URL="${HOOK_URL%/}"

echo
echo "In Meta Developer Console:"
echo "  1. WhatsApp → Configuration → Webhook"
echo "  2. Callback URL:  ${HOOK_URL}/"
echo "  3. Verify token:  (same as you entered above)"
echo "  4. Subscribe to:  messages"
echo
echo "Start local webhook (if not already running):"
echo "  ./start.sh"
echo "  # webhook listens on 127.0.0.1:8089"
echo
echo "After Meta shows Verified:"
echo "  1. Set CF_WHATSAPP_ENABLED=true in .env"
echo "  2. ./stop.sh && ./start.sh"
echo "  3. ./scripts/verify_whatsapp.sh"
echo "  4. Mark whatsapp_tls_verified=true in config/pilot_signoff.json"
echo
echo "Docs: docs/WHATSAPP_TLS.md"
echo "=============================================="
