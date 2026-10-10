# CyberFortress — How to Use

## 1. Install

```bash
git clone https://github.com/trintechdigitaldefense/CyberFortress.git
cd CyberFortress
pip install -r requirements.txt
cp .env.example .env && chmod 600 .env
```

## 2. Safety defaults (leave as-is until pilot sign-off)

```bash
CF_CONTAINMENT_LIVE=false
CF_ALLOW_FORCE=false
CF_WATCHDOG_FAIL_CLOSED=true
```

## 3. Preflight

```bash
./scripts/check_client_ready.sh
python3 -m agents.healthcheck
python3 -m agents.watchdog_agent --once
python3 playbooks/execute.py --list
```

## 4. Run a dry-run action

```bash
# Tier 1 (ROE-allowed) — no force needed
python3 playbooks/execute.py --action block_ip --target 203.0.113.50

# Rollback
python3 playbooks/execute.py --action unblock_ip --target 203.0.113.50
```

Tier 2 actions need WhatsApp APPROVE when WhatsApp is enabled.

## 5. Dashboard

```bash
export CF_DASHBOARD_USER=operator
export CF_DASHBOARD_PASS='your-strong-password'
python3 -m agents.dashboard
# http://127.0.0.1:8091
```

Remote:

```bash
ssh -L 8091:127.0.0.1:8091 -L 8090:127.0.0.1:8090 user@cf-host
```

## 6. Evidence pack

```bash
python3 playbooks/evidence.py --client "Acme Ltd" --engagement ENG-2026-001
```

## 7. WhatsApp + TLS

Follow **docs/WHATSAPP_TLS.md**, then set:

```bash
CF_WHATSAPP_ENABLED=true
# + token, phone id, admins, verify token
```

## 8. Go live (only after full checklist)

```bash
cp config/pilot_signoff.example.json config/pilot_signoff.json
# Complete flags + authorized_actions
./scripts/enable_live_mode.sh --check
./scripts/enable_live_mode.sh --enable
docker compose -f docker/docker-compose.yml up -d
```

Rollback live mode:

```bash
./scripts/disable_live_mode.sh
```

## 9. Operator daily use

See **docs/OPERATOR_RUNBOOK.md** — shift start, APPROVE rules, emergency stop.

## 10. Docker

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

| Service | Address |
|---------|---------|
| Dashboard | `127.0.0.1:8091` |
| Health | `127.0.0.1:8090` |
| WhatsApp webhook | `127.0.0.1:8089` + TLS proxy |
