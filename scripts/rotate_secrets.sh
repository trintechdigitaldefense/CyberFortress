#!/usr/bin/env bash
# Rotate local CyberFortress secrets in .env (does not print values).
# Usage:
#   ./scripts/rotate_secrets.sh
#   ./scripts/rotate_secrets.sh --keys CF_DASHBOARD_PASS,CF_SIEM_INGEST_TOKEN
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

ENV_FILE="${CF_ENV_FILE:-$ROOT/.env}"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "[!] No $ENV_FILE — copy from .env.example first"
  exit 1
fi

KEYS_ARG=""
if [[ "${1:-}" == "--keys" && -n "${2:-}" ]]; then
  KEYS_ARG="$2"
fi

python3 - <<PY
import os
from pathlib import Path
from core.secrets_mgmt import rotate_env_keys, check_env_permissions, redact

env = Path(os.environ.get("CF_ENV_FILE", "$ENV_FILE"))
keys = None
arg = "$KEYS_ARG".strip()
if arg:
    keys = [k.strip() for k in arg.split(",") if k.strip()]
updated = rotate_env_keys(env, keys)
ok, msg = check_env_permissions(env)
print(f"[+] Rotated {len(updated)} key(s) in {env}")
for k in sorted(updated):
    print(f"    {k} = {redact(updated[k])}")
print(f"[+] Permissions: {msg}" + ("" if ok else " — run: chmod 600 .env"))
print("[i] Update Meta / operators with new WhatsApp verify token if rotated")
print("[i] Restart agents after rotation: bash stop.sh && bash start.sh local")
PY
