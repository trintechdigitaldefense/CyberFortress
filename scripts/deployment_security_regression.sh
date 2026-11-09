#!/usr/bin/env bash
# Static release gate for systemd privilege boundaries and isolated installs.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENT="$ROOT/deploy/systemd/cyberfortress-agent@.service"
FIREWALL="$ROOT/deploy/systemd/cyberfortress-firewall.service"
INSTALLER="$ROOT/deploy/systemd/install_systemd.sh"

grep -q '^User=cyberfortress$' "$AGENT"
grep -q '^Group=cyberfortress$' "$AGENT"
grep -q '^NoNewPrivileges=true$' "$AGENT"
grep -q '^ProtectSystem=strict$' "$AGENT"
grep -q '^ExecStart=/opt/CyberFortress/.venv/bin/python ' "$AGENT"
grep -q '^User=cyberfortress$' "$FIREWALL"
grep -q '^CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_RAW$' "$FIREWALL"
grep -q '^AmbientCapabilities=CAP_NET_ADMIN CAP_NET_RAW$' "$FIREWALL"
grep -q '^NoNewPrivileges=true$' "$FIREWALL"
grep -q 'useradd --system --gid cyberfortress' "$INSTALLER"
grep -q 'chown -R cyberfortress:cyberfortress' "$INSTALLER"
! grep -q '^User=root$' "$AGENT"
! grep -q '^User=root$' "$FIREWALL"

python3 - "$ROOT" <<'PY'
import sys
from pathlib import Path

root = Path(sys.argv[1])
for rel in ("agents/dashboard.py", "agents/soc_api_agent.py"):
    source = (root / rel).read_text()
    assert source.count("assert_single_tenant_runtime()") >= 2, f"{rel} lacks GET/POST tenant guard"
rbac = (root / "core/soc/rbac.py").read_text()
assert "if role is None:\n        return False" in rbac
print("PASS: dashboard and SOC API enforce isolated tenant runtime and fail-closed RBAC")
PY

echo "PASS: systemd agents run unprivileged; firewall has only bounded network capabilities"
