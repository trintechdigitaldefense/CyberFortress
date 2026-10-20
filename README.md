# CyberFortress

[![ci](https://github.com/trintechdigitaldefense/CyberFortress/actions/workflows/ci.yml/badge.svg)](https://github.com/trintechdigitaldefense/CyberFortress/actions/workflows/ci.yml)

**Autonomous Incident Response Platform**  
*TrinTech Digital Defense · Trinidad & Tobago* 🇹🇹  
**v0.3.1 — production monitoring platform**

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

## Live firewall host check

```bash
./scripts/check_netadmin.sh
```

Must pass on a real VM with `CAP_NET_ADMIN` before arming containment. See [docs/HOST_REQUIREMENTS.md](docs/HOST_REQUIREMENTS.md).

---

## Tests

```bash
./scripts/run_tests.sh
python3 scripts/verify_audit_chain.py
bash scripts/pilot_dry_run.sh
```

---

## Arming containment (operators only)

1. **NDA** — [docs/templates/NDA_TEMPLATE.md](docs/templates/NDA_TEMPLATE.md)  
2. **ROE** — [docs/templates/ROE_TEMPLATE.md](docs/templates/ROE_TEMPLATE.md)  
3. **Host** — `./scripts/check_netadmin.sh`  
4. **WhatsApp + HTTPS** — `./scripts/setup_whatsapp_live.sh`  
5. **`config/pilot_signoff.json`** — all flags true, no placeholders  
6. **Arm** — `./scripts/enable_live_mode.sh --check` then `--enable`  

See [docs/GO_LIVE.md](docs/GO_LIVE.md).

---

## What’s included

- Rules-driven telemetry fusion + tiered autonomy (Tier 1 act / Tier 2 WhatsApp `APPROVE <nonce>`)
- Allow-listed containment · CF_BLOCK firewall · rollback · **hash-chained CMA audit** · Evidence Pack
- Circuit breaker · 24/7 watchdog · operator-gated arming · **pytest suite + CI**

**Safety defaults:** containment OFF · force OFF · admin UIs on localhost only.

---

## Docs

| Doc | Purpose |
|-----|---------|
| [docs/OVERVIEW.md](docs/OVERVIEW.md) | What it is |
| [docs/HOW_TO_USE.md](docs/HOW_TO_USE.md) | How to operate |
| [docs/HOW_TO_SELL.md](docs/HOW_TO_SELL.md) | Positioning |
| [docs/WHATSAPP_TLS.md](docs/WHATSAPP_TLS.md) | Live Meta WhatsApp + HTTPS |
| [docs/HOST_REQUIREMENTS.md](docs/HOST_REQUIREMENTS.md) | VM + CAP_NET_ADMIN for live CF_BLOCK |
| [docs/GO_LIVE.md](docs/GO_LIVE.md) | NDA / ROE / operator arming |
| [CHANGELOG.md](CHANGELOG.md) | Release history |
| [SECURITY.md](SECURITY.md) | Vulnerability reporting |

---

## Contact

**TrinTech Digital Defense**  
Email: trintechdigitaldefense@gmail.com  
WhatsApp: +1 (868) 362-0679  
Web: https://trintechdigitaldefense.github.io

---

*Defend. Detect. Dominate.*  
Authorized defensive use only. All rights reserved.
