#!/usr/bin/env bash
# Verify an off-box backup and extract it to a NEW staging directory.
# Never overwrites the live logs/ or evidence/ directories.
set -euo pipefail

if [[ "$#" -lt 1 || "$#" -gt 2 ]]; then
  echo "Usage: $0 /path/to/cf_backup_YYYYMMDD_HHMMSS.tar.gz [staging-root]" >&2
  exit 2
fi

ARCHIVE="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
STAGING_ROOT="${2:-./restore_staging}"
SIDECAR="$ARCHIVE.sha256"

[[ -f "$ARCHIVE" ]] || { echo "[!] Backup archive not found: $ARCHIVE" >&2; exit 1; }
[[ -f "$SIDECAR" ]] || { echo "[!] SHA-256 sidecar missing: $SIDECAR" >&2; exit 1; }
command -v sha256sum >/dev/null 2>&1 || { echo "[!] sha256sum is required" >&2; exit 1; }

(
  cd "$(dirname "$ARCHIVE")"
  sha256sum -c "$(basename "$SIDECAR")"
)

python3 - "$ARCHIVE" "$STAGING_ROOT" <<'PY'
import shutil
import sys
import tarfile
from pathlib import Path, PurePosixPath

archive = Path(sys.argv[1]).resolve()
staging_root = Path(sys.argv[2]).resolve()
name = archive.name[:-7] if archive.name.endswith(".tar.gz") else ""
if not name or not name.startswith("cf_backup_"):
    raise SystemExit("Refusing archive with unexpected CyberFortress backup name")

staging_root.mkdir(parents=True, exist_ok=True)
destination = staging_root / name
if destination.exists():
    raise SystemExit(f"Refusing to overwrite existing staging directory: {destination}")

created = False
try:
    with tarfile.open(archive, "r:gz") as bundle:
        members = bundle.getmembers()
        if not members:
            raise ValueError("backup archive is empty")
        seen = set()
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != name:
                raise ValueError(f"unsafe archive path: {member.name}")
            if member.name in seen:
                raise ValueError(f"duplicate archive path: {member.name}")
            seen.add(member.name)
            if not (member.isdir() or member.isfile()):
                raise ValueError(f"unsupported archive member type: {member.name}")
        destination.mkdir(mode=0o700)
        created = True
        for member in members:
            relative = PurePosixPath(member.name).relative_to(name)
            target = destination.joinpath(*relative.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True, mode=0o700)
                continue
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            source = bundle.extractfile(member)
            if source is None:
                raise ValueError(f"unable to read archive member: {member.name}")
            with source, target.open("xb") as output:
                shutil.copyfileobj(source, output)
            target.chmod(0o600)
    manifest = destination / "BACKUP_MANIFEST.txt"
    if not manifest.is_file():
        raise ValueError("backup manifest is missing")
except Exception:
    if created:
        shutil.rmtree(destination, ignore_errors=True)
    raise

print(f"PASS: verified backup safely staged at {destination}")
print("No live files were overwritten. Review staged logs/ and evidence/ before a controlled restore.")
PY
