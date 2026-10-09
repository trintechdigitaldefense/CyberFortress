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
- **Real Containment Drivers** (iptables, session kill, decoy deployment)
- **Smart Escalation** (LOW → HIGH → CRITICAL)

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
│   └── execute.py
├── core/
│   ├── autonomy.py              # decision + containment orchestration
│   ├── whatsapp_gateway.py
│   ├── legal_mapper.py
│   ├── escalation.py
│   ├── containment/
│   │   └── drivers.py           # iptables / session / decoy
│   └── telemetry/
│       ├── adapters.py
│       └── fusion.py
├── telemetry/                   # drop zone for alerts
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

# Safe test (DRY-RUN by default)
python3 playbooks/execute.py --action block_ip --target 203.0.113.50
python3 playbooks/execute.py --action isolate_endpoint --target 10.0.5.12 --force

# Enable REAL containment (use with extreme care)
export CF_CONTAINMENT_LIVE=true
python3 playbooks/execute.py --action block_ip --target 203.0.113.50 --force
```

---

## Status (2026-10-09)

### Priority 1 — Core Autonomy & Response ✅
- [x] Full Playbook Library
- [x] WhatsApp HITL Gateway
- [x] Smart Escalation Engine

### Priority 2 — Telemetry Fusion ✅
- [x] Adapters + Fusion Engine + continuous agent

### Priority 3 — Real Containment Drivers ✅
- [x] IPTablesDriver (block_ip, isolate_endpoint, subnet_isolation)
- [x] SessionKiller (terminate_session)
- [x] DecoyDeployer (deploy_decoy)
- [x] Fully wired into autonomy engine
- [x] Dry-run by default (set `CF_CONTAINMENT_LIVE=true` for live actions)

### Next Up
- [ ] Evidence pack + client-facing report
- [ ] Fail-safe / circuit breaker
- [ ] Production WhatsApp Business API + webhook receiver
- [ ] Credential rotation & halt_operations drivers
- [ ] Direct API connectors for Sentinel / Mirage

---

## Safety Notes

- All containment actions default to **DRY-RUN**.
- Live mode requires explicit `CF_CONTAINMENT_LIVE=true`.
- Every action is logged with TT Computer Misuse Act justification.
- Tier 2 actions still require WhatsApp APPROVE (unless `--force`).

---

## Contact

**TrinTech Digital Defense**  
Email: trintechdigitaldefense@gmail.com  
WhatsApp: +1 (868) 362-0679  
Web: https://trintechdigitaldefense.github.io

---

*Defend. Detect. Dominate.*  
Authorized defensive use only. All rights reserved.
