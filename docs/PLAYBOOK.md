# CyberFortress Autonomous Incident Response & Operations Playbook

**PROTECTED ASSET • TRINTECH DIGITAL DEFENSE**

## 1. Platform Overview

CyberFortress is a containerized (Docker/Ubuntu) autonomous security platform designed for Caribbean enterprise environments. It uses **rules-driven telemetry fusion**, continuous credential resilience testing, and dynamic telemetry mapping to detect and isolate threats with minimal human latency.

**Core Objective**: Drastically reduce Mean Time to Containment (MTTC) while maintaining strict adherence to executive risk management protocols and regional legislation.

## 2. Human-in-the-Loop (HITL) Guardrails

To balance speed with safety, CyberFortress implements a tiered autonomy model. The system operates autonomously for low-impact containment (e.g., blocking individual anomalous IP addresses). For structural changes, it relies on out-of-band WhatsApp API approvals with an approver allow-list and nonce challenge.

### Approval Tiers

- **Tier 1 (Autonomy: Full)**: Single IP blocks, user session termination, active decoy deployment.  
  Action executed instantly; WhatsApp notification sent for visibility.

- **Tier 2 (Autonomy: Guarded)**: Subnet isolation, widespread credential rotation, halt operations.  
  Execution paused; WhatsApp prompt with one-time code. Approver must reply `APPROVE <code>` from a registered admin number. Timeout = DENY.

## 3. Legal Mapping & Compliance

All automated actions and mitigation playbooks are programmatically mapped against the Trinidad and Tobago Computer Misuse Act. This ensures that active defense measures remain within lawful jurisdictional bounds.

Every executed playbook generates a tamper-proof log entry containing the exact system action alongside its specific legislative justification, rendering the environment continually audit-ready.

## 4. CyberFortress Quick Reference Cheat Sheet

| Alert Tier       | Trigger Conditions                          | System Action                          | Admin Required     |
|------------------|---------------------------------------------|----------------------------------------|--------------------|
| LOW (Notice)     | Failed login spikes, minor policy violations | Log to Compliance Feed                 | No                 |
| HIGH (Action)    | Decoy trigger, credential traversal          | Isolate endpoint, drop active connection | No (Notified) / Tier 2 if ROE requires |
| CRITICAL (Halt)  | Data exfiltration, widespread encryption attempt | Halt operations, stage subnet lockdown | YES (WhatsApp + nonce) |

### Docker / one-command ops

```bash
./install.sh
./start.sh
./stop.sh

# View Real-time Compliance Logs (Filtered for CMA)
tail -f logs/cma_audit.jsonl
# or: docker logs -f cf_compliance_logger | grep "TT_CMA_TAG"

# Tier 1 dry-run
python3 playbooks/execute.py --action block_ip --target 203.0.113.50
```
