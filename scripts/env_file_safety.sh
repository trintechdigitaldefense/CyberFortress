#!/usr/bin/env bash
# Verify that configuration is parsed as data, never evaluated as shell.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT
SENTINEL="$TMP/should-not-exist"
cat > "$TMP/.env" <<EOF
CF_TEST_VALUE=hello world
CF_TEST_LITERAL=\$(touch "$SENTINEL")
PATH=/malicious/path
# comment
EOF
source "$ROOT/scripts/load_env.sh"
load_cyberfortress_env "$TMP/.env"
[[ "${CF_TEST_VALUE:-}" == "hello world" ]]
[[ "${CF_TEST_LITERAL:-}" == "\$(touch "$SENTINEL")" ]]
[[ ! -e "$SENTINEL" ]]
[[ "$PATH" != "/malicious/path" ]]
echo "PASS: .env is parsed as data and cannot execute shell commands"
