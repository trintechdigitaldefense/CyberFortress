#!/usr/bin/env bash
# Enable CF_CONTAINMENT_LIVE only after pilot sign-off (NDA + ROE + WhatsApp + checklist).
# Usage:
#   ./scripts/enable_live_mode.sh --check
#   ./scripts/enable_live_mode.sh --enable

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SIGNOFF="$ROOT/config/pilot_signoff.json"
ENV_FILE="$ROOT/.env"

require_signoff() {
  if [[ ! -f "$SIGNOFF" ]]; then
    echo "[!] Missing $SIGNOFF"
    echo "    cp config/pilot_signoff.example.json config/pilot_signoff.json"
    echo "    Sign NDA + ROE (docs/templates/), complete WhatsApp TLS, set all flags true."
    echo "    See docs/GO_LIVE.md"
    exit 1
  fi

  python3 - "$SIGNOFF" <<'PY'
import json, sys
path = sys.argv[1]
with open(path, encoding="utf-8") as f:
    data = json.load(f)

required_true = [
    "checklist_complete",
    "whatsapp_tls_verified",
    "operator_runbook_acknowledged",
    "roe_signed",
    "nda_signed",
]
missing = [k for k in required_true if data.get(k) is not True]
if missing:
    print("[!] Sign-off incomplete. Set these to true in config/pilot_signoff.json:")
    for k in missing:
        print(f"    - {k}")
    print("    Templates: docs/templates/NDA_TEMPLATE.md · docs/templates/ROE_TEMPLATE.md")
    print("    WhatsApp:  docs/WHATSAPP_TLS.md · ./scripts/setup_whatsapp_live.sh")
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

actions = data.get("authorized_actions") or []
if not isinstance(actions, list) or len(actions) < 1:
    print("[!] authorized_actions must be a non-empty list (from signed ROE)")
    sys.exit(1)

admins = data.get("whatsapp_admins") or []
if not isinstance(admins, list) or not any(str(a).strip() for a in admins):
    print("[!] whatsapp_admins must list at least one E.164 number from ROE")
    sys.exit(1)

print("[+] Pilot sign-off looks complete")
print(f"    Client      : {data.get('client_name')}")
print(f"    Engagement  : {data.get('engagement_id')}")
print(f"    Signed by   : {data.get('signed_by')}")
print(f"    Client      : {data.get('client_approver')}")
print(f"    Date (UTC)  : {data.get('signoff_date_utc')}")
print(f"    ROE actions : {', '.join(actions)}")
print(f"    WA admins   : {len(admins)} number(s)")
PY
}

cmd="${1:---check}"

case "$cmd" in
  --check)
    require_signoff
    echo "[+] Ready for intentional live mode (not enabled yet)"
    echo "    Run: ./scripts/enable_live_mode.sh --enable"
    ;;
  --enable)
    require_signoff
    echo
    echo "WARNING: This enables REAL containment actions on the host/network."
    echo "Type exactly: ENABLE LIVE MODE"
    read -r confirm
    if [[ "$confirm" != "ENABLE LIVE MODE" ]]; then
      echo "[!] Aborted — confirmation phrase did not match"
      exit 1
    fi

    if [[ ! -f "$ENV_FILE" ]]; then
      cp "$ROOT/.env.example" "$ENV_FILE"
      chmod 600 "$ENV_FILE"
      echo "[+] Created .env from example"
    fi

    if grep -q '^CF_CONTAINMENT_LIVE=' "$ENV_FILE" 2>/dev/null; then
      sed -i.bak 's/^CF_CONTAINMENT_LIVE=.*/CF_CONTAINMENT_LIVE=true/' "$ENV_FILE"
      rm -f "$ENV_FILE.bak"
    else
      echo "CF_CONTAINMENT_LIVE=true" >> "$ENV_FILE"
    fi

    if grep -q '^CF_ALLOW_FORCE=' "$ENV_FILE" 2>/dev/null; then
      sed -i.bak 's/^CF_ALLOW_FORCE=.*/CF_ALLOW_FORCE=false/' "$ENV_FILE"
      rm -f "$ENV_FILE.bak"
    else
      echo "CF_ALLOW_FORCE=false" >> "$ENV_FILE"
    fi

    if grep -q '^CF_WATCHDOG_FAIL_CLOSED=' "$ENV_FILE" 2>/dev/null; then
      sed -i.bak 's/^CF_WATCHDOG_FAIL_CLOSED=.*/CF_WATCHDOG_FAIL_CLOSED=true/' "$ENV_FILE"
      rm -f "$ENV_FILE.bak"
    else
      echo "CF_WATCHDOG_FAIL_CLOSED=true" >> "$ENV_FILE"
    fi

    chmod 600 "$ENV_FILE"
    echo "[+] CF_CONTAINMENT_LIVE=true written to .env"
    echo "[+] CF_ALLOW_FORCE=false (prefer WhatsApp APPROVE)"
    echo "[+] CF_WATCHDOG_FAIL_CLOSED=true"
    echo
    echo "Next steps:"
    echo "  1. ./stop.sh && ./start.sh"
    echo "  2. python3 -m agents.healthcheck"
    echo "  3. Follow docs/OPERATOR_RUNBOOK.md for first 48 hours"
    echo "  4. Rollback: ./scripts/disable_live_mode.sh"
    ;;
  *)
    echo "Usage: $0 --check | --enable"
    exit 2
    ;;
esac
