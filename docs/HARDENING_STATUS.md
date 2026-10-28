# Hardening status — Phases 1–7

**Branch:** `hardening/cyberfortress-final-release`  
**Version:** see `VERSION`  
**Default mode:** MONITORING (`CF_CONTAINMENT_LIVE=false`)

## Phase completion (software)

| Phase | Status | Notes |
|-------|--------|-------|
| 1 Reliability & security | Done | Metrics deadlock fixed, audit fail-closed, CI blocking, dashboard auth, WhatsApp signatures, firewall ROE |
| 2 Tenant / secrets | Done | `tenant_guard`, case isolation, SIEM token, secrets rotation |
| 3 Defensive SOC depth | Done | Telemetry schema, scoring docs, IR state machine, evidence integrity |
| 4 Operational readiness | Done | `readiness_check`, install polish, live enable requires soak+legal |
| 5 Test & release quality | Done | 138 tests, `release_gate.sh`, hardened CI |
| 6 Docs / version | Done | This file + QUALITY_STATUS + VERSION + CHANGELOG |
| 7 GitHub delivery | In progress | PR to main; merge after green CI + review |

## Not replaced by software

- Isolated VM soak (`docs/PILOT_SOAK.md`)
- Legal/ROE/E&O (`docs/LEGAL_GATE.md`)

## Verify

```bash
./scripts/release_gate.sh
./scripts/readiness_check.sh
python3 -m pytest tests/ -q
```
