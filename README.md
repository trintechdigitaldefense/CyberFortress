# CyberFortress

**Autonomous Incident Response Platform**  
*TrinTech Digital Defense · Trinidad & Tobago* 🇹🇹  
**PROTECTED ASSET — PILOT-READY MVP**

> Automated threat detection and tiered response — WhatsApp approval for high-impact moves, full TT Computer Misuse Act audit trail.

**License:** Proprietary — see [LICENSE](LICENSE). All rights reserved. Authorized defensive use only under written agreement with TrinTech Digital Defense.

---

## One-command start

```bash
git clone https://github.com/trintechdigitaldefense/CyberFortress.git
cd CyberFortress
./install.sh
./start.sh
```

| Command | What it does |
|---------|----------------|
| `./install.sh` | Installs core Python deps, creates `.env`, runtime folders |
| `./start.sh` | Starts **everything** (Docker if available, else local processes) |
| `./stop.sh` | Stops everything |
| `./start.sh status` | Shows what’s running |

After start:

- **Dashboard:** http://127.0.0.1:8091  
- **Health:** http://127.0.0.1:8090  
- **Default mode:** dry-run (`CF_CONTAINMENT_LIVE=false`)

---

## What’s included

- Rules-driven telemetry fusion + tiered autonomy (Tier 1 act / Tier 2 WhatsApp `APPROVE <nonce>`)
- ROE allow-list · containment + rollback playbooks
- CMA audit log · Evidence Pack · circuit breaker · 24/7 watchdog
- Dashboard (optional auth) · gated live mode

**Safety defaults:** live OFF · force OFF · admin UIs on localhost only.

See **[FIXES_VERIFIED.md](FIXES_VERIFIED.md)** for the last end-to-end demo verification.

---

## Docs

| Doc | Purpose |
|-----|---------|
| [docs/OVERVIEW.md](docs/OVERVIEW.md) | What it is |
| [docs/HOW_TO_USE.md](docs/HOW_TO_USE.md) | How to operate |
| [docs/HOW_TO_SELL.md](docs/HOW_TO_SELL.md) | Packages & USD pricing |
| [docs/CHEATSHEET.md](docs/CHEATSHEET.md) | Commands |
| [docs/PILOT_DEPLOYMENT.md](docs/PILOT_DEPLOYMENT.md) | Pilot checklist |
| [docs/WHATSAPP_TLS.md](docs/WHATSAPP_TLS.md) | Hardened WhatsApp HITL |
| [docs/OPERATOR_RUNBOOK.md](docs/OPERATOR_RUNBOOK.md) | Shift process |
| [docs/GO_LIVE.md](docs/GO_LIVE.md) | Intentional live mode |

---

## Contact

**TrinTech Digital Defense**  
Email: trintechdigitaldefense@gmail.com  
WhatsApp: +1 (868) 362-0679  
Web: https://trintechdigitaldefense.github.io

---

*Defend. Detect. Dominate.*  
Authorized defensive use only. All rights reserved.
