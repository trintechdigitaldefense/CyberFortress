#!/usr/bin/env bash
# Approve the newest pending Tier-2 request (lab/mock only).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PENDING="${CF_WHATSAPP_PENDING_DIR:-$ROOT/logs/whatsapp_pending}"
latest=$(ls -t "$PENDING"/*.json 2>/dev/null | head -1 || true)
if [[ -z "${latest:-}" ]]; then
  echo "No pending Tier-2 requests in $PENDING"
  exit 1
fi
rid=$(basename "$latest" .json)
nonce=$(python3 -c "import json;print(json.load(open('$latest')).get('nonce',''))")
echo "{\"decision\":\"APPROVE\",\"nonce_ok\":true,\"sender_hash\":\"mock-drill\",\"nonce\":\"$nonce\"}" \
  > "$PENDING/${rid}.decision"
echo "Wrote APPROVE for $rid nonce=$nonce"
