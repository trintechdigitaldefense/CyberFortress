# CyberFortress Pilot Deployment Checklist

**TrinTech Digital Defense — Protected Asset**

**Mandatory:** complete this checklist before placing CyberFortress on any client network  
and **before** setting `CF_CONTAINMENT_LIVE=true`.

---

## Hardening defaults (enforced in repo)

| Control | Default | Notes |
|---------|---------|-------|
| `CF_CONTAINMENT_LIVE` | `false` | Keep until pilot sign-off |
| `CF_WATCHDOG_FAIL_CLOSED` | `true` | Auto-trip breaker if UNHEALTHY |
| `CF_ALLOW_FORCE` | `false` | Prefer WhatsApp APPROVE over `--force` |
| Dashboard / health / webhook binds | `127.0.0.1` | Admin network / SSH tunnel only |
| Container user | non-root `cfops` (uid 10001) | Dockerfile + compose |
| Secrets | `.env` / secrets manager | Never commit; use `.env.example` |
| WhatsApp webhook TLS | reverse proxy required | See `docker/caddy.whatsapp.example` |
| Off-box backup | `scripts/backup_offbox.sh` | `logs/` + `evidence/` |

---

## 1. Legal & Authorization

- [ ] Signed NDA in place
- [ ] Signed Rules of Engagement (ROE) that explicitly authorizes:
  - Network monitoring
  - Automated containment actions (list which ones)
  - Credential rotation if used
  - Out-of-band WhatsApp notifications/approvals
- [ ] Client has designated primary + secondary WhatsApp admin numbers
- [ ] Written confirmation that TT Computer Misuse Act justifications are acceptable to the client
- [ ] Pilot sign-off recorded before enabling live containment

---

## 2. Environment Preparation

- [ ] Linux host (Ubuntu 22.04+ recommended) with Docker
- [ ] Network placement allows visibility of target assets
- [ ] Firewall: only admin VPN/SSH can reach host management ports
- [ ] Firewall: outbound allowed to WhatsApp Cloud API (if used)
- [ ] Time synchronized (NTP)
- [ ] Off-box backup destination prepared (`CF_BACKUP_DEST`)

---

## 3. Configuration (no secrets in git)

```bash
cp .env.example .env
chmod 600 .env
# Edit .env — never commit it

# Mandatory safety until pilot sign-off
CF_CONTAINMENT_LIVE=false
CF_ALLOW_FORCE=false
CF_WATCHDOG_FAIL_CLOSED=true
```

- [ ] All secrets only in `.env` or a secrets manager
- [ ] `.env` is **not** committed (confirmed in `.gitignore`)
- [ ] WhatsApp / LDAP / Azure credentials not present in any tracked file

---

## 4. Pre-Flight Tests (Dry-Run)

```bash
python3 -m agents.healthcheck
python3 -m agents.watchdog_agent --once
python3 playbooks/execute.py --list

# Tier 1 dry-run (no force required)
# Tier 2 should go through WhatsApp when enabled
python3 playbooks/breaker.py status
python3 playbooks/evidence.py --client "PILOT-CLIENT" --engagement ENG-PILOT-001
./scripts/backup_offbox.sh   # after setting CF_BACKUP_DEST
```

- [ ] Health + watchdog run cleanly
- [ ] Evidence pack generated
- [ ] Circuit breaker CLOSED
- [ ] Off-box backup succeeds

---

## 5. WhatsApp Webhook + TLS

- [ ] Webhook container bound to `127.0.0.1:8089` only
- [ ] TLS reverse proxy or tunnel in front (Caddy example: `docker/caddy.whatsapp.example`)
- [ ] Meta Developer Console points to `https://your-host/...`
- [ ] Verify token matches `CF_WHATSAPP_VERIFY_TOKEN`
- [ ] Test APPROVE / DENY recorded under `logs/whatsapp_pending/`

**Do not expose dashboard/health on the public internet.**  
Access via SSH tunnel:

```bash
ssh -L 8091:127.0.0.1:8091 -L 8090:127.0.0.1:8090 user@cf-host
```

---

## 6. Go-Live Decision (only after sections 1–5)

```bash
# Explicit pilot sign-off required
export CF_CONTAINMENT_LIVE=true
# Keep CF_ALLOW_FORCE=false unless emergency supervised use
```

- [ ] Operator monitoring first 24–48 hours
- [ ] Client briefed on WhatsApp messages
- [ ] Rollback agreed: `CF_CONTAINMENT_LIVE=false` + `python3 playbooks/breaker.py trip`
- [ ] Watchdog running with `CF_WATCHDOG_FAIL_CLOSED=true`

---

## 7. Ongoing

- [ ] Daily or on-demand Evidence Pack generation
- [ ] Scheduled off-box backup (`scripts/backup_offbox.sh`)
- [ ] Weekly review of circuit-breaker trips and held actions
- [ ] Prefer WhatsApp APPROVE; avoid `--force`
- [ ] Keep ROE and admin numbers up to date

---

*Defend. Detect. Dominate.*  
TrinTech Digital Defense
