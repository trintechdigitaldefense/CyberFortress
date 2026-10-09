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
- **Legal Mapping** to the Trinidad & Tobago Computer Misuse Act
- **Telemetry Fusion** from Sentinel + Mirage + local sources
- **Real Containment Drivers** (iptables, session, decoy, credential rotation, emergency halt)
- **Pluggable Identity Providers** (Local Linux working, LDAP & Azure AD ready)
- **Smart Escalation**, **Evidence Pack**, **Fail-Safe Circuit Breaker**

---

## Identity Providers for Credential Rotation

| Provider        | Status          | How to enable                                      |
|-----------------|-----------------|----------------------------------------------------|
| `local_linux`   | Fully working   | Default. Uses `chpasswd` / `usermod`               |
| `ldap` / `ad`   | Config stub     | Set `CF_LDAP_SERVER`, `CF_LDAP_BIND_DN`, etc.      |
| `azure_ad`      | Config stub     | Set `CF_AZURE_TENANT_ID`, `CF_AZURE_CLIENT_ID`, …  |

```bash
# Use local Linux accounts (default)
export CF_IDENTITY_PROVIDER=local_linux
python3 playbooks/execute.py --action credential_rotation --target admin,www-data --force

# Point at LDAP / AD (once configured)
export CF_IDENTITY_PROVIDER=ldap
export CF_LDAP_SERVER=ldap://dc.example.tt
# … etc.
```

---

## Quick Start

```bash
git clone https://github.com/trintechdigitaldefense/CyberFortress.git
cd CyberFortress

python3 playbooks/execute.py --list
python3 playbooks/execute.py --action credential_rotation --target admin --force
python3 playbooks/evidence.py --client "Acme Ltd"
python3 playbooks/breaker.py status
```

---

## Status (2026-10-09)

### Completed
- [x] Full Playbook Library + WhatsApp HITL + Escalation
- [x] Telemetry Fusion (Sentinel / Mirage / local)
- [x] Real Containment Drivers (all major actions)
- [x] Credential Rotation with **pluggable Identity Providers**
- [x] Emergency Halt Operations
- [x] Evidence Pack (executive report + SHA-256 manifest)
- [x] Fail-Safe Circuit Breaker

### Next Up
- [ ] Production WhatsApp Business API + webhook receiver
- [ ] Direct API connectors for Sentinel / Mirage
- [ ] Complete LDAP / Azure AD implementations (currently safe stubs)

---

## Safety Notes

- All containment actions default to **DRY-RUN** (`CF_CONTAINMENT_LIVE=true` required for live).
- Credential secrets are written to `./secrets/rotated/` with mode 600.
- Circuit Breaker automatically blocks runaway autonomy.
- Every action carries a Trinidad & Tobago Computer Misuse Act justification.

---

## Contact

**TrinTech Digital Defense**  
Email: trintechdigitaldefense@gmail.com  
WhatsApp: +1 (868) 362-0679  
Web: https://trintechdigitaldefense.github.io

---

*Defend. Detect. Dominate.*  
Authorized defensive use only. All rights reserved.
