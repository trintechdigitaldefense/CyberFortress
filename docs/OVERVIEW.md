# CyberFortress — Overview

**TrinTech Digital Defense · Trinidad & Tobago**

CyberFortress is an **autonomous incident response platform** that detects threats, decides what to do, asks a human when needed (WhatsApp), and can contain the threat — with every action mapped to the **Trinidad & Tobago Computer Misuse Act** and packaged as client evidence.

---

## What problem it solves

Caribbean SMBs and enterprises often face:
- Slow response when something bad is happening on the network
- No clear audit trail tied to local law
- Tools that either do nothing automatic or do too much without approval

CyberFortress shortens **Mean Time to Containment** while keeping a human in the loop for high-impact actions.

---

## How it works (simple)

```
Alerts (Sentinel / Mirage / files / APIs)
        ↓
Telemetry Fusion + Escalation (LOW → HIGH → CRITICAL)
        ↓
Autonomy Engine
  • Tier 1 → act + notify
  • Tier 2 → WhatsApp APPROVE / DENY
        ↓
Containment drivers (block, isolate, rotate, halt…)
  or Rollback (unblock, restore)
        ↓
CMA audit log + Evidence Pack + Dashboard + Watchdog
```

---

## Core capabilities

| Area | Capability |
|------|------------|
| Autonomy | Tiered HITL via WhatsApp |
| Legal | TT CMA justification on every action |
| ROE | Only `authorized_actions` from pilot sign-off may run |
| Containment | block IP, isolate host/subnet, session kill, decoy, credentials, halt |
| Rollback | unblock IP, restore endpoint/subnet |
| Safety | Dry-run default, force gate, circuit breaker, fail-closed watchdog |
| Ops | Dashboard (auth), health, evidence pack, off-box backup |
| Go-live | Checklist + sign-off + gated `enable_live_mode.sh` |

---

## What it is *not*

- Not a full SIEM replacement
- Not unsupervised “set and forget” without pilot sign-off
- Not a substitute for signed ROE / NDA

---

## Status

**Pilot-ready** with hardened defaults.  
**Live mode** only after checklist, WhatsApp+TLS, operator process, and intentional enable.

*Defend. Detect. Dominate.*
