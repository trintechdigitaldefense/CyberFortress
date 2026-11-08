# CyberFortress — Feature Register

**Current hardening checkpoint:** `hardening/cyberfortress-final-release` @ `7bc892b20f7a715bf2900b7c358b32f707b9680b`  
**Purpose:** Distinguish source presence from verified product capability.

Status meanings:
- **IMPLEMENTED:** code is present and required acceptance evidence exists.
- **IMPLEMENTED_BUT_UNVERIFIED:** source exists; required runtime/integration/operational evidence is missing.
- **PARTIALLY_IMPLEMENTED:** only part of the required behaviour is present.
- **NOT_IMPLEMENTED:** no sufficient implementation identified.
- **DEPRECATED:** intentionally retired; replacement documented.

> Initial statuses below are conservative source-review classifications, not a claim that every path has been exhaustively executed.

| Capability | Main implementation | Initial status | Required proof |
|---|---|---|---|
| Agent runtime and watchdog | `core/agent_runtime.py`, `core/watchdog.py` | IMPLEMENTED_BUT_UNVERIFIED | Start/stop/restart, backoff, heartbeat and failure tests |
| Telemetry adapters | `core/telemetry/adapters.py`, `api_connectors.py`, `host_signals.py` | IMPLEMENTED_BUT_UNVERIFIED | Adapter contract tests and synthetic end-to-end events |
| Canonical telemetry schema | `core/telemetry/schema.py` | IMPLEMENTED_BUT_UNVERIFIED | Invalid payload, timestamp, tenant and schema-version tests |
| Telemetry fusion | `core/telemetry/fusion.py` | IMPLEMENTED_BUT_UNVERIFIED | Correlation, dedupe, audit failure and event-loss tests |
| Detection/rules/scoring | `core/rules.py`, `core/escalation.py`, `core/ir/scoring.py` | IMPLEMENTED_BUT_UNVERIFIED | Explainability, precision/false-positive and regression corpus |
| Threat intelligence | `core/soc/threat_intel.py`, `agents/threat_intel_agent.py` | IMPLEMENTED_BUT_UNVERIFIED | Feed validation, freshness, provenance and safe enrichment tests |
| Incident cases/state machine | `core/ir/cases.py`, `state_machine.py` | IMPLEMENTED_BUT_UNVERIFIED | Tenant-scoped storage, path-safe case IDs and valid/invalid lifecycle transitions now pass unit tests; concurrency and all API paths remain |
| Evidence packages | `core/evidence/pack.py`, reporting agents | IMPLEMENTED_BUT_UNVERIFIED | Hash verification, export, retention and restore tests |
| Audit chain | `core/audit_chain.py`, `agents/compliance_logger.py`, `core/telemetry/fusion.py`, `core/whatsapp_gateway.py` | IMPLEMENTED_BUT_UNVERIFIED | Existing-chain verification before append, fsync/permission fail-closed and tamper refusal are tested; multi-process concurrency and external checkpoint remain |
| Metrics persistence | `core/monitoring_metrics.py` | IMPLEMENTED_BUT_UNVERIFIED | Concurrent writers, atomic replace and storage-failure tests |
| Dashboard authentication/RBAC | `agents/dashboard.py`, `core/soc/rbac.py` | IMPLEMENTED_BUT_UNVERIFIED | Tests cover per-user SOC roles, read-only auditor/investigator/viewer, no empty password and anonymous read-only mode; remote deployment/CSRF session review remains |
| WhatsApp approval | `agents/whatsapp_webhook.py`, `core/whatsapp_gateway.py`, `core/defense.py` | IMPLEMENTED_BUT_UNVERIFIED | Unit tests pass for signature, configured startup secrets, nonce expiry, replay and atomic decision; live Meta integration/soak remains |
| ROE/sign-off | `core/roe.py`, `core/readiness.py` | IMPLEMENTED_BUT_UNVERIFIED | Fail-closed missing/invalid sign-off tests pass; full client engagement expiry, scope and revocation acceptance remains |
| Autonomy and approval tiers | `core/autonomy.py`, `core/circuit_breaker.py`, `core/containment/drivers.py` | IMPLEMENTED_BUT_UNVERIFIED | Tests cover driver failure, dry-run vs execution, process termination verification and no force bypass of Tier-2 approval; live isolated-VM proof remains |
| Firewall containment | `core/containment/*`, `agents/firewall_agent.py` | IMPLEMENTED_BUT_UNVERIFIED | Mocked acceptance covers ROE, bidirectional apply verification, partial rollback and read-back failure; isolated-VM apply/verify/rollback still required |
| Tenant isolation | `core/tenant.py`, `tenant_guard.py`, SOC RBAC | IMPLEMENTED_BUT_UNVERIFIED | Cross-tenant adversarial tests for every resource/API |
| SIEM/API integration | `core/soc/siem.py`, `agents/siem_bridge_agent.py`, `soc_api_agent.py` | IMPLEMENTED_BUT_UNVERIFIED | Ingest-token enforcement and trusted tenant stamping pass tests; retry, backpressure and delivery soak remain |
| Playbooks/SOAR | `core/soc/playbooks.py`, `playbooks/*` | IMPLEMENTED_BUT_UNVERIFIED | Dry-run, authorisation, idempotency, timeout and rollback |
| Deployment profiles | `install.sh`, Docker and systemd assets | IMPLEMENTED_BUT_UNVERIFIED | Clean install/upgrade/rollback on each claimed platform |
| Secrets management | `core/secrets_mgmt.py` | IMPLEMENTED_BUT_UNVERIFIED | Secure token generation, private file writes, env rotation and permission checks pass unit tests; operator recovery/rotation drill remains |\n| Client branding | README text identity; no dedicated image assets found in inspected tree | PARTIALLY_IMPLEMENTED | Approved logo pack, dashboard/report integration and brand review |

## Register maintenance

Update this file whenever a capability changes. A status may advance to IMPLEMENTED only when a linked test/report/CI run proves the acceptance criteria. Never promote a capability based solely on a README or status-document claim.


## Current verification checkpoint

CI run [42522541273](https://github.com/trintechdigitaldefense/CyberFortress/actions/runs/42522541273) passed with 128 tests, Ruff, Bandit, pip-audit and repository security checks. This is automated evidence only; rows remain UNVERIFIED where live integration, isolated-VM operation, soak, concurrency or independent review is still outstanding.
