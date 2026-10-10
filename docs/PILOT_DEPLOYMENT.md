# CyberFortress Pilot Deployment Checklist

**TrinTech Digital Defense — Protected Asset**

**Mandatory** before any client network placement and **before** live mode.

Related docs:
- **Live WhatsApp + TLS:** [WHATSAPP_TLS.md](WHATSAPP_TLS.md)
- **Operator process:** [OPERATOR_RUNBOOK.md](OPERATOR_RUNBOOK.md)
- **Intentional live mode:** [GO_LIVE.md](GO_LIVE.md)

```bash
# Preflight
./scripts/check_client_ready.sh
```

---

## Hardening defaults (enforced in repo)

| Control | Default | Notes |
|---------|---------|-------|
| `CF_CONTAINMENT_LIVE` | `false` | Enable only via `scripts/enable_live_mode.sh` |
| `CF_WATCHDOG_FAIL_CLOSED` | `true` | Auto-trip breaker if UNHEALTHY |
| `CF_ALLOW_FORCE` | `false` | Prefer WhatsApp APPROVE |
| Admin ports | `127.0.0.1` | SSH tunnel / admin VPN only |
| Containers | non-root `cfops` | uid 10001 |
| Secrets | `.env` only | Never commit |
| WhatsApp TLS | required for HITL | [WHATSAPP_TLS.md](WHATSAPP_TLS.md) |
| Off-box backup | script | `scripts/backup_offbox.sh` |

---

## 1. Legal & Authorization

- [ ] Signed NDA
- [ ] Signed ROE (monitoring, listed containment actions, credential rotation if used, WhatsApp HITL)
- [ ] Primary + secondary WhatsApp admin numbers designated
- [ ] TT Computer Misuse Act justifications accepted by client
- [ ] Operators assigned per [OPERATOR_RUNBOOK.md](OPERATOR_RUNBOOK.md)

---

## 2. Environment

- [ ] Ubuntu 22.04+ host with Docker
- [ ] Visibility to target assets per ROE
- [ ] Firewall: management only via admin VPN/SSH
- [ ] Outbound to WhatsApp Cloud API allowed
- [ ] NTP synced
- [ ] `CF_BACKUP_DEST` off-box path ready

---

## 3. Configuration

```bash
cp .env.example .env && chmod 600 .env
# CF_CONTAINMENT_LIVE=false
# CF_ALLOW_FORCE=false
# CF_WATCHDOG_FAIL_CLOSED=true
```

- [ ] No secrets in git
- [ ] `.env` permissions 600

---

## 4. Dry-run pre-flight

```bash
./scripts/check_client_ready.sh
python3 -m agents.healthcheck
python3 -m agents.watchdog_agent --once
python3 playbooks/execute.py --list
python3 playbooks/breaker.py status
python3 playbooks/evidence.py --client "PILOT-CLIENT" --engagement ENG-PILOT-001
./scripts/backup_offbox.sh
```

- [ ] All checks pass
- [ ] Evidence pack OK
- [ ] Breaker CLOSED

---

## 5. Live WhatsApp + TLS

Complete **[WHATSAPP_TLS.md](WHATSAPP_TLS.md)** in full.

- [ ] Webhook on `127.0.0.1:8089` only
- [ ] Public HTTPS (Caddy / Cloudflare Tunnel)
- [ ] Meta webhook verified
- [ ] APPROVE/DENY test successful
- [ ] Dashboard/health **not** public

---

## 6. Operator process ready

Complete **[OPERATOR_RUNBOOK.md](OPERATOR_RUNBOOK.md)** briefing.

- [ ] Lead + on-call named
- [ ] Shift-start checks practiced
- [ ] Emergency stop known: `./scripts/disable_live_mode.sh`
- [ ] Client briefed on WhatsApp alerts

---

## 7. Sign-off file

```bash
cp config/pilot_signoff.example.json config/pilot_signoff.json
chmod 600 config/pilot_signoff.json
# Set all flags true; fill client, engagement, names, date
./scripts/enable_live_mode.sh --check
```

- [ ] `checklist_complete: true`
- [ ] `whatsapp_tls_verified: true`
- [ ] `operator_runbook_acknowledged: true`
- [ ] `roe_signed` / `nda_signed: true`

---

## 8. Intentional live mode (only after 1–7)

See **[GO_LIVE.md](GO_LIVE.md)**.

```bash
./scripts/enable_live_mode.sh --enable
# Type: ENABLE LIVE MODE
docker compose -f docker/docker-compose.yml up -d
python3 -m agents.healthcheck
```

- [ ] Operator on watch 24–48h
- [ ] Rollback tested: `./scripts/disable_live_mode.sh`

---

## 9. Ongoing

- [ ] Evidence packs after significant activity
- [ ] Scheduled off-box backups
- [ ] Weekly breaker / held-action review
- [ ] Prefer WhatsApp APPROVE; avoid force

---

*Defend. Detect. Dominate.*  
TrinTech Digital Defense
