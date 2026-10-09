# CyberFortress

**Autonomous Incident Response & Operations Platform**  
*TrinTech Digital Defense · Trinidad & Tobago* 🇹🇹  
**PROTECTED ASSET**

---

## Overview

CyberFortress is a containerized autonomous security platform built for Caribbean enterprise environments.  
It reduces Mean Time to Containment (MTTC) while staying fully aligned with the Trinidad & Tobago Computer Misuse Act.

---

## Capabilities (Complete)

| Feature | Status |
|---------|--------|
| Tiered Autonomy (Tier 1 instant / Tier 2 WhatsApp APPROVE) | ✅ Production Meta Cloud API |
| Legal mapping to TT Computer Misuse Act | ✅ |
| Smart Escalation (LOW → HIGH → CRITICAL) | ✅ |
| Telemetry Fusion (file + live API) | ✅ Sentinel & Mirage connectors |
| Real Containment Drivers | ✅ iptables, session, decoy, credential rotation, halt |
| Identity Providers | ✅ Local Linux, LDAP/AD, Azure AD / Entra ID |
| Evidence Pack (client-ready + SHA-256) | ✅ |
| Fail-Safe Circuit Breaker | ✅ |
| WhatsApp Webhook Receiver | ✅ |
| Health Check endpoint | ✅ |
| Pilot Deployment Checklist | ✅ |

---

## Quick Start

```bash
git clone https://github.com/trintechdigitaldefense/CyberFortress.git
cd CyberFortress
pip install -r requirements.txt

# Health
python3 -m agents.healthcheck

# Dry-run playbook
python3 playbooks/execute.py --action block_ip --target 203.0.113.50 --force

# Evidence pack
python3 playbooks/evidence.py --client "Acme Ltd" --engagement ENG-2026-001

# Circuit breaker
python3 playbooks/breaker.py status
```

See **docs/PILOT_DEPLOYMENT.md** before any client engagement.

---

## Key Environment Variables

```bash
# Safety
CF_CONTAINMENT_LIVE=false          # keep false until pilot is ready

# WhatsApp (Meta Cloud API)
CF_WHATSAPP_ENABLED=true
CF_WHATSAPP_TOKEN=...
CF_WHATSAPP_PHONE_NUMBER_ID=...
CF_WHATSAPP_ADMINS=+1868...,+1868...
CF_WHATSAPP_VERIFY_TOKEN=...

# Identity
CF_IDENTITY_PROVIDER=local_linux   # or ldap / azure_ad

# Live telemetry (optional)
CF_SENTINEL_API_URL=http://sentinel:port/api/alerts
CF_MIRAGE_API_URL=http://mirage:port/api/events
```

---

## Docker

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

Services: `cf_threat_agent`, `cf_compliance_logger`, `cf_fusion_agent`, `cf_whatsapp_webhook` (:8089), `cf_health` (:8090)

---

## Safety

- Default mode is **DRY-RUN**. Live actions require `CF_CONTAINMENT_LIVE=true`.
- Circuit breaker automatically blocks runaway autonomy.
- Every action is logged with TT Computer Misuse Act justification.
- Secrets written to `./secrets/rotated/` with mode 600.

---

## Contact

**TrinTech Digital Defense**  
Email: trintechdigitaldefense@gmail.com  
WhatsApp: +1 (868) 362-0679  
Web: https://trintechdigitaldefense.github.io

---

*Defend. Detect. Dominate.*  
Authorized defensive use only. All rights reserved.
