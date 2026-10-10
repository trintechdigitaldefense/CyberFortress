# FIXES_VERIFIED — CyberFortress pilot MVP

**Date:** 2026-10-10 (updated)  
**Repo:** github.com/trintechdigitaldefense/CyberFortress

---

## Demo flow results (fresh clone)

| Step | Result |
|------|--------|
| `./install.sh` + `./start.sh local` | PASS |
| Dashboard / health dry-run | PASS |
| Fusion escalation HIGH | PASS |
| Tier 1 block_ip + CMA | PASS |
| Evidence Pack | PASS |
| Tier 2 mock approve / TIMEOUT-DENY | PASS |
| `./stop.sh` | PASS |

---

## Follow-on (this update)

| Item | Status |
|------|--------|
| **Pricing removed** | No dollar amounts in HOW_TO_SELL or marketing docs — product still building |
| **Live Meta WhatsApp + HTTPS** | `scripts/setup_whatsapp_live.sh`, `scripts/verify_whatsapp.sh`, expanded `docs/WHATSAPP_TLS.md`, Caddy example |
| **NDA / ROE / pilot_signoff** | Templates under `docs/templates/`; `enable_live_mode.sh` requires flags + authorized_actions + whatsapp_admins |
| **GitHub repo description** | Cannot change via API from this environment (403 / no `gh`). Set manually in GitHub UI (see below) |

### Set repo description (human — GitHub UI)

**Settings → General → Description:**

```text
Automated threat detection and tiered response for Caribbean enterprises — TrinTech Digital Defense (Trinidad & Tobago)
```

---

## Safety controls preserved

- Dry-run default · force off · ROE allow-list · breaker · watchdog · go-live gate  
- Live mode blocked without signed NDA + ROE + WhatsApp TLS + pilot_signoff  
- No secrets committed  
