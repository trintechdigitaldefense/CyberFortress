#!/usr/bin/env bash
# Preflight: can this host manage CF_BLOCK / iptables?
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

PASS=0
FAIL=0
ok()  { echo "  [+] $1"; PASS=$((PASS+1)); }
bad() { echo "  [!] $1"; FAIL=$((FAIL+1)); }

echo "=============================================="
echo " CyberFortress — NET_ADMIN / iptables check"
echo "=============================================="

if command -v iptables >/dev/null 2>&1; then
  ok "iptables on PATH: $(command -v iptables)"
else
  bad "iptables not found — install iptables (or iptables-legacy)"
fi

UID_NOW="$(id -u)"
if [[ "$UID_NOW" == "0" ]]; then
  ok "Running as root (uid 0)"
else
  echo "  [INFO] Not root (uid $UID_NOW) — live chain setup may fail without sudo/capabilities"
fi

if command -v capsh >/dev/null 2>&1; then
  if capsh --print 2>/dev/null | grep -qi "cap_net_admin"; then
    ok "capsh reports CAP_NET_ADMIN in bounding/effective set (or similar)"
  else
    echo "  [INFO] capsh present but CAP_NET_ADMIN not clearly listed"
  fi
fi

if command -v iptables >/dev/null 2>&1; then
  if iptables -L -n >/dev/null 2>&1; then
    ok "iptables -L -n succeeded (netfilter reachable)"
  else
    ERR="$(iptables -L -n 2>&1 || true)"
    bad "iptables -L failed — host cannot use netfilter"
    echo "         $ERR"
  fi
fi

if python3 - <<'PY' 2>/tmp/cf_fw_check.txt
from core.containment.firewall import firewall_status
import json
st = firewall_status()
print(json.dumps(st, indent=2))
label = st.get("mode_label", "")
if label == "UNAVAILABLE" or st.get("host_blocked"):
    raise SystemExit(2)
if not st.get("iptables_present"):
    raise SystemExit(2)
PY
then
  ok "firewall_status usable (not UNAVAILABLE)"
  sed 's/^/         /' /tmp/cf_fw_check.txt | head -20
else
  bad "firewall_status UNAVAILABLE or error — live DROP not supported on this host"
  sed 's/^/         /' /tmp/cf_fw_check.txt | head -25
fi

echo
echo "=============================================="
echo " Result: $PASS passed, $FAIL failed"
if [[ "$FAIL" -gt 0 ]]; then
  echo " Status: NOT suitable for live CF_BLOCK — use MONITORING only"
  echo " Docs:   docs/HOST_REQUIREMENTS.md"
  exit 1
fi
echo " Status: Host can manage netfilter — complete ROE + pilot_signoff before arming"
echo " Next:   docs/GO_LIVE.md · ./scripts/enable_live_mode.sh --check"
echo "=============================================="
