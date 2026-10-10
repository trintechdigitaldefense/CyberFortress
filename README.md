# CyberFortress

**Autonomous Incident Response & Operations Platform**  
*TrinTech Digital Defense · Trinidad & Tobago* 🇹🇹  
**PROTECTED ASSET**

---

## Overview

CyberFortress is a containerized autonomous security platform built for Caribbean enterprise environments.  
It reduces Mean Time to Containment (MTTC) while staying aligned with the Trinidad & Tobago Computer Misuse Act.

**Before any client deployment:** complete **[docs/PILOT_DEPLOYMENT.md](docs/PILOT_DEPLOYMENT.md)**.

---

## Hardening (enforced in repo)

| Control | Default |
|---------|--------|
| `CF_CONTAINMENT_LIVE` | `false` until pilot sign-off |
| `CF_WATCHDOG_FAIL_CLOSED` | `true` (24/7 fail-closed) |
| `CF_ALLOW_FORCE` | `false` — prefer WhatsApp APPROVE |
| Dashboard / health / webhook | Bound to `127.0.0.1` only |
| Containers | Non-root user `cfops` (uid 10001) |
| Secrets | `.env` only — never commit (see `.env.example`) |
| WhatsApp TLS | Reverse proxy example: `docker/caddy.whatsapp.example` |
| Off-box backup | `scripts/backup_offbox.sh` for `logs/` + `evidence/` |

```bash
cp .env.example .env && chmod 600 .env
# Keep CF_CONTAINMENT_LIVE=false until pilot sign-off
```

---

## Capabilities

| Feature | Status |
|---------|--------|
| Tiered Autonomy + WhatsApp HITL | ✅ |
| Legal mapping (TT CMA) | ✅ |
| Smart Escalation | ✅ |
| Telemetry Fusion (file + API) | ✅ |
| Containment Drivers | ✅ |
| Identity Providers (Linux / LDAP / Azure AD) | ✅ |
| Evidence Pack | ✅ |
| Circuit Breaker | ✅ |
| Real-Time Dashboard (`127.0.0.1:8091`) | ✅ |
| Health Check (`127.0.0.1:8090`) | ✅ |
| 24/7 Self-Monitoring Watchdog | ✅ |
| Off-box backup script | ✅ |

---

## Quick Start

```bash
git clone https://github.com/trintechdigitaldefense/CyberFortress.git
cd CyberFortress
pip install -r requirements.txt
cp .env.example .env && chmod 600 .env

python3 -m agents.healthcheck
python3 -m agents.watchdog_agent --once
python3 playbooks/execute.py --list

# Dashboard (local only)
python3 -m agents.dashboard   # http://127.0.0.1:8091

# Off-box backup
export CF_BACKUP_DEST=/mnt/offbox/cyberfortress-backups
./scripts/backup_offbox.sh
```

Admin remote access via SSH tunnel:

```bash
ssh -L 8091:127.0.0.1:8091 -L 8090:127.0.0.1:8090 user@cf-host
```

---

## Client readiness

**Pilot-ready (supervised):** Yes — dry-run default, ROE/NDA, operator on watch.  
**Unsupervised 24/7 production:** Only after full pilot checklist + live WhatsApp TLS + intentional `CF_CONTAINMENT_LIVE=true`.

---

## Docker

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

| Service | Bind |
|---------|------|
| Dashboard | `127.0.0.1:8091` |
| Health | `127.0.0.1:8090` |
| WhatsApp Webhook | `127.0.0.1:8089` (TLS proxy in front) |
| Watchdog | internal, fail-closed on |

---

## Contact

**TrinTech Digital Defense**  
Email: trintechdigitaldefense@gmail.com  
WhatsApp: +1 (868) 362-0679  
Web: https://trintechdigitaldefense.github.io

---

*Defend. Detect. Dominate.*  
Authorized defensive use only. All rights reserved.
