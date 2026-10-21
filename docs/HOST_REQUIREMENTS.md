# CyberFortress host requirements

## Minimum (MONITORING / dry-run)

- Linux (Ubuntu 22.04+ recommended)
- Python 3.10+
- Outbound HTTPS if using Meta WhatsApp
- Local ports 8089 / 8090 / 8091 (bind localhost by default)

## Live containment (armed DROP)

- Root or CAP_NET_ADMIN
- `iptables` binary on PATH
- Real VM or bare metal (or privileged container)

```bash
./scripts/check_netadmin.sh
./scripts/pilot_vm_preflight.sh
```

Both must be **green** before `./scripts/enable_live_mode.sh --enable`.

## Packages

```bash
# Debian/Ubuntu
sudo apt-get update && sudo apt-get install -y iptables

# RHEL/CentOS
sudo yum install -y iptables
```

Without the `iptables` binary, firewall mode stays **UNAVAILABLE** (MONITORING still works).

## Safety defaults

- `CF_CONTAINMENT_LIVE=false` until pilot sign-off
- Dashboard/health on localhost — tunnel or reverse proxy for remote ops
- Secrets only in `.env` / secrets manager (never committed)
