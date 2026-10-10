# CyberFortress

**Autonomous Incident Response Platform**  
*TrinTech Digital Defense · Trinidad & Tobago* 🇹🇹  
**PROTECTED ASSET — MVP CLOSED**

> Fast containment, WhatsApp approval for big moves, full TT Computer Misuse Act audit trail.

---

## Start here (close-out docs)

| Doc | Purpose |
|-----|---------|
| **[docs/OVERVIEW.md](docs/OVERVIEW.md)** | What it is |
| **[docs/HOW_TO_USE.md](docs/HOW_TO_USE.md)** | How to operate |
| **[docs/HOW_TO_SELL.md](docs/HOW_TO_SELL.md)** | How to package & sell |
| **[docs/CHEATSHEET.md](docs/CHEATSHEET.md)** | Commands & switches |
| [docs/PILOT_DEPLOYMENT.md](docs/PILOT_DEPLOYMENT.md) | Pilot checklist |
| [docs/WHATSAPP_TLS.md](docs/WHATSAPP_TLS.md) | Live WhatsApp + HTTPS |
| [docs/OPERATOR_RUNBOOK.md](docs/OPERATOR_RUNBOOK.md) | Shift process |
| [docs/GO_LIVE.md](docs/GO_LIVE.md) | Intentional live mode |

```bash
./scripts/check_client_ready.sh
```

---

## What’s included

- Tiered autonomy (Tier 1 act / Tier 2 WhatsApp APPROVE)
- **ROE allow-list** (`authorized_actions` in pilot sign-off)
- Containment + **rollback** playbooks
- CMA-mapped audit log + Evidence Pack
- Circuit breaker + 24/7 fail-closed watchdog
- Dashboard with optional **HTTP Basic Auth** (`127.0.0.1`)
- Gated live mode (`enable_live_mode.sh` / `disable_live_mode.sh`)
- Identity providers: local Linux, LDAP/AD, Azure AD

---

## Hardened defaults

| Control | Default |
|---------|--------|
| Live containment | **OFF** |
| `--force` | **OFF** |
| Watchdog fail-closed | **ON** |
| Admin UIs | localhost only |
| Containers | non-root |

---

## Quick start

```bash
git clone https://github.com/trintechdigitaldefense/CyberFortress.git
cd CyberFortress
pip install -r requirements.txt
cp .env.example .env && chmod 600 .env

./scripts/check_client_ready.sh
python3 playbooks/execute.py --list
export CF_DASHBOARD_PASS='change-me'
python3 -m agents.dashboard   # http://127.0.0.1:8091
```

---

## Contact

**TrinTech Digital Defense**  
Email: trintechdigitaldefense@gmail.com  
WhatsApp: +1 (868) 362-0679  
Web: https://trintechdigitaldefense.github.io

---

*Defend. Detect. Dominate.*  
Authorized defensive use only. All rights reserved.
