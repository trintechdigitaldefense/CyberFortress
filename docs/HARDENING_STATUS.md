# Hardening status — Phases 1–7

**Branch:** `hardening/cyberfortress-final-release`  
**Version:** see `VERSION`  
**Default mode:** MONITORING (`CF_CONTAINMENT_LIVE=false`)

## Phase completion (software)

| Phase | Status | Notes |
|-------|--------|-------|
| 1 Reliability & security | Done | Metrics deadlock fixed, audit fail-closed, CI blocking, dashboard auth, WhatsApp signatures, firewall ROE |
| 2 Tenant / secrets | Engineering gate complete | One tenant per isolated runtime; fail-closed dashboard/SOC API/agent guards; tenant path and SIEM token controls |
| 3 Defensive SOC depth | Done | Telemetry schema, scoring docs, IR state machine, evidence integrity |
| 4 Operational readiness | Done | `readiness_check`, install polish, live enable requires soak+legal |
| 5 Test & release quality | CI verified | 141 tests; blocking Ruff/Bandit/pip-audit and install, upgrade, backup/restore, firewall and deployment regressions |
| 6 Docs / version | Done | This file + QUALITY_STATUS + VERSION + CHANGELOG |
| 7 GitHub delivery | Pending owner/reviewer decision | Keep this hardening branch intact; no merge or release tag until R1/R4/R5, owner VM validation and required review/sign-offs are complete |

## Not replaced by software

- Isolated VM soak (`docs/PILOT_SOAK.md`)
- Legal/ROE/E&O (`docs/LEGAL_GATE.md`)

Latest R2/R3 baseline CI evidence: [run #416](https://github.com/trintechdigitaldefense/CyberFortress/actions/runs/42617182784) passed on `1ccc6712488ccb6be71a16e006fdf9eef59411b7` with 141 tests, Ruff, Bandit, pip-audit, installer/upgrade/lifecycle checks, tenant/API controls, firewall namespace acceptance and malicious-archive plus backup-failure regressions. R2 and R3 engineering gates are closed; owner VM validation and later roadmap/release gates remain outstanding. These are engineering CI results, not owner VM or client acceptance.

## Verify

```bash
./scripts/release_gate.sh
./scripts/readiness_check.sh
python3 -m pytest tests/ -q
```
