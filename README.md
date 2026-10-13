# CyberFortress

**Autonomous Incident Response Platform**  
*TrinTech Digital Defense · Trinidad & Tobago* 🇹🇹  
**v0.3.0 — production monitoring platform**

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

After start: **Dashboard** http://127.0.0.1:8091 · **Health** http://127.0.0.1:8090 · **monitoring mode** by default (firewall standby until an operator arms containment).

---

## Tests

```bash
./scripts/run_tests.sh
# or: pytest tests/ -v
```

Verify audit chain:

```bash
python3 scripts/verify_audit_chain.py
```

Pilot drill (synthetic event → fusion → evidence pack):

```bash
bash scripts/pilot_dry_run.sh
```

---

## Arming containment (operators only — not on the client dashboard)

Containment stays in **monitoring** until an operator completes the offline go-live process:

1. **NDA** — [docs/templates/NDA_TEMPLATE.md](docs/templates/NDA_TEMPLATE.md)  
2. **ROE** — [docs/templates/ROE_TEMPLATE.md](docs/templates/ROE_TEMPLATE.md)  
3. **WhatsApp + HTTPS** — `./scripts/setup_whatsapp_live.sh` · [docs/WHATSAPP_TLS.md](docs/WHATSAPP_TLS.md)  
4. **Authorization file** — `config/pilot_signoff.json` (operator host only; never shown on the dashboard)  
5. **Arm** — `./scripts/enable_live_mode.sh --check` then `--enable`  

See [docs/GO_LIVE.md](docs/GO_LIVE.md). The client dashboard shows protection status only — not legal sign-off.

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
