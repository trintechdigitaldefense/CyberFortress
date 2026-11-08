#!/usr/bin/env bash
# Verify that configuration is parsed as data, never evaluated as shell.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT
SENTINEL="$TMP/should-not-exist"
printf 'CF_TEST_VALUE=hello world\n' > "$TMP/.env"
printf 'CF_TEST_LITERAL=$(touch "%s")\n' "$SENTINEL" >> "$TMP/.env"
printf 'PATH=/malicious/path\n# comment\n' >> "$TMP/.env"
source "$ROOT/scripts/load_env.sh"
load_cyberfortress_env "$TMP/.env"
expected="$(printf '$(touch "%s")' "$SENTINEL")"
[[ "${CF_TEST_VALUE:-}" == "hello world" ]]
[[ "${CF_TEST_LITERAL:-}" == "$expected" ]]
[[ ! -e "$SENTINEL" ]]
[[ "$PATH" != "/malicious/path" ]]
echo "PASS: .env is parsed as data and cannot execute shell commands"
