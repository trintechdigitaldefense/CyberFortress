#!/usr/bin/env bash
# Client-readiness preflight — run before any client pilot or go-live.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

PASS=0
FAIL=0

ok() { echo "  [PASS] $1"; PASS=$((PASS+1)); }
bad() { echo "  [FAIL] $1"; FAIL=$((FAIL+1)); }

echo "=============================================="
echo " CyberFortress Client-Readiness Check"
echo "=============================================="

echo
echo "1. Safety defaults"
if [[ "${CF_CONTAINMENT_LIVE:-false}" == "true" ]]; then
  bad "CF_CONTAINMENT_LIVE is true (expected false until go-live)"
else
  ok "CF_CONTAINMENT_LIVE is false (safe default)"
fi
if [[ "${CF_ALLOW_FORCE:-false}" == "true" ]]; then
  bad "CF_ALLOW_FORCE is true (prefer WhatsApp APPROVE)"
else
  ok "CF_ALLOW_FORCE is false"
fi

echo
echo "2. Documentation present"
for f in docs/PILOT_DEPLOYMENT.md docs/WHATSAPP_TLS.md docs/OPERATOR_RUNBOOK.md docs/GO_LIVE.md; do
  [[ -f "$f" ]] && ok "$f" || bad "Missing $f"
done

echo
echo "3. Scripts present"
for f in scripts/enable_live_mode.sh scripts/disable_live_mode.sh scripts/backup_offbox.sh; do
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
echo "5. Sign-off (optional until go-live)"
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
echo " Status: Preflight OK — complete PILOT_DEPLOYMENT + WHATSAPP_TLS + operator process before live mode"
echo "=============================================="
