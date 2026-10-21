#!/usr/bin/env bash
# CyberFortress defensive posture self-check
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

echo "=============================================="
echo " CyberFortress — Defense check"
echo "=============================================="
PASS=0; FAIL=0
ok(){ echo "  [+] $1"; PASS=$((PASS+1)); }
bad(){ echo "  [!] $1"; FAIL=$((FAIL+1)); }
info(){ echo "  [i] $1"; }

if [[ "${CF_CONTAINMENT_LIVE:-false}" != "true" ]]; then
  ok "Containment not live by default (MONITORING)"
else
  bad "CF_CONTAINMENT_LIVE is true — ensure pilot sign-off exists"
fi

if [[ "${CF_ALLOW_FORCE:-false}" != "true" ]]; then
  ok "CF_ALLOW_FORCE is off"
else
  bad "CF_ALLOW_FORCE is true — high risk"
fi

if git check-ignore -q .env 2>/dev/null || grep -q '^\.env$' .gitignore 2>/dev/null; then
  ok ".env is gitignored"
else
  bad ".env not ignored — secrets risk"
fi

if [[ -n "${CF_DASHBOARD_PASS:-}" ]]; then
  ok "Dashboard password set"
else
  info "CF_DASHBOARD_PASS empty — set for non-localhost ops"
fi

if [[ "${CF_ALLOW_PUBLIC_BIND:-false}" == "true" ]]; then
  info "Public bind allowed — ensure TLS reverse proxy + firewall"
else
  ok "Public bind locked (localhost-only services)"
fi

if [[ "${CF_WHATSAPP_REQUIRE_SIGNATURE:-false}" == "true" ]]; then
  ok "WhatsApp signature verification required"
  [[ -n "${CF_WHATSAPP_APP_SECRET:-}" ]] && ok "App secret present" || bad "Signature required but no CF_WHATSAPP_APP_SECRET"
else
  info "CF_WHATSAPP_REQUIRE_SIGNATURE not set — enable for production Meta"
fi

python3 - <<'PY'
from core.defense import defense_status
import json
print("  Defense status:", json.dumps(defense_status()))
PY

echo "=============================================="
echo " Result: $PASS passed, $FAIL failed/warnings above"
echo " Docs: SECURITY.md · docs/GO_LIVE.md"
echo "=============================================="
[[ "$FAIL" -eq 0 ]] || exit 1
