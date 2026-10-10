# Rules of Engagement (ROE) — CyberFortress (Template)

**Client:** [CLIENT LEGAL NAME]  
**Engagement ID:** [ENG-YYYY-NNN]  
**TrinTech Digital Defense**  
**Effective:** [YYYY-MM-DD] → **Ends:** [YYYY-MM-DD]

> Template for signed ROE. Replace bracketed fields. Live containment is **prohibited** until this ROE and NDA are signed and `config/pilot_signoff.json` is complete.

---

## 1. Scope

| Item | Detail |
|------|--------|
| In-scope networks / hosts | [CIDRs, VLANs, hostnames] |
| Out of scope | [OT, third-party cloud, executive laptops, etc.] |
| Business hours | [e.g. 24/7 or Mon–Fri 08:00–18:00 AST] |
| Emergency contacts | [Client] / [TrinTech on-call] |

## 2. Authorized actions (allow-list)

Only the following may be executed when live mode is enabled. Copy the same list into `authorized_actions` in `config/pilot_signoff.json`.

| Action | Tier | Notes |
|--------|------|-------|
| `block_ip` | 1 | Single IP block |
| `unblock_ip` | 1 | Rollback |
| `terminate_session` | 1 | |
| `deploy_decoy` | 1 | |
| `isolate_endpoint` | 2 | Requires WhatsApp `APPROVE <nonce>` |
| `restore_endpoint` | 1/2 | Rollback |
| `subnet_isolation` | 2 | Optional — include only if Client accepts |
| `credential_rotation` | 2 | Optional |
| `halt_operations` | 2 | Optional — highest impact |

Any action **not** listed is **denied** by the platform.

## 3. Human-in-the-loop

- **Tier 1:** may execute automatically within scope; operators notified  
- **Tier 2:** requires WhatsApp approval from numbers listed below  
- Approver reply format: `APPROVE <nonce>` or `DENY <nonce>`  
- Timeout without reply = **DENY**

**WhatsApp admin numbers (must match CF_WHATSAPP_ADMINS):**

1. [+1868…] — [Name / role]  
2. [+1868…] — [Name / role]

## 4. Safety defaults

- Engagement starts in **dry-run** (`CF_CONTAINMENT_LIVE=false`)  
- Live mode only after NDA + this ROE + pilot checklist + typed confirmation  
- Client may request immediate disable of live mode at any time

## 5. Legal basis

Actions are authorized defensive measures under the engagement and mapped for audit to the Trinidad & Tobago Computer Misuse Act where applicable. This ROE does not authorize offensive operations outside the listed targets.

## 6. Evidence

TrinTech may produce Evidence Packs (audit logs, action summaries). Client receives copies under the NDA.

---

**Client approver**  
Signature: ________________  Name: ________________  Date: ________

**TrinTech lead operator**  
Signature: ________________  Name: ________________  Date: ________

*After signing: set `roe_signed: true` in `config/pilot_signoff.json` and list the same `authorized_actions` and `whatsapp_admins`.*
