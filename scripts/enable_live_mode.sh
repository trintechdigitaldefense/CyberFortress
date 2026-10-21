#!/usr/bin/env bash
# Enable CF_CONTAINMENT_LIVE only after pilot sign-off + netadmin GREEN.
# WhatsApp may be deferred (whatsapp_deferred=true) until credentials are ready.
# Usage:
#   ./scripts/enable_live_mode.sh --check
#   ./scripts/enable_live_mode.sh --enable

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SIGNOFF="$ROOT/config/pilot_signoff.json"
CAP="$ROOT/config/host_capability.json"
ENV_FILE="$ROOT/.env"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

require_signoff() {
  if [[ ! -f "$SIGNOFF" ]]; then
    echo "[!] Missing $SIGNOFF"
    echo "    cp config/pilot_signoff.example.json config/pilot_signoff.json"
    echo "    Run ./scripts/pilot_vm_preflight.sh  (netadmin must be green)"
    echo "    Sign NDA + ROE; WhatsApp can wait (whatsapp_deferred=true)"
    echo "    See docs/PILOT_VM.md · docs/GO_LIVE.md"
    exit 1
  fi

  python3 - "$SIGNOFF" "$CAP" <<'PY'
import json, sys
from pathlib import Path

path = Path(sys.argv[1])
cap_path = Path(sys.argv[2])
data = json.loads(path.read_text(encoding="utf-8"))

required_true = [
    "checklist_complete",
    "operator_runbook_acknowledged",
    "roe_signed",
    "nda_signed",
    "host_netadmin_verified",
]
wa_deferred = data.get("whatsapp_deferred") is True
if not wa_deferred:
    required_true.append("whatsapp_tls_verified")

missing = [k for k in required_true if data.get(k) is not True]
if missing:
    print("[!] Sign-off incomplete. Set these to true in config/pilot_signoff.json:")
    for k in missing:
        print(f"    - {k}")
    print("    Host:     ./scripts/check_netadmin.sh or ./scripts/pilot_vm_preflight.sh")
    if "whatsapp_tls_verified" in missing:
        print("    WhatsApp: set whatsapp_deferred=true to arm without Meta creds yet")
    sys.exit(1)

for field in ("client_name", "engagement_id", "signed_by", "signoff_date_utc", "client_approver"):
    val = str(data.get(field, "")).strip()
    bad = (
        not val
        or "CLIENT_LEGAL" in val
        or "ENG-YYYY" in val
        or val == "YYYY-MM-DD"
        or val == "Lead Operator Name"
        or val == "Client Contact Name"
    )
    if bad:
        print(f"[!] Replace placeholder value for: {field}")
        sys.exit(1)

for field in ("roe_document", "nda_document"):
    val = str(data.get(field, "")).strip()
    if not val or "path/or/filename" in val:
        print(f"[!] Set real path/filename for signed document: {field}")
        sys.exit(1)

actions = data.get("authorized_actions") or []
if not isinstance(actions, list) or len(actions) < 1:
    print("[!] authorized_actions must be a non-empty list (from signed ROE)")
    sys.exit(1)

admins = data.get("whatsapp_admins") or []
if not wa_deferred:
    if not isinstance(admins, list) or not any(str(a).strip() for a in admins):
        print("[!] whatsapp_admins must list at least one E.164 number from ROE")
        sys.exit(1)
else:
    print("[i] whatsapp_deferred=true — Tier-2 WhatsApp APPROVE not live until credentials added")

if cap_path.exists():
    cap = json.loads(cap_path.read_text(encoding="utf-8"))
    if not cap.get("netadmin_ok"):
        print("[!] config/host_capability.json says netadmin_ok=false")
        print("    Re-run ./scripts/check_netadmin.sh on this VM")
        sys.exit(1)
    print(f"[+] host_capability.json netadmin_ok=true (checked {cap.get('checked_at_utc')})")
else:
    print("[i] No host_capability.json yet — runtime check_netadmin will still run")

print("[+] Pilot sign-off looks complete")
print(f"    Client      : {data.get('client_name')}")
print(f"    Engagement  : {data.get('engagement_id')}")
print(f"    NET_ADMIN   : verified={data.get('host_netadmin_verified')}")
print(f"    WhatsApp    : tls={data.get('whatsapp_tls_verified')} deferred={wa_deferred}")
PY
}

require_netadmin_runtime() {
  echo "[*] Runtime netfilter probe (must be green before arming)..."
  if ! bash "$ROOT/scripts/check_netadmin.sh"; then
    echo "[!] Host failed check_netadmin.sh — refuse to enable live containment"
    echo "    Fix host (real VM + CAP_NET_ADMIN) or keep MONITORING only."
    echo "    docs/HOST_REQUIREMENTS.md · docs/PILOT_VM.md"
    exit 1
  fi
}

set_live_env() {
  if [[ ! -f "$ENV_FILE" ]]; then
    cp "$ROOT/.env.example" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
  fi
  if grep -q '^CF_CONTAINMENT_LIVE=' "$ENV_FILE" 2>/dev/null; then
    sed -i.bak 's/^CF_CONTAINMENT_LIVE=.*/CF_CONTAINMENT_LIVE=true/' "$ENV_FILE"
  else
    echo "CF_CONTAINMENT_LIVE=true" >>"$ENV_FILE"
  fi
  chmod 600 "$ENV_FILE"
  echo "[+] CF_CONTAINMENT_LIVE=true written to .env"
  echo "    Restart: ./stop.sh && ./start.sh"
}

MODE="${1:-}"
case "$MODE" in
  --check)
    require_signoff
    require_netadmin_runtime
    echo "[+] --check OK — safe to run --enable when ready"
    ;;
  --enable)
    require_signoff
    require_netadmin_runtime
    echo
    echo "WARNING: This arms LIVE containment (real DROP rules when playbooks run)."
    echo "Type exactly: ENABLE LIVE MODE"
    read -r CONFIRM
    if [[ "$CONFIRM" != "ENABLE LIVE MODE" ]]; then
      echo "[!] Aborted — confirmation mismatch"
      exit 1
    fi
    set_live_env
    echo "[+] Live mode enabled. Confirm health shows containment_live=true after restart."
    ;;
  *)
    echo "Usage: $0 --check | --enable"
    exit 2
    ;;
esac
