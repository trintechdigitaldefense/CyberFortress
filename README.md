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

## Identity Providers (Credential Rotation)

| Provider | Status | Requirements |
|----------|--------|--------------|
| **local_linux** | Fully working | Default. Uses `chpasswd` / `usermod` |
| **ldap** / **ad** | Fully working | `ldap3` + `CF_LDAP_*` env vars |
| **azure_ad** / **entra** | Fully working | `msal` + `CF_AZURE_*` env vars + Graph permissions |

### LDAP / Active Directory
```bash
export CF_IDENTITY_PROVIDER=ldap
export CF_LDAP_SERVER=ldaps://dc.example.tt
export CF_LDAP_BIND_DN="cn=admin,dc=example,dc=tt"
export CF_LDAP_BIND_PASSWORD="..."
export CF_LDAP_USER_BASE="ou=users,dc=example,dc=tt"
# Optional for AD:
# export CF_LDAP_USER_FILTER="(sAMAccountName={username})"
```

### Microsoft Entra ID (Azure AD)
```bash
export CF_IDENTITY_PROVIDER=azure_ad
export CF_AZURE_TENANT_ID="your-tenant-id"
export CF_AZURE_CLIENT_ID="your-app-client-id"
export CF_AZURE_CLIENT_SECRET="your-client-secret"
# App Registration needs User.ReadWrite.All (application permission) + admin consent
```

---

## Quick Start

```bash
git clone https://github.com/trintechdigitaldefense/CyberFortress.git
cd CyberFortress
pip install -r requirements.txt

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
- [x] Credential Rotation with **real** Identity Providers:
  - Local Linux (chpasswd)
  - LDAP / Active Directory (ldap3)
  - Microsoft Entra ID / Azure AD (MSAL + Graph)
- [x] Emergency Halt Operations
- [x] Evidence Pack (executive report + SHA-256 manifest)
- [x] Fail-Safe Circuit Breaker

### Next Up
- [ ] Production WhatsApp Business API + webhook receiver
- [ ] Direct API connectors for Sentinel / Mirage

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
