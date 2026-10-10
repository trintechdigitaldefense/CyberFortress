# CyberFortress

**Autonomous Incident Response & Operations Platform**  
*TrinTech Digital Defense · Trinidad & Tobago* 🇹🇹  
**PROTECTED ASSET**

---

## Overview

CyberFortress reduces Mean Time to Containment while aligning with the Trinidad & Tobago Computer Misuse Act.

### Client-ready path (required order)

1. **[docs/PILOT_DEPLOYMENT.md](docs/PILOT_DEPLOYMENT.md)** — pilot checklist  
2. **[docs/WHATSAPP_TLS.md](docs/WHATSAPP_TLS.md)** — live WhatsApp + HTTPS  
3. **[docs/OPERATOR_RUNBOOK.md](docs/OPERATOR_RUNBOOK.md)** — operator process  
4. **[docs/GO_LIVE.md](docs/GO_LIVE.md)** — intentional live mode only after sign-off  

```bash
./scripts/check_client_ready.sh
# Live mode (gated):
./scripts/enable_live_mode.sh --check
./scripts/enable_live_mode.sh --enable   # requires config/pilot_signoff.json
./scripts/disable_live_mode.sh           # emergency rollback
```

---

## Hardening (enforced)

| Control | Default |
|---------|--------|
| `CF_CONTAINMENT_LIVE` | `false` — enable only via gated script + sign-off |
| `CF_WATCHDOG_FAIL_CLOSED` | `true` |
| `CF_ALLOW_FORCE` | `false` — prefer WhatsApp APPROVE |
| Admin ports | `127.0.0.1` only |
| Containers | non-root `cfops` |
| Secrets | `.env` never committed |
| WhatsApp | localhost webhook + TLS proxy |
| Backup | `scripts/backup_offbox.sh` |

---

## Capabilities

| Feature | Status |
|---------|--------|
| Tiered Autonomy + WhatsApp HITL | ✅ |
| Legal mapping (TT CMA) | ✅ |
| Telemetry Fusion + Containment Drivers | ✅ |
| Identity Providers | ✅ |
| Evidence Pack + Circuit Breaker + Watchdog | ✅ |
| Dashboard / Health (localhost) | ✅ |
| Pilot checklist + Operator runbook | ✅ |
| WhatsApp TLS guide | ✅ |
| Gated live mode enable/disable | ✅ |

---

## Quick Start

```bash
git clone https://github.com/trintechdigitaldefense/CyberFortress.git
cd CyberFortress
pip install -r requirements.txt
cp .env.example .env && chmod 600 .env

./scripts/check_client_ready.sh
python3 -m agents.healthcheck
python3 -m agents.dashboard   # http://127.0.0.1:8091
```

SSH tunnel for remote admin:

```bash
ssh -L 8091:127.0.0.1:8091 -L 8090:127.0.0.1:8090 user@cf-host
```

---

## Docker

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

| Service | Bind |
|---------|------|
| Dashboard | `127.0.0.1:8091` |
| Health | `127.0.0.1:8090` |
| WhatsApp Webhook | `127.0.0.1:8089` + TLS proxy |
| Watchdog | fail-closed on |

---

## Contact

**TrinTech Digital Defense**  
Email: trintechdigitaldefense@gmail.com  
WhatsApp: +1 (868) 362-0679  
Web: https://trintechdigitaldefense.github.io

---

*Defend. Detect. Dominate.*  
Authorized defensive use only. All rights reserved.
