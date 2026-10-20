#!/usr/bin/env bash
# CyberFortress client-ready preflight
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

PASS=0
FAIL=0
ok()  { echo "  [+] $1"; PASS=$((PASS+1)); }
bad() { echo "  [!] $1"; FAIL=$((FAIL+1)); }

echo "=============================================="
echo " CyberFortress — client-ready preflight"
echo "=============================================="

echo
echo "1. Core files"
for f in start.sh stop.sh install.sh requirements.txt .env.example; do
  [[ -f "$f" ]] && ok "$f" || bad "Missing $f"
done

echo
echo "2. Docs"
for f in docs/PILOT_DEPLOYMENT.md docs/WHATSAPP_TLS.md docs/OPERATOR_RUNBOOK.md docs/GO_LIVE.md docs/HOST_REQUIREMENTS.md; do
  [[ -f "$f" ]] && ok "$f" || bad "Missing $f"
done

echo
echo "3. Scripts present"
for f in scripts/enable_live_mode.sh scripts/disable_live_mode.sh scripts/backup_offbox.sh scripts/check_netadmin.sh; do
  [[ -f "$f" ]] && ok "$f" || bad "Missing $f"
done

echo
echo "4. Runtime smoke"
if python3 -m agents.healthcheck >/tmp/cf_health_out.txt 2>&1; then
  ok "healthcheck runs"
else
  bad "healthcheck failed (see /tmp/cf_health_out.txt)"
fi
if python3 -m agents.watchdog_agent --once >/tmp/cf_wd_out.txt 2>&1; then
  ok "watchdog --once runs"
else
  bad "watchdog failed (see /tmp/cf_wd_out.txt)"
fi
if python3 playbooks/execute.py --list >/tmp/cf_pb_out.txt 2>&1; then
  ok "playbook list runs"
else
  bad "playbook list failed"
fi

echo
echo "5. Host netfilter (required for live CF_BLOCK)"
if ./scripts/check_netadmin.sh >/tmp/cf_netadmin.txt 2>&1; then
  ok "check_netadmin.sh passed"
else
  echo "  [INFO] check_netadmin failed — MONITORING only on this host (not a hard fail for preflight)"
  head -15 /tmp/cf_netadmin.txt | sed 's/^/         /'
fi

echo
echo "6. Sign-off (required before live mode)"
if [[ -f config/pilot_signoff.json ]]; then
  if ./scripts/enable_live_mode.sh --check >/tmp/cf_signoff.txt 2>&1; then
    ok "pilot_signoff.json valid for live mode"
  else
    bad "pilot_signoff.json incomplete (required before --enable)"
    cat /tmp/cf_signoff.txt | sed 's/^/         /'
  fi
else
  echo "  [INFO] No config/pilot_signoff.json yet (required only for live mode)"
fi

echo
echo "=============================================="
echo " Result: $PASS passed, $FAIL failed"
if [[ "$FAIL" -gt 0 ]]; then
  echo " Status: NOT client-ready until failures are fixed"
  exit 1
fi
echo " Status: Preflight OK — complete PILOT_DEPLOYMENT + HOST_REQUIREMENTS + ROE/NDA before live mode"
echo "=============================================="
