# CyberFortress Host Requirements (Live Firewall)

**TrinTech Digital Defense**

Live `CF_BLOCK` DROP rules need a host that can talk to Linux netfilter.  
Restricted containers (no `CAP_NET_ADMIN`) stay **UNAVAILABLE** — detection, audit, WhatsApp, and evidence still work.

---

## Minimum for MONITORING (no live DROP)

| Requirement | Notes |
|-------------|--------|
| Linux x86_64 or aarch64 | Ubuntu 22.04+ / Debian 12 recommended |
| Python 3.10+ | `./install.sh` |
| Disk for `logs/` + `evidence/` | Off-box backup recommended |
| Outbound HTTPS | Meta WhatsApp API (if enabled) |

---

## Extra for LIVE containment (CF_BLOCK)

| Requirement | Why |
|-------------|-----|
| **Real VM or bare metal** | Not a locked-down nested container |
| **`iptables` (or iptables-legacy)** on PATH | Backend for CF_BLOCK |
| **`CAP_NET_ADMIN`** (and usually `CAP_NET_RAW`) | Create chains / DROP rules |
| Root or equivalent for first `ensure_chain` | Chain create + INPUT/OUTPUT jump |
| Signed **ROE** + **`config/pilot_signoff.json`** | Legal allow-list before arming |
| `CF_CONTAINMENT_LIVE=true` via `enable_live_mode.sh` only | Never hand-edit casually |

### Quick capability check

```bash
./scripts/check_netadmin.sh
```

Expect iptables present, netfilter usable, status not UNAVAILABLE.

If you see **Permission denied** / **UNAVAILABLE**, do **not** arm live mode on that host.

---

## Recommended deploy patterns

### A. KVM / cloud VM (preferred for pilots)

1. Provision Ubuntu 22.04 VM (2 vCPU, 4 GB RAM minimum).  
2. Install CyberFortress; run as root or with sudo for firewall agent.  
3. `./scripts/check_netadmin.sh` → green.  
4. Complete NDA/ROE → `pilot_signoff.json` → `./scripts/enable_live_mode.sh --enable`.

### B. Docker with capabilities

Firewall service in `docker/docker-compose.yml` includes:

```yaml
cap_add:
  - NET_ADMIN
  - NET_RAW
```

Host kernel must still allow netfilter.

### C. What will **not** work for DROP

- Many LXC/OpenVZ “VPS” without netfilter  
- Unprivileged containers without `NET_ADMIN`  
- Hosts where `iptables -L` returns Permission denied  

On those hosts: keep **MONITORING** only.

---

## Operator sequence (live firewall)

1. `./scripts/check_netadmin.sh` — pass  
2. NDA + ROE signed (`docs/templates/`)  
3. `cp config/pilot_signoff.example.json config/pilot_signoff.json` and fill **all** fields  
4. `./scripts/enable_live_mode.sh --check` then `--enable`  
5. `./stop.sh && ./start.sh`  
6. Confirm firewall API shows RUNNING/ARMED  

See [GO_LIVE.md](GO_LIVE.md) · [PILOT_DEPLOYMENT.md](PILOT_DEPLOYMENT.md).
