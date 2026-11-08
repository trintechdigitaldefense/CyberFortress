#!/usr/bin/env bash
# Disarm live containment and remove rules from the dedicated CF_BLOCK chain.
# Does not delete parent-chain hooks or alter unrelated host firewall policy.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"
cd "$ROOT"

echo "[!] Disabling live containment..."

if [[ ! -f "$ENV_FILE" ]]; then
  install -m 600 /dev/null "$ENV_FILE"
fi
if grep -q '^CF_CONTAINMENT_LIVE=' "$ENV_FILE"; then
  sed -i.bak 's/^CF_CONTAINMENT_LIVE=.*/CF_CONTAINMENT_LIVE=false/' "$ENV_FILE"
  rm -f "$ENV_FILE.bak"
else
  printf '%s\n' 'CF_CONTAINMENT_LIVE=false' >> "$ENV_FILE"
fi
chmod 600 "$ENV_FILE"
export CF_CONTAINMENT_LIVE=false

echo "[+] CF_CONTAINMENT_LIVE=false written to .env"

if ! command -v iptables >/dev/null 2>&1; then
  echo "[!] iptables is unavailable; cannot prove whether stale CF_BLOCK rules remain." >&2
  echo "[!] Live mode is disarmed in .env, but host firewall recovery requires an operator." >&2
  exit 1
fi

if iptables -L -n >/dev/null 2>&1; then
  if iptables -L CF_BLOCK -n >/dev/null 2>&1; then
    echo "[*] Clearing only the dedicated CF_BLOCK chain..."
    iptables -F CF_BLOCK
    # Verify that the chain contains no rules. -S emits only '-N CF_BLOCK'
    # when the chain exists and is empty.
    RULES="$(iptables -S CF_BLOCK)"
    if [[ "$RULES" != "-N CF_BLOCK" ]]; then
      echo "[!] CF_BLOCK is not empty after flush; manual recovery required." >&2
      printf '%s\n' "$RULES" >&2
      exit 1
    fi
    echo "[+] CF_BLOCK is empty; existing CyberFortress DROP rules were removed."
  else
    echo "[+] CF_BLOCK does not exist; no CyberFortress chain rules to clear."
  fi
else
  echo "[!] iptables cannot inspect the host firewall; stale rules cannot be ruled out." >&2
  exit 1
fi

echo "[+] Live containment is disarmed and CF_BLOCK rollback verified."
echo "[+] Restart services to apply the disarmed mode:"
echo "    ./stop.sh && ./start.sh"
echo "[+] Parent-chain hooks are intentionally retained; they reference an empty CF_BLOCK."
echo "[+] See docs/OPERATOR_RUNBOOK.md"
