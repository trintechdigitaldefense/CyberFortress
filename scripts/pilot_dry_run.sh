#!/usr/bin/env bash
# CyberFortress — one-command pilot dry-run
# Usage:  bash scripts/pilot_dry_run.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
export CF_CONTAINMENT_LIVE=false
export CF_ALLOW_FORCE="${CF_ALLOW_FORCE:-false}"
export CF_CLIENT_NAME="${CF_CLIENT_NAME:-Pilot Demo Client}"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
  # Re-assert dry-run after .env (never let a stale .env force live during pilot drill)
  export CF_CONTAINMENT_LIVE=false
fi

exec python3 scripts/pilot_dry_run.py
