# CyberFortress Pilot Deployment Checklist

**TrinTech Digital Defense — Protected Asset**

**Mandatory** before any client network placement and **before** live mode.

Related docs:
- **Host / CAP_NET_ADMIN:** [HOST_REQUIREMENTS.md](HOST_REQUIREMENTS.md)
- **Live WhatsApp + TLS:** [WHATSAPP_TLS.md](WHATSAPP_TLS.md)
- **Operator process:** [OPERATOR_RUNBOOK.md](OPERATOR_RUNBOOK.md)
- **Intentional live mode:** [GO_LIVE.md](GO_LIVE.md)

```bash
# Preflight
./scripts/check_client_ready.sh
./scripts/check_netadmin.sh   # required before live CF_BLOCK
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

## 0. Host (live firewall)

- [ ] Pilot runs on **VM or bare metal** (not a netfilter-locked container)
- [ ] `./scripts/check_netadmin.sh` passes
- [ ] `host_netadmin_verified: true` in `config/pilot_signoff.json` before arming

If check fails → **MONITORING only** until host is fixed.

## 1. Legal & Authorization

- [ ] Signed NDA ([templates/NDA_TEMPLATE.md](templates/NDA_TEMPLATE.md))
- [ ] Signed ROE ([templates/ROE_TEMPLATE.md](templates/ROE_TEMPLATE.md)) — monitoring, listed containment actions, WhatsApp HITL
- [ ] Primary + secondary WhatsApp admin numbers designated
- [ ] TT Computer Misuse Act justifications accepted by client
- [ ] Operators assigned per [OPERATOR_RUNBOOK.md](OPERATOR_RUNBOOK.md)
- [ ] `config/pilot_signoff.json` filled (no placeholders; all flags true only after real signatures)

## 2. Technical preflight

- [ ] `./install.sh` and `./start.sh` healthy
- [ ] Dashboard + health on localhost only
- [ ] Dry-run pilot: `bash scripts/pilot_dry_run.sh`
- [ ] Audit chain verifies

## 3. WhatsApp

- [ ] Meta token + phone number ID in `.env` (never committed)
- [ ] TLS in front of webhook for inbound APPROVE
- [ ] Test message / daily report path verified

## 4. Go-live

- [ ] `./scripts/enable_live_mode.sh --check`
- [ ] `./scripts/enable_live_mode.sh --enable`
- [ ] Restart; confirm `containment_live=true` and firewall not UNAVAILABLE

---

*Defend. Detect. Dominate.*
