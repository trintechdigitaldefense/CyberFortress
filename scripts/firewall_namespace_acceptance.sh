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
  ip netns del "$NS" >/dev/null 2>&1 || true
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
PY

echo "PASS: isolated firewall acceptance completed; namespace cleanup will remove all test rules."
