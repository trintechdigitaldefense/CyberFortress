# CyberFortress — Feature Register

**Baseline:** `hardening/cyberfortress-final-release` @ `eaffd671f5802d2c20b80110f624b9aac0f868bf`  
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
| Incident cases/state machine | `core/ir/cases.py`, `state_machine.py` | IMPLEMENTED_BUT_UNVERIFIED | Full lifecycle, concurrency, tenant isolation and invalid transitions |
| Evidence packages | `core/evidence/pack.py`, reporting agents | IMPLEMENTED_BUT_UNVERIFIED | Hash verification, export, retention and restore tests |
| Audit chain | `core/audit_chain.py` | IMPLEMENTED_BUT_UNVERIFIED | Full-chain verification, concurrent append, tamper/truncation and checkpoint tests |
| Metrics persistence | `core/monitoring_metrics.py` | IMPLEMENTED_BUT_UNVERIFIED | Concurrent writers, atomic replace and storage-failure tests |
| Dashboard authentication/RBAC | `agents/dashboard.py`, `core/soc/rbac.py` | IMPLEMENTED_BUT_UNVERIFIED | Anonymous, role, CSRF, session and privilege-boundary tests |
| WhatsApp approval | `agents/whatsapp_webhook.py`, `core/whatsapp_gateway.py`, `core/defense.py` | PARTIALLY_IMPLEMENTED | Signature interface, nonce expiry, replay and atomic decision tests |
| ROE/sign-off | `core/roe.py`, `core/readiness.py` | PARTIALLY_IMPLEMENTED | Missing/invalid/expired sign-off must deny every live action |
| Autonomy and approval tiers | `core/autonomy.py`, `core/circuit_breaker.py` | IMPLEMENTED_BUT_UNVERIFIED | Driver failure, approval, scope, circuit-breaker and audit tests |
| Firewall containment | `core/containment/*`, `agents/firewall_agent.py` | IMPLEMENTED_BUT_UNVERIFIED | Mocked tests then isolated-VM apply/verify/rollback tests |
| Tenant isolation | `core/tenant.py`, `tenant_guard.py`, SOC RBAC | IMPLEMENTED_BUT_UNVERIFIED | Cross-tenant adversarial tests for every resource/API |
| SIEM/API integration | `core/soc/siem.py`, `agents/siem_bridge_agent.py`, `soc_api_agent.py` | IMPLEMENTED_BUT_UNVERIFIED | Auth, schema, retry, backpressure and delivery tests |
| Playbooks/SOAR | `core/soc/playbooks.py`, `playbooks/*` | IMPLEMENTED_BUT_UNVERIFIED | Dry-run, authorisation, idempotency, timeout and rollback |
| Deployment profiles | `install.sh`, Docker and systemd assets | IMPLEMENTED_BUT_UNVERIFIED | Clean install/upgrade/rollback on each claimed platform |
| Client branding | README text identity; no dedicated image assets found in inspected tree | PARTIALLY_IMPLEMENTED | Approved logo pack, dashboard/report integration and brand review |

## Register maintenance

Update this file whenever a capability changes. A status may advance to IMPLEMENTED only when a linked test/report/CI run proves the acceptance criteria. Never promote a capability based solely on a README or status-document claim.
