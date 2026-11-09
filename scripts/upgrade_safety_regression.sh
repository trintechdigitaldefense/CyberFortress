#!/usr/bin/env bash
# Exercise fast-forward upgrade and dirty-tree refusal using a local bare remote.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf -- "$TMP"' EXIT

git init --bare "$TMP/origin.git" >/dev/null
git init -b main "$TMP/source" >/dev/null
git -C "$TMP/source" config user.name "CyberFortress CI"
git -C "$TMP/source" config user.email "ci@example.invalid"
mkdir -p "$TMP/source/scripts"
printf '#!/usr/bin/env bash\nexit 0\n' > "$TMP/source/install.sh"
cp "$ROOT/scripts/upgrade.sh" "$TMP/source/scripts/upgrade.sh"
printf 'initial\n' > "$TMP/source/README.md"
git -C "$TMP/source" add .
git -C "$TMP/source" commit -m initial >/dev/null
git -C "$TMP/source" remote add origin "$TMP/origin.git"
git -C "$TMP/source" push -u origin main >/dev/null

git clone "$TMP/origin.git" "$TMP/client" >/dev/null 2>&1
git -C "$TMP/client" config user.name "CyberFortress CI"
git -C "$TMP/client" config user.email "ci@example.invalid"

printf 'updated\n' >> "$TMP/source/README.md"
git -C "$TMP/source" add README.md
git -C "$TMP/source" commit -m update >/dev/null
git -C "$TMP/source" push origin main >/dev/null

BEFORE="$(git -C "$TMP/client" rev-parse HEAD)"
bash "$TMP/client/scripts/upgrade.sh"
AFTER="$(git -C "$TMP/client" rev-parse HEAD)"
[[ "$BEFORE" != "$AFTER" ]]
git -C "$TMP/client" show-ref --verify --quiet "$(git -C "$TMP/client" for-each-ref --format='%(refname)' refs/cyberfortress/rollback | head -n 1)"

touch "$TMP/client/dirty-file"
if bash "$TMP/client/scripts/upgrade.sh" >/dev/null 2>&1; then
  echo "FAIL: upgrade accepted a dirty working tree" >&2
  exit 1
fi

echo "PASS: fast-forward upgrade, rollback ref and dirty-tree refusal"
