# CyberFortress Operator Runbook

**TrinTech Digital Defense — day-to-day process for pilots and live mode**

This is the **operator process**. Follow it on every client engagement.

---

## Roles

| Role | Responsibility |
|------|----------------|
| **Lead operator** | Go-live decisions, breaker trips, client contact |
| **On-call operator** | WhatsApp APPROVE/DENY, dashboard watch, first response |
| **Client admin** | Named on ROE; may receive WhatsApp alerts only |

At least **one** TrinTech operator must be reachable while `CF_CONTAINMENT_LIVE=true`.

---

## Shift start (every day / every handoff)

1. SSH to host (or jump host).
2. Open admin tunnel:
   ```bash
   ssh -L 8091:127.0.0.1:8091 -L 8090:127.0.0.1:8090 user@cf-host
   ```
3. Check health + watchdog:
   ```bash
   python3 -m agents.healthcheck
   python3 -m agents.watchdog_agent --once
   # or open http://127.0.0.1:8090 and http://127.0.0.1:8091
   ```
4. Confirm:
   - Circuit breaker **CLOSED** (or know why OPEN)
   - Containment mode matches engagement phase (DRY-RUN vs LIVE)
   - No large pending-approval backlog
5. Confirm phone has WhatsApp access for listed `CF_WHATSAPP_ADMINS` numbers.

---

## Handling WhatsApp Tier 2 requests

1. Read **Action**, **Target**, **Severity**, **Legal justification**.
2. Cross-check dashboard recent actions if unsure.
3. **APPROVE** only if:
   - Target is in ROE scope
   - Action is authorized on the ROE
   - Impact is understood (e.g. isolate host vs subnet)
4. **DENY** if uncertain — safe default is hold.
5. Log verbal/client notification if the action affects business operations.

**Do not use `--force`** unless:
- `CF_ALLOW_FORCE=true` was explicitly enabled for this emergency, **and**
- Lead operator authorizes it, **and**
- It is recorded in the engagement notes.

---

## Incident response (platform)

| Symptom | Action |
|---------|--------|
| Watchdog **UNHEALTHY** | Investigate heartbeats; if fail-closed tripped breaker, fix root cause then `python3 playbooks/breaker.py reset` |
| Breaker **OPEN** | No new autonomy until reset; notify lead |
| WhatsApp down | Tier 2 will hold; do **not** blindly enable force |
| Unexpected LIVE containment | `./scripts/disable_live_mode.sh` immediately |
| Suspected compromise of host | Trip breaker, disable live mode, isolate host, preserve logs |

Emergency stop:

```bash
./scripts/disable_live_mode.sh
python3 playbooks/breaker.py trip --reason "Operator emergency stop"
```

---

## Evidence & reporting

After significant activity or end of day:

```bash
python3 playbooks/evidence.py --client "CLIENT_NAME" --engagement ENG-YYYY-NNN
export CF_BACKUP_DEST=/path/offbox
./scripts/backup_offbox.sh
```

Deliver Evidence Pack under NDA as agreed in the engagement letter.

---

## Shift end

- [ ] Pending approvals cleared or handed over
- [ ] Breaker state noted in handoff
- [ ] LIVE vs DRY-RUN state noted
- [ ] Next on-call named and reachable

---

## Handoff template (copy/paste)

```
Client:
Phase: DRY-RUN | LIVE
Breaker: CLOSED | OPEN (reason:)
Pending approvals:
Watchdog: HEALTHY | DEGRADED | UNHEALTHY
Notes:
Next on-call:
```

---

*See also: docs/PILOT_DEPLOYMENT.md · docs/WHATSAPP_TLS.md · docs/GO_LIVE.md*
