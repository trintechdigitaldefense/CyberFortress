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

- **Telemetry Fusion**  
  Ingests and correlates alerts from Sentinel, Mirage, and local sources → escalates → recommends (or auto-runs) the right playbook.

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
│   ├── compliance_logger.py
│   └── telemetry_fusion_agent.py    # continuous fusion loop
├── playbooks/
│   ├── library.py
│   └── execute.py
├── core/
│   ├── autonomy.py
│   ├── whatsapp_gateway.py
│   ├── legal_mapper.py
│   ├── escalation.py
│   └── telemetry/
│       ├── adapters.py              # Sentinel / Mirage / Local
│       └── fusion.py                # central fusion engine
├── telemetry/                       # drop zone for source alerts
│   ├── sentinel/
│   └── mirage/
├── docker/
├── config/
└── docs/
```

---

## Quick Start

```bash
git clone https://github.com/trintechdigitaldefense/CyberFortress.git
cd CyberFortress

# List playbooks
python3 playbooks/execute.py --list

# Manual playbook run
python3 playbooks/execute.py --action isolate_endpoint --target SEC-WEB-01

# Run Telemetry Fusion once (processes sample alerts)
python3 -c "
from core.telemetry.fusion import TelemetryFusion
fusion = TelemetryFusion(auto_respond=False)
fusion.register_defaults()
results = fusion.process()
for r in results:
    print(r['escalated_level'], r['recommended_playbook'], r['event']['target'])
"

# Continuous fusion agent
python3 -m agents.telemetry_fusion_agent
```

---

## Status (2026-10-09)

### Priority 1 — Core Autonomy & Response ✅
- [x] Full Playbook Library
- [x] WhatsApp HITL Gateway
- [x] Smart Escalation Engine
- [x] Autonomy engine fully wired

### Priority 2 — Telemetry Fusion ✅
- [x] Adapters for Sentinel, Mirage, and local/custom sources
- [x] Central Fusion Engine (collect → normalize → escalate → recommend)
- [x] Continuous Fusion Agent
- [x] Sample alerts for immediate testing
- [x] Docker service for fusion_agent

### Next Up
- [ ] Real containment drivers (iptables / agent commands)
- [ ] Evidence pack + client-facing report
- [ ] Fail-safe / circuit breaker
- [ ] Production WhatsApp Business API + webhook receiver
- [ ] Direct API connectors (instead of file drop) for Sentinel / Mirage

---

## Contact

**TrinTech Digital Defense**  
Email: trintechdigitaldefense@gmail.com  
WhatsApp: +1 (868) 362-0679  
Web: https://trintechdigitaldefense.github.io

---

*Defend. Detect. Dominate.*  
Authorized defensive use only. All rights reserved.
