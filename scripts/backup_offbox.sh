#!/usr/bin/env bash
# CyberFortress off-box backup for logs/ and evidence/
# Prefer rsync/scp to a remote host or mounted volume outside the primary box.
#
# Usage:
#   export CF_BACKUP_DEST=/mnt/offbox/cyberfortress-backups
#   # or: export CF_BACKUP_DEST=user@backup-host:/path/cf-backups
#   ./scripts/backup_offbox.sh
#
# Cron example (daily 02:15):
#   15 2 * * * cd /opt/CyberFortress && ./scripts/backup_offbox.sh >> logs/backup.log 2>&1

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${CF_BACKUP_DEST:-}"
STAMP="$(date -u +%Y%m%d_%H%M%S)"
NAME="cf_backup_${STAMP}"

if [[ -z "$DEST" ]]; then
  echo "[!] Set CF_BACKUP_DEST to an off-box path or user@host:/path"
  echo "    Example: export CF_BACKUP_DEST=/mnt/nas/cyberfortress-backups"
  exit 1
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/$NAME"

# Copy critical operational data
[[ -d "$ROOT/logs" ]] && rsync -a --exclude 'whatsapp_pending/*.decision' "$ROOT/logs/" "$TMP/$NAME/logs/" || true
[[ -d "$ROOT/evidence" ]] && rsync -a "$ROOT/evidence/" "$TMP/$NAME/evidence/" || true

# Manifest
{
  echo "generated_utc=$STAMP"
  echo "host=$(hostname -f 2>/dev/null || hostname)"
  echo "containment_live=${CF_CONTAINMENT_LIVE:-false}"
  find "$TMP/$NAME" -type f | wc -l | xargs -I{} echo "file_count={}"
} > "$TMP/$NAME/BACKUP_MANIFEST.txt"

ARCHIVE="$TMP/${NAME}.tar.gz"
tar -C "$TMP" -czf "$ARCHIVE" "$NAME"

echo "[+] Archive: $ARCHIVE ($(du -h "$ARCHIVE" | cut -f1))"

if [[ "$DEST" == *:* ]] && [[ "$DEST" != /* ]]; then
  # remote scp target user@host:path
  scp -q "$ARCHIVE" "$DEST/"
  echo "[+] Uploaded to $DEST/"
else
  mkdir -p "$DEST"
  cp "$ARCHIVE" "$DEST/"
  echo "[+] Copied to $DEST/$(basename "$ARCHIVE")"
fi

echo "[+] Off-box backup complete"
