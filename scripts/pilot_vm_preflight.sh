#!/usr/bin/env bash
# Real-VM pilot preflight — netadmin MUST be green before arming.
# WhatsApp credentials can be added later (Tier-2 HITL deferred).
#
# Usage:
#   ./scripts/pilot_vm_preflight.sh
#   ./scripts/pilot_vm_preflight.sh --strict-whatsapp
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

STRICT_WA=false
if [[ "${1:-}" == "--strict-whatsapp" ]]; then
  STRICT_WA=true
fi

PASS=0
FAIL=0
ok()  { echo "  [+] $1"; PASS=$((PASS+1)); }
bad() { echo "  [!] $1"; FAIL=$((FAIL+1)); }
info(){ echo "  [i] $1"; }

echo "=============================================="
echo " CyberFortress — Real VM pilot preflight"
echo "=============================================="
echo " Goal: prove this host can run live CF_BLOCK later."
echo " WhatsApp credentials: optional for now (add later)."
echo

echo "1. Repo / Python"
command -v python3 >/dev/null && ok "python3: $(python3 --version 2>&1)" || bad "python3 missing"
[[ -f start.sh && -f stop.sh ]] && ok "start.sh / stop.sh present" || bad "missing start/stop"
[[ -f scripts/check_netadmin.sh ]] && ok "check_netadmin.sh present" || bad "missing check_netadmin.sh"

echo
echo "2. Netfilter / CAP_NET_ADMIN (required before arming)"
if bash scripts/check_netadmin.sh; then
  ok "check_netadmin.sh GREEN"
  if [[ -f config/host_capability.json ]]; then
    info "capability stamp present"
  fi
else
  bad "check_netadmin.sh FAILED — do not arm on this host"
  echo
  echo "  Fix: deploy on a real VM (Ubuntu 22.04+) with iptables + root/CAP_NET_ADMIN"
  echo "  Docs: docs/HOST_REQUIREMENTS.md"
  echo
  echo "=============================================="
  echo " Result: FAIL — MONITORING only until netadmin is green"
  echo "=============================================="
  exit 1
fi

echo
echo "3. Platform smoke"
if [[ -f logs/pids/dashboard.pid ]] || [[ -f logs/pids/health.pid ]]; then
  ok "local agents appear started (pid files present)"
else
  info "Agents not running — start with: bash start.sh local"
fi
if python3 -m agents.healthcheck >/tmp/cf_pilot_health.txt 2>&1; then
  ok "healthcheck runs"
else
  info "healthcheck one-shot failed (start platform if needed)"
fi

echo
echo "4. Legal / sign-off readiness"
if [[ -f config/pilot_signoff.json ]]; then
  ok "config/pilot_signoff.json exists"
  python3 - <<'PY'
import json, sys
from pathlib import Path
data = json.loads(Path("config/pilot_signoff.json").read_text(encoding="utf-8"))
need = ["roe_signed", "nda_signed", "host_netadmin_verified", "operator_runbook_acknowledged", "checklist_complete"]
for k in need:
    v = data.get(k)
    mark = "yes" if v is True else "NO"
    print(f"         {k}: {mark}")
print(f"         whatsapp_tls_verified: {data.get('whatsapp_tls_verified')}")
print(f"         whatsapp_deferred: {data.get('whatsapp_deferred')}")
if data.get("host_netadmin_verified") is not True:
    print("[!] host_netadmin_verified is not true — re-run check_netadmin.sh")
    sys.exit(1)
PY
  ok "host_netadmin_verified is true in signoff"
else
  info "No pilot_signoff.json yet"
  echo "         cp config/pilot_signoff.example.json config/pilot_signoff.json"
  echo "         Fill NDA/ROE fields; set whatsapp_deferred=true until Meta creds are ready"
fi

if [[ "$STRICT_WA" == "true" ]]; then
  echo
  echo "5. Strict WhatsApp (requested)"
  if [[ -f config/pilot_signoff.json ]]; then
    python3 - <<'PY'
import json, sys
from pathlib import Path
data = json.loads(Path("config/pilot_signoff.json").read_text(encoding="utf-8"))
if data.get("whatsapp_tls_verified") is not True:
    print("[!] whatsapp_tls_verified must be true in --strict-whatsapp mode")
    sys.exit(1)
print("[+] WhatsApp TLS flag set")
PY
  else
    bad "signoff missing for strict WhatsApp check"
  fi
else
  echo
  echo "5. WhatsApp"
  info "Deferred — add Meta token later (docs/WHATSAPP_TLS.md)"
  info "For live arming without WA yet: set whatsapp_deferred=true in pilot_signoff.json"
fi

echo
echo "=============================================="
echo " Result: $PASS checks noted, $FAIL hard fails"
if [[ "$FAIL" -gt 0 ]]; then
  echo " Status: NOT ready to arm"
  exit 1
fi
echo " Status: VM netadmin GREEN — safe path toward arming after NDA/ROE"
echo
echo " Next steps:"
echo "   1. Keep MONITORING (CF_CONTAINMENT_LIVE=false) until NDA+ROE signed"
echo "   2. Edit config/pilot_signoff.json (whatsapp_deferred=true OK for now)"
echo "   3. ./scripts/enable_live_mode.sh --check"
echo "   4. ./scripts/enable_live_mode.sh --enable"
echo "   5. Later: Meta WhatsApp creds → whatsapp_tls_verified=true"
echo " Docs: docs/PILOT_VM.md"
echo "=============================================="
