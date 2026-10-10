# CyberFortress

**Autonomous Incident Response & Operations Platform**  
*TrinTech Digital Defense · Trinidad & Tobago* 🇹🇹  
**PROTECTED ASSET**

---

## Overview

CyberFortress is a containerized autonomous security platform built for Caribbean enterprise environments.  
It reduces Mean Time to Containment (MTTC) while staying aligned with the Trinidad & Tobago Computer Misuse Act.

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
| Real-Time Dashboard (`:8091`) | ✅ |
| Health Check (`:8090`) | ✅ |
| **24/7 Self-Monitoring Watchdog** | ✅ |

---

## 24/7 Watchdog

Monitors that the platform is actually doing its job:

- Agent heartbeats (fusion, threat, compliance)
- Circuit breaker state
- Audit log freshness
- Pending WhatsApp approval backlog
- Disk space
- Optional **fail-closed** (auto-trip breaker if UNHEALTHY)

```bash
# Single check
python3 -m agents.watchdog_agent --once

# Continuous 24/7 loop
python3 -m agents.watchdog_agent

# Fail closed on critical self-failure
export CF_WATCHDOG_FAIL_CLOSED=true
```

Status written to `logs/watchdog_status.json`. Alerts can go out via WhatsApp on state change.

---

## Quick Start

```bash
git clone https://github.com/trintechdigitaldefense/CyberFortress.git
cd CyberFortress
pip install -r requirements.txt

python3 -m agents.healthcheck
python3 -m agents.watchdog_agent --once
python3 -m agents.dashboard          # http://localhost:8091
python3 playbooks/execute.py --list
```

See **docs/PILOT_DEPLOYMENT.md** before any client engagement.

---

## Client readiness

**Pilot-ready (supervised):** Yes — with dry-run first, signed ROE/NDA, and an operator watching.

**Unsupervised 24/7 production:** Not yet. Enable live containment only after:
1. WhatsApp Cloud API credentials + public webhook HTTPS
2. Live Sentinel/Mirage API URLs (or confirmed file feeds)
3. Pilot checklist completed
4. Watchdog running with alerts
5. `CF_CONTAINMENT_LIVE=true` only when intentionally going live

---

## Hardening recommendations

1. Keep `CF_CONTAINMENT_LIVE=false` until pilot sign-off
2. Set `CF_WATCHDOG_FAIL_CLOSED=true` for 24/7 fail-closed behaviour
3. Restrict dashboard/health ports to admin network only
4. Store secrets in env/secrets manager — never in git
5. Run under non-root user in production containers
6. TLS terminate WhatsApp webhook (Cloudflare Tunnel / reverse proxy)
7. Rotate WhatsApp and directory credentials regularly
8. Review Evidence Packs after every significant incident
9. Limit `--force` usage; prefer WhatsApp APPROVE path
10. Backup `logs/` and `evidence/` off-box

---

## Docker

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

| Service | Port |
|---------|------|
| Dashboard | 8091 |
| Health | 8090 |
| WhatsApp Webhook | 8089 |
| Watchdog | internal |

---

## Contact

**TrinTech Digital Defense**  
Email: trintechdigitaldefense@gmail.com  
WhatsApp: +1 (868) 362-0679  
Web: https://trintechdigitaldefense.github.io

---

*Defend. Detect. Dominate.*  
Authorized defensive use only. All rights reserved.
