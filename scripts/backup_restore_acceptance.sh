#!/usr/bin/env bash
# Disposable backup/restore acceptance. Never touches real client data.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

FIXTURE="$TMP/source"
DEST="$TMP/offbox"
STAGE="$TMP/staged"
mkdir -p "$FIXTURE/logs/whatsapp_pending" "$FIXTURE/evidence"
printf '%s\n' 'synthetic operator log' > "$FIXTURE/logs/operator.log"
printf '%s\n' 'synthetic evidence artifact' > "$FIXTURE/evidence/sample.txt"
printf '%s\n' 'synthetic pending request with nonce' > "$FIXTURE/logs/whatsapp_pending/sample.json"
printf '%s\n' 'synthetic pending decision must not be backed up' > "$FIXTURE/logs/whatsapp_pending/sample.decision"

CF_ROOT="$FIXTURE" CF_BACKUP_DEST="$DEST" bash "$ROOT/scripts/backup_offbox.sh"
ARCHIVE="$(find "$DEST" -maxdepth 1 -type f -name 'cf_backup_*.tar.gz' -print -quit)"
[[ -n "$ARCHIVE" && -f "$ARCHIVE.sha256" ]]

bash "$ROOT/scripts/restore_offbox.sh" "$ARCHIVE" "$STAGE"
NAME="$(basename "$ARCHIVE" .tar.gz)"
RESTORED="$STAGE/$NAME"
cmp "$FIXTURE/logs/operator.log" "$RESTORED/logs/operator.log"
cmp "$FIXTURE/evidence/sample.txt" "$RESTORED/evidence/sample.txt"
[[ ! -e "$RESTORED/logs/whatsapp_pending/sample.decision" ]]
[[ ! -e "$RESTORED/logs/whatsapp_pending/sample.json" ]]
[[ -f "$RESTORED/BACKUP_MANIFEST.txt" ]]

# The restore command must refuse to overwrite an existing staging target.
if bash "$ROOT/scripts/restore_offbox.sh" "$ARCHIVE" "$STAGE"; then
  echo "FAIL: restore unexpectedly overwrote an existing staging directory" >&2
  exit 1
fi

echo "PASS: off-box backup, checksum verification, safe staging and no-overwrite recovery"
