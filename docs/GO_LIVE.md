# CyberFortress — Go-Live (Arm Containment)

**TrinTech Digital Defense**

Live mode executes real containment (e.g. iptables `CF_BLOCK` DROP).  
It is **blocked** until legal sign-off **and** the host can manage netfilter.

---

## Prerequisites (all required)

| # | Item | How |
|---|------|-----|
| 1 | **NDA signed** | [templates/NDA_TEMPLATE.md](templates/NDA_TEMPLATE.md) → set `nda_signed: true` + `nda_document` |
| 2 | **ROE signed** | [templates/ROE_TEMPLATE.md](templates/ROE_TEMPLATE.md) → `roe_signed: true` + `roe_document` + `authorized_actions` |
| 3 | **Host can run firewall** | [HOST_REQUIREMENTS.md](HOST_REQUIREMENTS.md) · `./scripts/check_netadmin.sh` → `host_netadmin_verified: true` |
| 4 | **WhatsApp + TLS** (for Tier 2) | [WHATSAPP_TLS.md](WHATSAPP_TLS.md) · `whatsapp_tls_verified: true` |
| 5 | **Operator runbook** | [OPERATOR_RUNBOOK.md](OPERATOR_RUNBOOK.md) · `operator_runbook_acknowledged: true` |
| 6 | **Checklist** | [PILOT_DEPLOYMENT.md](PILOT_DEPLOYMENT.md) · `checklist_complete: true` |

Restricted containers that print `iptables: Permission denied` **must not** be armed. Use MONITORING only there.

---

## Create pilot_signoff.json

```bash
cp config/pilot_signoff.example.json config/pilot_signoff.json
chmod 600 config/pilot_signoff.json
# Edit every field — no placeholders
# After ./scripts/check_netadmin.sh passes:
#   "host_netadmin_verified": true
```

`enable_live_mode.sh` refuses if any required flag is not `true` or placeholders remain.

---

## Enable live mode

```bash
./scripts/check_netadmin.sh
./scripts/enable_live_mode.sh --check
./scripts/enable_live_mode.sh --enable   # type: ENABLE LIVE MODE
./stop.sh && ./start.sh
curl -s http://127.0.0.1:8090/health | python3 -m json.tool
curl -s http://127.0.0.1:8091/api/firewall | python3 -m json.tool
```

---

## Disable (rollback)

```bash
./scripts/disable_live_mode.sh
./stop.sh && ./start.sh
```

---

## What “live” means

| Mode | Behaviour |
|------|-----------|
| MONITORING (default) | Detect, audit, report; DROP not applied |
| LIVE (armed) | Allow-listed playbooks can change the host firewall |

Tier 1: execute + notify. Tier 2: WhatsApp `APPROVE <nonce>` still required.

---

*Defend. Detect. Dominate.*
