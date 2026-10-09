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

## Architecture (Current)

```
CyberFortress/
├── agents/
│   ├── threat_hunting_agent.py
│   └── compliance_logger.py
├── playbooks/
│   ├── library.py               # Full playbook registry
│   └── execute.py               # CLI runner with HITL
├── core/
│   ├── autonomy.py              # Tiered decision engine (wired)
│   ├── whatsapp_gateway.py      # HITL APPROVE / DENY + notifications
│   ├── legal_mapper.py          # TT Computer Misuse Act mapping
│   └── escalation.py            # Smart LOW → HIGH → CRITICAL promotion
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── config/
│   └── settings.yaml
└── docs/
    └── PLAYBOOK.md
```

---

## Quick Start

```bash
git clone https://github.com/trintechdigitaldefense/CyberFortress.git
cd CyberFortress

# List all playbooks
python3 playbooks/execute.py --list

# Run a Tier 1 action (auto-executes + notifies)
python3 playbooks/execute.py --action block_ip --target 203.0.113.50

# Run a Tier 2 action (requests WhatsApp APPROVE)
python3 playbooks/execute.py --action isolate_endpoint --target SEC-WEB-01

# Force a Tier 2 action (bypass HITL — still fully logged)
python3 playbooks/execute.py --action subnet_isolation --target 10.0.5.0/24 --force
```

---

## Status (2026-10-09)

### Priority 1 — Core Autonomy & Response ✅
- [x] Full Playbook Library (block_ip, terminate_session, deploy_decoy, isolate_endpoint, subnet_isolation, credential_rotation, halt_operations)
- [x] WhatsApp HITL Gateway (Tier 1 notify + Tier 2 interactive APPROVE/DENY with timeout)
- [x] Smart Escalation Engine (velocity + impact based promotion)
- [x] Autonomy engine fully wired to legal mapper + compliance logger + WhatsApp

### Next Up
- [ ] Telemetry fusion from Sentinel / Mirage
- [ ] Real containment drivers (iptables / agent commands)
- [ ] Evidence pack + client-facing report
- [ ] Fail-safe / circuit breaker
- [ ] Production WhatsApp Business API credentials + webhook receiver

---

## Contact

**TrinTech Digital Defense**  
Email: trintechdigitaldefense@gmail.com  
WhatsApp: +1 (868) 362-0679  
Web: https://trintechdigitaldefense.github.io

---

*Defend. Detect. Dominate.*  
Authorized defensive use only. All rights reserved.
