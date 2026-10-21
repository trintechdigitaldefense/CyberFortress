#!/usr/bin/env bash
# Preflight: can this host manage CF_BLOCK / iptables?
# On success writes config/host_capability.json (used before arming).
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

MODE_LABEL="unknown"
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
  MODE_LABEL=$(python3 -c "import json; print(json.load(open('/tmp/cf_fw_check.txt')).get('mode_label',''))" 2>/dev/null || echo "ok")
else
  bad "firewall_status UNAVAILABLE or error — live DROP not supported on this host"
  sed 's/^/         /' /tmp/cf_fw_check.txt | head -25
fi

echo
echo "=============================================="
echo " Result: $PASS passed, $FAIL failed"

CAP="$ROOT/config/host_capability.json"
mkdir -p "$ROOT/config"
if [[ "$FAIL" -gt 0 ]]; then
  python3 - <<PY
import json
from datetime import datetime, timezone
path = "$CAP"
data = {
    "netadmin_ok": False,
    "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    "pass_count": $PASS,
    "fail_count": $FAIL,
    "mode_label": "$MODE_LABEL",
    "message": "NOT suitable for live CF_BLOCK — MONITORING only",
}
open(path, "w", encoding="utf-8").write(json.dumps(data, indent=2) + "\n")
print("  Wrote", path, "(netadmin_ok=false)")
PY
  echo " Status: NOT suitable for live CF_BLOCK — use MONITORING only"
  echo " Docs:   docs/HOST_REQUIREMENTS.md · docs/PILOT_VM.md"
  exit 1
fi

python3 - <<PY
import json
from datetime import datetime, timezone
path = "$CAP"
data = {
    "netadmin_ok": True,
    "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    "pass_count": $PASS,
    "fail_count": 0,
    "mode_label": "$MODE_LABEL",
    "message": "Host can manage netfilter — ROE + pilot_signoff still required before arming",
}
open(path, "w", encoding="utf-8").write(json.dumps(data, indent=2) + "\n")
print("  Wrote", path, "(netadmin_ok=true)")
PY

if [[ -f "$ROOT/config/pilot_signoff.json" ]]; then
  python3 - <<'PY'
import json
from pathlib import Path
p = Path("config/pilot_signoff.json")
data = json.loads(p.read_text(encoding="utf-8"))
if data.get("host_netadmin_verified") is not True:
    data["host_netadmin_verified"] = True
    data["host_netadmin_checked_at_utc"] = json.loads(Path("config/host_capability.json").read_text())["checked_at_utc"]
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("  [+] Stamped host_netadmin_verified=true in config/pilot_signoff.json")
else:
    print("  [+] pilot_signoff.json already has host_netadmin_verified=true")
PY
fi

echo " Status: Host can manage netfilter — complete ROE + pilot_signoff before arming"
echo " Next:   ./scripts/pilot_vm_preflight.sh   OR   docs/PILOT_VM.md"
echo "=============================================="
