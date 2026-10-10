# Intentional Live Mode

**TrinTech Digital Defense — CyberFortress**

Live containment (`CF_CONTAINMENT_LIVE=true`) is **never** the default.  
It is enabled only after pilot checklist completion and explicit sign-off.

---

## Prerequisites (all required)

1. **docs/PILOT_DEPLOYMENT.md** checklist completed and filed
2. **docs/WHATSAPP_TLS.md** completed — live WhatsApp + HTTPS working
3. **docs/OPERATOR_RUNBOOK.md** understood by on-call operators
4. Signed NDA + ROE authorizing listed containment actions
5. Sign-off record present: `config/pilot_signoff.json` (from example template)

---

## Enable live mode (controlled)

```bash
# 1. Confirm sign-off file exists and is valid
./scripts/enable_live_mode.sh --check

# 2. Enable (writes env flag + reminds operator process)
./scripts/enable_live_mode.sh --enable

# 3. Restart services so containers pick up CF_CONTAINMENT_LIVE=true
docker compose -f docker/docker-compose.yml up -d

# 4. Verify
python3 -m agents.healthcheck
# Containment live should report true
```

The enable script **refuses** to run if:
- `config/pilot_signoff.json` is missing or incomplete
- Required fields (client, signed_by, date, checklist_complete) are absent
- Operator does not type the confirmation phrase

---

## Disable live mode (rollback)

```bash
./scripts/disable_live_mode.sh
docker compose -f docker/docker-compose.yml up -d
python3 playbooks/breaker.py trip --reason "Live mode disabled by operator"
# Optional: reset breaker after situation is stable
# python3 playbooks/breaker.py reset
```

---

## What “live” means

| Mode | Behaviour |
|------|-----------|
| DRY-RUN (default) | Drivers log intended iptables/session/etc. actions only |
| LIVE | Drivers execute real containment on the host/network |

Tier rules still apply:
- Tier 1: execute + notify
- Tier 2: WhatsApp APPROVE required (`CF_ALLOW_FORCE` still false unless emergency)

---

## First 48 hours after go-live

- [ ] Operator on watch per OPERATOR_RUNBOOK
- [ ] Watchdog running with fail-closed
- [ ] Evidence pack at 24h and 48h
- [ ] Off-box backup scheduled
- [ ] Client knows how WhatsApp alerts look and who approves

---

## Sign-off file

Copy and complete:

```bash
cp config/pilot_signoff.example.json config/pilot_signoff.json
chmod 600 config/pilot_signoff.json
# Edit with client name, dates, operator names, checklist confirmation
```

`config/pilot_signoff.json` is gitignored — do not commit client sign-offs.

---

*Defend. Detect. Dominate.*
