# CyberFortress — Go-Live (Arm Containment)

**TrinTech Digital Defense**

Live mode executes real containment (e.g. iptables `CF_BLOCK` DROP).  
It is **blocked** until legal sign-off **and** the host can manage netfilter.

Full legal / E&O checklist: **[LEGAL_GATE.md](LEGAL_GATE.md)** (attorney review + insurance before paying-client LIVE).

## VM pilot first

```bash
./scripts/pilot_vm_preflight.sh   # check_netadmin must be GREEN
```

WhatsApp can wait: set `whatsapp_deferred: true` in `pilot_signoff.json` until Meta credentials are ready.  
See [PILOT_VM.md](PILOT_VM.md).

## Prerequisites (all required except WhatsApp when deferred)

| # | Item | How |
|---|------|-----|
| 1 | **NDA signed** | templates → `nda_signed: true` + `nda_document` |
| 2 | **ROE signed** | templates → `roe_signed: true` + `roe_document` + `authorized_actions` |
| 3 | **Attorney review** | `docs/LEGAL_GATE.md` → `attorney_review_completed: true` |
| 4 | **E&O insurance** | Paying clients: `eo_insurance_confirmed: true` (COI offline) |
| 5 | **Host can run firewall** | `./scripts/pilot_vm_preflight.sh` → `host_netadmin_verified: true` |
| 6 | **WhatsApp + TLS** | Required unless `whatsapp_deferred: true` |
| 7 | **Operator runbook** | `operator_runbook_acknowledged: true` |
| 8 | **Checklist** | `checklist_complete: true` |

Restricted containers that print iptables Permission denied **must not** be armed.

## Create pilot_signoff.json

```bash
cp config/pilot_signoff.example.json config/pilot_signoff.json
chmod 600 config/pilot_signoff.json
# Edit every field — no placeholders
# After pilot_vm_preflight / check_netadmin passes:
#   "host_netadmin_verified": true
# Until Meta token is ready:
#   "whatsapp_deferred": true
```

## Enable live mode

```bash
./scripts/pilot_vm_preflight.sh
./scripts/enable_live_mode.sh --check
./scripts/enable_live_mode.sh --enable   # type: ENABLE LIVE MODE
./stop.sh && ./start.sh
```

## Disable

```bash
./scripts/disable_live_mode.sh
./stop.sh && ./start.sh
```

*Defend. Detect. Dominate.*
