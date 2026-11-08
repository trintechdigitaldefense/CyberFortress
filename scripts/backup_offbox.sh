#!/usr/bin/env bash
# Create and verify an off-box backup of operational logs and evidence.
# Secrets, .env, sign-off files and pending WhatsApp decisions are excluded.
set -euo pipefail

ROOT="${CF_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
DEST="${CF_BACKUP_DEST:-}"
STAMP="$(date -u +%Y%m%d_%H%M%S)"
NAME="cf_backup_${STAMP}"

if [[ -z "$DEST" ]]; then
  echo "[!] Set CF_BACKUP_DEST to an off-box path or user@host:/path" >&2
  exit 1
fi
for cmd in rsync tar sha256sum; do
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "[!] Required backup command missing: $cmd" >&2
    exit 1
  }
done
[[ -d "$ROOT" ]] || { echo "[!] Backup source root missing: $ROOT" >&2; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/$NAME/logs" "$TMP/$NAME/evidence"

if [[ -d "$ROOT/logs" ]]; then
  rsync -a --exclude 'whatsapp_pending/***' "$ROOT/logs/" "$TMP/$NAME/logs/"
fi
if [[ -d "$ROOT/evidence" ]]; then
  rsync -a "$ROOT/evidence/" "$TMP/$NAME/evidence/"
fi

{
  echo "generated_utc=$STAMP"
  echo "host=$(hostname -f 2>/dev/null || hostname)"
  echo "containment_live=${CF_CONTAINMENT_LIVE:-false}"
  echo "source_profile=logs+evidence_only"
  echo "file_count=$(find "$TMP/$NAME" -type f | wc -l | tr -d ' ')"
} > "$TMP/$NAME/BACKUP_MANIFEST.txt"

ARCHIVE="$TMP/${NAME}.tar.gz"
tar -C "$TMP" -czf "$ARCHIVE" "$NAME"
tar -tzf "$ARCHIVE" >/dev/null
(
  cd "$TMP"
  sha256sum "$(basename "$ARCHIVE")" > "$(basename "$ARCHIVE").sha256"
)

if [[ "$DEST" == *:* ]] && [[ "$DEST" != /* ]]; then
  scp -q "$ARCHIVE" "$ARCHIVE.sha256" "$DEST/"
  echo "[+] Uploaded archive and SHA-256 sidecar to $DEST/"
else
  mkdir -p "$DEST"
  cp "$ARCHIVE" "$ARCHIVE.sha256" "$DEST/"
  echo "[+] Copied archive and SHA-256 sidecar to $DEST/"
fi

echo "[+] Backup archive integrity verified before transfer."
echo "[+] Backup complete: $(basename "$ARCHIVE")"
