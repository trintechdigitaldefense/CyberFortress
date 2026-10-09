# CyberFortress

**Autonomous Incident Response & Operations Platform**  
*TrinTech Digital Defense · Trinidad & Tobago* 🇹🇹  
**PROTECTED ASSET**

---

## Overview

CyberFortress is a containerized autonomous security platform built for Caribbean enterprise environments.  
It reduces Mean Time to Containment (MTTC) while staying fully aligned with the Trinidad & Tobago Computer Misuse Act.

---

## Capabilities

| Feature | Status |
|---------|--------|
| Tiered Autonomy (Tier 1 instant / Tier 2 WhatsApp APPROVE) | ✅ Production Meta Cloud API |
| Legal mapping to TT Computer Misuse Act | ✅ |
| Smart Escalation (LOW → HIGH → CRITICAL) | ✅ |
| Telemetry Fusion (file + live API) | ✅ Sentinel & Mirage |
| Real Containment Drivers | ✅ iptables, session, decoy, credential rotation, halt |
| Identity Providers | ✅ Local Linux, LDAP/AD, Azure AD |
| Evidence Pack | ✅ |
| Fail-Safe Circuit Breaker | ✅ |
| WhatsApp Webhook | ✅ |
| Health Check | ✅ `:8090` |
| **Real-Time Dashboard** | ✅ `:8091` |
| Pilot Deployment Checklist | ✅ |

---

## Real-Time Dashboard

```bash
python3 -m agents.dashboard
# Open http://localhost:8091
```

Shows live:
- Containment mode (LIVE / DRY-RUN)
- Circuit breaker state
- Pending WhatsApp approvals
- Recent CMA-mapped actions
- Identity provider in use

Auto-refreshes every 5 seconds.

---

## Quick Start

```bash
git clone https://github.com/trintechdigitaldefense/CyberFortress.git
cd CyberFortress
pip install -r requirements.txt

python3 -m agents.healthcheck
python3 -m agents.dashboard          # http://localhost:8091
python3 playbooks/execute.py --list
python3 playbooks/evidence.py --client "Acme Ltd"
```

See **docs/PILOT_DEPLOYMENT.md** before any client engagement.

---

## Docker

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

| Service | Port |
|---------|------|
| Dashboard | **8091** |
| Health | 8090 |
| WhatsApp Webhook | 8089 |
| Fusion / Threat / Compliance agents | internal |

---

## Safety

- Default mode is **DRY-RUN**. Live actions require `CF_CONTAINMENT_LIVE=true`.
- Circuit breaker automatically blocks runaway autonomy.
- Every action is logged with TT Computer Misuse Act justification.

---

## Contact

**TrinTech Digital Defense**  
Email: trintechdigitaldefense@gmail.com  
WhatsApp: +1 (868) 362-0679  
Web: https://trintechdigitaldefense.github.io

---

*Defend. Detect. Dominate.*  
Authorized defensive use only. All rights reserved.
