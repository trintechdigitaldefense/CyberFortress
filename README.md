# CyberFortress

**Autonomous Incident Response & Operations Platform**  
*TrinTech Digital Defense · Trinidad & Tobago* 🇹🇹  
**PROTECTED ASSET**

---

## Overview

CyberFortress is a containerized (Docker/Ubuntu) autonomous security platform designed for Caribbean enterprise environments.  
It combines AI-driven threat hunting, continuous credential resilience testing, and dynamic telemetry mapping to detect and isolate threats with minimal human latency.

**Core Objective**  
Drastically reduce Mean Time to Containment (MTTC) while maintaining strict adherence to executive risk management protocols and regional legislation (Trinidad & Tobago Computer Misuse Act).

---

## Key Capabilities

- **Tiered Autonomy (Human-in-the-Loop)**  
  - **Tier 1 (Full)**: Single IP blocks, session termination, active decoy deployment → executes instantly + WhatsApp notification  
  - **Tier 2 (Guarded)**: Subnet isolation, widespread credential rotation → pauses and requires WhatsApp “APPROVE”

- **Legal Mapping & Audit**  
  Every automated action is programmatically mapped to the Trinidad & Tobago Computer Misuse Act.  
  Tamper-proof logs pair the exact system action with its legislative justification.

- **Alert Tiers**

| Alert Tier       | Trigger Conditions                          | System Action                          | Admin Required     |
|------------------|---------------------------------------------|----------------------------------------|--------------------|
| **LOW (Notice)** | Failed login spikes, minor policy violations | Log to Compliance Feed                 | No                 |
| **HIGH (Action)**| Decoy trigger, credential traversal          | Isolate endpoint, drop active connection | No (Notified)     |
| **CRITICAL (Halt)** | Data exfiltration, widespread encryption attempt | Halt operations, stage subnet lockdown | **YES (WhatsApp)** |

---

## Architecture (MVP)

```
CyberFortress/
├── agents/
│   ├── threat_hunting_agent.py      # AI-driven continuous hunting
│   └── compliance_logger.py         # Tamper-proof CMA-mapped logs
├── playbooks/
│   └── execute.py                   # Playbook runner + Tier 2 force override
├── core/
│   ├── autonomy.py                  # HITL decision engine
│   ├── whatsapp_gateway.py          # Out-of-band approval channel
│   └── legal_mapper.py              # TT Computer Misuse Act mapping
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── config/
│   └── settings.yaml
└── docs/
    └── PLAYBOOK.md                  # Full operational playbook
```

---

## Quick Start (Development)

```bash
# Clone
git clone https://github.com/trintechdigitaldefense/CyberFortress.git
cd CyberFortress

# Build & run core services
docker compose up -d

# Restart Threat Hunting Agent
docker restart cf_threat_agent

# View real-time Compliance Logs (filtered for TT CMA)
docker logs -f cf_compliance_logger | grep "TT_CMA_TAG"

# Manually trigger Tier 2 isolation (force)
python3 playbooks/execute.py --target=SEC-WEB-01 --force
```

---

## Status

- [x] Repository initialized
- [ ] Core autonomy engine
- [ ] WhatsApp HITL gateway
- [ ] Legal mapper (TT Computer Misuse Act)
- [ ] Threat hunting agent
- [ ] Compliance logger
- [ ] Docker packaging
- [ ] Full playbook suite

---

## Contact

**TrinTech Digital Defense**  
Email: trintechdigitaldefense@gmail.com  
WhatsApp: +1 (868) 362-0679  
Web: https://trintechdigitaldefense.github.io

---

*Defend. Detect. Dominate.*  
Authorized defensive use only. All rights reserved.
