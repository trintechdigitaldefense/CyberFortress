#!/usr/bin/env bash
# Verify WhatsApp env + local webhook reachability (not Meta HTTPS itself)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

echo "CyberFortress WhatsApp verification"
echo "----------------------------------"
ok=1

check() {
  local name="$1" cond="$2"
  if eval "$cond"; then
    echo "[OK] $name"
  else
    echo "[!!] $name"
    ok=0
  fi
}

check "CF_WHATSAPP_TOKEN set" '[[ -n "${CF_WHATSAPP_TOKEN:-}" ]]'
check "CF_WHATSAPP_PHONE_NUMBER_ID set" '[[ -n "${CF_WHATSAPP_PHONE_NUMBER_ID:-}" ]]'
check "CF_WHATSAPP_ADMINS set" '[[ -n "${CF_WHATSAPP_ADMINS:-}" ]]'
check "CF_WHATSAPP_VERIFY_TOKEN not default" '[[ -n "${CF_WHATSAPP_VERIFY_TOKEN:-}" && "${CF_WHATSAPP_VERIFY_TOKEN}" != "change_me_to_a_long_random_string" && "${CF_WHATSAPP_VERIFY_TOKEN}" != "cf_verify_token_change_me" ]]'
check "CF_APPROVAL_TIMEOUT set" '[[ -n "${CF_APPROVAL_TIMEOUT:-}" ]]'

if [[ "${CF_WHATSAPP_ENABLED:-false}" == "true" ]]; then
  echo "[OK] CF_WHATSAPP_ENABLED=true"
else
  echo "[i ] CF_WHATSAPP_ENABLED is false — set true after Meta webhook Verified"
fi

if [[ "${CF_WHATSAPP_MOCK:-false}" == "true" ]]; then
  echo "[i ] CF_WHATSAPP_MOCK=true (demo path — not live Meta)"
fi

if curl -s -o /dev/null -w "" --connect-timeout 2 "http://127.0.0.1:8089/" 2>/dev/null; then
  echo "[OK] Local webhook port 8089 responds"
else
  # GET without challenge may 403 — still means process is up
  code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 "http://127.0.0.1:8089/?hub.mode=subscribe&hub.verify_token=${CF_WHATSAPP_VERIFY_TOKEN:-x}&hub.challenge=cf_test" || echo 000)
  if [[ "$code" == "200" ]]; then
    echo "[OK] Local webhook verify challenge returned 200"
  else
    echo "[!!] Local webhook on 127.0.0.1:8089 not reachable (start with ./start.sh)"
    ok=0
  fi
fi

echo "----------------------------------"
if [[ "$ok" -eq 1 ]]; then
  echo "Local config looks ready."
  echo "Confirm Meta Console shows Webhook = Verified over HTTPS."
  echo "Then set whatsapp_tls_verified=true in config/pilot_signoff.json"
  exit 0
else
  echo "Fix items marked [!!] — see docs/WHATSAPP_TLS.md"
  exit 1
fi
