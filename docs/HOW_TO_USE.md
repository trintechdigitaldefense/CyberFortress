# CyberFortress — How to Use

## Fast path (recommended)

```bash
git clone https://github.com/trintechdigitaldefense/CyberFortress.git
cd CyberFortress
./install.sh    # deps + .env + folders
./start.sh      # start everything
```

| Command | Action |
|---------|--------|
| `./install.sh` | Install requirements, create `.env`, runtime dirs |
| `./start.sh` | Start all services (Docker if available, else local) |
| `./stop.sh` | Stop all services |
| `./start.sh status` | Show running status |
| `./start.sh local` | Force local Python processes |
| `./start.sh docker` | Force Docker Compose |

After start:
- Dashboard: http://127.0.0.1:8091  
- Health: http://127.0.0.1:8090  
- Default: **dry-run** (safe)

---

## Safety defaults (leave until pilot sign-off)

```bash
CF_CONTAINMENT_LIVE=false
CF_ALLOW_FORCE=false
CF_WATCHDOG_FAIL_CLOSED=true
```

These are set in `.env` by `./install.sh`.

---

## Run a dry-run action

```bash
python3 playbooks/execute.py --list
python3 playbooks/execute.py --action block_ip --target 203.0.113.50
python3 playbooks/execute.py --action unblock_ip --target 203.0.113.50
```

Tier 2 needs WhatsApp APPROVE when WhatsApp is enabled.

---

## Dashboard password (optional)

```bash
# in .env
CF_DASHBOARD_USER=operator
CF_DASHBOARD_PASS=your-strong-password
./stop.sh && ./start.sh
```

Remote access:

```bash
ssh -L 8091:127.0.0.1:8091 -L 8090:127.0.0.1:8090 user@cf-host
```

---

## Evidence pack

```bash
python3 playbooks/evidence.py --client "Acme Ltd" --engagement ENG-2026-001
```

---

## WhatsApp + TLS

Follow **docs/WHATSAPP_TLS.md**, set tokens in `.env`, then `./stop.sh && ./start.sh`.

---

## Go live (only after full checklist)

```bash
cp config/pilot_signoff.example.json config/pilot_signoff.json
# Complete flags + authorized_actions
./scripts/enable_live_mode.sh --check
./scripts/enable_live_mode.sh --enable
./stop.sh && ./start.sh
```

Rollback live mode:

```bash
./scripts/disable_live_mode.sh
./stop.sh && ./start.sh
```

---

## Operator daily use

See **docs/OPERATOR_RUNBOOK.md** — shift start, APPROVE rules, emergency stop.

Emergency:

```bash
./scripts/disable_live_mode.sh
python3 playbooks/breaker.py trip --reason "Operator emergency stop"
./stop.sh
```
