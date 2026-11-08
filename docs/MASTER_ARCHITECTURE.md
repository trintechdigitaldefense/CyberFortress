# CyberFortress — Master Architecture Baseline

**Product:** CyberFortress  
**Organisation:** TrinTech Digital Defense  
**Target release:** 1.0.0  
**Baseline branch:** `hardening/cyberfortress-final-release`  
**Baseline commit:** `eaffd671f5802d2c20b80110f624b9aac0f868bf`  
**Status:** Preliminary source-map; implementation and runtime verification remain in progress.

## Product purpose

CyberFortress is intended to provide defensive security monitoring, telemetry processing, incident management, evidence preservation, and controlled response for explicitly authorised client environments. Monitoring is the default. Live containment is a separately gated capability and is not approved merely because code or configuration exists.

## Repository inventory

The inspected Git tree contains **197 tracked files**, not 228. The count is a point-in-time inventory at the baseline commit above.

## Component map

| Layer | Current repository locations | Verification status |
|---|---|---|
| Agent lifecycle | `core/agent_runtime.py`, `core/watchdog.py`, `agents/*` | Implemented source; runtime/agent coverage needs verification |
| Telemetry | `core/telemetry/adapters.py`, `api_connectors.py`, `host_signals.py`, `schema.py`, `fusion.py` | Implemented source; end-to-end data completeness unverified |
| Detection and intelligence | `core/rules.py`, `core/escalation.py`, `core/intelligence.py`, `core/soc/threat_intel.py` | Implemented source; efficacy and feed quality unverified |
| SOC orchestration | `core/soc/event_bus.py`, `metrics.py`, `siem.py`, `playbooks.py`, `auto_defense.py` | Implemented source; integration coverage unverified |
| Incident response | `core/ir/cases.py`, `state_machine.py`, `scoring.py`, `agents/ir_*` | Implemented source; lifecycle acceptance unverified |
| Evidence and audit | `core/evidence/pack.py`, `core/audit_chain.py`, reporting agents | Implemented source; end-to-end integrity and recovery need verification |
| Identity and tenancy | `core/identity/*`, `core/tenant.py`, `core/tenant_guard.py`, `core/soc/rbac.py` | Implemented source; adversarial isolation verification required |
| Response and containment | `core/autonomy.py`, `core/roe.py`, `core/circuit_breaker.py`, `core/containment/*` | Implemented source; live-action safety is NOT accepted |
| Operator interfaces | `agents/dashboard.py`, `dashboard_ui.py`, `soc_api_agent.py`, WhatsApp webhook | Implemented source; security and interface contract tests required |
| Deployment | `install.sh`, `start.sh`, `stop.sh`, `docker/*`, `deploy/systemd/*` | Deployment artifacts exist; supported-host validation required |

## Main data flow (intended)

1. Adapters collect events from configured, authorised sources.
2. Telemetry schema validates and normalises events.
3. Fusion and detection/rules enrich and correlate events.
4. SOC and incident-response components create/update cases.
5. Evidence and audit components preserve attributable records.
6. Response engine evaluates ROE, target scope, approval tier and circuit breaker.
7. Approved response driver executes; result is verified and audited.
8. Dashboard, APIs and reports expose tenant-authorised operational state.

Every transition above must be demonstrated by integration tests before it is called an accepted end-to-end capability.

## Deployment profiles

- **Android Termux / Ubuntu proot:** monitoring and reporting only unless a capability is explicitly tested and supported. Do not assume systemd or host firewall privileges.
- **Dedicated Linux VM:** monitoring; containment remains disabled until host capability, engagement scope, sign-off, approval and rollback checks pass.
- **Docker:** only claim host protection when networking and privileges have been explicitly designed and tested.

## Important baseline discrepancies

- `README.md` reports v0.3.11.
- `VERSION` reports the current 0.6.0-rc1 development track.
- `CHANGELOG.md` and quality documentation must be reconciled to one authoritative release history.
- `docs/HARDENING_STATUS.md` and `docs/QUALITY_STATUS.md` contain completion claims that must be independently verified against code, tests and CI before being retained.

## Verification policy

A source file, documented feature, or passing unit test alone does not establish client readiness. Record implementation, automated test evidence, integration evidence, host/profile limitations, and operational sign-off separately.
