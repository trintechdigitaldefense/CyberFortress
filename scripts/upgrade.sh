#!/usr/bin/env bash
# Fast-forward-only, rollback-capable source upgrade.
# Usage: bash scripts/upgrade.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

command -v git >/dev/null 2>&1 || { echo "[!] git is required" >&2; exit 1; }
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "[!] Not a Git checkout" >&2; exit 1; }

BRANCH="$(git branch --show-current)"
[[ -n "$BRANCH" ]] || { echo "[!] Detached HEAD; checkout a branch before upgrading" >&2; exit 1; }
UPSTREAM="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
[[ -n "$UPSTREAM" ]] || { echo "[!] No upstream configured for $BRANCH; refusing an ambiguous upgrade" >&2; exit 1; }

if [[ -n "$(git status --porcelain --untracked-files=normal)" ]]; then
  echo "[!] Working tree is not clean. Commit or safely move local changes before upgrading." >&2
  exit 1
fi

BEFORE="$(git rev-parse HEAD)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
ROLLBACK_REF="refs/cyberfortress/rollback/$STAMP"
git update-ref "$ROLLBACK_REF" "$BEFORE"

echo "[+] Fetching upstream updates..."
git fetch --prune
git merge-base --is-ancestor "$BEFORE" "$UPSTREAM" || {
  echo "[!] Local branch is ahead of or diverged from upstream; refusing non-fast-forward update." >&2
  exit 1
}
git merge --ff-only "$UPSTREAM"

echo "[+] Updating isolated Python environment..."
if ! bash "$ROOT/install.sh"; then
  echo "[!] Dependency installation failed; restoring source to $BEFORE" >&2
  git reset --hard "$BEFORE"
  echo "[!] Python environment may contain partial dependency updates; rerun install.sh after resolving the cause." >&2
  exit 1
fi

echo "[+] Upgrade completed."
echo "    Previous source retained at $ROLLBACK_REF"
echo "    Review release notes, then restart CyberFortress during an approved maintenance window."
