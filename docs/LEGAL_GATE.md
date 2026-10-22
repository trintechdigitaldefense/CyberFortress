# Legal gate — before live containment

**TrinTech Digital Defense · CyberFortress**

Live containment (`CF_CONTAINMENT_LIVE=true`) is **prohibited** until this gate is complete. The platform defaults to MONITORING / dry-run. This document is an operational checklist — **not legal advice**. Have counsel review engagement documents for each jurisdiction (including Trinidad & Tobago).

---

## 1. Must-have documents

| Document | Template | Outcome |
|----------|----------|---------|
| **NDA** | `docs/templates/NDA_TEMPLATE.md` | Signed PDF on file |
| **Rules of Engagement (ROE)** | `docs/templates/ROE_TEMPLATE.md` | Signed PDF; allow-list of actions |
| **Pilot sign-off** | `config/pilot_signoff.example.json` → `config/pilot_signoff.json` | Real names, dates, document paths, `authorized_actions` |

Never commit `config/pilot_signoff.json` or signed PDFs with secrets.

---

## 2. Attorney review checklist (send to counsel)

Counsel should confirm at least:

- [ ] Scope of authorized defensive actions is clear and limited to listed networks/hosts  
- [ ] Client authority to authorize network blocks / session termination / endpoint isolation  
- [ ] Human-in-the-loop (Tier-2 WhatsApp APPROVE) and timeout = DENY are acceptable  
- [ ] Liability allocation, indemnification, and limitation of liability in the MSA/SOW  
- [ ] Data handling of logs / Evidence Packs under NDA and applicable privacy rules  
- [ ] Mapping to local computer-crime / cyber law (e.g. T&T Computer Misuse Act) is accurate for **defensive** use only  
- [ ] No language that promises “fully automatic” or “guaranteed prevention”  
- [ ] Right of client to demand immediate disable of live mode  
- [ ] Term, renewal, and offboarding (return/destruction of evidence copies)

Record: counsel name / firm / review date in engagement notes (not necessarily in git).

---

## 3. Errors & Omissions (E&O) insurance

Before arming live containment on a **paying** client network:

- [ ] Active **cyber / tech E&O** (or professional liability) policy covering security monitoring and incident response services  
- [ ] Policy limits appropriate to engagement risk  
- [ ] Client and engagement type not excluded  
- [ ] Notification requirements understood if a claim-related event occurs  
- [ ] Certificate of insurance available if client contract requires it  

TrinTech internal: store COI offline; do not put policy numbers in the public repo.

---

## 4. Platform technical gates (still required)

| Gate | How |
|------|-----|
| NDA signed | `pilot_signoff.json` → `nda_signed: true` + `nda_document` |
| ROE signed | `roe_signed: true` + `roe_document` + matching `authorized_actions` |
| Host netadmin | `./scripts/pilot_vm_preflight.sh` GREEN → `host_netadmin_verified: true` |
| WhatsApp / TLS | Live or `whatsapp_deferred: true` only for early pilot |
| Operator runbook | `operator_runbook_acknowledged: true` |
| Checklist | `checklist_complete: true` |

Then:

```bash
./scripts/enable_live_mode.sh --check
./scripts/enable_live_mode.sh --enable   # typed confirmation required
```

Disable anytime:

```bash
./scripts/disable_live_mode.sh
```

---

## 5. Claims discipline (sales + dashboard)

Allowed: rules-driven detection, gated containment, operator-approved Tier-2, monitoring, evidence packs.

Avoid: “fully automatic defense,” “AI stops all attacks,” “guaranteed safe,” “we replace your entire SOC with zero human oversight.”

---

## 6. Order of operations (recommended)

1. NDA + ROE drafted → **attorney review**  
2. Client signs NDA + ROE  
3. Confirm **E&O** coverage  
4. Fill `pilot_signoff.json` with real values  
5. ≥7 day MONITORING soak on pilot host  
6. Select client rule pack (`./scripts/select_rule_pack.sh`)  
7. WhatsApp live (or documented deferral)  
8. `enable_live_mode.sh` only after all boxes green  

See also: [GO_LIVE.md](GO_LIVE.md) · [FIRST_PILOT.md](FIRST_PILOT.md) · [ROE_TEMPLATE.md](templates/ROE_TEMPLATE.md)
