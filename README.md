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

- **Tiered Autonomy (Human-in-the-Loop)** via WhatsApp
- **Legal Mapping** to the Trinidad & Tobago Computer Misuse Act on every action
- **Telemetry Fusion** from Sentinel + Mirage + local sources
- **Real Containment Drivers** (iptables, session kill, decoy, **credential rotation**, **emergency halt**)
- **Smart Escalation** (LOW → HIGH → CRITICAL)
- **Evidence Pack** — client-ready, integrity-protected report of every action
- **Fail-Safe Circuit Breaker** — automatically pauses autonomy if too many high-impact actions occur

---

## Architecture (Current)

```
CyberFortress/
├── agents/
│   ├── threat_hunting_agent.py
│   ├── compliance_logger.py
│   └── telemetry_fusion_agent.py
├── playbooks/
│   ├── library.py
│   ├── execute.py
│   ├── evidence.py
│   └── breaker.py
├── core/
│   ├── autonomy.py
│   ├── whatsapp_gateway.py
│   ├── legal_mapper.py
│   ├── escalation.py
│   ├── circuit_breaker.py
│   ├── containment/drivers.py   # All real drivers live here
│   ├── telemetry/
│   └── evidence/
├── telemetry/
├── evidence/
├── secrets/rotated/             # One-time rotated credentials (mode 600)
├── docker/
├── config/
└── docs/
```

---

## Quick Start

```bash
git clone https://github.com/trintechdigitaldefense/CyberFortress.git
cd CyberFortress

# List all playbooks
python3 playbooks/execute.py --list

# Credential rotation (Tier 2 — requires approval or --force)
python3 playbooks/execute.py --action credential_rotation --target admin,www-data --force

# Emergency halt
python3 playbooks/execute.py --action halt_operations --target 10.0.5.0/24 --force

# Generate Evidence Pack
python3 playbooks/evidence.py --client "Acme Ltd" --engagement ENG-2026-042
```

---

## Status (2026-10-09)

### Completed
- [x] Full Playbook Library
- [x] WhatsApp HITL Gateway
- [x] Smart Escalation Engine
- [x] Telemetry Fusion (Sentinel / Mirage / local)
- [x] Real Containment Drivers (iptables, session, decoy)
- [x] **Credential Rotation driver**
- [x] **Emergency Halt Operations driver**
- [x] Evidence Pack (executive report + SHA-256 manifest)
- [x] Fail-Safe Circuit Breaker

### Next Up
- [ ] Production WhatsApp Business API + webhook receiver
- [ ] Direct API connectors for Sentinel / Mirage
- [ ] Identity provider integrations (AD / LDAP / cloud IAM) for credential rotation

---

## Safety Notes

- All containment actions default to **DRY-RUN**.
- Live mode requires explicit `CF_CONTAINMENT_LIVE=true`.
- Credential rotation stores new secrets in `./secrets/rotated/` with mode 600.
- Every action is logged with TT Computer Misuse Act justification.
- Circuit Breaker automatically blocks further autonomous actions if thresholds are exceeded.

---

## Contact

**TrinTech Digital Defense**  
Email: trintechdigitaldefense@gmail.com  
WhatsApp: +1 (868) 362-0679  
Web: https://trintechdigitaldefense.github.io

---

*Defend. Detect. Dominate.*  
Authorized defensive use only. All rights reserved.
