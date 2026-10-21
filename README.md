# CyberFortress

[![ci](https://github.com/trintechdigitaldefense/CyberFortress/actions/workflows/ci.yml/badge.svg)](https://github.com/trintechdigitaldefense/CyberFortress/actions/workflows/ci.yml)

**Autonomous Incident Response Platform**  
*TrinTech Digital Defense · Trinidad & Tobago* 🇹🇹  
**v0.3.11 — monitoring + IR response team (pilot-ready)**

> Automated threat detection and tiered response — WhatsApp approval for high-impact moves, active firewall containment when armed, full TT Computer Misuse Act audit trail.

**License:** Proprietary — see [LICENSE](LICENSE). All rights reserved.  
**Pricing:** On request.

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

After start: **Dashboard** http://127.0.0.1:8091 · **Health** http://127.0.0.1:8090 · **monitoring mode** by default.

---

## IR response team

Detect → Investigate → Respond → Report agents run with `./start.sh`.

- Cases: `logs/ir_cases/`
- Reports: `evidence/ir_reports/`
- API: `GET /api/ir/cases`
- Docs: [docs/IR_RESPONSE_TEAM.md](docs/IR_RESPONSE_TEAM.md)

---

## Live firewall host check (real VM pilot)

```bash
./scripts/pilot_vm_preflight.sh   # preferred — full pilot gate
./scripts/check_netadmin.sh       # netfilter only
```

**Must be green** before arming. WhatsApp credentials can be added later (`whatsapp_deferred: true`).  
See [docs/PILOT_VM.md](docs/PILOT_VM.md) · [docs/HOST_REQUIREMENTS.md](docs/HOST_REQUIREMENTS.md).

---

## Tests

```bash
./scripts/run_tests.sh
python3 scripts/verify_audit_chain.py
bash scripts/pilot_dry_run.sh
bash scripts/quality_check.sh
```

---

## Arming containment (operators only)

1. **NDA** — docs/templates/NDA_TEMPLATE.md  
2. **ROE** — docs/templates/ROE_TEMPLATE.md  
3. **Host** — `./scripts/pilot_vm_preflight.sh` (green)  
4. **`config/pilot_signoff.json`** — `whatsapp_deferred: true` until Meta creds  
5. **Arm** — `./scripts/enable_live_mode.sh --check` then `--enable`  
6. **Later** — WhatsApp TLS · `whatsapp_tls_verified: true`  

See [docs/GO_LIVE.md](docs/GO_LIVE.md).

---

## Docs

| Doc | Purpose |
|-----|---------|
| [docs/OVERVIEW.md](docs/OVERVIEW.md) | What it is |
| [docs/QUALITY_STATUS.md](docs/QUALITY_STATUS.md) | Honest scorecard |
| [docs/IR_RESPONSE_TEAM.md](docs/IR_RESPONSE_TEAM.md) | Detect→report agents |
| [docs/PILOT_VM.md](docs/PILOT_VM.md) | Real VM pilot + netadmin gate |
| [docs/HOST_REQUIREMENTS.md](docs/HOST_REQUIREMENTS.md) | CAP_NET_ADMIN for live CF_BLOCK |
| [docs/GO_LIVE.md](docs/GO_LIVE.md) | NDA / ROE / operator arming |
| [docs/WHATSAPP_TLS.md](docs/WHATSAPP_TLS.md) | Live Meta WhatsApp (add later) |
| [CHANGELOG.md](CHANGELOG.md) | Release history |
