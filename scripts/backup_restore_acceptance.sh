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

# Reject a checksum-mismatched archive.
cp "$ARCHIVE" "$TMP/corrupt.tar.gz"
printf 'tamper' >> "$TMP/corrupt.tar.gz"
(cd "$(dirname "$ARCHIVE")" && sha256sum "$(basename "$ARCHIVE")") | sed "s|$(basename "$ARCHIVE")|corrupt.tar.gz|" > "$TMP/corrupt.tar.gz.sha256"
if bash "$ROOT/scripts/restore_offbox.sh" "$TMP/corrupt.tar.gz" "$TMP/corrupt-stage"; then
  echo "FAIL: restore accepted a checksum-mismatched archive" >&2
  exit 1
fi

# Reject traversal and special-file members even when the archive checksum is valid.
python3 - "$TMP" <<'PY'
import io
import sys
import tarfile
from pathlib import Path

root = Path(sys.argv[1])
for filename, member_name, member_type in (
    ("cf_backup_traversal.tar.gz", "cf_backup_traversal/../../escape.txt", tarfile.REGTYPE),
    ("cf_backup_symlink.tar.gz", "cf_backup_symlink/link", tarfile.SYMTYPE),
):
    path = root / filename
    with tarfile.open(path, "w:gz") as archive:
        info = tarfile.TarInfo(member_name)
        info.type = member_type
        if member_type == tarfile.REGTYPE:
            payload = b"escape"
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
        else:
            info.linkname = "/etc/passwd"
            archive.addfile(info)
PY
for BAD in "$TMP/cf_backup_traversal.tar.gz" "$TMP/cf_backup_symlink.tar.gz"; do
  sha256sum "$BAD" > "$BAD.sha256"
  if bash "$ROOT/scripts/restore_offbox.sh" "$BAD" "$TMP/bad-stage"; then
    echo "FAIL: restore accepted an unsafe archive member in $BAD" >&2
    exit 1
  fi
done
[[ ! -e "$TMP/escape.txt" ]]

# Simulate interrupted source-copy and storage-write failures.
FAILBIN="$TMP/failbin"
mkdir -p "$FAILBIN"
printf '#!/usr/bin/env sh\nexit 23\n' > "$FAILBIN/rsync"
chmod +x "$FAILBIN/rsync"
if PATH="$FAILBIN:$PATH" CF_ROOT="$FIXTURE" CF_BACKUP_DEST="$TMP/rsync-fail" bash "$ROOT/scripts/backup_offbox.sh"; then
  echo "FAIL: backup accepted an interrupted rsync copy" >&2
  exit 1
fi
printf '#!/usr/bin/env sh\nexit 28\n' > "$FAILBIN/tar"
chmod +x "$FAILBIN/tar"
if PATH="$FAILBIN:$PATH" CF_ROOT="$FIXTURE" CF_BACKUP_DEST="$TMP/tar-fail" bash "$ROOT/scripts/backup_offbox.sh"; then
  echo "FAIL: backup accepted a simulated storage-write failure" >&2
  exit 1
fi
printf 'not-a-directory\n' > "$TMP/blocked-destination"
if CF_ROOT="$FIXTURE" CF_BACKUP_DEST="$TMP/blocked-destination" bash "$ROOT/scripts/backup_offbox.sh"; then
  echo "FAIL: backup accepted a destination permission/type failure" >&2
  exit 1
fi

echo "PASS: backup/restore integrity, traversal/symlink rejection, interrupted-copy and write-failure recovery"
