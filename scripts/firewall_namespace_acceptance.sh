#!/usr/bin/env bash
# Run only inside a dedicated disposable Linux VM as root.
# All iptables changes are confined to a newly-created network namespace.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for cmd in ip iptables python3; do
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "Missing required command: $cmd" >&2
    exit 2
  }
done

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run this acceptance harness as root inside a disposable Linux VM." >&2
  exit 2
fi

NS="cf-acceptance-$$"
TMP="$(mktemp -d)"
SIGNOFF="$TMP/pilot_signoff.json"
printf '%s\n' '{"authorized_actions":["block_ip","unblock_ip"]}' > "$SIGNOFF"
chmod 600 "$SIGNOFF"

cleanup() {
  if ip netns list | awk '{print $1}' | grep -Fxq "$NS"; then
    ip netns del "$NS"
  fi
  rm -rf "$TMP"
}
trap cleanup EXIT INT TERM

ip netns add "$NS"
ip netns exec "$NS" ip link set lo up

echo "Running isolated CyberFortress firewall apply/verify/rollback acceptance in $NS"
ip netns exec "$NS" env \
  PYTHONPATH="$ROOT" \
  CF_CONTAINMENT_LIVE=true \
  CF_FIREWALL_AUTO_START=false \
  CF_PILOT_SIGNOFF="$SIGNOFF" \
  python3 - <<'PY'
from core.containment import firewall

target = "8.8.8.8"
applied = firewall.block_ip(target, dry_run=False)
assert applied.get("success") is True, applied
assert applied.get("verify", {}).get("verified") is True, applied
assert applied.get("verify", {}).get("bidirectional") is True, applied
print("PASS: live DROP rules applied and bidirectionally verified inside isolated namespace")

restored = firewall.unblock_ip(target, dry_run=False)
assert restored.get("success") is True, restored
assert restored.get("verify", {}).get("cleared") is True, restored
print("PASS: DROP rules removed and rollback read-back verified inside isolated namespace")

# Re-arm only inside this disposable namespace, then exercise the operator
# emergency-disarm script against a temporary env file.
applied = firewall.block_ip(target, dry_run=False, comment="acceptance-disarm")
assert applied.get("success") is True, applied
print("PASS: re-applied test rules for emergency-disarm acceptance")
PY

printf '%s\\n' 'CF_CONTAINMENT_LIVE=true' > "$TMP/cf.env"
ip netns exec "$NS" env \\
  PATH="$PATH" \\
  CF_ENV_FILE="$TMP/cf.env" \\
  bash "$ROOT/scripts/disable_live_mode.sh"
grep -Fxq 'CF_CONTAINMENT_LIVE=false' "$TMP/cf.env"
ip netns exec "$NS" iptables -L CF_BLOCK -n | grep -q '^Chain CF_BLOCK'
if ip netns exec "$NS" iptables -S CF_BLOCK | grep -qv '^-N CF_BLOCK

echo "PASS: isolated firewall acceptance completed; namespace cleanup will remove all test rules."
; then
  echo "FAIL: CF_BLOCK still contains rules after emergency disarm" >&2
  exit 1
fi
echo "PASS: emergency disarm disabled live mode and emptied CF_BLOCK"


echo "PASS: isolated firewall acceptance completed; namespace cleanup will remove all test rules."
