# Intentional Live Mode

**TrinTech Digital Defense — CyberFortress**

Live containment (`CF_CONTAINMENT_LIVE=true`) is **never** the default.  
It is enabled only after legal + operational gates are complete.

---

## Prerequisites (all required)

| # | Gate | Evidence |
|---|------|----------|
| 1 | **NDA signed** | `docs/templates/NDA_TEMPLATE.md` → signed PDF; `nda_signed: true` |
| 2 | **ROE signed** | `docs/templates/ROE_TEMPLATE.md` → signed PDF; `roe_signed: true`; same `authorized_actions` + WhatsApp admins |
| 3 | **WhatsApp + HTTPS** | `docs/WHATSAPP_TLS.md` + `./scripts/setup_whatsapp_live.sh` + `./scripts/verify_whatsapp.sh`; `whatsapp_tls_verified: true` |
| 4 | **Operator runbook** | `docs/OPERATOR_RUNBOOK.md` acknowledged; flag true |
| 5 | **Pilot checklist** | `docs/PILOT_DEPLOYMENT.md` complete; `checklist_complete: true` |
| 6 | **Sign-off file** | `config/pilot_signoff.json` (from example; **gitignored**) |

```bash
cp config/pilot_signoff.example.json config/pilot_signoff.json
chmod 600 config/pilot_signoff.json
# Edit every field — no placeholders left
```

---

## Enable live mode (controlled)

```bash
./scripts/enable_live_mode.sh --check
./scripts/enable_live_mode.sh --enable   # type: ENABLE LIVE MODE
./stop.sh && ./start.sh
python3 -m agents.healthcheck           # containment_live must be true
```

The enable script **refuses** if sign-off is missing, flags are false, or placeholders remain.

---

## Disable (rollback)

```bash
./scripts/disable_live_mode.sh
./stop.sh && ./start.sh
python3 playbooks/breaker.py trip --reason "Live mode disabled by operator"
```

---

## What “live” means

| Mode | Behaviour |
|------|-----------|
| DRY-RUN (default) | Drivers log intended actions only |
| LIVE | Drivers execute real containment |

Tier rules still apply: Tier 1 execute+notify; Tier 2 WhatsApp `APPROVE <nonce>`.

---

## First 48 hours after go-live

- [ ] Operator on watch per OPERATOR_RUNBOOK  
- [ ] Watchdog fail-closed on  
- [ ] Evidence pack at 24h and 48h  
- [ ] Client knows who can approve on WhatsApp  

---

*Defend. Detect. Dominate.*
