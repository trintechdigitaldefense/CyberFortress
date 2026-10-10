# CyberFortress

**Autonomous Incident Response Platform**  
*TrinTech Digital Defense · Trinidad & Tobago* 🇹🇹  
**PROTECTED ASSET — PILOT-READY MVP**

> Automated threat detection and tiered response — WhatsApp approval for high-impact moves, full TT Computer Misuse Act audit trail.

**License:** Proprietary — see [LICENSE](LICENSE). All rights reserved. Authorized defensive use only under written agreement with TrinTech Digital Defense.

**Pricing:** not published yet — still building. Stay tuned.

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

After start: **Dashboard** http://127.0.0.1:8091 · **Health** http://127.0.0.1:8090 · **dry-run** by default.

---

## Before any client live mode

1. **NDA** — [docs/templates/NDA_TEMPLATE.md](docs/templates/NDA_TEMPLATE.md)  
2. **ROE** — [docs/templates/ROE_TEMPLATE.md](docs/templates/ROE_TEMPLATE.md)  
3. **WhatsApp + HTTPS** — `./scripts/setup_whatsapp_live.sh` · [docs/WHATSAPP_TLS.md](docs/WHATSAPP_TLS.md)  
4. **Sign-off** — `config/pilot_signoff.json` from example  
5. **Enable** — `./scripts/enable_live_mode.sh --check` then `--enable`  

See [docs/GO_LIVE.md](docs/GO_LIVE.md).

---

## What’s included

- Rules-driven telemetry fusion + tiered autonomy (Tier 1 act / Tier 2 WhatsApp `APPROVE <nonce>`)
- ROE allow-list · containment + rollback · CMA audit · Evidence Pack
- Circuit breaker · 24/7 watchdog · gated live mode

**Safety defaults:** live OFF · force OFF · admin UIs on localhost only.

---

## Docs

| Doc | Purpose |
|-----|---------|
| [docs/OVERVIEW.md](docs/OVERVIEW.md) | What it is |
| [docs/HOW_TO_USE.md](docs/HOW_TO_USE.md) | How to operate |
| [docs/HOW_TO_SELL.md](docs/HOW_TO_SELL.md) | Positioning (no prices yet) |
| [docs/WHATSAPP_TLS.md](docs/WHATSAPP_TLS.md) | Live Meta WhatsApp + HTTPS |
| [docs/GO_LIVE.md](docs/GO_LIVE.md) | NDA / ROE / sign-off / live |
| [docs/OPERATOR_RUNBOOK.md](docs/OPERATOR_RUNBOOK.md) | Shift process |
| [docs/CHEATSHEET.md](docs/CHEATSHEET.md) | Commands |

---

## Contact

**TrinTech Digital Defense**  
Email: trintechdigitaldefense@gmail.com  
WhatsApp: +1 (868) 362-0679  
Web: https://trintechdigitaldefense.github.io

---

*Defend. Detect. Dominate.*  
Authorized defensive use only. All rights reserved.
