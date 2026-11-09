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

Latest R2/R3 baseline CI evidence: [run #408](https://github.com/trintechdigitaldefense/CyberFortress/actions/runs/42614223976) passed on `a3a50bd2823aa55f8223378d0158596196001d2d`; subsequent hardening changes are validated by [run #415](https://github.com/trintechdigitaldefense/CyberFortress/actions/runs/42614686172) on `81202daf17b4cd7abc5e90b3aca50fa13bf883fc`. The additional malicious-archive/failure-injection regression in the current head is awaiting [run #416](https://github.com/trintechdigitaldefense/CyberFortress/actions/runs/42617182784). These are engineering CI results, not owner VM or client acceptance.

## Verify

```bash
./scripts/release_gate.sh
./scripts/readiness_check.sh
python3 -m pytest tests/ -q
```
