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
- **Evidence Pack** — client-ready, integrity-protected report of every action

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
│   └── evidence.py              # Generate client evidence pack
├── core/
│   ├── autonomy.py
│   ├── whatsapp_gateway.py
│   ├── legal_mapper.py
│   ├── escalation.py
│   ├── containment/
│   │   └── drivers.py
│   ├── telemetry/
│   │   ├── adapters.py
│   │   └── fusion.py
│   └── evidence/
│       └── pack.py              # Evidence pack generator
├── telemetry/
├── evidence/                    # Generated packs land here
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
python3 playbooks/execute.py --action block_ip --target 203.0.113.50 --force

# Generate client Evidence Pack
python3 playbooks/evidence.py --client "Acme Ltd" --engagement ENG-2026-042
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
- [x] IPTables / Session / Decoy drivers (dry-run by default)

### Priority 4 — Evidence Pack ✅
- [x] Executive Markdown report (client-friendly)
- [x] Full machine-readable audit (JSON)
- [x] Raw CMA audit log copy
- [x] SHA-256 integrity manifest
- [x] One-command ZIP for delivery

### Next Up
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
