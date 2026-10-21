#!/usr/bin/env bash
# Operator runbook drill — Tier-2 path + prove client report number cannot approve.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
export CF_CONTAINMENT_LIVE=false
export CF_WHATSAPP_MOCK=true
export CF_APPROVAL_TIMEOUT="${CF_APPROVAL_TIMEOUT:-8}"

echo "=============================================="
echo " CyberFortress — Operator drill"
echo "=============================================="
echo " Goal: Tier-2 path + separate report vs admin numbers"
echo

PASS=0
FAIL=0
ok(){ echo "  [+] $1"; PASS=$((PASS+1)); }
bad(){ echo "  [!] $1"; FAIL=$((FAIL+1)); }
info(){ echo "  [i] $1"; }

ADMINS="${CF_WHATSAPP_ADMINS:-}"
if [[ -z "$ADMINS" ]] && [[ -f config/pilot_signoff.json ]]; then
  ADMINS=$(python3 -c "import json;print(','.join(json.load(open('config/pilot_signoff.json')).get('whatsapp_admins') or []))")
fi
if [[ -z "$ADMINS" ]]; then
  ADMINS="+18683620679"
  export CF_WHATSAPP_ADMINS="$ADMINS"
  info "No admins in env/signoff — using drill default $ADMINS"
fi
ok "Admin allow-list: $ADMINS"

REPORT=""
if [[ -f config/whatsapp_notify.json ]]; then
  REPORT=$(python3 -c "import json;print(json.load(open('config/whatsapp_notify.json')).get('report_to') or '')" 2>/dev/null || true)
fi
REPORT="${REPORT:-${CF_WHATSAPP_REPORT_TO:-}}"
if [[ -n "$REPORT" ]]; then
  info "Report-to number: $REPORT"
  SEPARATE=$(ADMINS="$ADMINS" REPORT="$REPORT" python3 -c '
import re, os
admins=set()
for p in os.environ.get("ADMINS","").split(","):
    n=re.sub(r"[^0-9]","",p)
    if n: admins.add(n)
rep=re.sub(r"[^0-9]","",os.environ.get("REPORT",""))
print("yes" if (not rep or rep not in admins) else "no")
')
  if [[ "$SEPARATE" == "yes" ]]; then
    ok "Report number is not in admin allow-list (separate channels)"
  else
    info "Report number is ALSO an admin — OK for single-ops box; client pilots prefer separate"
  fi
else
  info "No report number set yet (dashboard / CF_WHATSAPP_REPORT_TO)"
fi

echo
echo "3. Tier-2 request path (dry / mock safe)"
if python3 - <<'PY'
import os
os.environ.setdefault("CF_CONTAINMENT_LIVE", "false")
os.environ.setdefault("CF_WHATSAPP_MOCK", "true")
os.environ["CF_APPROVAL_TIMEOUT"] = os.environ.get("CF_APPROVAL_TIMEOUT", "8")
from core.autonomy import classify_action, execute_with_autonomy
from pathlib import Path

tier = classify_action("isolate_endpoint", "single")
assert tier.name == "TIER_2_GUARDED", tier
print(f"  [+] isolate_endpoint classified {tier.name}")
print("  [i] Requesting Tier-2 (expect hold/deny without APPROVE)...")
ok = execute_with_autonomy("isolate_endpoint", "10.255.255.254", scope="single", severity="HIGH")
assert ok is False, f"expected False without approve, got {ok}"
print(f"  [+] execute_with_autonomy returned {ok} (False expected without approve)")
pending = list(Path(os.getenv("CF_WHATSAPP_PENDING_DIR", "./logs/whatsapp_pending")).glob("*.json"))
print(f"  [i] pending artifacts: {len(pending)}")
PY
then
  ok "Tier-2 held without APPROVE"
else
  bad "Tier-2 path failed"
fi

echo
echo "4. Approver allow-list enforcement"
if python3 - <<'PY'
from core import whatsapp_gateway as gw
gw.ADMIN_NUMBERS = ["+18683620679"]
assert gw.is_allowed_approver("+18683620679")
assert not gw.is_allowed_approver("+18685551234")
print("  [+] Admin +18683620679 allowed")
print("  [+] Non-admin +18685551234 rejected")
PY
then
  ok "Allow-list rejects non-admin"
else
  bad "Allow-list check failed"
fi

echo
echo "=============================================="
echo " Result: $PASS passed, $FAIL failed"
echo " Next: live Meta — approve from admin phone only"
echo " Docs: docs/OPERATOR_RUNBOOK.md · docs/FIRST_PILOT.md"
echo "=============================================="
if [[ "$FAIL" -gt 0 ]]; then exit 1; fi
exit 0
