# CyberFortress

[![ci](https://github.com/trintechdigitaldefense/CyberFortress/actions/workflows/ci.yml/badge.svg)](https://github.com/trintechdigitaldefense/CyberFortress/actions/workflows/ci.yml)

**Incident Response and Defensive Monitoring Platform**  
*TrinTech Digital Defense · Trinidad & Tobago* 🇹🇹  
**Version 0.6.0-rc1 — engineering release candidate; owner VM validation pending**

> Rules-driven threat detection, incident investigation, evidence collection and tiered response workflows. Monitoring is the default. High-impact containment remains disabled unless the technical, engagement and human-approval gates are satisfied.

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
| `./install.sh` | Creates `.venv`, installs pinned dependencies, creates `.env` if absent |
| `./start.sh` | Starts the selected local services |
| `./stop.sh` | Stops services |
| `./start.sh status` | Shows service status |
| `bash scripts/upgrade.sh` | Fast-forward-only source upgrade with source rollback on install failure |

Dashboard: http://127.0.0.1:8091 · Health: http://127.0.0.1:8090

**Safety default:** `CF_CONTAINMENT_LIVE=false`. Keep the platform in monitoring/dry-run mode during installation and validation.

---

## Incident response workflow

The platform is designed to support detection → investigation → response decision → reporting.

- Cases: `logs/ir_cases/`
- Reports: `evidence/ir_reports/`
- API: `GET /api/ir/cases`
- Docs: [docs/IR_RESPONSE_TEAM.md](docs/IR_RESPONSE_TEAM.md)

---

## Deployment profiles

| Profile | Supported use | Live containment |
|---|---|---|
| Native Ubuntu/Debian VM | Candidate environment for owner-run validation | Not approved by this release candidate |
| Android Termux / Ubuntu proot | Monitoring, analysis and dry-run | Forced monitoring-only |
| Standard Docker Compose | Application services and monitoring | Forced monitoring-only |

The owner-run VM validation is still pending. CI namespace tests do not prove host capability or client readiness. See [docs/PILOT_DEPLOYMENT.md](docs/PILOT_DEPLOYMENT.md), [docs/PILOT_VM.md](docs/PILOT_VM.md) and [docs/HOST_REQUIREMENTS.md](docs/HOST_REQUIREMENTS.md).

---

## Tests

```bash
./scripts/run_tests.sh
python3 scripts/verify_audit_chain.py
bash scripts/pilot_dry_run.sh
bash scripts/quality_check.sh
bash scripts/release_gate.sh
```

See [docs/INSTALL_UPGRADE.md](docs/INSTALL_UPGRADE.md) for install/upgrade and systemd instructions. Multi-tenant operation is limited to one isolated runtime per tenant; see [docs/TENANT_AND_API_SECURITY.md](docs/TENANT_AND_API_SECURITY.md). See [docs/QUALITY_STATUS.md](docs/QUALITY_STATUS.md) for evidence status and limitations.

---

## Live containment is separately gated

Do not enable live mode during development or routine validation. Any future client deployment requires, at minimum, a real host capability check, an approved client allowlist and Rules of Engagement, signed engagement records, appropriate legal/insurance review, human approval controls, and documented recovery procedures.

See [docs/LEGAL_GATE.md](docs/LEGAL_GATE.md), [docs/GO_LIVE.md](docs/GO_LIVE.md) and [docs/SECURITY_ACCEPTANCE.md](docs/SECURITY_ACCEPTANCE.md).

---

## Documentation

| Document | Purpose |
|---|---|
| [docs/ROADMAP.md](docs/ROADMAP.md) | Engineering completion plan and owner-run validation gates |
| [docs/INSTALL_UPGRADE.md](docs/INSTALL_UPGRADE.md) | Clean install, safe upgrade and systemd deployment |
| [docs/TENANT_AND_API_SECURITY.md](docs/TENANT_AND_API_SECURITY.md) | Tenant runtime boundary and SOC API authentication/RBAC |
| [docs/OVERVIEW.md](docs/OVERVIEW.md) | Product overview |
| [docs/FEATURE_REGISTER.md](docs/FEATURE_REGISTER.md) | Capability status and required proof |
| [docs/QUALITY_STATUS.md](docs/QUALITY_STATUS.md) | Honest quality scorecard |
| [docs/SECURITY_ACCEPTANCE.md](docs/SECURITY_ACCEPTANCE.md) | Security acceptance criteria |
| [docs/IR_RESPONSE_TEAM.md](docs/IR_RESPONSE_TEAM.md) | Incident response workflow |
| [docs/PILOT_DEPLOYMENT.md](docs/PILOT_DEPLOYMENT.md) | Deployment and recovery profiles |
| [docs/LEGAL_GATE.md](docs/LEGAL_GATE.md) | Legal and engagement requirements |
| [docs/GO_LIVE.md](docs/GO_LIVE.md) | Live-mode gate |
| [CHANGELOG.md](CHANGELOG.md) | Release history |
