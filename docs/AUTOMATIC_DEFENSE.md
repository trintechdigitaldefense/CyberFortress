# Policy-gated automatic defense

## What we sell (honest)

CyberFortress provides **rules-driven, policy-gated automatic defense** — not unsupervised “fully automatic” god-mode.

| Mode | What happens automatically |
|------|----------------------------|
| **MONITORING** (`LIVE=false`) | Detect, score, case, dry-run containment, reports |
| **LIVE + ROE** | Tier-1 actions (e.g. `block_ip`) execute without WhatsApp |
| **Tier-2** | Always needs operator `APPROVE <nonce>` |

## Controls that always remain

1. `CF_CONTAINMENT_LIVE=false` by default
2. ROE / `pilot_signoff.json` allow-list
3. Circuit breaker
4. Firewall allowlist / IP validation
5. WhatsApp Tier-2 approvals
6. Watchdog fail-closed (optional)

## Agents

- **auto_defense** — continuous Tier-1 from HIGH/CRITICAL signals
- **playbook** — YAML SOAR-lite → autonomy
- **ir_respond** — case-driven response

Disable continuous path: `export CF_AUTO_DEFENSE=false`

## Marketing language

**Use:** “Policy-gated automatic containment for authorized Tier-1 actions.”  
**Avoid:** “Fully automatic defense with no human oversight.”

*TrinTech Digital Defense — authorized defensive use only.*
