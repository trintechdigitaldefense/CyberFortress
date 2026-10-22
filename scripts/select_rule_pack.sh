#!/usr/bin/env bash
# Select / show CyberFortress client rule pack (no live actions — rules only propose).
# Usage:
#   ./scripts/select_rule_pack.sh                  # show active + available
#   ./scripts/select_rule_pack.sh smb              # set CF_RULE_PACK_NAME in .env
#   ./scripts/select_rule_pack.sh retail --restart # set + restart local stack
#   ./scripts/select_rule_pack.sh --list
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PACK_DIR="$ROOT/config/rule_packs"
ENV_FILE="$ROOT/.env"
NAME="${1:-}"
RESTART=false

for arg in "$@"; do
  [[ "$arg" == "--restart" ]] && RESTART=true
done

list_packs() {
  echo "Available packs under config/rule_packs/:"
  for f in "$PACK_DIR"/*.yaml; do
    [[ -f "$f" ]] || continue
    id=$(grep -E '^pack_id:' "$f" | head -1 | sed 's/pack_id:[[:space:]]*//')
    desc=$(grep -E '^description:' "$f" | head -1 | sed 's/description:[[:space:]]*//' | tr -d '"')
    echo "  $(basename "$f")  pack_id=$id  $desc"
  done
  echo
  echo "Aliases: default | smb | retail | finance"
  echo "Env:     CF_RULE_PACK_NAME=smb   or   CF_RULE_PACK=config/rule_packs/smb_v1.yaml"
  echo "Tenant:  config/tenants/<id>/rule_pack.yaml when CF_TENANT_ID is set"
}

show_active() {
  local active="${CF_RULE_PACK_NAME:-}"
  if [[ -f "$ENV_FILE" ]]; then
    active=$(grep -E '^CF_RULE_PACK_NAME=' "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d '"' || true)
  fi
  active="${active:-default}"
  echo "Active (from .env / env): CF_RULE_PACK_NAME=${active}"
  python3 - <<'PY' 2>/dev/null || true
import os
from pathlib import Path
os.chdir(Path(".") if Path("core").exists() else Path("."))
try:
    from core.rules import pack_summary, load_pack
    p = load_pack(force=True)
    s = pack_summary()
    print(f"Loaded: pack_id={s.get('pack_id')} rules={s.get('rule_count')} path={s.get('path')}")
    print(f"Description: {p.get('description') or '—'}")
except Exception as e:
    print(f"(could not load pack: {e})")
PY
}

if [[ -z "$NAME" || "$NAME" == "--list" || "$NAME" == "list" ]]; then
  list_packs
  echo
  show_active
  exit 0
fi

case "$NAME" in
  default|default_v1|smb|smb_v1|retail|retail_v1|finance|finance_v1) ;;
  --restart) list_packs; show_active; exit 0 ;;
  *)
    if [[ -f "$PACK_DIR/${NAME}.yaml" ]]; then
      :
    elif [[ -f "$PACK_DIR/$NAME" ]]; then
      NAME="${NAME%.yaml}"
    else
      echo "[!] Unknown pack: $NAME"
      list_packs
      exit 1
    fi
    ;;
esac

case "$NAME" in
  default_v1) NAME=default ;;
  smb_v1) NAME=smb ;;
  retail_v1) NAME=retail ;;
  finance_v1) NAME=finance ;;
esac

touch "$ENV_FILE"
chmod 600 "$ENV_FILE"
if grep -q '^CF_RULE_PACK_NAME=' "$ENV_FILE" 2>/dev/null; then
  sed -i.bak "s|^CF_RULE_PACK_NAME=.*|CF_RULE_PACK_NAME=$NAME|" "$ENV_FILE"
  rm -f "${ENV_FILE}.bak"
else
  echo "CF_RULE_PACK_NAME=$NAME" >> "$ENV_FILE"
fi

echo "[+] Set CF_RULE_PACK_NAME=$NAME in $ENV_FILE"
export CF_RULE_PACK_NAME="$NAME"
show_active

if $RESTART; then
  echo "[+] Restarting local stack..."
  if [[ -x "$ROOT/stop.sh" ]]; then "./stop.sh" || true; fi
  if [[ -x "$ROOT/start.sh" ]]; then "./start.sh" local; fi
fi

echo
echo "Dashboard → Rule pack KPI should show the new pack after refresh."
echo "Rules only propose actions; LIVE + ROE + Tier-2 still gate execution."
