# CyberFortress Operator Runbook

**TrinTech Digital Defense — day-to-day process for pilots and live mode**

---

## Roles

| Role | Responsibility |
|------|----------------|
| **Lead operator** | Go-live decisions, breaker trips, client contact |
| **On-call operator** | WhatsApp `APPROVE <nonce>` / `DENY <nonce>`, dashboard watch |
| **Client admin** | Named on ROE; may receive alerts only if listed in `CF_WHATSAPP_ADMINS` |

At least **one** TrinTech operator must be reachable while `CF_CONTAINMENT_LIVE=true`.

---

## Shift start

1. SSH tunnel:
   ```bash
   ssh -L 8091:127.0.0.1:8091 -L 8090:127.0.0.1:8090 user@cf-host
   ```
2. `./start.sh status` or health/dashboard checks
3. Confirm breaker CLOSED, mode DRY-RUN vs LIVE, phone is a listed admin number

---

## Handling Tier 2 WhatsApp requests

Messages include **Action**, **Target**, **Severity**, **Legal justification**, and a **nonce**.

Reply **exactly** (from your registered number only):

```text
APPROVE A1B2C3
```

or

```text
DENY A1B2C3
```

Rules:

1. Read action/target/severity carefully; cross-check dashboard if unsure.
2. **APPROVE** only if target is in ROE scope and action is authorized.
3. **DENY** if uncertain — safe default.
4. Unknown numbers cannot approve (logged as DENY-UNKNOWN-SENDER).
5. Wrong or missing nonce → DENY-BAD-NONCE.
6. No reply within timeout (default 15 minutes) → **TIMEOUT-DENY** (logged in CMA audit).

**Do not use `--force`** unless `CF_ALLOW_FORCE=true`, lead authorizes, and it is noted in engagement records.

---

## Incident response (platform)

| Symptom | Action |
|---------|--------|
| Watchdog UNHEALTHY | Fix root cause; reset breaker if fail-closed tripped |
| Breaker OPEN | No new autonomy until reset |
| WhatsApp down | Tier 2 holds/denies — do not enable force casually |
| Unexpected LIVE | `./scripts/disable_live_mode.sh` immediately |

```bash
./scripts/disable_live_mode.sh
python3 playbooks/breaker.py trip --reason "Operator emergency stop"
```

---

## Evidence

```bash
python3 playbooks/evidence.py --client "CLIENT_NAME" --engagement ENG-YYYY-NNN
export CF_BACKUP_DEST=/path/offbox
./scripts/backup_offbox.sh
```

---

## Shift end checklist

- [ ] Pending approvals cleared or handed over
- [ ] Breaker + LIVE/DRY-RUN state noted
- [ ] Next on-call named and reachable

---

*See also: docs/WHATSAPP_TLS.md · docs/PILOT_DEPLOYMENT.md · docs/GO_LIVE.md*
