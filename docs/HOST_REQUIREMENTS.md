# CyberFortress host requirements

## Monitoring / dry-run (minimum)

- Linux (Ubuntu 22.04+ recommended)
- Python 3.10+
- Outbound HTTPS if using Meta WhatsApp
- Local ports 8089 / 8090 / 8091 / 8092 (bind localhost by default)

## Live containment candidate profile

- Native Ubuntu/Debian VM or bare metal
- Root or effective `CAP_NET_ADMIN`
- `iptables` binary and reachable netfilter backend
- Console/out-of-band recovery and an approved maintenance window
- Client-specific signed ROE, NDA, counsel review and E&O confirmation

Run:

```bash
./scripts/check_netadmin.sh
./scripts/pilot_vm_preflight.sh
./scripts/enable_live_mode.sh --check
```

The host check must create, verify, delete and clean up a temporary unreferenced firewall chain and rule. A read-only `iptables -L` is not sufficient. The test does not hook parent chains or modify production `CF_BLOCK`.

## Explicitly monitoring-only profiles

- Android Termux and Ubuntu proot (enforced by `start.sh`)
- Standard Docker Compose (no NET_ADMIN capability; LIVE=false enforced)
- Restricted or unprivileged containers
- Any host where the capability probe or firewall read-back fails

Do not use a privileged container or host-network Docker mode as a workaround. Such a profile requires a separate design, threat review and acceptance.

## Packages

```bash
# Debian/Ubuntu
sudo apt-get update && sudo apt-get install -y iptables rsync

# RHEL/CentOS
sudo yum install -y iptables rsync
```

Without iptables or effective capabilities, firewall containment is unavailable; monitoring may still operate.

## Safety and recovery

- `CF_CONTAINMENT_LIVE=false` by default.
- `CF_FIREWALL_AUTO_START=false` by default for client deployment.
- Dashboard/health/SOC endpoints bind to localhost; use a controlled SSH tunnel or approved admin VPN.
- Secrets stay in `.env` / approved secrets manager, never Git.
- `scripts/disable_live_mode.sh` disarms and flushes only `CF_BLOCK`, then verifies the chain is empty.
- Backups must be off-box, checksum-verified and staged before any restore.

See [PILOT_DEPLOYMENT.md](PILOT_DEPLOYMENT.md) and [PILOT_VM.md](PILOT_VM.md).
