# CyberFortress Cheatsheet

## Safety switches

| Variable | Safe value | Meaning |
|----------|------------|---------|
| `CF_CONTAINMENT_LIVE` | `false` | Dry-run |
| `CF_ALLOW_FORCE` | `false` | No `--force` |
| `CF_WATCHDOG_FAIL_CLOSED` | `true` | Trip breaker if unhealthy |
| `CF_DASHBOARD_PASS` | set | Dashboard basic auth |

## Essential commands

```bash
./scripts/check_client_ready.sh
python3 -m agents.healthcheck
python3 -m agents.watchdog_agent --once
python3 -m agents.dashboard
python3 playbooks/execute.py --list
python3 playbooks/execute.py --action block_ip --target 203.0.113.50
python3 playbooks/execute.py --action unblock_ip --target 203.0.113.50
python3 playbooks/breaker.py status|reset|trip
python3 playbooks/evidence.py --client "NAME" --engagement ENG-ID
./scripts/backup_offbox.sh
./scripts/enable_live_mode.sh --check|--enable
./scripts/disable_live_mode.sh
```

## Playbooks

**Contain:** `block_ip` · `terminate_session` · `deploy_decoy` · `isolate_endpoint` · `subnet_isolation` · `credential_rotation` · `halt_operations`  
**Rollback:** `unblock_ip` · `restore_endpoint` · `restore_subnet`

Tier 1 = act + notify · Tier 2 = WhatsApp APPROVE  
ROE: only `authorized_actions` in `config/pilot_signoff.json`

## Ports (localhost only)

| Port | Service |
|------|---------|
| 8091 | Dashboard |
| 8090 | Health |
| 8089 | WhatsApp webhook (TLS proxy in front) |

```bash
ssh -L 8091:127.0.0.1:8091 -L 8090:127.0.0.1:8090 user@host
```

## Emergency stop

```bash
./scripts/disable_live_mode.sh
python3 playbooks/breaker.py trip --reason "Operator emergency stop"
```

## Docs map

| Doc | Use |
|-----|-----|
| OVERVIEW.md | What it is |
| HOW_TO_USE.md | Operate it |
| HOW_TO_SELL.md | Package & pitch |
| PILOT_DEPLOYMENT.md | Checklist |
| WHATSAPP_TLS.md | Live HITL |
| OPERATOR_RUNBOOK.md | Shifts |
| GO_LIVE.md | Intentional live |
| CHEATSHEET.md | This page |

## Sales one-liner

> Fast containment, WhatsApp approval for big moves, full TT CMA audit trail.
