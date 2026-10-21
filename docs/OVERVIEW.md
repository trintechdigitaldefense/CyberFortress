# CyberFortress — Overview

**TrinTech Digital Defense · Trinidad & Tobago**  
**Version:** v0.5.1 (strengthened enterprise SOC edge platform)

## What it is

CyberFortress is an **automated detection and tiered response platform**.  
It watches networks and hosts, correlates signals, runs IR-style cases, and can contain threats — only under written rules (ROE) and explicit live arming.

It is **rules-driven** (not “AI magic”). High-impact actions can require WhatsApp operator approval.

## Who it’s for

- Local businesses and multi-site SMB / mid-market
- Edge / gateway Linux hosts that need monitored response
- Teams that want audit-ready evidence (TT Computer Misuse Act mapping)

## Core capabilities

| Layer | What you get |
|-------|----------------|
| **Monitoring** | Telemetry fusion, host signals, rule packs |
| **Intelligence** | Correlation window, burst/multi-signal, asset criticality |
| **IR team** | Detect → Investigate → Respond → Report |
| **Containment** | CF_BLOCK firewall, allowlist, verify |
| **SOAR-lite** | YAML playbooks (LIVE/ROE gated) |
| **SIEM bridge** | JSON/CEF ingest, event bus, syslog export |
| **SOC API** | Prometheus metrics + ingest on `:8092` |
| **Multi-tenant** | Isolated paths + orchestrator |
| **Safety** | Dry-run default, breaker, RBAC, rate limits, HA |
| **Evidence** | Tamper-evident audit + evidence packs |

## Safety model

1. **MONITORING by default** (`CF_CONTAINMENT_LIVE=false`)
2. Arm only after pilot sign-off + green host preflight
3. Tier-2 may require WhatsApp `APPROVE <nonce>` (operators only)
4. Circuit breaker stops runaway automation
5. Never-block allowlist protects operator/gateway IPs

## One-command use

```bash
git clone https://github.com/trintechdigitaldefense/CyberFortress.git
cd CyberFortress && ./install.sh && ./start.sh
```

| URL | Purpose |
|-----|---------|
| http://127.0.0.1:8091 | Dashboard |
| http://127.0.0.1:8090 | Health |
| http://127.0.0.1:8089 | WhatsApp webhook |
| http://127.0.0.1:8092 | SOC API |

## Honest maturity

Pilot MONITORING ready · Live containment after sign-off · Multi-site mid-market ready · Enterprise edge SOC strong (~9/10) · Not a global SIEM replacement.

*TrinTech Digital Defense — authorized defensive use only.*
